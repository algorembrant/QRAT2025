#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

#property indicator_type1   DRAW_COLOR_CANDLES
#property indicator_color1  clrBlue, clrRed
#property indicator_label1  "First Daily Candle"

//--- buffers
double OpenBuf[];
double HighBuf[];
double LowBuf[];
double CloseBuf[];
double ColorBuf[];

//--- colors index
#define BULL 0
#define BEAR 1

int OnInit()
{
   SetIndexBuffer(0, OpenBuf,  INDICATOR_DATA);
   SetIndexBuffer(1, HighBuf,  INDICATOR_DATA);
   SetIndexBuffer(2, LowBuf,   INDICATOR_DATA);
   SetIndexBuffer(3, CloseBuf, INDICATOR_DATA);
   SetIndexBuffer(4, ColorBuf, INDICATOR_COLOR_INDEX);

   PlotIndexSetInteger(0, PLOT_DRAW_BEGIN, 1);

   //--- chart appearance
   ChartSetInteger(0, CHART_SHOW_GRID, false);      // remove grid
   ChartSetInteger(0, CHART_SHOW_BID_LINE, true);   // show bid line
   ChartSetInteger(0, CHART_SHOW_ASK_LINE, true);   // show ask line

   return(INIT_SUCCEEDED);
}

int OnCalculate(
   const int rates_total,
   const int prev_calculated,
   const datetime &time[],
   const double &open[],
   const double &high[],
   const double &low[],
   const double &close[],
   const long &tick_volume[],
   const long &volume[],
   const int &spread[]
)
{
   if(rates_total < 2)
      return 0;

   int start = prev_calculated > 1 ? prev_calculated - 1 : 1;

   for(int i = start; i < rates_total; i++)
   {
      OpenBuf[i]  = EMPTY_VALUE;
      HighBuf[i]  = EMPTY_VALUE;
      LowBuf[i]   = EMPTY_VALUE;
      CloseBuf[i] = EMPTY_VALUE;

      datetime cur = time[i];
      datetime prev = time[i - 1];

      MqlDateTime tcur, tprev;
      TimeToStruct(cur, tcur);
      TimeToStruct(prev, tprev);

      bool is_first_daily_candle =
         (tcur.hour == 0 && tcur.min == 0) ||
         (tcur.day != tprev.day);

      if(is_first_daily_candle)
      {
         OpenBuf[i]  = open[i];
         HighBuf[i]  = high[i];
         LowBuf[i]   = low[i];
         CloseBuf[i] = close[i];

         ColorBuf[i] = close[i] >= open[i] ? BULL : BEAR;
      }
   }

   return(rates_total);
}
