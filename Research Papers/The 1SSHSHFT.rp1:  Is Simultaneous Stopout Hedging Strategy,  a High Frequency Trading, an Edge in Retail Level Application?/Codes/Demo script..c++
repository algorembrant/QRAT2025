


//+------------------------------------------------------------------+
//|               #1EATB.mq5                                         |
//|   Auto straddle + hedge on TP/SL, loops indefinitely             |
//+------------------------------------------------------------------+
#property strict
#include <Trade/Trade.mqh>


input double InpRiskPercent = 1.0; // Risk percent per trade
input int    InpPipsEntry = 50;
input int    InpPipsSL    = 100;
input int    InpPipsTP    = 1000;
input int    InpSlippage  = 10;
input ulong  InpMagic     = 7777;
input int    InpTrailTriggerPips = 50;  // Profit pips to start trailing
input int    InpTrailDistancePips = 40; // Trailing distance


CTrade trade;


ulong buyStopTicket  = 0;
ulong sellStopTicket = 0;


//+------------------------------------------------------------------+
double Pip()
{
    double point  = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    int digits    = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    return (digits == 3 || digits == 5) ? point * 10.0 : point;
}
//+------------------------------------------------------------------+
double CalculateLotSize(double stopLossPips)
{
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double pipValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);


    // StopLoss in money
    double slMoney = stopLossPips * pipValue;


    double riskMoney = equity * InpRiskPercent / 100.0;


    double lots = riskMoney / slMoney;


    // Normalize lot to step & min/max
    lots = MathFloor(lots / lotStep) * lotStep;
    if(lots < minLot) lots = minLot;
    if(lots > maxLot) lots = maxLot;


    return(lots);
}
//+------------------------------------------------------------------+
bool PlacePending(ENUM_ORDER_TYPE type, double price, double sl, double tp, ulong &ticket, string comment)
{
    double stopLossPips = (type == ORDER_TYPE_BUY_STOP || type == ORDER_TYPE_BUY_LIMIT) ? (price - sl)/Pip()
                                                                                      : (sl - price)/Pip();
    double lots = CalculateLotSize(stopLossPips);


    MqlTradeRequest req;
    MqlTradeResult  res;
    ZeroMemory(req);
    ZeroMemory(res);


    req.action      = TRADE_ACTION_PENDING;
    req.symbol      = _Symbol;
    req.type        = type;
    req.volume      = lots;
    req.price       = price;
    req.sl          = sl;
    req.tp          = tp;
    req.magic       = InpMagic;
    req.deviation   = InpSlippage;
    req.type_time   = ORDER_TIME_GTC;
    req.type_filling= ORDER_FILLING_FOK;
    req.comment     = comment;


    if(!OrderSend(req, res))
    {
        Print("OrderSend failed: ", res.retcode, " ", res.comment);
        ticket = 0;
        return false;
    }


    ticket = res.order;
    return true;
}
//+------------------------------------------------------------------+
void PlaceStraddle()
{
    double pip   = Pip();
    double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    int digits   = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);


    double buyE  = NormalizeDouble(ask + InpPipsEntry * pip, digits);
    double buySL = NormalizeDouble(buyE - InpPipsSL * pip, digits);
    double buyTP = NormalizeDouble(buyE + InpPipsTP * pip, digits);


    double sellE  = NormalizeDouble(bid - InpPipsEntry * pip, digits);
    double sellSL = NormalizeDouble(sellE + InpPipsSL * pip, digits);
    double sellTP = NormalizeDouble(sellE - InpPipsTP * pip, digits);


    PlacePending(ORDER_TYPE_BUY_STOP,  buyE,  buySL,  buyTP,  buyStopTicket,  "BUY_STOP_EA");
    PlacePending(ORDER_TYPE_SELL_STOP, sellE, sellSL, sellTP, sellStopTicket, "SELL_STOP_EA");
}
//+------------------------------------------------------------------+
bool PendingOrderExists(ulong ticket)
{
    if(ticket == 0) return false;


    if(OrderSelect(ticket))
        return true;


    return false;
}
//+------------------------------------------------------------------+
bool PositionExists(string type)
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(!PositionSelectByTicket(ticket)) continue;


        if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagic) continue;
        if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;


        ENUM_POSITION_TYPE ptype = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
        if(type == "BUY"  && ptype == POSITION_TYPE_BUY)  return true;
        if(type == "SELL" && ptype == POSITION_TYPE_SELL) return true;
    }
    return false;
}
//+------------------------------------------------------------------+
void CancelOrder(ulong &ticket)
{
    if(ticket == 0) return;


    MqlTradeRequest req;
    MqlTradeResult  res;


    ZeroMemory(req);
    ZeroMemory(res);


    req.action = TRADE_ACTION_REMOVE;
    req.order  = ticket;
    req.symbol = _Symbol;


    if(OrderSend(req, res))
    {
        Print("Cancelled pending order: ", ticket);
        ticket = 0;
    }
    else
        Print("Failed to cancel order ", ticket, " ret=", res.retcode);
}
//+------------------------------------------------------------------+
void CheckAndRebuild()
{
    bool buyPos  = PositionExists("BUY");
    bool sellPos = PositionExists("SELL");


    bool buyActive  = PendingOrderExists(buyStopTicket);
    bool sellActive = PendingOrderExists(sellStopTicket);


    // One triggered → cancel opposite pending
    if(buyPos && sellActive)
        CancelOrder(sellStopTicket);
    if(sellPos && buyActive)
        CancelOrder(buyStopTicket);


    // Loop: if both positions closed → rebuild straddle
    if(!buyPos && !sellPos && !buyActive && !sellActive)
    {
        Print("Both positions closed → placing new straddle");
        PlaceStraddle();
    }


    // Check solo pending orders and cancel them
    if(buyActive && !sellActive)
        CancelOrder(buyStopTicket);
    if(sellActive && !buyActive)
        CancelOrder(sellStopTicket);
}
//+------------------------------------------------------------------+
void TrailStops()
{
    double pip = Pip();


    for(int i=0; i<PositionsTotal(); i++)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket == 0) continue;
        if(!PositionSelectByTicket(ticket)) continue;


        if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagic) continue;
        if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;


        double open    = PositionGetDouble(POSITION_PRICE_OPEN);
        double current = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                                                  : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double sl      = PositionGetDouble(POSITION_SL);
        ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);


        double profitPips = (type == POSITION_TYPE_BUY)  ? (current - open)/pip
                                                         : (open - current)/pip;


        if(profitPips >= InpTrailTriggerPips)
        {
            double newSL = (type == POSITION_TYPE_BUY)  ? current - InpTrailDistancePips*pip
                                                        : current + InpTrailDistancePips*pip;


            // Only move SL forward (do not move backward)
            if((type == POSITION_TYPE_BUY && newSL > sl) || (type == POSITION_TYPE_SELL && newSL < sl))
            {
                trade.PositionModify(ticket, newSL, PositionGetDouble(POSITION_TP));
                Print("Trailing SL modified for ticket ", ticket, " newSL=", newSL);
            }
        }
    }
}
//+------------------------------------------------------------------+
int OnInit()
{
    PlaceStraddle();
    return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
void OnTick()
{
    CheckAndRebuild();
    TrailStops();
}
//+------------------------------------------------------------------+
