#property strict
#include <Trade/Trade.mqh>

CTrade trade;

// =====================
// INPUTS
// =====================
input double RiskPercent = 1.0;   // 1% risk per trade
input int    TimerSec    = 5;     // timer interval in seconds

// =====================
// GLOBALS
// =====================
string   TradeSymbol;
datetime lastEntryBarTime   = 0; // track last original entry bar
datetime lastTrailBarTime   = 0; // track last trailing bar
bool     originalEntryDone  = false; // flag for original entry per day
bool     originalEntryLoss  = false; // true if original entry closed at loss
bool     reverseEntryDone   = false; // flag for reverse entry per day
long     originalEntryType  = -1;    // POSITION_TYPE_BUY or POSITION_TYPE_SELL
double   initialSL          = 0.0;   // store initial SL
ulong    originalTicket     = 0;     // ticket of original entry

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
    ResetFlags();      // reset daily flags if new day
    HandleEntry();
    HandleReverseEntry();
    HandleTrailing();
    CheckOriginalTradeProfit();
}

// ============================================================
// ORIGINAL ENTRY LOGIC
// ============================================================
void HandleEntry()
{
    if(PositionSelect(TradeSymbol) || originalEntryDone)
        return;

    datetime barTime = iTime(TradeSymbol, PERIOD_H3, 1);
    if(barTime == 0 || barTime == lastEntryBarTime)
        return;

    lastEntryBarTime = barTime;

    MqlDateTime t;
    TimeToStruct(barTime, t);
    if(t.hour != 0) // only 0:00–3:00 H3 candle
        return;

    double open  = iOpen(TradeSymbol, PERIOD_H3, 1);
    double close = iClose(TradeSymbol, PERIOD_H3, 1);
    double low   = iLow(TradeSymbol, PERIOD_H3, 1);
    double high  = iHigh(TradeSymbol, PERIOD_H3, 1);

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
            {
                initialSL = sl;
                originalEntryDone = true;
                originalEntryType = POSITION_TYPE_BUY;
                originalTicket = trade.ResultOrder(); // store ticket
            }
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
            {
                initialSL = sl;
                originalEntryDone = true;
                originalEntryType = POSITION_TYPE_SELL;
                originalTicket = trade.ResultOrder(); // store ticket
            }
        }
    }
}

// ============================================================
// CHECK IF ORIGINAL TRADE CLOSED IN LOSS OR PROFIT
// ============================================================
void CheckOriginalTradeProfit()
{
    if(!originalEntryDone || originalTicket == 0)
        return;

    // Check if original trade exists
    if(!PositionSelect(TradeSymbol))
        return;

    long type = PositionGetInteger(POSITION_TYPE);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);

    double profit = 0.0;
    if(type == POSITION_TYPE_BUY)
        profit = currentPrice - openPrice;
    else if(type == POSITION_TYPE_SELL)
        profit = openPrice - currentPrice;

    if(profit > 0)
        originalEntryLoss = false; // profitable → reverse-entry disabled
    else
        originalEntryLoss = true;  // loss → reverse-entry possible
}

// ============================================================
// REVERSE ENTRY LOGIC (IMMEDIATE ON LOSS, SL FROM PREVIOUS CANDLE)
// ============================================================
void HandleReverseEntry()
{
    if(reverseEntryDone || !originalEntryDone || !originalEntryLoss)
        return;

    if(!PositionSelect(TradeSymbol))
    {
        // Current H3 candle (position = 0)
        double open0  = iOpen(TradeSymbol, PERIOD_H3, 0);
        double close0 = iClose(TradeSymbol, PERIOD_H3, 0);
        double low0   = iLow(TradeSymbol, PERIOD_H3, 0);
        double high0  = iHigh(TradeSymbol, PERIOD_H3, 0);

        // Previous candle (position = -1)
        double lowPrev  = iLow(TradeSymbol, PERIOD_H3, 1);
        double highPrev = iHigh(TradeSymbol, PERIOD_H3, 1);

        // Original trade was BUY → Reverse SELL
        if(originalEntryType == POSITION_TYPE_BUY)
        {
            double bid = SymbolInfoDouble(TradeSymbol, SYMBOL_BID);
            if(initialSL > 0 && bid <= initialSL) // original BUY SL hit in negative profit
            {
                double sl = highPrev; // SL of reverse SELL = high of previous candle
                double vol = CalculateRiskVolume(bid, sl);
                if(vol > 0)
                {
                    if(trade.Sell(vol, TradeSymbol, bid, sl, 0.0))
                        reverseEntryDone = true;
                }
            }
        }

        // Original trade was SELL → Reverse BUY
        if(originalEntryType == POSITION_TYPE_SELL)
        {
            double ask = SymbolInfoDouble(TradeSymbol, SYMBOL_ASK);
            if(initialSL > 0 && ask >= initialSL) // original SELL SL hit in negative profit
            {
                double sl = lowPrev; // SL of reverse BUY = low of previous candle
                double vol = CalculateRiskVolume(ask, sl);
                if(vol > 0)
                {
                    if(trade.Buy(vol, TradeSymbol, ask, sl, 0.0))
                        reverseEntryDone = true;
                }
            }
        }
    }
}

// ============================================================
// TRAILING LOGIC (STRICT CLOSED H3 CANDLES ONLY)
// ============================================================
void HandleTrailing()
{
    if(!PositionSelect(TradeSymbol))
        return;

    datetime barTime = iTime(TradeSymbol, PERIOD_H3, 1);
    if(barTime == 0 || barTime == lastTrailBarTime)
        return;

    lastTrailBarTime = barTime;

    long type = PositionGetInteger(POSITION_TYPE);
    double currentSL = PositionGetDouble(POSITION_SL);

    double open  = iOpen(TradeSymbol, PERIOD_H3, 1);
    double close = iClose(TradeSymbol, PERIOD_H3, 1);
    double low   = iLow(TradeSymbol, PERIOD_H3, 1);
    double high  = iHigh(TradeSymbol, PERIOD_H3, 1);

    // ---------------- BUY ----------------
    if(type == POSITION_TYPE_BUY)
    {
        if(close > open && low > currentSL)
            trade.PositionModify(TradeSymbol, low, 0.0);
    }

    // ---------------- SELL ----------------
    if(type == POSITION_TYPE_SELL)
    {
        if(close < open && high < currentSL)
            trade.PositionModify(TradeSymbol, high, 0.0);
    }
}

// ============================================================
// RISK-BASED LOT CALCULATION
// ============================================================
double CalculateRiskVolume(double entry, double stop)
{
    double distance = MathAbs(entry - stop);
    if(distance <= 0)
        return 0;

    int spread_points = (int)SymbolInfoInteger(TradeSymbol, SYMBOL_SPREAD);
    double spread     = spread_points * SymbolInfoDouble(TradeSymbol, SYMBOL_POINT);
    if(distance < spread * 10)
        return 0;

    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskAmt = balance * (RiskPercent / 100.0);

    double tickSize  = SymbolInfoDouble(TradeSymbol, SYMBOL_TRADE_TICK_SIZE);
    double tickValue = SymbolInfoDouble(TradeSymbol, SYMBOL_TRADE_TICK_VALUE);

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
// DAILY RESET OF FLAGS
// ============================================================
void ResetFlags()
{
    static datetime lastResetTime = 0;
    datetime now = TimeCurrent();
    MqlDateTime t;
    TimeToStruct(now, t);

    if(t.hour == 0 && lastResetTime < now - 3600)
    {
        originalEntryDone = false;
        originalEntryLoss = false;
        reverseEntryDone  = false;
        initialSL         = 0.0;
        originalEntryType = -1;
        originalTicket    = 0;
        lastResetTime = now;
    }
}
