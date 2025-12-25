#property strict
#include <Trade/Trade.mqh>

CTrade trade;

// =====================
// INPUTS
// =====================
input double RiskPercent = 1.0;   // 1% risk
input int    TimerSec    = 5;     // timer interval in seconds

// =====================
// GLOBALS
// =====================
string   TradeSymbol;
datetime lastEntryBarTime = 0;     // track entry bar
datetime lastTrailBarTime = 0;     // track trailing bar

double BuyInitialSL = 0.0;         // store initial BUY SL
double SellInitialSL = 0.0;        // store initial SELL SL

// =====================
// INIT
// =====================
int OnInit()
{
   TradeSymbol = _Symbol;
   if(!SymbolSelect(TradeSymbol, true))
      return INIT_FAILED;

   EventSetTimer(TimerSec);
   return INIT_SUCCEEDED;
}

// =====================
void OnDeinit(const int reason)
{
   EventKillTimer();
}

// =====================
void OnTimer()
{
   HandleEntry();
   HandleReversal();
   HandleTrailing();
}

// ============================================================
// ENTRY LOGIC
// ============================================================
void HandleEntry()
{
   // Only one position at a time
   if(PositionSelect(TradeSymbol))
      return;

   // Get the last closed H3 candle (00:00–03:00)
   datetime barTime = iTime(TradeSymbol, PERIOD_H3, 1);
   if(barTime == 0 || barTime == lastEntryBarTime)
      return;

   lastEntryBarTime = barTime;

   // Confirm this is the 00:00 H3 candle close (03:00 UTC)
   MqlDateTime t;
   TimeToStruct(barTime, t);
   if(t.hour != 0)
      return;

   double open  = iOpen (TradeSymbol, PERIOD_H3, 1);
   double close = iClose(TradeSymbol, PERIOD_H3, 1);
   double low   = iLow  (TradeSymbol, PERIOD_H3, 1);
   double high  = iHigh (TradeSymbol, PERIOD_H3, 1);

   trade.SetDeviationInPoints(20);
   trade.SetTypeFillingBySymbol(TradeSymbol);

   // ---------------- BUY ----------------
   if(close > open)
   {
      double entry = SymbolInfoDouble(TradeSymbol, SYMBOL_ASK);
      double sl    = low;
      double vol   = CalculateRiskVolume(entry, sl);
      if(vol > 0)
      {
         if(trade.Buy(vol, TradeSymbol, entry, sl, 0.0))
            BuyInitialSL = sl; // store initial SL
      }
   }

   // ---------------- SELL ----------------
   if(close < open)
   {
      double entry = SymbolInfoDouble(TradeSymbol, SYMBOL_BID);
      double sl    = high;
      double vol   = CalculateRiskVolume(entry, sl);
      if(vol > 0)
      {
         if(trade.Sell(vol, TradeSymbol, entry, sl, 0.0))
            SellInitialSL = sl; // store initial SL
      }
   }
}

// ============================================================
// REVERSAL LOGIC (ONLY IF INITIAL SL HIT)
// ============================================================
void HandleReversal()
{
   double bid = SymbolInfoDouble(TradeSymbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(TradeSymbol, SYMBOL_ASK);

   // ---------- BUY Reversal ----------
   if(BuyInitialSL > 0 && !PositionSelect(TradeSymbol))
   {
      if(bid <= BuyInitialSL) // BUY SL hit
      {
         datetime firstBullishBarTime = FindFirstBullishH3From0();
         if(firstBullishBarTime > 0)
         {
            int shift = iBarShift(TradeSymbol, PERIOD_H3, firstBullishBarTime);
            double sl = iHigh(TradeSymbol, PERIOD_H3, shift);
            double vol = CalculateRiskVolume(bid, sl);
            if(vol > 0)
            {
               if(trade.Sell(vol, TradeSymbol, bid, sl, 0.0))
                  BuyInitialSL = 0.0; // reset
            }
         }
      }
   }

   // ---------- SELL Reversal ----------
   if(SellInitialSL > 0 && !PositionSelect(TradeSymbol))
   {
      if(ask >= SellInitialSL) // SELL SL hit
      {
         datetime firstBearishBarTime = FindFirstBearishH3From0();
         if(firstBearishBarTime > 0)
         {
            int shift = iBarShift(TradeSymbol, PERIOD_H3, firstBearishBarTime);
            double sl = iLow(TradeSymbol, PERIOD_H3, shift);
            double vol = CalculateRiskVolume(ask, sl);
            if(vol > 0)
            {
               if(trade.Buy(vol, TradeSymbol, ask, sl, 0.0))
                  SellInitialSL = 0.0; // reset
            }
         }
      }
   }
}

// ============================================================
// TRAILING LOGIC (STRICT RULES)
// ============================================================
void HandleTrailing()
{
   if(!PositionSelect(TradeSymbol))
      return;

   // Trailing only after H3 candle closes
   datetime barTime = iTime(TradeSymbol, PERIOD_H3, 1);
   if(barTime == 0 || barTime == lastTrailBarTime)
      return;

   lastTrailBarTime = barTime;

   long   type      = PositionGetInteger(POSITION_TYPE);
   double currentSL = PositionGetDouble(POSITION_SL);

   double open  = iOpen (TradeSymbol, PERIOD_H3, 1);
   double close = iClose(TradeSymbol, PERIOD_H3, 1);
   double low   = iLow  (TradeSymbol, PERIOD_H3, 1);
   double high  = iHigh (TradeSymbol, PERIOD_H3, 1);

   // ---------------- BUY ----------------
   if(type == POSITION_TYPE_BUY)
   {
      // Only trail on bullish H3 candle low
      if(close > open && low > currentSL)
      {
         trade.PositionModify(TradeSymbol, low, 0.0);
      }
   }

   // ---------------- SELL ----------------
   if(type == POSITION_TYPE_SELL)
   {
      // Only trail on bearish H3 candle high
      if(close < open && high < currentSL)
      {
         trade.PositionModify(TradeSymbol, high, 0.0);
      }
   }
}

// ============================================================
// RISK-BASED LOT CALCULATION
// ============================================================
double CalculateRiskVolume(double entry, double stop)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt = balance * (RiskPercent / 100.0);

   double tickSize  = SymbolInfoDouble(TradeSymbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(TradeSymbol, SYMBOL_TRADE_TICK_VALUE);

   double distance = MathAbs(entry - stop);
   if(distance <= 0)
      return 0;

   double costPerLot = (distance / tickSize) * tickValue;
   if(costPerLot <= 0)
      return 0;

   double volume = riskAmt / costPerLot;

   double minLot  = SymbolInfoDouble(TradeSymbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(TradeSymbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(TradeSymbol, SYMBOL_VOLUME_STEP);

   volume = MathFloor(volume / stepLot) * stepLot;
   volume = MathMax(volume, minLot);
   volume = MathMin(volume, maxLot);

   return volume;
}

// ============================================================
// HELPER FUNCTIONS TO FIND FIRST H3 BULLISH/BEARISH BAR FROM 0:00
// ============================================================
datetime FindFirstBullishH3From0()
{
   MqlDateTime t;
   datetime today = iTime(TradeSymbol, PERIOD_D1, 0);
   TimeToStruct(today, t);
   datetime start = StructToTime(t);

   for(int i=0; i<50; i++)
   {
      datetime bar = iTime(TradeSymbol, PERIOD_H3, i);
      if(bar < start) break;
      double open = iOpen(TradeSymbol, PERIOD_H3, i);
      double close = iClose(TradeSymbol, PERIOD_H3, i);
      if(close > open) return bar;
   }
   return 0;
}

datetime FindFirstBearishH3From0()
{
   MqlDateTime t;
   datetime today = iTime(TradeSymbol, PERIOD_D1, 0);
   TimeToStruct(today, t);
   datetime start = StructToTime(t);

   for(int i=0; i<50; i++)
   {
      datetime bar = iTime(TradeSymbol, PERIOD_H3, i);
      if(bar < start) break;
      double open = iOpen(TradeSymbol, PERIOD_H3, i);
      double close = iClose(TradeSymbol, PERIOD_H3, i);
      if(close < open) return bar;
   }
   return 0;
}
