//@version=5
strategy("8PM–9PM Range Strategy + 4AM Candle", overlay=true, initial_capital=2000)

// ----------------------
// TIME SETTINGS
// ----------------------
tz = "Asia/Manila"
startHour = 20
endHour   = 21
riskPerc = 3.0

barHour = hour(time, tz)
barMin  = minute(time, tz)
inSession = barHour >= startHour and barHour < endHour
sessionOpen = barHour == startHour and barMin == 0
sessionClose = barHour == endHour and barMin == 0
is4am = barHour == 4 and barMin == 0

// ----------------------
// RANGE VARIABLES (from indicator)
// ----------------------
var float sHigh = na
var float sLow  = na
var int sStart = na
var int sEnd   = na
var bool touchedMid = false
var bool ordersPlaced = false

// capture range during session
if sessionOpen
    sHigh := high
    sLow  := low
    sStart := bar_index
    sEnd := na
    touchedMid := false
    ordersPlaced := false

if inSession
    sHigh := math.max(sHigh, high)
    sLow  := math.min(sLow, low)

if sessionClose and not na(sHigh)
    sEnd := bar_index

// ----------------------
// USE INDICATOR COORDINATES
// ----------------------
mid = (sHigh + sLow)/2
buyStop  = sHigh
buySL    = mid
buyTP    = sHigh + 2*(sHigh - mid)
sellStop = sLow
sellSL   = mid
sellTP   = sLow - 2*(mid - sLow)

// ----------------------
// DETECT MID TOUCH (entry condition)
// ----------------------
if not na(mid) and not ordersPlaced
    if high >= mid and low <= mid
        touchedMid := true

// ----------------------
// PLACE ORDERS BASED ON INDICATOR COORDINATES
// ----------------------
if touchedMid and not ordersPlaced
    riskAmount = strategy.equity * riskPerc / 100.0

    stopDistBuy = math.abs(buyStop - buySL)
    stopDistSell = math.abs(sellStop - sellSL)
    qtyBuy = stopDistBuy > 0 ? math.max(1, math.round(riskAmount / stopDistBuy)) : 0
    qtySell = stopDistSell > 0 ? math.max(1, math.round(riskAmount / stopDistSell)) : 0

    if qtyBuy > 0
        strategy.entry("BUY_STOP", strategy.long, qty=qtyBuy, stop=buyStop)
        strategy.exit("EXIT_BUY", from_entry="BUY_STOP", stop=buySL, limit=buyTP)

    if qtySell > 0
        strategy.entry("SELL_STOP", strategy.short, qty=qtySell, stop=sellStop)
        strategy.exit("EXIT_SELL", from_entry="SELL_STOP", stop=sellSL, limit=sellTP)

    ordersPlaced := true

// ----------------------
// CANCEL / CLOSE ORDERS AT 4AM
// ----------------------
if is4am
    strategy.cancel("BUY_STOP")
    strategy.cancel("SELL_STOP")
    if strategy.position_size > 0
        strategy.close("BUY_STOP")
    if strategy.position_size < 0
        strategy.close("SELL_STOP")
    touchedMid := false
    ordersPlaced := false
