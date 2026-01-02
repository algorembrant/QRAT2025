
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------
# User parameters
# -----------------------
SYMBOL = "XAUUSDc"          # symbol used earlier in conversation
TIMEFRAME = mt5.TIMEFRAME_M3
N_BARS = 2000               # number of bars to fetch
VG = None                   # Volume Gate: if None, will use median volume * param
VG_MULTIPLIER = 0.5         # VG = median(volume_last_100) * VG_MULTIPLIER (if VG unspecified)
VOLUME_BOOM_FACTOR = 2      # Current volume >= VOLUME_BOOM_FACTOR * sum(prev_k_volumes)
VOLUME_BOOM_LOOKBACK = 10   # number of previous candles to sum for boom check

# VTR specs as (multiplier m, lookback l)
VTR_SPECS = {
    "VTR_3_12": (3, 12),
    "VTR_10_1": (10, 1),
    "VTR_11_2": (11, 2),
}

WILDER_PERIOD = 14         # for DMag (ADX) calculations
DMAG_THRESHOLD = 20        # DMag > 20 required
VERBOSE = True

# -----------------------
# Helper functions
# -----------------------
def to_dataframe(mt5_rates):
    df = pd.DataFrame(mt5_rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=False)
    return df

def true_range(high, low, close_prev):
    return np.maximum.reduce([
        high - low,
        np.abs(high - close_prev),
        np.abs(low - close_prev)
    ])

def wilder_smoothing(series, period):
    """
    Wilder smoothing:
    first value = series[:period].sum()
    subsequent: prev_smoothed - (prev_smoothed / period) + current
    This returns an array aligned with original series (np.nan for first entries before period)
    """
    series = np.asarray(series, dtype=float)
    out = np.full_like(series, np.nan)
    if len(series) < period:
        return out
    # first smoothed value uses simple sum of first 'period' values
    first = series[:period].sum()
    out[period-1] = first
    prev = first
    for i in range(period, len(series)):
        curr = series[i]
        prev = prev - (prev / period) + curr
        out[i] = prev
    return out

# -----------------------
# Connect to MT5 and fetch data
# -----------------------
if not mt5.initialize():
    raise RuntimeError("Failed to initialize MT5. Make sure terminal is running and logged in.")

# request last N bars:
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, N_BARS)
if rates is None or len(rates) == 0:
    mt5.shutdown()
    raise RuntimeError(f"No data returned for {SYMBOL}. Check symbol name and MT5 market watch.")

df = to_dataframe(rates)
# keep important columns and convert to pandas Series
df = pd.DataFrame({
    'time': pd.to_datetime(df['time'], unit='s'),
    'open': df['open'],
    'high': df['high'],
    'low': df['low'],
    'close': df['close'],
    'tick_volume': df['tick_volume'],  # use tick_volume as volume proxy
})
df.set_index('time', inplace=True)
df.sort_index(inplace=True)

# Working arrays
high = df['high'].values
low = df['low'].values
close = df['close'].values
vol = df['tick_volume'].values

# -----------------------
# Volume Gate & Volume Boom
# -----------------------
if VG is None:
    med = np.median(vol[-100:]) if len(vol) >= 100 else np.median(vol)
    VG = max(1.0, med * VG_MULTIPLIER)  # simple default
if VERBOSE:
    print(f"Volume Gate (VG) set to: {VG:.2f}")

# Volume Gate boolean series
volume_gate = vol >= VG

# Volume Boom: current volume >= factor * sum(prev K volumes)
vol_sum_prev_k = np.array([np.sum(vol[max(0,i-VOLUME_BOOM_LOOKBACK):i]) for i in range(len(vol))])
volume_boom = vol >= (VOLUME_BOOM_FACTOR * (vol_sum_prev_k))
# For first few bars vol_sum_prev_k may be small; we treat boom=False when insufficient history
volume_boom[:VOLUME_BOOM_LOOKBACK+1] = False

df['volume_gate'] = volume_gate
df['volume_boom'] = volume_boom

# -----------------------
# VTR calculations
# -----------------------
# Compute TR series (per-bar)
close_prev = np.roll(close, 1)
close_prev[0] = close[0]
TR = true_range(high, low, close_prev)
df['TR'] = TR

# VTR definition: VTR = m * (1/l) * sum_{i=0..l-1} TR_{t-i}
for name, (m, l) in VTR_SPECS.items():
    # rolling mean of TR over l bars
    if l <= 0:
        df[name] = 0.0
    else:
        df[name] = m * df['TR'].rolling(window=l, min_periods=l).mean()
# define a simple threshold for "VTR significant" using recent TR mean
recent_TR_mean = df['TR'].rolling(window=50, min_periods=1).mean()
# threshold multiplier (tuneable)
VTR_THRESHOLD_MULT = 1.2
df['vtr_threshold'] = recent_TR_mean * VTR_THRESHOLD_MULT

# compute boolean if all VTRs exceed threshold
df['vtr_all_above'] = True
for name in VTR_SPECS.keys():
    df['vtr_all_above'] &= (df[name] > df['vtr_threshold'])

# -----------------------
# +DM, -DM, TR smoothing -> +DI, -DI, DX, ADX (DMag)
# -----------------------
# raw +DM / -DM calculation
up_move = high - np.roll(high, 1)
down_move = np.roll(low, 1) - low
up_move[0] = 0.0
down_move[0] = 0.0
plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
df['+DM_raw'] = plus_dm
df['-DM_raw'] = minus_dm

# Wilder smoothing for +DM, -DM, TR
smoothed_TR = wilder_smoothing(df['TR'].values, WILDER_PERIOD)
smoothed_plus_dm = wilder_smoothing(df['+DM_raw'].values, WILDER_PERIOD)
smoothed_minus_dm = wilder_smoothing(df['-DM_raw'].values, WILDER_PERIOD)

# Avoid division by zero later; store in df aligned
df['TR_smooth'] = smoothed_TR
df['+DM_smooth'] = smoothed_plus_dm
df['-DM_smooth'] = smoothed_minus_dm

# +DI and -DI
df['+DI'] = 100.0 * (df['+DM_smooth'] / df['TR_smooth'])
df['-DI'] = 100.0 * (df['-DM_smooth'] / df['TR_smooth'])

# DX
df['DX'] = 100.0 * (np.abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
# DX can be nan for early entries; set to 0
df['DX'] = df['DX'].fillna(0.0)

# ADX (Wilder smoothing of DX over period)
# We'll compute ADX as Wilder smoothed DX (common approach is initial average then wilder smoothing)
dx_vals = df['DX'].values
DMag = wilder_smoothing(dx_vals, WILDER_PERIOD)
df['DMag'] = DMag

# DMag rising check
df['DMag_rising'] = df['DMag'] > np.roll(df['DMag'], 1)
df['DMag_rising'].fillna(False, inplace=True)

# -----------------------
# Signal logic (visual-only)
# -----------------------
# Direction via DI
df['direction_bull'] = df['+DI'] > df['-DI']
df['direction_bear'] = df['+DI'] < df['-DI']

# final bullish signal: all confirmations
df['signal_buy'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bull'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

df['signal_sell'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bear'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

# remove signals at very early bars where indicators are nan
valid_idx = ~df[['TR', '+DM_smooth', '-DM_smooth', 'TR_smooth', 'DMag']].isnull().any(axis=1)
df.loc[~valid_idx, ['signal_buy','signal_sell']] = False

# -----------------------
# Plot with Plotly
# -----------------------
print("Preparing plot...")

candlestick = go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price',
    increasing_line_color='green',
    decreasing_line_color='red',
    opacity=0.9
)

volume_bar = go.Bar(
    x=df.index,
    y=df['tick_volume'],
    name='Tick Volume',
    yaxis='y2',
    opacity=0.6
)

# Buy / Sell markers
buy_markers = go.Scatter(
    x=df.index[df['signal_buy']],
    y=df['low'][df['signal_buy']] * 0.997,
    mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='Buy Signal'
)
sell_markers = go.Scatter(
    x=df.index[df['signal_sell']],
    y=df['high'][df['signal_sell']] * 1.003,
    mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='magenta'),
    name='Sell Signal'
)

# add VTR and DMag traces (scaled for overlay)
vtr_traces = []
for name in VTR_SPECS.keys():
    vtr_traces.append(go.Scatter(
        x=df.index,
        y=df[name],
        mode='lines',
        name=name,
        line=dict(width=1),
        yaxis='y3'
    ))

dmag_trace = go.Scatter(
    x=df.index,
    y=df['DMag'],
    mode='lines',
    name='DMag (ADX)',
    line=dict(width=2, dash='dash'),
    yaxis='y4'
)

layout = go.Layout(
    title=f"{SYMBOL} - Signals demo (no backtest) — last {len(df)} bars",
    xaxis=dict(rangeslider=dict(visible=False)),
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Volume", overlaying='y', side='right', showgrid=False, position=0.98),
    yaxis3=dict(title="VTRs (scaled)", overlaying='y', side='left', anchor='free', position=0.02, showgrid=False),
    yaxis4=dict(title="DMag", overlaying='y', side='right', anchor='free', position=0.98, showgrid=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=800
)

fig = go.Figure(data=[candlestick, volume_bar, buy_markers, sell_markers] + vtr_traces + [dmag_trace], layout=layout)

# Add simple annotations for VG and VTR threshold on volume and VTR panels
fig.add_hline(y=VG, line=dict(color='gray', dash='dot'), annotation_text="Volume Gate", annotation_position="top left")

# show
fig.show()

# -----------------------
# Cleanup
# -----------------------
mt5.shutdown()

print("Done. Signals plotted. Review the chart to inspect markers and indicator overlays.")


import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------
# User parameters
# -----------------------
SYMBOL = "XAUUSDc"          # symbol used earlier in conversation
TIMEFRAME = mt5.TIMEFRAME_M3
N_BARS = 2000               # number of bars to fetch
VG = None                   # Volume Gate: if None, will use median volume * param
VG_MULTIPLIER = 0.5         # VG = median(volume_last_100) * VG_MULTIPLIER (if VG unspecified)
VOLUME_BOOM_FACTOR = 2      # Current volume >= VOLUME_BOOM_FACTOR * sum(prev_k_volumes)
VOLUME_BOOM_LOOKBACK = 10   # number of previous candles to sum for boom check

# VTR specs as (multiplier m, lookback l)
VTR_SPECS = {
    "VTR_3_12": (3, 12),
    "VTR_10_1": (10, 1),
    "VTR_11_2": (11, 2),
}

WILDER_PERIOD = 14         # for DMag (ADX) calculations
DMAG_THRESHOLD = 20        # DMag > 20 required
VERBOSE = True

# -----------------------
# Helper functions
# -----------------------
def to_dataframe(mt5_rates):
    df = pd.DataFrame(mt5_rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=False)
    return df

def true_range(high, low, close_prev):
    return np.maximum.reduce([
        high - low,
        np.abs(high - close_prev),
        np.abs(low - close_prev)
    ])

def wilder_smoothing(series, period):
    """
    Wilder smoothing:
    first value = series[:period].sum()
    subsequent: prev_smoothed - (prev_smoothed / period) + current
    This returns an array aligned with original series (np.nan for first entries before period)
    """
    series = np.asarray(series, dtype=float)
    out = np.full_like(series, np.nan)
    if len(series) < period:
        return out
    # first smoothed value uses simple sum of first 'period' values
    first = series[:period].sum()
    out[period-1] = first
    prev = first
    for i in range(period, len(series)):
        curr = series[i]
        prev = prev - (prev / period) + curr
        out[i] = prev
    return out

# -----------------------
# Connect to MT5 and fetch data
# -----------------------
if not mt5.initialize():
    raise RuntimeError("Failed to initialize MT5. Make sure terminal is running and logged in.")

# request last N bars:
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, N_BARS)
if rates is None or len(rates) == 0:
    mt5.shutdown()
    raise RuntimeError(f"No data returned for {SYMBOL}. Check symbol name and MT5 market watch.")

df = to_dataframe(rates)
# keep important columns and convert to pandas Series
df = pd.DataFrame({
    'time': pd.to_datetime(df['time'], unit='s'),
    'open': df['open'],
    'high': df['high'],
    'low': df['low'],
    'close': df['close'],
    'tick_volume': df['tick_volume'],  # use tick_volume as volume proxy
})
df.set_index('time', inplace=True)
df.sort_index(inplace=True)

# Working arrays
high = df['high'].values
low = df['low'].values
close = df['close'].values
vol = df['tick_volume'].values

# -----------------------
# Volume Gate & Volume Boom
# -----------------------
if VG is None:
    med = np.median(vol[-100:]) if len(vol) >= 100 else np.median(vol)
    VG = max(1.0, med * VG_MULTIPLIER)  # simple default
if VERBOSE:
    print(f"Volume Gate (VG) set to: {VG:.2f}")

# Volume Gate boolean series
volume_gate = vol >= VG

# Volume Boom: current volume >= factor * sum(prev K volumes)
vol_sum_prev_k = np.array([np.sum(vol[max(0,i-VOLUME_BOOM_LOOKBACK):i]) for i in range(len(vol))])
volume_boom = vol >= (VOLUME_BOOM_FACTOR * (vol_sum_prev_k))
# For first few bars vol_sum_prev_k may be small; we treat boom=False when insufficient history
volume_boom[:VOLUME_BOOM_LOOKBACK+1] = False

df['volume_gate'] = volume_gate
df['volume_boom'] = volume_boom

# -----------------------
# VTR calculations
# -----------------------
# Compute TR series (per-bar)
close_prev = np.roll(close, 1)
close_prev[0] = close[0]
TR = true_range(high, low, close_prev)
df['TR'] = TR

# VTR definition: VTR = m * (1/l) * sum_{i=0..l-1} TR_{t-i}
for name, (m, l) in VTR_SPECS.items():
    # rolling mean of TR over l bars
    if l <= 0:
        df[name] = 0.0
    else:
        df[name] = m * df['TR'].rolling(window=l, min_periods=l).mean()
# define a simple threshold for "VTR significant" using recent TR mean
recent_TR_mean = df['TR'].rolling(window=50, min_periods=1).mean()
# threshold multiplier (tuneable)
VTR_THRESHOLD_MULT = 1.2
df['vtr_threshold'] = recent_TR_mean * VTR_THRESHOLD_MULT

# compute boolean if all VTRs exceed threshold
df['vtr_all_above'] = True
for name in VTR_SPECS.keys():
    df['vtr_all_above'] &= (df[name] > df['vtr_threshold'])

# -----------------------
# +DM, -DM, TR smoothing -> +DI, -DI, DX, ADX (DMag)
# -----------------------
# raw +DM / -DM calculation
up_move = high - np.roll(high, 1)
down_move = np.roll(low, 1) - low
up_move[0] = 0.0
down_move[0] = 0.0
plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
df['+DM_raw'] = plus_dm
df['-DM_raw'] = minus_dm

# Wilder smoothing for +DM, -DM, TR
smoothed_TR = wilder_smoothing(df['TR'].values, WILDER_PERIOD)
smoothed_plus_dm = wilder_smoothing(df['+DM_raw'].values, WILDER_PERIOD)
smoothed_minus_dm = wilder_smoothing(df['-DM_raw'].values, WILDER_PERIOD)

# Avoid division by zero later; store in df aligned
df['TR_smooth'] = smoothed_TR
df['+DM_smooth'] = smoothed_plus_dm
df['-DM_smooth'] = smoothed_minus_dm

# +DI and -DI
df['+DI'] = 100.0 * (df['+DM_smooth'] / df['TR_smooth'])
df['-DI'] = 100.0 * (df['-DM_smooth'] / df['TR_smooth'])

# DX
df['DX'] = 100.0 * (np.abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
# DX can be nan for early entries; set to 0
df['DX'] = df['DX'].fillna(0.0)

# ADX (Wilder smoothing of DX over period)
# We'll compute ADX as Wilder smoothed DX (common approach is initial average then wilder smoothing)
dx_vals = df['DX'].values
DMag = wilder_smoothing(dx_vals, WILDER_PERIOD)
df['DMag'] = DMag

# DMag rising check
df['DMag_rising'] = df['DMag'] > np.roll(df['DMag'], 1)
df['DMag_rising'].fillna(False, inplace=True)

# -----------------------
# Signal logic (visual-only)
# -----------------------
# Direction via DI
df['direction_bull'] = df['+DI'] > df['-DI']
df['direction_bear'] = df['+DI'] < df['-DI']

# final bullish signal: all confirmations
df['signal_buy'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bull'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

df['signal_sell'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bear'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

# remove signals at very early bars where indicators are nan
valid_idx = ~df[['TR', '+DM_smooth', '-DM_smooth', 'TR_smooth', 'DMag']].isnull().any(axis=1)
df.loc[~valid_idx, ['signal_buy','signal_sell']] = False

# -----------------------
# Plot with Plotly
# -----------------------
print("Preparing plot...")

candlestick = go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price',
    increasing_line_color='green',
    decreasing_line_color='red',
    opacity=0.9
)

volume_bar = go.Bar(
    x=df.index,
    y=df['tick_volume'],
    name='Tick Volume',
    yaxis='y2',
    opacity=0.6
)

# Buy / Sell markers
buy_markers = go.Scatter(
    x=df.index[df['signal_buy']],
    y=df['low'][df['signal_buy']] * 0.997,
    mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='Buy Signal'
)
sell_markers = go.Scatter(
    x=df.index[df['signal_sell']],
    y=df['high'][df['signal_sell']] * 1.003,
    mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='magenta'),
    name='Sell Signal'
)

# add VTR and DMag traces (scaled for overlay)
vtr_traces = []
for name in VTR_SPECS.keys():
    vtr_traces.append(go.Scatter(
        x=df.index,
        y=df[name],
        mode='lines',
        name=name,
        line=dict(width=1),
        yaxis='y3'
    ))

dmag_trace = go.Scatter(
    x=df.index,
    y=df['DMag'],
    mode='lines',
    name='DMag (ADX)',
    line=dict(width=2, dash='dash'),
    yaxis='y4'
)

layout = go.Layout(
    title=f"{SYMBOL} - Signals demo (no backtest) — last {len(df)} bars",
    xaxis=dict(rangeslider=dict(visible=False)),
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Volume", overlaying='y', side='right', showgrid=False, position=0.98),
    yaxis3=dict(title="VTRs (scaled)", overlaying='y', side='left', anchor='free', position=0.02, showgrid=False),
    yaxis4=dict(title="DMag", overlaying='y', side='right', anchor='free', position=0.98, showgrid=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=800
)

fig = go.Figure(data=[candlestick, volume_bar, buy_markers, sell_markers] + vtr_traces + [dmag_trace], layout=layout)

# Add simple annotations for VG and VTR threshold on volume and VTR panels
fig.add_hline(y=VG, line=dict(color='gray', dash='dot'), annotation_text="Volume Gate", annotation_position="top left")

# show
fig.show()

# -----------------------
# Cleanup
# -----------------------
mt5.shutdown()

print("Done. Signals plotted. Review the chart to inspect markers and indicator overlays.")

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------
# User parameters
# -----------------------
SYMBOL = "XAUUSDc"          # symbol used earlier in conversation
TIMEFRAME = mt5.TIMEFRAME_M3
N_BARS = 2000               # number of bars to fetch
VG = None                   # Volume Gate: if None, will use median volume * param
VG_MULTIPLIER = 0.5         # VG = median(volume_last_100) * VG_MULTIPLIER (if VG unspecified)
VOLUME_BOOM_FACTOR = 2      # Current volume >= VOLUME_BOOM_FACTOR * sum(prev_k_volumes)
VOLUME_BOOM_LOOKBACK = 10   # number of previous candles to sum for boom check

# VTR specs as (multiplier m, lookback l)
VTR_SPECS = {
    "VTR_3_12": (3, 12),
    "VTR_10_1": (10, 1),
    "VTR_11_2": (11, 2),
}

WILDER_PERIOD = 14         # for DMag (ADX) calculations
DMAG_THRESHOLD = 20        # DMag > 20 required
VERBOSE = True

# -----------------------
# Helper functions
# -----------------------
def to_dataframe(mt5_rates):
    df = pd.DataFrame(mt5_rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=False)
    return df

def true_range(high, low, close_prev):
    return np.maximum.reduce([
        high - low,
        np.abs(high - close_prev),
        np.abs(low - close_prev)
    ])

def wilder_smoothing(series, period):
    """
    Wilder smoothing:
    first value = series[:period].sum()
    subsequent: prev_smoothed - (prev_smoothed / period) + current
    This returns an array aligned with original series (np.nan for first entries before period)
    """
    series = np.asarray(series, dtype=float)
    out = np.full_like(series, np.nan)
    if len(series) < period:
        return out
    # first smoothed value uses simple sum of first 'period' values
    first = series[:period].sum()
    out[period-1] = first
    prev = first
    for i in range(period, len(series)):
        curr = series[i]
        prev = prev - (prev / period) + curr
        out[i] = prev
    return out

# -----------------------
# Connect to MT5 and fetch data
# -----------------------
if not mt5.initialize():
    raise RuntimeError("Failed to initialize MT5. Make sure terminal is running and logged in.")

# request last N bars:
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, N_BARS)
if rates is None or len(rates) == 0:
    mt5.shutdown()
    raise RuntimeError(f"No data returned for {SYMBOL}. Check symbol name and MT5 market watch.")

df = to_dataframe(rates)
# keep important columns and convert to pandas Series
df = pd.DataFrame({
    'time': pd.to_datetime(df['time'], unit='s'),
    'open': df['open'],
    'high': df['high'],
    'low': df['low'],
    'close': df['close'],
    'tick_volume': df['tick_volume'],  # use tick_volume as volume proxy
})
df.set_index('time', inplace=True)
df.sort_index(inplace=True)

# Working arrays
high = df['high'].values
low = df['low'].values
close = df['close'].values
vol = df['tick_volume'].values

# -----------------------
# Volume Gate & Volume Boom
# -----------------------
if VG is None:
    med = np.median(vol[-100:]) if len(vol) >= 100 else np.median(vol)
    VG = max(1.0, med * VG_MULTIPLIER)  # simple default
if VERBOSE:
    print(f"Volume Gate (VG) set to: {VG:.2f}")

# Volume Gate boolean series
volume_gate = vol >= VG

# Volume Boom: current volume >= factor * sum(prev K volumes)
vol_sum_prev_k = np.array([np.sum(vol[max(0,i-VOLUME_BOOM_LOOKBACK):i]) for i in range(len(vol))])
volume_boom = vol >= (VOLUME_BOOM_FACTOR * (vol_sum_prev_k))
# For first few bars vol_sum_prev_k may be small; we treat boom=False when insufficient history
volume_boom[:VOLUME_BOOM_LOOKBACK+1] = False

df['volume_gate'] = volume_gate
df['volume_boom'] = volume_boom

# -----------------------
# VTR calculations
# -----------------------
# Compute TR series (per-bar)
close_prev = np.roll(close, 1)
close_prev[0] = close[0]
TR = true_range(high, low, close_prev)
df['TR'] = TR

# VTR definition: VTR = m * (1/l) * sum_{i=0..l-1} TR_{t-i}
for name, (m, l) in VTR_SPECS.items():
    # rolling mean of TR over l bars
    if l <= 0:
        df[name] = 0.0
    else:
        df[name] = m * df['TR'].rolling(window=l, min_periods=l).mean()
# define a simple threshold for "VTR significant" using recent TR mean
recent_TR_mean = df['TR'].rolling(window=50, min_periods=1).mean()
# threshold multiplier (tuneable)
VTR_THRESHOLD_MULT = 1.2
df['vtr_threshold'] = recent_TR_mean * VTR_THRESHOLD_MULT

# compute boolean if all VTRs exceed threshold
df['vtr_all_above'] = True
for name in VTR_SPECS.keys():
    df['vtr_all_above'] &= (df[name] > df['vtr_threshold'])

# -----------------------
# +DM, -DM, TR smoothing -> +DI, -DI, DX, ADX (DMag)
# -----------------------
# raw +DM / -DM calculation
up_move = high - np.roll(high, 1)
down_move = np.roll(low, 1) - low
up_move[0] = 0.0
down_move[0] = 0.0
plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
df['+DM_raw'] = plus_dm
df['-DM_raw'] = minus_dm

# Wilder smoothing for +DM, -DM, TR
smoothed_TR = wilder_smoothing(df['TR'].values, WILDER_PERIOD)
smoothed_plus_dm = wilder_smoothing(df['+DM_raw'].values, WILDER_PERIOD)
smoothed_minus_dm = wilder_smoothing(df['-DM_raw'].values, WILDER_PERIOD)

# Avoid division by zero later; store in df aligned
df['TR_smooth'] = smoothed_TR
df['+DM_smooth'] = smoothed_plus_dm
df['-DM_smooth'] = smoothed_minus_dm

# +DI and -DI
df['+DI'] = 100.0 * (df['+DM_smooth'] / df['TR_smooth'])
df['-DI'] = 100.0 * (df['-DM_smooth'] / df['TR_smooth'])

# DX
df['DX'] = 100.0 * (np.abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
# DX can be nan for early entries; set to 0
df['DX'] = df['DX'].fillna(0.0)

# ADX (Wilder smoothing of DX over period)
# We'll compute ADX as Wilder smoothed DX (common approach is initial average then wilder smoothing)
dx_vals = df['DX'].values
DMag = wilder_smoothing(dx_vals, WILDER_PERIOD)
df['DMag'] = DMag

# DMag rising check
df['DMag_rising'] = df['DMag'] > np.roll(df['DMag'], 1)
df['DMag_rising'].fillna(False, inplace=True)

# -----------------------
# Signal logic (visual-only)
# -----------------------
# Direction via DI
df['direction_bull'] = df['+DI'] > df['-DI']
df['direction_bear'] = df['+DI'] < df['-DI']

# final bullish signal: all confirmations
df['signal_buy'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bull'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

df['signal_sell'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bear'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

# remove signals at very early bars where indicators are nan
valid_idx = ~df[['TR', '+DM_smooth', '-DM_smooth', 'TR_smooth', 'DMag']].isnull().any(axis=1)
df.loc[~valid_idx, ['signal_buy','signal_sell']] = False

# -----------------------
# Plot with Plotly
# -----------------------
print("Preparing plot...")

candlestick = go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price',
    increasing_line_color='green',
    decreasing_line_color='red',
    opacity=0.9
)

volume_bar = go.Bar(
    x=df.index,
    y=df['tick_volume'],
    name='Tick Volume',
    yaxis='y2',
    opacity=0.6
)

# Buy / Sell markers
buy_markers = go.Scatter(
    x=df.index[df['signal_buy']],
    y=df['low'][df['signal_buy']] * 0.997,
    mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='Buy Signal'
)
sell_markers = go.Scatter(
    x=df.index[df['signal_sell']],
    y=df['high'][df['signal_sell']] * 1.003,
    mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='magenta'),
    name='Sell Signal'
)

# add VTR and DMag traces (scaled for overlay)
vtr_traces = []
for name in VTR_SPECS.keys():
    vtr_traces.append(go.Scatter(
        x=df.index,
        y=df[name],
        mode='lines',
        name=name,
        line=dict(width=1),
        yaxis='y3'
    ))

dmag_trace = go.Scatter(
    x=df.index,
    y=df['DMag'],
    mode='lines',
    name='DMag (ADX)',
    line=dict(width=2, dash='dash'),
    yaxis='y4'
)

layout = go.Layout(
    title=f"{SYMBOL} - Signals demo (no backtest) — last {len(df)} bars",
    xaxis=dict(rangeslider=dict(visible=False)),
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Volume", overlaying='y', side='right', showgrid=False, position=0.98),
    yaxis3=dict(title="VTRs (scaled)", overlaying='y', side='left', anchor='free', position=0.02, showgrid=False),
    yaxis4=dict(title="DMag", overlaying='y', side='right', anchor='free', position=0.98, showgrid=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=800
)

fig = go.Figure(data=[candlestick, volume_bar, buy_markers, sell_markers] + vtr_traces + [dmag_trace], layout=layout)

# Add simple annotations for VG and VTR threshold on volume and VTR panels
fig.add_hline(y=VG, line=dict(color='gray', dash='dot'), annotation_text="Volume Gate", annotation_position="top left")

# show
fig.show()

# -----------------------
# Cleanup
# -----------------------
mt5.shutdown()

print("Done. Signals plotted. Review the chart to inspect markers and indicator overlays.")

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------
# User parameters
# -----------------------
SYMBOL = "XAUUSDc"          # symbol used earlier in conversation
TIMEFRAME = mt5.TIMEFRAME_M3
N_BARS = 2000               # number of bars to fetch
VG = None                   # Volume Gate: if None, will use median volume * param
VG_MULTIPLIER = 0.5         # VG = median(volume_last_100) * VG_MULTIPLIER (if VG unspecified)
VOLUME_BOOM_FACTOR = 2      # Current volume >= VOLUME_BOOM_FACTOR * sum(prev_k_volumes)
VOLUME_BOOM_LOOKBACK = 10   # number of previous candles to sum for boom check

# VTR specs as (multiplier m, lookback l)
VTR_SPECS = {
    "VTR_3_12": (3, 12),
    "VTR_10_1": (10, 1),
    "VTR_11_2": (11, 2),
}

WILDER_PERIOD = 14         # for DMag (ADX) calculations
DMAG_THRESHOLD = 20        # DMag > 20 required
VERBOSE = True

# -----------------------
# Helper functions
# -----------------------
def to_dataframe(mt5_rates):
    df = pd.DataFrame(mt5_rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=False)
    return df

def true_range(high, low, close_prev):
    return np.maximum.reduce([
        high - low,
        np.abs(high - close_prev),
        np.abs(low - close_prev)
    ])

def wilder_smoothing(series, period):
    """
    Wilder smoothing:
    first value = series[:period].sum()
    subsequent: prev_smoothed - (prev_smoothed / period) + current
    This returns an array aligned with original series (np.nan for first entries before period)
    """
    series = np.asarray(series, dtype=float)
    out = np.full_like(series, np.nan)
    if len(series) < period:
        return out
    # first smoothed value uses simple sum of first 'period' values
    first = series[:period].sum()
    out[period-1] = first
    prev = first
    for i in range(period, len(series)):
        curr = series[i]
        prev = prev - (prev / period) + curr
        out[i] = prev
    return out

# -----------------------
# Connect to MT5 and fetch data
# -----------------------
if not mt5.initialize():
    raise RuntimeError("Failed to initialize MT5. Make sure terminal is running and logged in.")

# request last N bars:
rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, N_BARS)
if rates is None or len(rates) == 0:
    mt5.shutdown()
    raise RuntimeError(f"No data returned for {SYMBOL}. Check symbol name and MT5 market watch.")

df = to_dataframe(rates)
# keep important columns and convert to pandas Series
df = pd.DataFrame({
    'time': pd.to_datetime(df['time'], unit='s'),
    'open': df['open'],
    'high': df['high'],
    'low': df['low'],
    'close': df['close'],
    'tick_volume': df['tick_volume'],  # use tick_volume as volume proxy
})
df.set_index('time', inplace=True)
df.sort_index(inplace=True)

# Working arrays
high = df['high'].values
low = df['low'].values
close = df['close'].values
vol = df['tick_volume'].values

# -----------------------
# Volume Gate & Volume Boom
# -----------------------
if VG is None:
    med = np.median(vol[-100:]) if len(vol) >= 100 else np.median(vol)
    VG = max(1.0, med * VG_MULTIPLIER)  # simple default
if VERBOSE:
    print(f"Volume Gate (VG) set to: {VG:.2f}")

# Volume Gate boolean series
volume_gate = vol >= VG

# Volume Boom: current volume >= factor * sum(prev K volumes)
vol_sum_prev_k = np.array([np.sum(vol[max(0,i-VOLUME_BOOM_LOOKBACK):i]) for i in range(len(vol))])
volume_boom = vol >= (VOLUME_BOOM_FACTOR * (vol_sum_prev_k))
# For first few bars vol_sum_prev_k may be small; we treat boom=False when insufficient history
volume_boom[:VOLUME_BOOM_LOOKBACK+1] = False

df['volume_gate'] = volume_gate
df['volume_boom'] = volume_boom

# -----------------------
# VTR calculations
# -----------------------
# Compute TR series (per-bar)
close_prev = np.roll(close, 1)
close_prev[0] = close[0]
TR = true_range(high, low, close_prev)
df['TR'] = TR

# VTR definition: VTR = m * (1/l) * sum_{i=0..l-1} TR_{t-i}
for name, (m, l) in VTR_SPECS.items():
    # rolling mean of TR over l bars
    if l <= 0:
        df[name] = 0.0
    else:
        df[name] = m * df['TR'].rolling(window=l, min_periods=l).mean()
# define a simple threshold for "VTR significant" using recent TR mean
recent_TR_mean = df['TR'].rolling(window=50, min_periods=1).mean()
# threshold multiplier (tuneable)
VTR_THRESHOLD_MULT = 1.2
df['vtr_threshold'] = recent_TR_mean * VTR_THRESHOLD_MULT

# compute boolean if all VTRs exceed threshold
df['vtr_all_above'] = True
for name in VTR_SPECS.keys():
    df['vtr_all_above'] &= (df[name] > df['vtr_threshold'])

# -----------------------
# +DM, -DM, TR smoothing -> +DI, -DI, DX, ADX (DMag)
# -----------------------
# raw +DM / -DM calculation
up_move = high - np.roll(high, 1)
down_move = np.roll(low, 1) - low
up_move[0] = 0.0
down_move[0] = 0.0
plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
df['+DM_raw'] = plus_dm
df['-DM_raw'] = minus_dm

# Wilder smoothing for +DM, -DM, TR
smoothed_TR = wilder_smoothing(df['TR'].values, WILDER_PERIOD)
smoothed_plus_dm = wilder_smoothing(df['+DM_raw'].values, WILDER_PERIOD)
smoothed_minus_dm = wilder_smoothing(df['-DM_raw'].values, WILDER_PERIOD)

# Avoid division by zero later; store in df aligned
df['TR_smooth'] = smoothed_TR
df['+DM_smooth'] = smoothed_plus_dm
df['-DM_smooth'] = smoothed_minus_dm

# +DI and -DI
df['+DI'] = 100.0 * (df['+DM_smooth'] / df['TR_smooth'])
df['-DI'] = 100.0 * (df['-DM_smooth'] / df['TR_smooth'])

# DX
df['DX'] = 100.0 * (np.abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))
# DX can be nan for early entries; set to 0
df['DX'] = df['DX'].fillna(0.0)

# ADX (Wilder smoothing of DX over period)
# We'll compute ADX as Wilder smoothed DX (common approach is initial average then wilder smoothing)
dx_vals = df['DX'].values
DMag = wilder_smoothing(dx_vals, WILDER_PERIOD)
df['DMag'] = DMag

# DMag rising check
df['DMag_rising'] = df['DMag'] > np.roll(df['DMag'], 1)
df['DMag_rising'].fillna(False, inplace=True)

# -----------------------
# Signal logic (visual-only)
# -----------------------
# Direction via DI
df['direction_bull'] = df['+DI'] > df['-DI']
df['direction_bear'] = df['+DI'] < df['-DI']

# final bullish signal: all confirmations
df['signal_buy'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bull'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

df['signal_sell'] = (
    df['volume_gate'] &
    df['volume_boom'] &
    df['vtr_all_above'] &
    df['direction_bear'] &
    (df['DMag'] > DMAG_THRESHOLD) &
    df['DMag_rising']
)

# remove signals at very early bars where indicators are nan
valid_idx = ~df[['TR', '+DM_smooth', '-DM_smooth', 'TR_smooth', 'DMag']].isnull().any(axis=1)
df.loc[~valid_idx, ['signal_buy','signal_sell']] = False

# -----------------------
# Plot with Plotly
# -----------------------
print("Preparing plot...")

candlestick = go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price',
    increasing_line_color='green',
    decreasing_line_color='red',
    opacity=0.9
)

volume_bar = go.Bar(
    x=df.index,
    y=df['tick_volume'],
    name='Tick Volume',
    yaxis='y2',
    opacity=0.6
)

# Buy / Sell markers
buy_markers = go.Scatter(
    x=df.index[df['signal_buy']],
    y=df['low'][df['signal_buy']] * 0.997,
    mode='markers',
    marker=dict(symbol='triangle-up', size=12, color='lime'),
    name='Buy Signal'
)
sell_markers = go.Scatter(
    x=df.index[df['signal_sell']],
    y=df['high'][df['signal_sell']] * 1.003,
    mode='markers',
    marker=dict(symbol='triangle-down', size=12, color='magenta'),
    name='Sell Signal'
)

# add VTR and DMag traces (scaled for overlay)
vtr_traces = []
for name in VTR_SPECS.keys():
    vtr_traces.append(go.Scatter(
        x=df.index,
        y=df[name],
        mode='lines',
        name=name,
        line=dict(width=1),
        yaxis='y3'
    ))

dmag_trace = go.Scatter(
    x=df.index,
    y=df['DMag'],
    mode='lines',
    name='DMag (ADX)',
    line=dict(width=2, dash='dash'),
    yaxis='y4'
)

layout = go.Layout(
    title=f"{SYMBOL} - Signals demo (no backtest) — last {len(df)} bars",
    xaxis=dict(rangeslider=dict(visible=False)),
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Volume", overlaying='y', side='right', showgrid=False, position=0.98),
    yaxis3=dict(title="VTRs (scaled)", overlaying='y', side='left', anchor='free', position=0.02, showgrid=False),
    yaxis4=dict(title="DMag", overlaying='y', side='right', anchor='free', position=0.98, showgrid=False),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=800
)

fig = go.Figure(data=[candlestick, volume_bar, buy_markers, sell_markers] + vtr_traces + [dmag_trace], layout=layout)

# Add simple annotations for VG and VTR threshold on volume and VTR panels
fig.add_hline(y=VG, line=dict(color='gray', dash='dot'), annotation_text="Volume Gate", annotation_position="top left")

# show
fig.show()

# -----------------------
# Cleanup
# -----------------------
mt5.shutdown()

print("Done. Signals plotted. Review the chart to inspect markers and indicator overlays.")