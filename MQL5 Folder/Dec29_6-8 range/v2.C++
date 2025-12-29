//+------------------------------------------------------------------+
//|                                     RangeBreakout_Visual_M3.mq5  |
//|                                  Copyright 2023, Gemini AI Asst. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Gemini AI"
#property link      "https://www.mql5.com"
#property version   "1.10"
#property strict

//--- Include Standard Library for easier trade execution
#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
input group "Risk Management"
input double   InpRiskPercent    = 1.0;      // Risk per trade (% of Balance)
input int      InpRewardRatio    = 10;       // Reward Ratio (TP = 10 * Risk)

input group "Time Settings"
input int      InpRangeStartHour = 22;       // Range Start Hour (UTC equivalent)
input int      InpRangeEndHour   = 0;        // Range End Hour (0 = Midnight)
input int      InpBrokerOffset   = 0;        // Broker Time Offset from UTC

input group "Visuals"
input bool     InpDrawRange      = true;     // Draw Range Box on Chart
input color    InpBoxColor       = clrLavender; // Color of the Range Box

input group "System"
input ulong    InpMagicNum       = 123456;   // Magic Number

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade         trade;
datetime       lastBarTime       = 0;
bool           tradeTakenToday   = false;
int            lastTradeDay      = -1;
string         rangeObjName      = "Range_Box_Visual";

// Structure to hold Range Data
struct RangeData {
   double   HHR;        // Highest High of Range
   double   LLR;        // Lowest Low of Range
   datetime timeHHR;    // Time of HHR (EP)
   datetime timeLLR;    // Time of LLR (EP)
   bool     isValid;    // Is range calculated?
};

RangeData currentRange;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNum);
   
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      Print("Warning: AutoTrading is disabled in Terminal.");
      
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Cleanup drawing objects when EA is removed
   if(ObjectFind(0, rangeObjName) >= 0) {
      ObjectDelete(0, rangeObjName);
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_M3, 0);
   if(currentBarTime == lastBarTime) return; // Wait for candle close
   lastBarTime = currentBarTime;

   // Reset Daily Flags
   MqlDateTime dt;
   TimeCurrent(dt);
   
   if(lastTradeDay != dt.day) {
      tradeTakenToday = false;
      lastTradeDay = dt.day;
      currentRange.isValid = false; 
      // Optional: Delete yesterday's box to keep chart clean
      if(ObjectFind(0, rangeObjName) >= 0) ObjectDelete(0, rangeObjName);
   }

   if(tradeTakenToday) return;

   // Calculate Range if not yet done
   if(!currentRange.isValid) {
      CalculateRange();
   }

   if(currentRange.isValid) {
      CheckBreakoutSignal();
   }
}

//+------------------------------------------------------------------+
//| Function to Calculate HHR and LLR                                |
//+------------------------------------------------------------------+
void CalculateRange()
{
   MqlDateTime dt;
   TimeCurrent(dt);

   int startHour = InpRangeStartHour + InpBrokerOffset;
   int endHour   = InpRangeEndHour + InpBrokerOffset;
   
   if(startHour >= 24) startHour -= 24;
   if(endHour >= 24) endHour -= 24;

   // Calculate specific time range (Yesterday 22:00 to Today 00:00)
   datetime timeEnd   = StringToTime(StringFormat("%04d.%02d.%02d %02d:00", dt.year, dt.mon, dt.day, endHour));
   datetime timeStart = timeEnd - (2 * 3600); // 2 hours duration
   
   // Check if the current time is actually past the range end
   if(TimeCurrent() < timeEnd) return; 

   // Get Bars inside the range
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   int copied = CopyRates(_Symbol, PERIOD_M3, timeStart, timeEnd, rates);
   
   if(copied > 0) {
      double highest = -DBL_MAX;
      double lowest  = DBL_MAX;
      datetime tHigh = 0;
      datetime tLow  = 0;

      for(int i=0; i<copied; i++) {
         if(rates[i].high > highest) {
            highest = rates[i].high;
            tHigh   = rates[i].time;
         }
         if(rates[i].low < lowest) {
            lowest = rates[i].low;
            tLow   = rates[i].time;
         }
      }
      
      currentRange.HHR = highest;
      currentRange.LLR = lowest;
      currentRange.timeHHR = tHigh;
      currentRange.timeLLR = tLow;
      currentRange.isValid = true;
      
      // DRAW THE RANGE
      if(InpDrawRange) {
         DrawRangeBox(timeStart, timeEnd, currentRange.HHR, currentRange.LLR);
      }
   }
}

//+------------------------------------------------------------------+
//| Function to Draw the Range Box                                   |
//+------------------------------------------------------------------+
void DrawRangeBox(datetime t1, datetime t2, double priceHigh, double priceLow)
{
   // Delete if exists to update
   if(ObjectFind(0, rangeObjName) >= 0) ObjectDelete(0, rangeObjName);

   // Create Rectangle
   if(ObjectCreate(0, rangeObjName, OBJ_RECTANGLE, 0, t1, priceHigh, t2, priceLow)) {
      ObjectSetInteger(0, rangeObjName, OBJPROP_COLOR, InpBoxColor);
      ObjectSetInteger(0, rangeObjName, OBJPROP_FILL, true);      // Fill the box
      ObjectSetInteger(0, rangeObjName, OBJPROP_BACK, true);      // Put behind candles
      ObjectSetInteger(0, rangeObjName, OBJPROP_WIDTH, 1);
      ObjectSetString(0, rangeObjName, OBJPROP_TEXT, "Daily Range");
   }
}

//+------------------------------------------------------------------+
//| Function to Check Breakout & Validation                          |
//+------------------------------------------------------------------+
void CheckBreakoutSignal()
{
   MqlRates bcc[];
   ArraySetAsSeries(bcc, true);
   if(CopyRates(_Symbol, PERIOD_M3, 1, 1, bcc) != 1) return;

   double bccClose = bcc[0].close;
   double bccHigh  = bcc[0].high;
   double bccLow   = bcc[0].low;
   datetime bccTime = bcc[0].time;

   // --- BUY LOGIC ---
   if(bccClose > currentRange.HHR) {
      if(IsPathClear(currentRange.timeHHR, bccTime, currentRange.HHR, true)) {
         
         double sl = bccLow;
         double riskDist = bccClose - sl;
         
         if(riskDist <= 0) return;
         
         double tp = bccClose + (riskDist * InpRewardRatio);
         double lotSize = CalculateLotSize(MathAbs(bccClose - sl));
         
         if(trade.Buy(lotSize, _Symbol, bccClose, sl, tp, "Range Breakout Buy")) {
            tradeTakenToday = true;
         }
      }
   }
   
   // --- SELL LOGIC ---
   else if(bccClose < currentRange.LLR) {
      if(IsPathClear(currentRange.timeLLR, bccTime, currentRange.LLR, false)) {
         
         double sl = bccHigh;
         double riskDist = sl - bccClose;
         
         if(riskDist <= 0) return;
         
         double tp = bccClose - (riskDist * InpRewardRatio);
         double lotSize = CalculateLotSize(MathAbs(sl - bccClose));
         
         if(trade.Sell(lotSize, _Symbol, bccClose, sl, tp, "Range Breakout Sell")) {
            tradeTakenToday = true;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Filter: Verify no touches between EP and BCC                     |
//+------------------------------------------------------------------+
bool IsPathClear(datetime startTime, datetime endTime, double level, bool isBuy)
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   int count = CopyRates(_Symbol, PERIOD_M3, startTime, endTime, rates);
   
   // Loop excludes start (EP) and end (BCC)
   for(int i = 1; i < count - 1; i++) {
      if(isBuy) {
         if(rates[i].high >= level) return false;
      } else {
         if(rates[i].low <= level) return false;
      }
   }
   return true;
}

//+------------------------------------------------------------------+
//| Risk Management                                                  |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDistancePrice)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = balance * (InpRiskPercent / 100.0);
   
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   
   if(tickSize == 0 || tickValue == 0 || slDistancePrice == 0) return 0.01;
   
   double slPoints = slDistancePrice / tickSize;
   double lotSize = riskMoney / (slPoints * tickValue);
   
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathFloor(lotSize / stepLot) * stepLot;
   
   if(lotSize < minLot) lotSize = minLot;
   if(lotSize > maxLot) lotSize = maxLot;
   
   return lotSize;
}
//+------------------------------------------------------------------+