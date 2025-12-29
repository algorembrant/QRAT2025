//+------------------------------------------------------------------+
//|                                             RangeBreakout_M3.mq5 |
//|                                  Copyright 2023, Gemini AI Asst. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Gemini AI"
#property link      "https://www.mql5.com"
#property version   "1.00"
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
input int      InpBrokerOffset   = 0;        // Broker Time Offset from UTC (e.g., if Broker is UTC+2, put 2)

input group "System"
input ulong    InpMagicNum       = 123456;   // Magic Number

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade         trade;
datetime       lastBarTime       = 0;
bool           tradeTakenToday   = false;
int            lastTradeDay      = -1;

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
   // Ensure we are allowed to trade
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      Print("Warning: AutoTrading is disabled in Terminal.");
      
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Check for New Bar on M3 Timeframe
   // We strictly use M3 per instructions
   datetime currentBarTime = iTime(_Symbol, PERIOD_M3, 0);
   if(currentBarTime == lastBarTime) return; // Wait for candle close
   lastBarTime = currentBarTime;

   // 2. Reset Daily Flags
   MqlDateTime dt;
   TimeCurrent(dt);
   
   if(lastTradeDay != dt.day) {
      tradeTakenToday = false;
      lastTradeDay = dt.day;
      currentRange.isValid = false; // Reset range for the new day
   }

   // 3. One Trade Per Day Logic
   if(tradeTakenToday) return;

   // 4. Calculate Range if not yet done and time is past 00:00
   // We need to define the 22:00 - 00:00 window of the *previous* session
   if(!currentRange.isValid) {
      CalculateRange();
   }

   // 5. If Range is valid, Check for Breakout Logic
   if(currentRange.isValid) {
      CheckBreakoutSignal();
   }
}

//+------------------------------------------------------------------+
//| Function to Calculate HHR and LLR (22:00 - 00:00)                |
//+------------------------------------------------------------------+
void CalculateRange()
{
   MqlDateTime dt;
   TimeCurrent(dt);

   // Determine the correct start and end time for the range
   // The range is 22:00 (Previous Day) to 00:00 (Today)
   // Adjusted for Broker Offset
   
   int startHour = InpRangeStartHour + InpBrokerOffset;
   int endHour   = InpRangeEndHour + InpBrokerOffset;
   
   // Handle hour overflow (e.g., 22 + 2 = 24 -> 00)
   if(startHour >= 24) startHour -= 24;
   if(endHour >= 24) endHour -= 24;

   // We need the range from yesterday's 22:00 to today's 00:00
   datetime timeEnd   = StringToTime(StringFormat("%04d.%02d.%02d %02d:00", dt.year, dt.mon, dt.day, endHour));
   datetime timeStart = timeEnd - (2 * 3600); // Subtract 2 hours (22 to 00 is 2 hours)
   
   // Check if we have passed the range end time
   if(TimeCurrent() < timeEnd) return; // Wait until range closes

   // Get Bars inside the range
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   // Get data from M3 timeframe
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
      
      // Print("Range Calculated: HHR=", currentRange.HHR, " LLR=", currentRange.LLR);
   }
}

//+------------------------------------------------------------------+
//| Function to Check Breakout & Validation                          |
//+------------------------------------------------------------------+
void CheckBreakoutSignal()
{
   // Get the Breakout Candle (BCC) - Index 1 (Closed Candle)
   MqlRates bcc[];
   ArraySetAsSeries(bcc, true);
   if(CopyRates(_Symbol, PERIOD_M3, 1, 1, bcc) != 1) return;

   double bccClose = bcc[0].close;
   double bccHigh  = bcc[0].high;
   double bccLow   = bcc[0].low;
   datetime bccTime = bcc[0].time;

   // --- BUY LOGIC ---
   if(bccClose > currentRange.HHR) {
      // Filter: Check candles from EP (timeHHR) until BCC
      // Ensure wicks haven't touched HHR in between
      if(IsPathClear(currentRange.timeHHR, bccTime, currentRange.HHR, true)) {
         
         double sl = bccLow;
         double riskDist = bccClose - sl;
         
         // Safety check for zero distance
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
      // Filter: Check candles from EP (timeLLR) until BCC
      // Ensure wicks haven't touched LLR in between
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
   // We need candles BETWEEN startTime and endTime (exclusive of start, exclusive of end)
   // Logic: Get bars from Start to End.
   
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   
   // Copy rates from start time to end time
   int count = CopyRates(_Symbol, PERIOD_M3, startTime, endTime, rates);
   
   // Iterate, skipping the first (which matches startTime/EP) and last (which is BCC - handled by logic)
   // Note: CopyRates with start/end includes the bars that contain those times.
   // Because Array is Series, index 0 is the bar AT endTime (The Breakout Candle). 
   // Index [count-1] is the bar AT startTime (The EP).
   
   for(int i = 1; i < count - 1; i++) {
      if(isBuy) {
         // For Buy: No High should have touched HHR
         if(rates[i].high >= level) return false;
      } else {
         // For Sell: No Low should have touched LLR
         if(rates[i].low <= level) return false;
      }
   }
   return true;
}

//+------------------------------------------------------------------+
//| Risk Management: Calculate Lots based on 1% Risk                 |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDistancePrice)
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = balance * (InpRiskPercent / 100.0);
   
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   
   if(tickSize == 0 || tickValue == 0 || slDistancePrice == 0) return 0.01; // Safety
   
   double slPoints = slDistancePrice / tickSize;
   double lotSize = riskMoney / (slPoints * tickValue);
   
   // Normalize Lot Size
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lotSize = MathFloor(lotSize / stepLot) * stepLot;
   
   if(lotSize < minLot) lotSize = minLot;
   if(lotSize > maxLot) lotSize = maxLot;
   
   return lotSize;
}
//+------------------------------------------------------------------+