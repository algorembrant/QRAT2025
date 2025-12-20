#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

#property indicator_type1   DRAW_COLOR_CANDLES
#property indicator_label1  "H3 00:00 Candle"
#property indicator_color1  clrBlue, clrRed

// =====================
// BUFFERS
// =====================
double OpenBuf[];
double HighBuf[];
double LowBuf[];
double CloseBuf[];
double ColorBuf[];

// =====================
// INIT
// =====================
int OnInit()
{
   // Chart visual settings
   ChartSetInteger(0, CHART_SHOW_GRID, false);
   ChartSetInteger(0, CHART_SHOW_BID_LINE, true);
   ChartSetInteger(0, CHART_SHOW_ASK_LINE, true);

   SetIndexBuffer(0, OpenBuf,  INDICATOR_DATA);
   SetIndexBuffer(1, HighBuf,  INDICATOR_DATA);
   SetIndexBuffer(2, LowBuf,   INDICATOR_DATA);
   SetIndexBuffer(3, CloseBuf, INDICATOR_DATA);
   SetIndexBuffer(4, ColorBuf, INDICATOR_COLOR_INDEX);

   PlotIndexSetInteger(0, PLOT_DRAW_BEGIN, 0);
   PlotIndexSetInteger(0, PLOT_COLOR_INDEXES, 2);

   IndicatorSetString(INDICATOR_SHORTNAME, "H3 00:00 Bull/Bear Candle");

   return(INIT_SUCCEEDED);
}

// =====================
// CALCULATION
// =====================
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
   if(_Period != PERIOD_H3)
      return(rates_total);

   int start = (prev_calculated > 0) ? prev_calculated - 1 : 0;

   for(int i = start; i < rates_total; i++)
   {
      OpenBuf[i]  = open[i];
      HighBuf[i]  = high[i];
      LowBuf[i]   = low[i];
      CloseBuf[i] = close[i];

      ColorBuf[i] = EMPTY_VALUE;

      MqlDateTime t;
      TimeToStruct(time[i], t);

      // H3 candle starting at 00:00
      if(t.hour == 0)
      {
         if(close[i] > open[i])
            ColorBuf[i] = 0; // Bullish (Blue)
         else if(close[i] < open[i])
            ColorBuf[i] = 1; // Bearish (Red)
      }
   }

   return(rates_total);
}
