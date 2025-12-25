#property strict
#include <Trade/Trade.mqh>

CTrade trade;

// =====================
// INPUTS
// =====================
input double RiskPercent = 1.0;   // 1% risk per trade
input int    TimerSec    = 5;     // timer interval in seconds

// =====================
// SYMBOL LIST
// =====================
string Symbols[] = {
   "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc",
   "CADJPYc","CHFJPYc","EURAUDc","EURCADc","EURCHFc","EURGBPc",
   "EURJPYc","EURNZDc","EURUSDc","GBPAUDc","GBPCADc","GBPCHFc",
   "GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
   "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
};

// =====================
// STATE STRUCT
// =====================
struct SymbolState
{
   datetime lastEntryBarTime;
   datetime lastTrailBarTime;
   double   BuyInitialSL;
   double   SellInitialSL;
};

SymbolState States[];

// =====================
// INIT
// =====================
int OnInit()
{
   ArrayResize(States, ArraySize(Symbols));

   // Select symbols
   for(int i=0; i<ArraySize(Symbols); i++)
   {
      SymbolSelect(Symbols[i], true);
   }

   EventSetTimer(TimerSec);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTimer()
{
   for(int i=0; i<ArraySize(Symbols); i++)
   {
      string sym = Symbols[i];
      HandleEntry(sym, i);
      HandleReversal(sym, i);
      HandleTrailing(sym, i);
   }
}

// ============================================================
// ENTRY LOGIC
// ============================================================
void HandleEntry(string sym, int idx)
{
   if(PositionSelect(sym))
      return;

   datetime barTime = iTime(sym, PERIOD_H3, 1);
   if(barTime == 0 || barTime == States[idx].lastEntryBarTime)
      return;

   States[idx].lastEntryBarTime = barTime;

   MqlDateTime t;
   TimeToStruct(barTime, t);
   if(t.hour != 0) return;

   double open  = iOpen(sym, PERIOD_H3, 1);
   double close = iClose(sym, PERIOD_H3, 1);
   double low   = iLow(sym, PERIOD_H3, 1);
   double high  = iHigh(sym, PERIOD_H3, 1);

   trade.SetDeviationInPoints(20);
   trade.SetTypeFillingBySymbol(sym);

   // ---------------- BUY ----------------
   if(close > open)
   {
      double entry = SymbolInfoDouble(sym, SYMBOL_ASK);
      double sl    = low;
      double vol   = CalculateRiskVolume(sym, entry, sl);
      if(vol > 0 && trade.Buy(vol, sym, entry, sl, 0.0))
         States[idx].BuyInitialSL = sl;
   }

   // ---------------- SELL ----------------
   if(close < open)
   {
      double entry = SymbolInfoDouble(sym, SYMBOL_BID);
      double sl    = high;
      double vol   = CalculateRiskVolume(sym, entry, sl);
      if(vol > 0 && trade.Sell(vol, sym, entry, sl, 0.0))
         States[idx].SellInitialSL = sl;
   }
}

// ============================================================
// REVERSAL LOGIC
// ============================================================
void HandleReversal(string sym, int idx)
{
   double bid = SymbolInfoDouble(sym, SYMBOL_BID);
   double ask = SymbolInfoDouble(sym, SYMBOL_ASK);

   // ---------- BUY Reversal ----------
   if(States[idx].BuyInitialSL > 0 && !PositionSelect(sym))
   {
      if(bid <= States[idx].BuyInitialSL)
      {
         datetime firstBullishBarTime = FindFirstBullishH3From0(sym);
         if(firstBullishBarTime > 0)
         {
            int shift = iBarShift(sym, PERIOD_H3, firstBullishBarTime);
            double sl = iHigh(sym, PERIOD_H3, shift);
            double vol = CalculateRiskVolume(sym, bid, sl);
            if(vol > 0 && trade.Sell(vol, sym, bid, sl, 0.0))
               States[idx].BuyInitialSL = 0.0;
         }
      }
   }

   // ---------- SELL Reversal ----------
   if(States[idx].SellInitialSL > 0 && !PositionSelect(sym))
   {
      if(ask >= States[idx].SellInitialSL)
      {
         datetime firstBearishBarTime = FindFirstBearishH3From0(sym);
         if(firstBearishBarTime > 0)
         {
            int shift = iBarShift(sym, PERIOD_H3, firstBearishBarTime);
            double sl = iLow(sym, PERIOD_H3, shift);
            double vol = CalculateRiskVolume(sym, ask, sl);
            if(vol > 0 && trade.Buy(vol, sym, ask, sl, 0.0))
               States[idx].SellInitialSL = 0.0;
         }
      }
   }
}

// ============================================================
// TRAILING LOGIC
// ============================================================
void HandleTrailing(string sym, int idx)
{
   if(!PositionSelect(sym)) return;

   datetime barTime = iTime(sym, PERIOD_H3, 1);
   if(barTime == 0 || barTime == States[idx].lastTrailBarTime) return;

   States[idx].lastTrailBarTime = barTime;

   long type = PositionGetInteger(POSITION_TYPE);
   double currentSL = PositionGetDouble(POSITION_SL);

   double open  = iOpen(sym, PERIOD_H3, 1);
   double close = iClose(sym, PERIOD_H3, 1);
   double low   = iLow(sym, PERIOD_H3, 1);
   double high  = iHigh(sym, PERIOD_H3, 1);

   // ---------------- BUY ----------------
   if(type == POSITION_TYPE_BUY)
   {
      if(close > open && low > currentSL)
         trade.PositionModify(sym, low, 0.0);
   }

   // ---------------- SELL ----------------
   if(type == POSITION_TYPE_SELL)
   {
      if(close < open && high < currentSL)
         trade.PositionModify(sym, high, 0.0);
   }
}

// ============================================================
// RISK CALCULATION
// ============================================================
double CalculateRiskVolume(string sym, double entry, double stop)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt = balance * (RiskPercent / 100.0);

   double tickSize  = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);

   double distance = MathAbs(entry - stop);
   if(distance <= 0) return 0;

   double costPerLot = (distance / tickSize) * tickValue;
   if(costPerLot <= 0) return 0;

   double volume = riskAmt / costPerLot;

   double minLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);

   volume = MathFloor(volume / stepLot) * stepLot;
   volume = MathMax(volume, minLot);
   volume = MathMin(volume, maxLot);

   return volume;
}

// ============================================================
// HELPERS TO FIND FIRST H3 BULLISH/BEARISH BAR FROM 0:00
// ============================================================
datetime FindFirstBullishH3From0(string sym)
{
   MqlDateTime t;
   datetime today = iTime(sym, PERIOD_D1, 0);
   TimeToStruct(today, t);
   datetime start = StructToTime(t);

   for(int i=0; i<50; i++)
   {
      datetime bar = iTime(sym, PERIOD_H3, i);
      if(bar < start) break;
      double open = iOpen(sym, PERIOD_H3, i);
      double close = iClose(sym, PERIOD_H3, i);
      if(close > open) return bar;
   }
   return 0;
}

datetime FindFirstBearishH3From0(string sym)
{
   MqlDateTime t;
   datetime today = iTime(sym, PERIOD_D1, 0);
   TimeToStruct(today, t);
   datetime start = StructToTime(t);

   for(int i=0; i<50; i++)
   {
      datetime bar = iTime(sym, PERIOD_H3, i);
      if(bar < start) break;
      double open = iOpen(sym, PERIOD_H3, i);
      double close = iClose(sym, PERIOD_H3, i);
      if(close < open) return bar;
   }
   return 0;
}
