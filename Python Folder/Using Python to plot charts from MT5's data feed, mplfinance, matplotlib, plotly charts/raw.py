# Install dependencies if needed
!pip install MetaTrader5 plotly pandas --quiet

# -----------------------------
# IMPORTS
# -----------------------------
import MetaTrader5 as mt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------
# 1. CONNECT TO MT5
# -----------------------------
if not mt.initialize():
    raise RuntimeError("MT5 initialization failed")
symbol = "XAUUSDm"           # Change to your broker's symbol
timeframe = mt.TIMEFRAME_M5  # 5-minute candles
num_candles = 500            # Number of candles to fetch

# -----------------------------
# 2. FETCH DATA
# -----------------------------
rates = mt.copy_rates_from_pos(symbol, timeframe, 0, num_candles)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)

# OHLC + tick volume
df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'tick_volume': 'Volume'
}, inplace=True)

# -----------------------------
# 3. CALCULATE DELTA
# -----------------------------
# Simple delta: +Volume if candle up, -Volume if candle down, 0 if neutral
df['Delta'] = df.apply(
    lambda row: row['Volume'] if row['Close'] > row['Open'] 
    else (-row['Volume'] if row['Close'] < row['Open'] else 0),
    axis=1
)

print(df.head())
# -----------------------------
# 4. CREATE PLOTLY FIGURE WITH TWO PANES
# -----------------------------
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.7, 0.3],
    subplot_titles=(f'{symbol} Price', 'Volume (Delta Colored)')
)

# Candlestick trace (top pane)
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Price'
), row=1, col=1)

# Volume trace (bottom pane), colored by delta
colors = ['green' if d > 0 else ('red' if d < 0 else 'gray') for d in df['Delta']]
fig.add_trace(go.Bar(
    x=df.index,
    y=df['Volume'],
    marker_color=colors,
    name='Volume'
), row=2, col=1)

# -----------------------------
# 5. LAYOUT
# -----------------------------
fig.update_layout(
    title=f'{symbol} Candlestick + Volume (Delta Colored)',
    xaxis_rangeslider_visible=False,
    template='plotly_dark',
    height=700
)

# Set axis labels
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="Volume", row=2, col=1)

fig.update_layout(
    xaxis_rangeslider_visible=True  # adds scrollable slider
)

fig.update_xaxes(
    rangeslider_visible=True,
    rangeslider_thickness=0.05  # height of the slider
)


fig.show()