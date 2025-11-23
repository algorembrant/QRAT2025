//@version=5
indicator("8PM–9PM Range Strategy (Midpoint as SL) + 4AM Candle", overlay=true, max_lines_count=500, max_labels_count=500, max_boxes_count=200)

//──────────────────────────────
// SETTINGS
//──────────────────────────────
tz = "Asia/Manila"
startHour = 20
endHour   = 21

//──────────────────────────────
// TIME DETECTION
//──────────────────────────────
barHour = hour(time, tz)
barMin  = minute(time, tz)
inSession    = barHour >= startHour and barHour < endHour
sessionOpen  = barHour == startHour and barMin == 0
sessionClose = barHour == endHour and barMin == 0

//──────────────────────────────
// TRACK RANGE DURING SESSION
//──────────────────────────────
var float sHigh = na
var float sLow  = na
var int   sStart = na
var int   sEnd   = na
var box   sBox = na

if sessionOpen
    sHigh := high
    sLow  := low
    sStart := bar_index
    sEnd := na

if inSession
    sHigh := math.max(sHigh, high)
    sLow  := math.min(sLow, low)

if sessionClose and not na(sHigh)
    sEnd := bar_index

    //──────────────────────────────
    // RANGE BOX
    //──────────────────────────────
    if not na(sBox)
        box.delete(sBox)
    sBox := box.new(
         left = sStart,
         right = sEnd,
         top = sHigh,
         bottom = sLow,
         bgcolor = color.new(#000000, 85),
         border_color = color.new(#000000, 0))

    //──────────────────────────────
    // CORE LEVELS
    //──────────────────────────────
    mid = (sHigh + sLow) / 2

    // BUY setup
    buyStop = sHigh
    buySL   = mid
    buyTP   = sHigh + (math.abs(sHigh - mid) * 2)

    // SELL setup (mirror)
    sellStop = sLow
    sellSL   = mid
    sellTP   = sLow - (math.abs(mid - sLow) * 2)

    //──────────────────────────────
    // DRAW RANGE LINES
    //──────────────────────────────
    line.new(sStart, sHigh, sEnd, sHigh, color=color.new(color.green, 0), style=line.style_dotted)
    line.new(sStart, sLow, sEnd, sLow, color=color.new(color.red, 0), style=line.style_dotted)
    line.new(sStart, mid, sEnd, mid, color=color.new(color.orange, 0), style=line.style_dotted)

    //──────────────────────────────
    // DRAW BUY SETUP
    //──────────────────────────────
    line.new(sEnd, buyStop, sEnd + 5, buyStop, color=color.new(color.lime, 0), width=2)
    line.new(sEnd, buySL, sEnd + 5, buySL, color=color.new(color.orange, 0), width=2, style=line.style_dashed)
    line.new(sEnd, buyTP, sEnd + 5, buyTP, color=color.new(color.lime, 0), width=2, style=line.style_dotted)

    label.new(sEnd + 5, buyStop,text=str.format("BUY STOP\n{0}", str.tostring(buyStop, format.mintick)),style=label.style_label_left, color=color.new(color.lime, 0), textcolor=color.white, size=size.tiny)

    label.new(sEnd + 5, buySL,text=str.format("SL (MID)\n{0}", str.tostring(buySL, format.mintick)), style=label.style_label_left, color=color.new(color.orange, 0), textcolor=color.white, size=size.tiny)

    label.new(sEnd + 5, buyTP,text=str.format("BUY TP\n{0}", str.tostring(buyTP, format.mintick)),style=label.style_label_left, color=color.new(color.lime, 0), textcolor=color.white, size=size.tiny)

    //──────────────────────────────
    // DRAW SELL SETUP
    //──────────────────────────────
    line.new(sEnd, sellStop, sEnd + 5, sellStop, color=color.new(color.red, 0), width=2)
    line.new(sEnd, sellSL, sEnd + 5, sellSL, color=color.new(color.orange, 0), width=2, style=line.style_dashed)
    line.new(sEnd, sellTP, sEnd + 5, sellTP, color=color.new(color.red, 0), width=2, style=line.style_dotted)

    label.new(sEnd + 5, sellStop, text=str.format("SELL STOP\n{0}", str.tostring(sellStop, format.mintick)), style=label.style_label_left, color=color.new(color.red, 0), textcolor=color.white, size=size.tiny)

    label.new(sEnd + 5, sellSL,text=str.format("SL (MID)\n{0}", str.tostring(sellSL, format.mintick)), style=label.style_label_left, color=color.new(color.orange, 0), textcolor=color.white, size=size.tiny)

    label.new(sEnd + 5, sellTP,  text=str.format("SELL TP\n{0}", str.tostring(sellTP, format.mintick)), style=label.style_label_left, color=color.new(color.red, 0),textcolor=color.white, size=size.tiny)

//──────────────────────────────
// 4:00 AM CANDLE HIGHLIGHT
//──────────────────────────────
is4am = barHour == 4 and barMin == 0
var box box4am = na
if is4am
    if not na(box4am)
        box.delete(box4am)
    box4am := box.new( left = bar_index, right = bar_index + 1, top = high,  bottom = low,  bgcolor = color.new(color.blue, 75), border_color = color.new(color.blue, 0))
    label.new(bar_index, high, "4 AM", style=label.style_label_down, color=color.new(color.blue, 0),textcolor=color.white,size=size.tiny)
