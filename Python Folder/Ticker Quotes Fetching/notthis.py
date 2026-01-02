import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
import MetaTrader5 as mt5
import pandas as pd

# -----------------------------
# Title
# -----------------------------
title = "For  needed_tick_points, needed_pips_points, and needed_symbol_price_points data is about: {How much 'distance needed' equivalent of 1 unit risk (account's money as unit. It's 1 USC (cent, for cent accounts) or 1 USD (dollar, for dollar accounts) in Exness Broker) if using a 0.01 volume lot size.}"

# -----------------------------
# Initialize MT5
# -----------------------------
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account = mt5.account_info()
if account is None or "Exness" not in account.company:
    mt5.shutdown()
    raise RuntimeError("MT5 is not connected to Exness")

# -----------------------------
# Pre-calculated needed distances
# -----------------------------
symbols_needed = {
    "symbol": [
        "BTCUSDc","AUDCADc","AUDCHFc","AUDJPYc","AUDNZDc","AUDUSDc","CADJPYc","CHFJPYc",
        "EURAUDc","EURCADc","EURCHFc","EURGBPc","EURJPYc","EURNZDc","EURUSDc","GBPAUDc",
        "GBPCADc","GBPCHFc","GBPJPYc","GBPNZDc","GBPUSDc","NZDJPYc","NZDUSDc","USDCADc",
        "USDCHFc","USDHKDc","USDJPYc","XAGUSDc","XAUUSDc"
    ],
    "needed_tick_points": [
        10000,138,80,156,173,100,156,156,151,138,80,75,156,174,100,151,138,80,156,174,100,156,100,138,80,778,156,20,1000
    ],
    "needed_pips_points": [
        1000,13.8,8,15.6,17.3,10,15.6,15.6,15.1,13.8,8,7.5,15.6,17.4,10,15.1,13.8,8,15.6,17.4,10,15.6,10,13.8,8,77.8,15.6,2,100
    ],
    "needed_symbol_price_points": [
        100,0.00138,0.0008,0.156,0.00173,0.001,0.156,0.156,0.00151,0.00138,0.0008,0.00075,0.156,0.00174,0.001,0.00151,
        0.00138,0.0008,0.156,0.00174,0.001,0.156,0.001,0.00138,0.0008,0.00778,0.156,0.02,1
    ]
}

df_needed = pd.DataFrame(symbols_needed)

# -----------------------------
# Add live MT5 data including requested columns
# -----------------------------
live_data = []

for i, sym in enumerate(df_needed["symbol"]):
    info = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)

    if info is None or tick is None:
        live_data.append({
            "bid": None,
            "ask": None,
            "spread_tick_points": None,
            "spread_price_points": None,
            "spread_pips_points": None,
            "digits": None,
            "volume_min": None,
            "volume_max": None,
            "volume_step": None,
            "swap_long": None,
            "swap_short": None,
            "needed_symbol_price_points": None,
            "price_difference": None
        })
        continue

    digits = info.digits
    bid = tick.bid
    ask = tick.ask
    spread_tick = info.spread if info.spread is not None else (ask - bid if ask and bid else None)
    spread_price = (ask - bid) if ask and bid else None

    # Calculate spread in pips points
    pip_value = df_needed.loc[i, "needed_symbol_price_points"] / df_needed.loc[i, "needed_pips_points"]
    spread_pips_points = spread_price / pip_value if spread_price is not None else None

    # Format all price-related values based on digits
    bid_fmt = f"{bid:.{digits}f}" if bid is not None else None
    ask_fmt = f"{ask:.{digits}f}" if ask is not None else None
    spread_price_fmt = f"{spread_price:.{digits}f}" if spread_price is not None else None
    needed_symbol_price_fmt = f"{df_needed.loc[i, 'needed_symbol_price_points']:.{digits}f}"

    # Calculate price_difference
    price_difference = spread_price / df_needed.loc[i, "needed_symbol_price_points"] if spread_price is not None else None

    live_data.append({
        "bid": bid_fmt,
        "ask": ask_fmt,
        "spread_tick_points": spread_tick,
        "spread_pips_points": spread_pips_points,
        "spread_price_points": spread_price_fmt,
        "digits": digits,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "needed_symbol_price_points": needed_symbol_price_fmt,
        "price_difference": price_difference
    })

df_live = pd.DataFrame(live_data)

# -----------------------------
# Combine pre-calculated distances with live data
# -----------------------------
df = pd.concat([df_needed.drop(columns="needed_symbol_price_points"), df_live], axis=1)

# -----------------------------
# Rearrange columns
# -----------------------------
column_order = [
    "symbol",
    "needed_tick_points",
    "needed_pips_points",
    "needed_symbol_price_points",
    "bid",
    "ask",
    "spread_tick_points",
    "spread_pips_points",
    "spread_price_points",
    "price_difference",
    "digits",
    "volume_min",
    "volume_max",
    "volume_step",
    "swap_long",
    "swap_short"
]

df = df[column_order]

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 300)

# -----------------------------
# Print everything
# -----------------------------
print(title)
print(df)

# -----------------------------
# Shutdown MT5
# -----------------------------
mt5.shutdown()
