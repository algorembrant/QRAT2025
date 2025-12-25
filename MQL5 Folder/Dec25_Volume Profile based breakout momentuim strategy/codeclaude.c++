//+------------------------------------------------------------------+
//|                                          VolumeProfileTradingEA.mq5 |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Volume Profile Trading EA"
#property version   "1.00"
#property strict

input double   RiskPercent = 1.0;              // Risk per trade (%)
input int      SpreadMultiplier = 10;          // Minimum SL = Spread x This
input double   ValueAreaPercent = 0.70;        // Value Area (70%)
input double   PriceStepForVP = 0.10;          // Price step for volume profile

// Global variables
datetime g_lastTradeHour = 0;                  // Track last trade hour
double g_cumVolume[];                          // Cumulative volume by price
double g_priceLevels[];                        // Price levels array
int g_volumeSize = 0;                          // Size of volume arrays

struct SessionData {
   datetime startTime;
   datetime currentTime;
   double poc;
   double vah;
   double val;
   bool isValid;
};

SessionData g_currentSession;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
   Print("Volume Profile Trading EA initialized");
   
   // Initialize session
   g_currentSession.isValid = false;
   g_lastTradeHour = 0;
   
   // Reserve array space
   ArrayResize(g_cumVolume, 10000);
   ArrayResize(g_priceLevels, 10000);
   ArrayFill(g_cumVolume, 0, 10000, 0.0);
   g_volumeSize = 0;
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
   Print("EA deinitialized: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
   datetime currentTime = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(currentTime, dt);
   
   // Detect new trading session (gap detection)
   if(IsNewTradingSession(currentTime)) {
      ResetSession(currentTime);
   }
   
   // Update developing POC/VAH/VAL with each new bar
   if(IsNewBar()) {
      UpdateVolumeProfile();
      
      // Check trading conditions on bar close
      CheckTradingSignals();
   }
}

//+------------------------------------------------------------------+
//| Detect new trading session based on time gaps                    |
//+------------------------------------------------------------------+
bool IsNewTradingSession(datetime currentTime) {
   static datetime lastBarTime = 0;
   
   if(lastBarTime == 0) {
      lastBarTime = currentTime;
      return true;
   }
   
   // Detect gap larger than normal bar interval
   int barInterval = PeriodSeconds();
   long timeDiff = currentTime - lastBarTime;
   
   lastBarTime = currentTime;
   
   // If gap is more than 2x normal interval, it's a new session
   if(timeDiff > barInterval * 2) {
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Reset session data                                               |
//+------------------------------------------------------------------+
void ResetSession(datetime startTime) {
   g_currentSession.startTime = startTime;
   g_currentSession.currentTime = startTime;
   g_currentSession.isValid = false;
   
   // Clear cumulative volume
   ArrayFill(g_cumVolume, 0, ArraySize(g_cumVolume), 0.0);
   g_volumeSize = 0;
   
   Print("New trading session started at: ", TimeToString(startTime));
}

//+------------------------------------------------------------------+
//| Check if new bar formed                                          |
//+------------------------------------------------------------------+
bool IsNewBar() {
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   
   if(currentBarTime != lastBarTime) {
      lastBarTime = currentBarTime;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Update developing volume profile                                 |
//+------------------------------------------------------------------+
void UpdateVolumeProfile() {
   int bar = 0;
   double high = iHigh(_Symbol, PERIOD_CURRENT, bar);
   double low = iLow(_Symbol, PERIOD_CURRENT, bar);
   long volume = iVolume(_Symbol, PERIOD_CURRENT, bar);
   
   if(volume <= 0) return;
   
   // Distribute volume across price levels
   double priceStep = PriceStepForVP;
   int numLevels = (int)MathCeil((high - low) / priceStep) + 1;
   
   if(numLevels <= 0) numLevels = 1;
   
   double volPerLevel = (double)volume / numLevels;
   
   for(double p = low; p <= high + 0.001; p += priceStep) {
      double priceLevel = NormalizeDouble(p, 2);
      AddVolumeToLevel(priceLevel, volPerLevel);
   }
   
   // Calculate POC, VAH, VAL
   CalculateVolumeProfileLevels();
}

//+------------------------------------------------------------------+
//| Add volume to specific price level                               |
//+------------------------------------------------------------------+
void AddVolumeToLevel(double price, double volume) {
   // Find if price level exists
   int index = -1;
   for(int i = 0; i < g_volumeSize; i++) {
      if(MathAbs(g_priceLevels[i] - price) < 0.001) {
         index = i;
         break;
      }
   }
   
   if(index >= 0) {
      g_cumVolume[index] += volume;
   } else {
      // Add new level
      if(g_volumeSize < ArraySize(g_cumVolume)) {
         g_priceLevels[g_volumeSize] = price;
         g_cumVolume[g_volumeSize] = volume;
         g_volumeSize++;
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate POC, VAH, VAL from cumulative volume                   |
//+------------------------------------------------------------------+
void CalculateVolumeProfileLevels() {
   if(g_volumeSize == 0) return;
   
   // Find POC (Point of Control - highest volume)
   int pocIndex = 0;
   double maxVolume = g_cumVolume[0];
   
   for(int i = 1; i < g_volumeSize; i++) {
      if(g_cumVolume[i] > maxVolume) {
         maxVolume = g_cumVolume[i];
         pocIndex = i;
      }
   }
   
   g_currentSession.poc = g_priceLevels[pocIndex];
   
   // Calculate total volume
   double totalVolume = 0;
   for(int i = 0; i < g_volumeSize; i++) {
      totalVolume += g_cumVolume[i];
   }
   
   // Calculate Value Area (70% of volume around POC)
   double targetVolume = totalVolume * ValueAreaPercent;
   double cumVol = g_cumVolume[pocIndex];
   
   int loIndex = pocIndex;
   int hiIndex = pocIndex;
   
   while(cumVol < targetVolume && (loIndex > 0 || hiIndex < g_volumeSize - 1)) {
      bool expandLow = false;
      bool expandHigh = false;
      
      if(loIndex > 0) expandLow = true;
      if(hiIndex < g_volumeSize - 1) expandHigh = true;
      
      if(expandLow && expandHigh) {
         // Expand to side with more volume
         if(g_cumVolume[loIndex - 1] > g_cumVolume[hiIndex + 1]) {
            loIndex--;
            cumVol += g_cumVolume[loIndex];
         } else {
            hiIndex++;
            cumVol += g_cumVolume[hiIndex];
         }
      } else if(expandLow) {
         loIndex--;
         cumVol += g_cumVolume[loIndex];
      } else if(expandHigh) {
         hiIndex++;
         cumVol += g_cumVolume[hiIndex];
      }
   }
   
   g_currentSession.vah = g_priceLevels[hiIndex];
   g_currentSession.val = g_priceLevels[loIndex];
   g_currentSession.isValid = true;
   g_currentSession.currentTime = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Check for trading signals                                        |
//+------------------------------------------------------------------+
void CheckTradingSignals() {
   if(!g_currentSession.isValid) return;
   
   // Only one trade per whole trading hour
   datetime currentTime = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(currentTime, dt);
   
   datetime currentHour = StringToTime(StringFormat("%04d.%02d.%02d %02d:00", 
                                       dt.year, dt.mon, dt.day, dt.hour));
   
   if(g_lastTradeHour == currentHour) {
      return; // Already traded this hour
   }
   
   // Check if we already have an open position
   if(PositionSelect(_Symbol)) {
      return; // Position already open
   }
   
   // Get latest closed candle
   int bar = 1;
   double close = iClose(_Symbol, PERIOD_CURRENT, bar);
   double high = iHigh(_Symbol, PERIOD_CURRENT, bar);
   double low = iLow(_Symbol, PERIOD_CURRENT, bar);
   double open = iOpen(_Symbol, PERIOD_CURRENT, bar);
   
   // Determine body boundaries
   double bodyHigh = MathMax(open, close);
   double bodyLow = MathMin(open, close);
   
   // Check if POC is between candle body (for exit check if position exists)
   // This will be handled in position management
   
   // Trading logic
   bool buySignal = false;
   bool sellSignal = false;
   double sl = 0;
   
   // Buy signal: Close above VAH
   if(close > g_currentSession.vah) {
      buySignal = true;
      sl = low;
   }
   
   // Sell signal: Close below VAL
   if(close < g_currentSession.val) {
      sellSignal = true;
      sl = high;
   }
   
   // Execute trades
   if(buySignal) {
      double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double slDistance = currentPrice - sl;
      
      // Check minimum SL distance
      if(slDistance >= spread * SpreadMultiplier) {
         OpenBuyTrade(currentPrice, sl);
         g_lastTradeHour = currentHour;
      }
   } else if(sellSignal) {
      double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      double slDistance = sl - currentPrice;
      
      // Check minimum SL distance
      if(slDistance >= spread * SpreadMultiplier) {
         OpenSellTrade(currentPrice, sl);
         g_lastTradeHour = currentHour;
      }
   }
   
   // Check exit conditions for existing positions
   CheckExitConditions(bodyLow, bodyHigh);
}

//+------------------------------------------------------------------+
//| Open Buy Trade with 1% risk                                      |
//+------------------------------------------------------------------+
void OpenBuyTrade(double price, double sl) {
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (RiskPercent / 100.0);
   double slDistance = price - sl;
   
   if(slDistance <= 0) return;
   
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   
   double lotSize = (riskAmount * tickSize) / (slDistance * tickValue);
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   lotSize = MathMax(lotSize, minLot);
   lotSize = MathMin(lotSize, maxLot);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lotSize;
   request.type = ORDER_TYPE_BUY;
   request.price = price;
   request.sl = sl;
   request.tp = 0; // Dynamic TP based on POC
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "VP Buy";
   
   if(OrderSend(request, result)) {
      Print("Buy order opened: ", result.order, " at ", price);
   } else {
      Print("Buy order failed: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Open Sell Trade with 1% risk                                     |
//+------------------------------------------------------------------+
void OpenSellTrade(double price, double sl) {
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * (RiskPercent / 100.0);
   double slDistance = sl - price;
   
   if(slDistance <= 0) return;
   
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   
   double lotSize = (riskAmount * tickSize) / (slDistance * tickValue);
   lotSize = MathFloor(lotSize / lotStep) * lotStep;
   lotSize = MathMax(lotSize, minLot);
   lotSize = MathMin(lotSize, maxLot);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lotSize;
   request.type = ORDER_TYPE_SELL;
   request.price = price;
   request.sl = sl;
   request.tp = 0; // Dynamic TP based on POC
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "VP Sell";
   
   if(OrderSend(request, result)) {
      Print("Sell order opened: ", result.order, " at ", price);
   } else {
      Print("Sell order failed: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Check exit conditions based on POC crossing candle body          |
//+------------------------------------------------------------------+
void CheckExitConditions(double bodyLow, double bodyHigh) {
   if(!PositionSelect(_Symbol)) return;
   
   // Check if POC is between candle body
   if(g_currentSession.poc >= bodyLow && g_currentSession.poc <= bodyHigh) {
      // Close position
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = PositionGetDouble(POSITION_VOLUME);
      request.deviation = 10;
      request.magic = 123456;
      
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) {
         request.type = ORDER_TYPE_SELL;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      } else {
         request.type = ORDER_TYPE_BUY;
         request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      }
      
      if(OrderSend(request, result)) {
         Print("Position closed: POC crossed candle body");
      }
   }
}
//+------------------------------------------------------------------+