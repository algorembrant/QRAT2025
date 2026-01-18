#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- INPUT PARAMETERS
input group             "Risk Management"
input double            InpRiskPercent       = 1.0;      // Risk per trade (%) or simply 1%
input double            InpPriceStep         = 0.10;     // VP Price Step (e.g., 0.10 XAU price unit precision)
input double            InpValueAreaPct      = 0.70;     // Value Area Percent (0.70)

input group             "Filters"
input int               InpMinSLDistance     = 10;       // Min StopLoss Factor (Spread * X) for example in XAU (Sl is not < 0.160 x 10)

input group             "System"
input int               InpMagicNumber       = 123456;   // Magic Number
input string            InpTradeComment      = "VP_Algo"; // Trade Comment

//--- GLOBAL OBJECTS
CTrade         m_trade;
CSymbolInfo    m_symbol;
CPositionInfo  m_position;
CAccountInfo   m_account;

//--- GLOBAL VARIABLES
datetime       m_last_calc_time;
datetime       m_last_trade_hour; // Tracks the hour of the last trade
double         m_developing_poc;
double         m_developing_vah;
double         m_developing_val;

//--- DATA STRUCTURE FOR VOLUME PROFILE
struct PriceLevel
{
   double price;
   double volume;
};

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!m_symbol.Name(Symbol())) 
      return(INIT_FAILED);
   
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetMarginMode();
   m_trade.SetTypeFillingBySymbol(Symbol());
   
   // Normalize Price Step to avoid zero division
   if(InpPriceStep <= 0) 
   {
      Print("Error: Price Step must be > 0");
      return(INIT_PARAMETERS_INCORRECT);
   }

   m_last_calc_time = 0;
   m_last_trade_hour = 0;
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!m_symbol.RefreshRates()) return;

   // 1. Manage Open Trades (Dynamic TP Logic)
   ManageOpenTrades();

   // 2. Check for New Bar to Calculate Profile and Signals
   // We only calculate logic on bar close as per requirement
   datetime time_0 = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(time_0 <= m_last_calc_time) return; // Already calculated for this bar
   
   m_last_calc_time = time_0;
   
   // --- CALCULATE PROFILE FOR PREVIOUS BARS ---
   CalculateVolumeProfile();
   
   // --- CHECK TRADING HOUR LOGIC ---
   // Logic: Max one trade per whole trading hour.
   datetime current_hour_dt = time_0 - (time_0 % 3600); // Floor to hour
   
   if(m_last_trade_hour == current_hour_dt) 
   {
      // We already traded this hour
      return; 
   }
   
   // --- CHECK ENTRY SIGNALS ---
   CheckEntrySignals(current_hour_dt);
}

//+------------------------------------------------------------------+
//| Logic: Calculate Developing POC/VAH/VAL                          |
//| Replicates the Python "cumulative_volume" distribution           |
//+------------------------------------------------------------------+
void CalculateVolumeProfile()
{
   // Get Start of Day (Session)
   datetime time_current = iTime(_Symbol, PERIOD_CURRENT, 0);
   datetime time_day_start = iTime(_Symbol, PERIOD_D1, 0);
   
   // If data is unavailable, fallback
   if(time_day_start == 0) time_day_start = time_current - 86400;

   // Get all bars from start of day up to index 1 (closed bar)
   int start_idx = iBarShift(_Symbol, PERIOD_CURRENT, time_day_start);
   int end_idx = 1; // We look at closed bars only for calculation
   
   if(start_idx < end_idx) return;

   // Map: Price(int normalized) -> Volume
   // Using dynamic arrays as a simple hash map replacement
   double volumes[]; 
   double prices[];
   int    total_levels = 0;
   
   // Resize initially to a reasonable estimate
   ArrayResize(volumes, 1000);
   ArrayResize(prices, 1000);
   ArrayInitialize(volumes, 0);
   ArrayInitialize(prices, 0);

   // --- ITERATE CANDLES ---
   for(int i = start_idx; i >= end_idx; i--)
   {
      double h = iHigh(_Symbol, PERIOD_CURRENT, i);
      double l = iLow(_Symbol, PERIOD_CURRENT, i);
      long   v = iVolume(_Symbol, PERIOD_CURRENT, i); // Tick Volume
      
      if(v <= 0) continue;
      
      // Python logic: prices = np.arange(low, high + 0.01, step)
      // Count steps
      int steps = (int)((h - l) / InpPriceStep) + 1;
      if(steps <= 0) steps = 1;
      
      double vol_per_step = (double)v / steps;
      
      for(int s = 0; s < steps; s++)
      {
         double p_raw = l + (s * InpPriceStep);
         double p_norm = NormalizeDouble(p_raw, _Digits);
         
         // Find or Add to array (Simple linear search is slow but robust for MQL5 arrays without generics)
         // Optimization: In production, use a sorted array + binary search or a min-max offset array.
         // Here we use a simplified accumulating method sufficient for M15 data.
         
         bool found = false;
         for(int k=0; k<total_levels; k++)
         {
             // Floating point comparison
             if(MathAbs(prices[k] - p_norm) < _Point)
             {
                 volumes[k] += vol_per_step;
                 found = true;
                 break;
             }
         }
         
         if(!found)
         {
             if(total_levels >= ArraySize(prices))
             {
                 ArrayResize(prices, total_levels + 500);
                 ArrayResize(volumes, total_levels + 500);
             }
             prices[total_levels] = p_norm;
             volumes[total_levels] = vol_per_step;
             total_levels++;
         }
      }
   }
   
   // Sort Data (Bubble sort is slow, we copy to struct array and use built-in Sort)
   PriceLevel levels[];
   ArrayResize(levels, total_levels);
   double total_vol = 0;
   
   for(int i=0; i<total_levels; i++)
   {
      levels[i].price = prices[i];
      levels[i].volume = volumes[i];
      total_vol += volumes[i];
   }
   
   // Sort by Price Ascending for Value Area calc
   // Note: We need a custom sort or manual sort. 
   // Simple selection sort for Price (since total_levels usually < 500 per session on M15)
   for(int i=0; i<total_levels-1; i++)
   {
      int min_idx = i;
      for(int j=i+1; j<total_levels; j++)
      {
         if(levels[j].price < levels[min_idx].price) min_idx = j;
      }
      PriceLevel temp = levels[min_idx];
      levels[min_idx] = levels[i];
      levels[i] = temp;
   }

   // --- FIND POC ---
   int poc_idx = 0;
   double max_vol = -1.0;
   
   for(int i=0; i<total_levels; i++)
   {
      if(levels[i].volume > max_vol)
      {
         max_vol = levels[i].volume;
         poc_idx = i;
      }
   }
   
   m_developing_poc = levels[poc_idx].price;
   
   // --- CALCULATE VAH / VAL (70% Rule) ---
   double target_vol = total_vol * InpValueAreaPct;
   double current_vol = levels[poc_idx].volume;
   int idx_low = poc_idx;
   int idx_high = poc_idx;
   
   // Expand outwards from POC
   while(current_vol < target_vol)
   {
      double vol_below = (idx_low > 0) ? levels[idx_low - 1].volume : 0;
      double vol_above = (idx_high < total_levels - 1) ? levels[idx_high + 1].volume : 0;
      
      // If we hit boundaries
      if(idx_low == 0 && idx_high == total_levels - 1) break;
      
      if(vol_above > vol_below || idx_low == 0)
      {
         if(idx_high < total_levels - 1)
         {
            idx_high++;
            current_vol += levels[idx_high].volume;
         }
      }
      else
      {
         if(idx_low > 0)
         {
            idx_low--;
            current_vol += levels[idx_low].volume;
         }
      }
   }
   
   m_developing_val = levels[idx_low].price;
   m_developing_vah = levels[idx_high].price;
}

//+------------------------------------------------------------------+
//| Check Logic and Open Trades                                      |
//+------------------------------------------------------------------+
void CheckEntrySignals(datetime current_hour)
{
   // Previous closed candle (Signal Candle)
   double close = iClose(_Symbol, PERIOD_CURRENT, 1);
   double low   = iLow(_Symbol, PERIOD_CURRENT, 1);
   double high  = iHigh(_Symbol, PERIOD_CURRENT, 1);
   
   // Get Spread
   double spread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   
   // --- BUY LOGIC ---
   // Candle Closes ABOVE VAH
   if(close > m_developing_vah)
   {
      double sl_price = low;
      double sl_dist = close - sl_price;
      
      // Filter: Stop Loss Distance < Spread * 10
      if(sl_dist < (spread * InpMinSLDistance)) return;
      
      // Calculate Lot Size
      double vol = GetLotSize(sl_dist);
      
      if(m_trade.Buy(vol, _Symbol, 0, sl_price, 0, InpTradeComment))
      {
         m_last_trade_hour = current_hour;
      }
   }
   
   // --- SELL LOGIC ---
   // Candle Closes BELOW VAL
   else if(close < m_developing_val)
   {
      double sl_price = high;
      double sl_dist = sl_price - close;
      
      // Filter: Stop Loss Distance < Spread * 10
      if(sl_dist < (spread * InpMinSLDistance)) return;
      
      double vol = GetLotSize(sl_dist);
      
      if(m_trade.Sell(vol, _Symbol, 0, sl_price, 0, InpTradeComment))
      {
         m_last_trade_hour = current_hour;
      }
   }
}

//+------------------------------------------------------------------+
//| Manage Open Trades (Dynamic Take Profit)                         |
//| "Close if corresponding POC closes between body of candle"       |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
   if(PositionsTotal() == 0) return;
   
   // Check current active candle data
   double open_current  = iOpen(_Symbol, PERIOD_CURRENT, 0);
   double close_current = iClose(_Symbol, PERIOD_CURRENT, 0); // Current price
   
   double body_high = MathMax(open_current, close_current);
   double body_low  = MathMin(open_current, close_current);
   
   // Iterate backwards to avoid index issues on close
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(m_position.SelectByIndex(i))
      {
         if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
         {
            // Logic: Is current POC inside current candle BODY?
            if(m_developing_poc >= body_low && m_developing_poc <= body_high)
            {
               // Close the trade
               m_trade.PositionClose(m_position.Ticket());
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Helper: Calculate Lot Size based on Risk %                       |
//+------------------------------------------------------------------+
double GetLotSize(double sl_distance)
{
   if(sl_distance <= 0) return 0.01;
   
   double risk_money = m_account.Balance() * (InpRiskPercent / 100.0);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   
   if(tick_size == 0 || tick_value == 0) return 0.01;
   
   double loss_per_lot = (sl_distance / tick_size) * tick_value;
   if(loss_per_lot == 0) return 0.01;
   
   double lots = risk_money / loss_per_lot;
   
   // Normalize lots
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lots = MathFloor(lots / step_lot) * step_lot;
   
   if(lots < min_lot) lots = min_lot;
   if(lots > max_lot) lots = max_lot;
   
   return lots;

}
