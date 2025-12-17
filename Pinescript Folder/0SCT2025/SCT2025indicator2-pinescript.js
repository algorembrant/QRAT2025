//@version=5
indicator("v6 Sunstoic VP&TPO", shorttitle = "v6 Sunstoic VP&TPO", overlay = true, max_lines_count = 500, max_boxes_count = 500, max_labels_count = 500, max_bars_back = 2000)


ti                                     = input.string(defval = "Regular", title = "Calculation Type", options = ["Regular", "Fixed Range", "Fixed Interval"], group = "Calculation Type")


auto                                   = input.string(defval = "Custom", options = ["Auto", "Custom"], title = "Auto Calculate Tick Levels? Custom?", inline = "1", group = "Current Session Configurations")
tickzz                                 = input.float(defval = 2000 ,title = "Ticks", inline = "1", group = "Current Session Configurations")
tickLevels                             = input.bool(false, title = "Show Tick Levels?", group = "Current Session Configurations")
textSize                               = input.string(defval = "Tiny", options = ["Auto","Tiny", "Small", "Normal", "Large", "Huge"], group = "Current Session Configurations")
showIb                                 = input.bool(defval = false, title = "Show Initial Balance Range?", group = "Current Session Configurations")
sess                                   = input.string(defval = "D", title = "Recalculate After How Much Time?", tooltip = "from 1 to 1440 for minutes \nfrom 1D to 365D for days \nfrom 1W to 52W for weeks \nfrom 1M to 12M for months", group = 'If "Regular" is Selected')
st                                     = input.time(defval = timestamp("19 Sep 2022 00:00 +0300"), title = "Fixed Range Start", group = 'If "Fixed Range" Is Selected')
timE                                   = input.session(defval = "1300-1700", title = "Time Range", group = 'If "Fixed Interval" is Selected', tooltip = 'Select "Fixed Interval" For The "Calculation Type" Setting To Activate This Feature')
showPre                                 = input.bool(defval = true, title = "Show Previous Sessions TPO?", group = "Previous Session Settings")
blackBox                                = input.bool(defval = false, title = "Segment Previous Sessions With Black Box?", group = "Previous Session Settings")
rang                                    = input.bool(defval = true, title = "Show Previous Sessions Ranges?", group = "Previous Session Settings")


distCalc                                = input.float(defval = 5.0, title = "% Distance to Hide Old SP Lines", tooltip = "If Price Exceeds The % Threshold Defined For This
                                             Setting (Price Distance From An Existing Sp Line - The Sp Line Will Dissapear Until Price Is Within Proximity Once More",
                                              group = "Previous Session Settings")
distCalc2                               = input.float(defval = 5.0, title = "% Distance to Hide Old VA Lines", tooltip = "If Price Exceeds The % Threshold Defined For This
                                             Setting (Price Distance From An Existing Va Line - The Va Line Will Dissapear Until Price Is Within Proximity Once More",
                                              group = "Previous Session Settings")
distCalc3                               = input.float(defval = 5.0, title = "% Distance to Hide Old POC Lines", tooltip = "If Price Exceeds The % Threshold Defined For This
                                             Setting (Price Distance From An Existing Poc Line - The Poc Line Will Dissapear Until Price Is Within Proximity Once More",
                                              group = "Previous Session Settings")


spShw                                  = input.bool(defval = true, title = "Show SP Lines and Labels", group = "Display Options", tooltip = "If Deselected, TPO Letters Will Only Turn Red When a SP Forms. No Other Identifying Features are Displayed")
fr                                     = input.bool(defval = true, title = "Show Fixed Range Label and Line?" , group ="Display Options")
warn                                   = input.bool(defval = true, title = "Show Warning", group = "Display Options")
col                                    = input.color(defval = color.gray, title = "Main Character Color (Gray Default)", group = "Colors")
col1                                   = input.color(defval = color.red  , title = "SP Character Color   (Red Default)", group = "Colors")
col2                                   = input.color(defval = color.yellow, title = "POC Character Color (Yellow Default)", group = "Colors")
col3                                   = input.color(defval = color.blue, title = "IB Character Color (Blue Default)", group = "Colors")
col4                                   = input.color(defval = color.rgb(0, 114, 59), title = "Value Area Color (Lime Default)", group = "Colors")
col5                                   = input.color(defval = color.rgb(163, 147, 0), title = "Value Area Letter Color (White Default)", group = "Colors")
fnt                                    = input.string(defval = "Default", title = "Font Type", options = ["Default", "Monospace"], group = "Colors")

if timeframe.isdwm
    ti := "Fixed Range"


if fr == true and barstate.islast
    line.new(math.round(st), close, math.round(st), close + 0.001, extend = extend.both, color = color.white, width = 4, xloc = xloc.bar_time)
    if ti != "Fixed Range"
        var box frStart = box.new(math.round(st), high + ta.tr, math.round(st), low - ta.tr,
     bgcolor = color.new(color.white, 100), border_color = na, text_size = size.normal, text_color = color.white, text_wrap = text.wrap_none,  text = "If Selected in Settings, \nFixed Range Begins Here", xloc = xloc.bar_time)


fixTime = time(timeframe.period, timE)


fonT = switch fnt
   
    "Default"   => font.family_default
    "Monospace" => font.family_monospace

finTim = switch ti
   
    "Regular" => timeframe.change(sess)
    "Fixed Range" => time[1] < st and time >= st
    "Fixed Interval" => na(fixTime[1]) and not na(fixTime)

sz = switch textSize
   
    "Auto"             => size.auto
    "Tiny"             => size.tiny
    "Small"            => size.small
    "Normal"           => size.normal
    "Large"            => size.large
    "Huge"             => size.huge

var string [] str = array.from(
   
     " A",
     " B",
     " C",
     " D",
     " E",
     " F",
     " G",
     " H",
     " I",
     " J",
     " K",
     " L",
     " M",
     " N",
     " O",
     " P",
     " Q",
     " R",
     " S",
     " T",
     " U",
     " V",
     " W",
     " X",
     " Y",
     " Z",
     " a",
     " b",
     " c",
     " d",
     " e",
     " f",
     " g",
     " h",
     " i",
     " j",
     " k",
     " l",  
     " m",
     " n",
     " o",
     " p",
     " q",
     " r",
     " s",
     " t",
     " u",
     " v",
     " w",
     " x",
     " y",
     " z"


     )


if barstate.isfirst

    sX = ""

    for i = 0 to 51
        sX := array.get(str, i) +  "1 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "2 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "3 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "4 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "5 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "6 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "7 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "8 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "9 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "10 "             // => Loops are run sequentially, not simultaneously, so string characters populate in order
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "11 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "12 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "13 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "14 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "15 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "16 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "17 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "18 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "19 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "20 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "21 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "22 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "23 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "24 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "25 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "26 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "27 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "28 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "29 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "30 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "31 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "32 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "33 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "34 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "35 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "36 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "37 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "38 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "39 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "39 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "40 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "41 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "42 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "43 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "44 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "45 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "46 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "47 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "48 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "49 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "50 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "51 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "52 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "53 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "54 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "55 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "56 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "57 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "58 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "59 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "60 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "61 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "62 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "63 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "64 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "65 "
        array.push(str, sX)
    for i = 0 to 51
        sX := array.get(str, i) +  "66 "
        array.push(str, sX)

cond(y, x) =>    
    not na(str.match(label.get_text(array.get(y, x)), "[1-9]"))

cond2(y, x) =>
    not na(str.match(label.get_text(array.get(y, x)), "[10-66]"))

atr                                      = ta.atr(14)
var float tickz                          = 0.0
ticks2 = array.new_float()


if ti == "Regular" or ti == "Fixed Interval"
    if last_bar_index - bar_index == 1601
        if syminfo.mintick >= 0.01
            tickz := auto == "Custom" ? tickzz :
             auto == "Auto" and timeframe.period == "1" ? atr * 50 :
             auto == "Auto" and timeframe.period == "5" ? atr * 40 :
                                                          atr * 30
           
        else
            tickz := auto == "Custom" ? tickzz : atr * 100000
else
    if time < st
        if syminfo.mintick >= 0.01
            tickz := auto == "Custom" ? tickzz :
             auto == "Auto" and timeframe.period == "1" ? atr * 50 :
             auto == "Auto" and timeframe.period == "5" ? atr * 40 :
                                                          atr * 30        
        else
            tickz := auto == "Custom" ? tickzz : atr * 100000        


var line [] tpoLines                = array.new_line()
ticks                               = array.new_float()
var float max                       = 0.0
var float min                       = 10000000
var float [] track                  = array.new_float()
var label [] pocL                   = array.new_label()
var float [] finChe                 = array.new_float()
var line j                          = line.new(time, high, time, low, color = color.aqua, width = 4, xloc = xloc.bar_time)
var int first                       = 0
var int firstBar                    = 0
max                                 := math.max(high, max)
min                                 := math.min(low, min)
var float ibF                       = 0.0
var line [] ib                      = array.new_line()
var label [] tpoLabels              = array.new_label()
var label [] SP                     = array.new_label()
var line  [] val                    = array.new_line()
var label [] VA                     = array.new_label()
var line ibBar                      = na
var linefill fil                    = na
var label op                        = label.new(time, open, xloc = xloc.bar_time, size = size.large, text_font_family = fonT, color = color.new(color.white, 100), text = "●", style = label.style_label_right, textcolor = color.blue)
var int timRound = 0
if session.isfirstbar_regular[4] and timRound == 0
    timRound := math.round(time - time[4])


timeCond = switch ti
   
    "Regular"        => last_bar_index - bar_index <= 1600
    "Fixed Range"    => time >= st
    "Fixed Interval" => last_bar_index - bar_index <= 1600


if timeCond
   
    if showIb == true and ti == "Regular"
        if time == ibF
           
            array.push(ib, line.new(first, max, time, max, color = color.new(col3, 50), xloc = xloc.bar_time))
            array.push(ib, line.new(first, min, time, min, color = color.new(col3, 50), xloc = xloc.bar_time))
       
        if array.size(ib) > 1
           
            linefill.new(array.get(ib, 0), array.get(ib, 1), color.new(col3, 95))
   
    if time == ibF and ti == "Regular"
        line.delete(ibBar)
        ibBar := line.new(first, max, first, min, color = color.blue, xloc =xloc.bar_time, width = 4)

    if finTim
       
        if array.size(val) > 0
            for i = 0 to array.size(val) - 1
                line.delete(array.shift(val))
       
        if array.size(VA) > 0
            for i = 0 to array.size(VA) - 1
                label.delete(array.shift(VA))
       
        if array.size(track) > 0
            array.clear(track)
       
        if array.size(finChe) > 0
            array.clear(finChe)
       
        if array.size(ib) > 0
            for i = 0 to array.size(ib) - 1
                line.delete(array.shift(ib))
       
        if array.size(tpoLines) > 0
            for i = 0 to array.size(tpoLines) - 1
                line.delete(array.shift(tpoLines))
       
        if array.size(tpoLabels) > 0
            for i = 0 to array.size(tpoLabels) - 1
                label.delete(array.shift(tpoLabels))
       
        if array.size(SP) > 0
            for i = 0 to array.size(SP) - 1
                label.delete(array.shift(SP))
       
        if array.size(pocL) > 0
            for i = 0 to array.size(pocL) - 1
                label.delete(array.shift(pocL))
       
        max := high
        min := low
       
        first := math.round(time)
        ibF   := math.round(timestamp(year, month, dayofmonth, hour + 1, minute, second))
       
        label.set_x(op, first), label.set_y(op, open)


        firstBar := bar_index
        array.push(ticks, low)
        array.push(track, low)
        for i = 1 to 500
            if array.get(ticks, i - 1) + (tickz * syminfo.mintick) <= high
                array.push(ticks, array.get(ticks, i - 1) + (tickz * syminfo.mintick))
            else
                break

        for i = 0 to array.size(ticks) - 1
            array.push(tpoLines, line.new(bar_index, array.get(ticks, i) ,
                                          bar_index + 1,  array.get(ticks, i),
                                          color = tickLevels == true ? color.new(color.lime, 75) : na, xloc = xloc.bar_index))
            array.push(tpoLabels, label.new(first,  array.get(ticks, i) , text = "   A", xloc = xloc.bar_time,
                                          color = color.new(col, 100), textcolor = col,  text_font_family = fonT, style = label.style_label_left))
        
if timeCond and not finTim and ti == "Regular"
  or barstate.islast and ti == "Fixed Range"
  or timeCond and not finTim and ti == "Fixed Interval" and fixTime


    calc = max - min
    var label ibav = label.new(bar_index, close, color = na, style = label.style_label_left,  text_font_family = fonT)
    if array.size(ib) > 1
        for i = 0 to array.size(ib) - 1
            line.set_x2(array.get(ib, i), time)
        label.set_y(ibav, math.avg(line.get_y1(array.get(ib, 0)), line.get_y1(array.get(ib, 1))))
        label.set_x(ibav, bar_index + 2)
        label.set_text(ibav, "Initial Balance Range")
        label.set_textcolor(ibav, col3)
        label.set_color(ibav,color.new(color.white, 100))
    else
        label.set_textcolor(ibav, na)
   
    if array.size(VA) > 0
        for i = 0 to array.size(VA) - 1
            label.delete(array.shift(VA))

    if array.size(val) > 0
        for i = 0 to array.size(val) - 1
            line.delete(array.shift(val))
       
    if array.size(tpoLines) > 0
        for i = 0 to array.size(tpoLines) - 1
            line.delete(array.shift(tpoLines))
   
    if array.size(tpoLabels) > 0
        for i = 0 to array.size(tpoLabels) - 1
            label.delete(array.shift(tpoLabels))
    if array.size(SP) > 0
        for i = 0 to array.size(SP) - 1
            label.delete(array.shift(SP))
   
    if array.size(pocL) > 0
        for i = 0 to array.size(pocL) - 1
            label.delete(array.shift(pocL))
   
    if array.size(finChe) > 0
        array.clear(finChe)


    if array.size(track) > 0
        array.push(ticks, array.get(track, array.size(track) - 1))
        for i = 1 to 500
            if array.get(ticks, i - 1) + (tickz * syminfo.mintick) <= max
                array.push(ticks, array.get(ticks, i - 1) + (tickz * syminfo.mintick))
            else
                break
        array.push(ticks2, array.get(track, array.size(track) - 1))
        for i = 1 to 500
            if array.get(ticks2, i - 1) - (tickz * syminfo.mintick) >= min
                array.push(ticks2, array.get(ticks2, i - 1) - (tickz * syminfo.mintick))
            else
                break
        for i = array.size(ticks2) - 1 to 0


            array.push(tpoLines, line.new( first, array.get(ticks2, i),


                                                 last_bar_time,  
                                                 array.get(ticks2, i),
                                                 color = tickLevels == true ? color.new(color.lime, 75) : na,
                                                 xloc = xloc.bar_time


                                                 ))


            array.push(tpoLabels, label.new( first, array.get(ticks2, i),


                                                 color = color.new(color.white, 100),
                                                 textcolor = col,
                                                 size = sz,
                                                 style = label.style_label_left,
                                                 xloc = xloc.bar_time ,
                                                 text_font_family = fonT
                                                 ))                
        for i = 0 to array.size(ticks) - 1
            array.push(tpoLines, line.new( first, array.get(ticks, i),


                                                 last_bar_time,  
                                                 array.get(ticks, i),
                                                 color = tickLevels == true ? color.new(color.lime, 75) : na,
                                                 xloc = xloc.bar_time


                                                 ))


            array.push(tpoLabels, label.new( first, array.get(ticks, i),


                                                 color = color.new(color.white, 100),
                                                 textcolor = col,
                                                 size = sz,
                                                 style = label.style_label_left,
                                                 xloc = xloc.bar_time,
                                                 text_font_family = fonT
                                                 ))


    if array.size(tpoLines) > 1 and bar_index - firstBar < array.size(str)
       
        levels = array.new_float()
        che = array.new_float(array.size(tpoLines), 0)
        for i = bar_index - firstBar to 0
            for x = 0 to array.size(tpoLines) - 1
                if line.get_y1(array.get(tpoLines, x)) <= high[i] and line.get_y1(array.get(tpoLines, x)) >= low[i]
                    label.set_text(array.get(tpoLabels, x),
                     text = label.get_text(array.get(tpoLabels, x)) + array.get(str, math.abs(bar_index - firstBar - i)))
                    array.set(che, x, array.get(che, x) + 1)
                   
       
        len = 0.0
        for x = 0 to array.size(tpoLabels) - 1
            len := math.max(len, array.get(che, x))
       
        lenTrack = 0
       
        for x = 0 to array.size(tpoLabels) - 1
           
            if array.get(che, x) == len
                label.set_textcolor(array.get(tpoLabels, x), col2)
                lenTrack := x
                if bar_index - firstBar >= 4
                   
                    line.set_color(array.get(tpoLines, x), color.new(col2, 75))
                    line.set_width(array.get(tpoLines, x), 2)
                    array.push(finChe, line.get_y1(array.get(tpoLines, x)))
                    if array.size(finChe) == 1
                        array.push(pocL, label.new(first, line.get_y1(array.get(tpoLines, x)), xloc = xloc.bar_time,
                         color = color.new(col, 100), textcolor = col2, style = label.style_label_right,  text_font_family = fonT, text = "POC", size = sz))
                       
                       
                        break
 
        sum = array.new_float()
        sum1 = array.new_float()
        lin = array.new_float()
        lin1 = array.new_float()
        cheX = array.new_float()
        cheX1 = array.new_float()
           
        if lenTrack > 0
            for x = lenTrack - 1 to 0
                array.push(sum , array.size(sum) == 0 ? array.get(che, x) : array.get(sum, array.size(sum) - 1) + array.get(che, x))
                array.push(lin, label.get_y(array.get(tpoLabels, x)))
                array.push(cheX, array.get(che, x))
            for x = lenTrack to array.size(che) - 1
                array.push(sum1, array.size(sum1) == 0 ? array.get(che, x) : array.get(sum1, array.size(sum1) - 1) + array.get(che, x))
                array.push(lin1, label.get_y(array.get(tpoLabels, x)))
                array.push(cheX1, array.get(che, x))
               
               
            miN = math.min(array.size(sum), array.size(sum1))
           
           
            for n = 0 to miN - 1
                if array.get(sum, n) + array.get(sum1, n) >= array.sum(che) * .7
                    array.push(val,line.new(first , array.get(lin, n), time,
                     array.get(lin, n), xloc = xloc.bar_time, color = color.new(col4, 75)))
                     
                    array.push(val,line.new(first, array.get(lin1, n), time,
                     array.get(lin1, n), xloc = xloc.bar_time, color = color.new(col4, 75)))
                   
                    array.push(VA, label.new(first, line.get_y1(array.get(val, 0)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAH" : "VAL",
                     textcolor = col4, size = sz, color = color.new(color.white, 100), style = label.style_label_right, text_font_family = fonT, xloc = xloc.bar_time))
                   
                    array.push(VA, label.new(first, line.get_y1(array.get(val, 1)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAL" : "VAH",
                     textcolor = col4, size = sz, color = color.new(color.white, 100), style = label.style_label_right, text_font_family = fonT, xloc = xloc.bar_time))
                                               
                   
                    break
                         
            if array.size(val) < 2
           
                stop = 0
           
                if miN == array.size(sum1)
               
               
                    for n = 0 to array.size(cheX1) - 1
                        if array.get(cheX1, n) >= math.round(len * .7)
                            stop := n
                    for n = 0 to array.size(sum) - 1    
                   
                        if array.get(sum, n) + array.get(sum1, stop) >= array.sum(che) * .7
                           
                            array.push(val,line.new(first, array.get(lin, n), time,
                             array.get(lin, n), xloc = xloc.bar_time, color = color.new(col4, 75)))
                           
                            array.push(val,line.new(first, array.get(lin1, stop), time,
                             array.get(lin1, stop), xloc = xloc.bar_time, color = color.new(col4, 75)))
                                   
                            array.push(VA, label.new(first, line.get_y1(array.get(val, 0)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAH" : "VAL",
                             textcolor = col4, size = sz, color = color.new(color.white, 100),  text_font_family = fonT, style = label.style_label_right, xloc = xloc.bar_time))
                           
                            array.push(VA, label.new(first, line.get_y1(array.get(val, 1)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAL" : "VAH",
                             textcolor = col4, size = sz, color = color.new(color.white, 100),  text_font_family = fonT, style = label.style_label_right, xloc = xloc.bar_time))
                                               
                            break
               
                else
               
                    for n = 0 to array.size(cheX) - 1
                        if array.get(cheX, n) >= math.round(len * .7)
                            stop := n
                    for n = 0 to array.size(sum1) - 1    
                   
                        if array.get(sum, stop) + array.get(sum1, n) >= array.sum(che) * .7
                   
                            array.push(val,line.new(first, array.get(lin1, n), time,
                             array.get(lin1, n), xloc = xloc.bar_time, color = color.new(col4, 75)))
                       
                            array.push(val,line.new(first, array.get(lin, stop), time,
                             array.get(lin, stop), xloc = xloc.bar_time, color = color.new(col4, 75)))
                                   
                            array.push(VA, label.new(first, line.get_y1(array.get(val, 0)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAH" : "VAL",
                             textcolor = col4, size = sz, color = color.new(color.white, 100),  text_font_family = fonT, style = label.style_label_right, xloc = xloc.bar_time))
                           
                            array.push(VA, label.new(first, line.get_y1(array.get(val, 1)), text = line.get_y1(array.get(val, 0)) > line.get_y1(array.get(val, 1)) ? "VAL" : "VAH",
                             textcolor = col4, size = sz, color = color.new(color.white, 100),  text_font_family = fonT, style = label.style_label_right, xloc = xloc.bar_time))
                                                     
                            break                
         
        if array.size(val) == 2 and array.size(pocL) > 0 and array.size(tpoLabels) > 0
            fil := linefill.new(array.get(val, 0), array.get(val, 1), color = color.new(col4, 90))
           
            for i = 0 to array.size(tpoLabels) - 1
                if line.get_y1(array.get(val, 0)) > line.get_y2(array.get(val, 1))
                    if label.get_y(array.get(tpoLabels, i)) <= line.get_y1(array.get(val, 0))
                      and label.get_y(array.get(tpoLabels, i)) >= line.get_y1(array.get(val, 1))
                      and label.get_y(array.get(tpoLabels, i)) != label.get_y(array.get(pocL, 0))
                        label.set_textcolor(array.get(tpoLabels, i), col5)
                   
                    else if label.get_y(array.get(tpoLabels, i)) == label.get_y(array.get(pocL, 0))
                        label.set_textcolor(array.get(tpoLabels, i), col2)
           
           
                else
                   
                    if label.get_y(array.get(tpoLabels, i)) >= line.get_y1(array.get(val, 0) )
                      and label.get_y(array.get(tpoLabels, i)) <= line.get_y1(array.get(val, 1))
                      and label.get_y(array.get(tpoLabels, i)) != label.get_y(array.get(pocL, 0))
                        label.set_textcolor(array.get(tpoLabels, i), col5)                          
                   
                    else if label.get_y(array.get(tpoLabels, i)) == label.get_y(array.get(pocL, 0))
                        label.set_textcolor(array.get(tpoLabels, i), col2)
         
         
        for x = 0 to array.size(tpoLabels) - 1
            if str.length(label.get_text(array.get(tpoLabels, x))) == 2
              or str.length(label.get_text(array.get(tpoLabels, x))) == 5 and cond2(tpoLabels, x) == true
              or str.length(label.get_text(array.get(tpoLabels, x))) == 4 and cond(tpoLabels, x) == true
                label.set_textcolor(array.get(tpoLabels, x), col1)
                if bar_index - firstBar >= 4 and spShw == true
                    line.set_color(array.get(tpoLines, x), color.new(col1, 75))
                    array.push(SP, label.new(time, line.get_y1(array.get(tpoLines, x)), xloc = xloc.bar_time, color = color.new(col, 100),
                     style = label.style_label_left, text = "SP", textcolor = col1,  text_font_family = fonT, size = size.tiny))
               
        if array.size(VA) == 2 and array.size(pocL) > 0
            if label.get_y(array.get(VA, 0)) == label.get_y(array.get(pocL, 0))
                label.set_x(array.get(VA, 0), first - timRound)
            if label.get_y(array.get(VA, 1)) == label.get_y(array.get(pocL, 0))
                label.set_x(array.get(VA, 1), first - timRound)
if ti == "Regular" or ti == "Fixed Range"  
    line.set_x1(j, first)
    line.set_x2(j, first)
    line.set_y1(j, max)
    line.set_y2(j, min)    
else
    if fixTime  
        line.set_x1(j, first)
        line.set_x2(j, first)
        line.set_y1(j, max)
        line.set_y2(j, min)    

var line  [] SPCopy        = array.new_line()
var line  [] valCopy       = array.new_line()
var label [] tpoLabelsCopy = array.new_label()
var line  [] pocCopy       = array.new_line()
var line  [] jCopy         = array.new_line()
var line  [] ibBarCopy     = array.new_line()
var box   [] bBox          = array.new_box()


tCnd = hour == str.tonumber(str.substring(timE, str.pos(timE, "-") + 1, str.length(timE) - 2))
     and minute == str.tonumber(str.substring(timE, str.pos(timE, "-") + 3))


if session.islastbar and barstate.isconfirmed
   and timeCond and ti == "Regular" and array.size(tpoLabels) > 0
   and showPre == true
   or tCnd and barstate.isconfirmed and timeCond and ti == "Fixed Interval"
   and array.size(tpoLabels) > 0 and showPre == true
   
    if blackBox == true  
        array.push(bBox, box.new(first, max, time, min, xloc = xloc.bar_time, bgcolor = #000000, border_color = na))
    if rang == true


        array.push(jCopy, line.copy(j))
        array.push(ibBarCopy, line.copy(ibBar))
    if array.size(val) > 0 and distCalc2 != 0
        for i = 0 to array.size(val) - 1
            array.push(valCopy, line.copy(array.get(val, i)))


    if array.size(tpoLabels) > 0
        for i = 0 to array.size(tpoLabels) - 1
            array.push(tpoLabelsCopy, label.copy(array.get(tpoLabels, i)))
            if label.get_y(array.get(tpoLabels, i)) == label.get_y(array.get(pocL, 0))
                array.push(pocCopy, line.copy(array.get(tpoLines, i)))
   
    if array.size(SP) > 0 and distCalc != 0
        for i = 0 to array.size(SP) - 1
            array.push(SPCopy, line.new(first, label.get_y(array.get(SP, i)), time, label.get_y(array.get(SP, i)), xloc = xloc.bar_time, color = color.new(col1, 80)))
   


if array.size(SPCopy) > 0
    for i = 0 to array.size(SPCopy) - 1
        if line.get_y1(array.get(SPCopy, i)) <= high and line.get_y1(array.get(SPCopy, i)) >= low  
            line.delete(array.get(SPCopy, i))
        else
            if math.abs((close / line.get_y1(array.get(SPCopy, i))- 1)* 100) <= distCalc
                line.set_x2(array.get(SPCopy, i), time)
            else if math.abs((close / line.get_y1(array.get(SPCopy, i)) - 1)* 100) >= distCalc
                line.set_x2(array.get(SPCopy, i), line.get_x1(array.get(SPCopy, i)))
               
if array.size(valCopy) > 0
    for i = 0 to array.size(valCopy) - 1
        if line.get_y1(array.get(valCopy, i)) <= high and line.get_y1(array.get(valCopy, i)) >= low  
            line.delete(array.get(valCopy, i))
        else if math.abs((close / line.get_y1(array.get(valCopy, i))- 1)* 100) <= distCalc2
            line.set_x2(array.get(valCopy, i), time)
        else if math.abs((close / line.get_y1(array.get(valCopy, i)) - 1)* 100) >= distCalc2
            line.set_x2(array.get(valCopy, i), line.get_x1(array.get(valCopy, i)))


if array.size(pocCopy) > 0
    for i = 0 to array.size(pocCopy) - 1
        if line.get_y1(array.get(pocCopy, i)) <= high and line.get_y1(array.get(pocCopy, i)) >= low  
            line.delete(array.get(pocCopy, i))
        else if math.abs((close / line.get_y1(array.get(pocCopy, i))- 1)* 100) <= distCalc3
            line.set_x2(array.get(pocCopy, i), time)
        else if math.abs((close / line.get_y1(array.get(pocCopy, i)) - 1)* 100) >= distCalc3
            line.set_x2(array.get(pocCopy, i), line.get_x1(array.get(pocCopy, i)))


if array.size(tpoLabelsCopy) > 500
    for i = 0 to array.size(tpoLabelsCopy) - 500
        label.delete(array.shift(tpoLabelsCopy))
    if array.size(ibBarCopy) > 1
        line.delete(array.shift(ibBarCopy))
        line.delete(array.shift(jCopy))
    if array.size(bBox) > 1
        box.delete(array.shift(bBox))


tf = input.timeframe("D", title = "Timeframe", inline = "0", group = "PROFILE SETTINGS")


vap = input.float(70, title = "Value Area %", group = "PROFILE SETTINGS")/100
lb_days = input.int(5, title = "# of Profiles", maxval = 20, minval = 1, tooltip = "Max: 20 \nLarge Display = Less Granular Profiles\nSmall Display = More Granular Profiles")
mp = input.bool(false, title = "Calculate As Market Profile", group = "PROFILE SETTINGS", tooltip = "Calculations will distribue a 1 instead of the candle's volume.")


disp_size = input.int(-10, minval = -500,maxval = 500,title  = "Display Size   ", inline = "3", group = "DISPLAY SETTINGS", tooltip = "The entire range of your profile will scale to fit inside this range.\n When Positive, the profile will display from the start of the day. \n When Negative, the profile will display from the end of the day.\nNotes:\n-This value is # bars away from your profile's Axis.\n-The farther from 0 this value is, the more granular your (horizontal) view will be. This does not change the Profiles' value; because of this, sometimes the POC looks tied with other values widely different. The POC CAN be tied to values close to it, but if the value is far away it is likely to just be a visual constraint. \n AUTO SCALE - Fits the profile within the lookback period.")
auto_size = input.bool(true, title = "Auto-Scale", inline = "3", group = "DISPLAY SETTINGS")


hi_width = input.int(10, maxval = 100, minval = 1,title = "[HVN] Analysis Width %      ↕", group = "High/Low Volume Nodes", tooltip = "[HVN] = High Volume Node\nAnalysis Width % = % of profile to take into account when determining what is a High Volume Node and what is Not.")*0.01
lo_width = input.int(10, maxval = 100, minval = 1, title = "[LVN]  Analysis Width %      ↕", group = "High/Low Volume Nodes", tooltip = "[LVN] = Low Volume Node\nAnalysis Width % = % of profile to take into account when determining what is a Low Volume Node and what is Not.")*0.01


poc_color = input.color(#d3be00, title = "POC Color", group = "Colors")
var_color = input.color(#886000, title = "Value High/Low Color", group = "Colors")
vaz_color = input.color(color.new(#886000,0), title = "Value Zone Color", group = "Colors")
ov_color = input.color(#886000, title = "Profile Color", group = "Colors")
lv_color = input.color(#886000, title  = "Low Volume Color", group = "Colors")
hv_color = input.color(#886000, title = "High Volume Color", group = "Colors")


fix_z(_val) => _val>0?_val:1


round_to(_round,_to) =>
    math.round(_round/_to)*_to


vgroup_pull(_var,_array,_num1,_num2) =>
    _var == 1 and _num1>=_num2?array.get(_array,_num1-_num2):
      _var == 2 and array.size(_array)-1 >= (_num1 + _num2)?array.get(_array,_num1+_num2)
      :0


prof_color(_num,_mv,_a1,_a2,_a3,_a4) =>
    _num==0?na:
     _num==_mv?poc_color:
     (_num==_a3 or _num==_a4)?var_color:
     array.includes(_a1,_num) and array.includes(_a2,_num)?((_num>_a3 or _num<_a4)?ov_color:vaz_color):
     array.includes(_a2,_num)?lv_color:
     array.includes(_a1,_num)?hv_color:
     (_num>_a3 or _num<_a4)?ov_color:
     vaz_color  


var line_array = array.new_line(na)
var box_array = array.new_box(na)


kill_bar = ta.valuewhen(timeframe.change(tf),bar_index,lb_days+1)+1
if array.size(line_array) > 0
    for i = array.size(line_array)-1 to 0
        ln = array.get(line_array,i)
        lx = line.get_x1(ln)
        if lx <= kill_bar
            line.delete(ln)
            array.remove(line_array,i)
if array.size(box_array) > 0
    for i = array.size(box_array)-1 to 0
        bx = array.get(box_array,i)
        bl = box.get_left(bx)
        if bl <= kill_bar or na(bl)
            box.delete(bx)
            array.remove(box_array,i)
if array.size(label.all) > 0
    for i = array.size(label.all)-1 to 0
        lb = array.get(label.all,i)
        lx = label.get_x(lb)
        if lx <= kill_bar
            label.delete(lb)
            array.remove(label.all,i)


get_prof(_mp,_tf) =>
    new_calc = timeframe.change(_tf)
    last_new_calc = ta.valuewhen(new_calc,bar_index,1)
    index_num = math.floor(1000/lb_days)-1
    start_time = request.security("",_tf,ta.valuewhen(bar_index == last_bar_index-lb_days,time,0))
    calc_bars = (bar_index - ta.valuewhen(new_calc,bar_index,0))[1]+1
    base = ta.lowest(low,fix_z(calc_bars)+1)[1]
    roof = ta.highest(high,fix_z(calc_bars)+1)[1]
    tick_size = round_to(math.max(((roof - base)/index_num),syminfo.mintick),(syminfo.mintick/100))
    c_hi = round_to(high,tick_size)
    c_lo = round_to(low,tick_size)
    candle_range = c_hi - c_lo
    candle_index = (candle_range/tick_size)+1
    tick_vol = _mp?1:volume/candle_index
    main = array.new_float(na)
    hvn_points = array.new_int(na)
    lvn_points = array.new_int(na)
    if new_calc and time >= start_time
        for i = 0 to index_num
            index_price = base + (i*tick_size)
            if index_price >= roof
                break
            float index_sum = 0
            for e = 1 to calc_bars
                if index_price <= c_hi[e] and index_price >= c_lo[e]
                    index_sum := index_sum + tick_vol[e]
            array.push(main,index_sum)
        max_index = math.round(math.avg(array.indexof(main,array.max(main)),array.lastindexof(main,array.max(main))))
        poc = base + (tick_size*max_index)
        max_vol = array.sum(main)*vap
        vol_count = max_index >=0?array.get(main, max_index):0.0
        up_count = max_index
        down_count = max_index
        if array.size(main) > 0
            for x = 0 to array.size(main)-1
                if vol_count >= max_vol
                    break                                                                  
                uppervol = up_count<array.size(main)-1?array.get(main, up_count + 1):na
                lowervol = down_count>0?array.get(main, down_count - 1):na
                if ((uppervol >= lowervol) and not na(uppervol)) or na(lowervol)
                    vol_count += uppervol
                    up_count += 1
                else                                                                        
                    vol_count += lowervol
                    down_count -= 1
        val = base + (tick_size*down_count)
        vah = base + (tick_size*up_count)
        uc = up_count
        dc = down_count
       

        ///////////////////////////////
        //Cluster ID for Volume Nodes//
        ///////////////////////////////
 
        if array.size(main) > 0
            for i = 0 to array.size(main)-1                    
                _val = array.get(main,i)                        
                ary = array.new_float(na)                              
                for e = 0 to int(array.size(main)*hi_width)                          
                    array.push(ary,vgroup_pull(1,main,i,e))        
                    array.push(ary,vgroup_pull(2,main,i,e))      
                max = array.max(ary)                      
                if _val >= math.avg(max,array.avg(ary))  
                    array.push(hvn_points,i)          


        if array.size(main) > 0    
            for i = 0 to array.size(main)-1
                _val = array.get(main,i)
                ary = array.new_float(na)
                for e = 0 to int(array.size(main)*lo_width)  
                    array.push(ary,vgroup_pull(1,main,i,e))
                    array.push(ary,vgroup_pull(2,main,i,e))
                min = array.min(ary)
                if _val <= math.avg(min,array.avg(ary))  
                    array.push(lvn_points,i)
        ///_________________________________________
        ///Cluster Merging
        ///‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
        merge_per = 0.02
        if array.size(hvn_points)>0
            for i = 0 to array.size(hvn_points)-1
                hi_found = false
                lo_found = false
                _val = array.get(hvn_points,i)
                for e = int(array.size(main)*merge_per) to 0
                    if array.includes(hvn_points,_val+e)
                        hi_found := true
                    if hi_found
                        array.push(hvn_points,_val+e)
                    if array.includes(hvn_points,_val-e)
                        lo_found := true
                    if lo_found
                        array.push(hvn_points,_val-e)


        if array.size(lvn_points)>0
            for i = 0 to array.size(lvn_points)-1
                hi_found = false
                lo_found = false
                _val = array.get(lvn_points,i)
                for e = int(array.size(main)*merge_per) to 0
                    if array.includes(lvn_points,_val+e)
                        hi_found := true
                    if hi_found
                        array.push(lvn_points,_val+e)
                    if array.includes(lvn_points,_val-e)
                        lo_found := true
                    if lo_found
                        array.push(lvn_points,_val-e)
        prof_axis = disp_size>0?last_new_calc:bar_index[1]
        display_size = auto_size and disp_size!=0?(disp_size/math.abs(disp_size))*(calc_bars-1):disp_size
        

        if array.size(main) > 0
            for i = 0 to array.size(main) - 1
                scale = display_size/array.max(main)
                scaled = math.round(array.get(main,i)*scale)
                if ((i>uc) or (i<dc)) and (array.size(line_array) <= 499)
                    array.push(line_array,line.new(prof_axis,base+(i*tick_size[1]),(prof_axis+scaled),base+(i*tick_size[1]), color = prof_color(i,max_index,hvn_points,lvn_points,uc,dc), style = (i<dc or i>uc?line.style_dotted:line.style_solid)))
                else if ((i<=uc) or (i>=dc)) and (array.size(box_array) <= 499)
                    array.push(box_array,box.new(prof_axis,base+(i*tick_size[1]),(prof_axis+scaled),base+(i*tick_size[1]), border_color = prof_color(i,max_index,hvn_points,lvn_points,uc,dc), border_style = (i<dc or i>uc?line.style_dotted:line.style_solid), border_width = 1))
                else if (array.size(line_array) <= 499)
                    array.push(line_array,line.new(prof_axis,base+(i*tick_size[1]),(prof_axis+scaled),base+(i*tick_size[1]), color = prof_color(i,max_index,hvn_points,lvn_points,uc,dc), style = (i<dc or i>uc?line.style_dotted:line.style_solid)))
                else if (array.size(box_array) <= 499)
                    array.push(box_array,box.new(prof_axis,base+(i*tick_size[1]),(prof_axis+scaled),base+(i*tick_size[1]), border_color = prof_color(i,max_index,hvn_points,lvn_points,uc,dc), border_style = (i<dc or i>uc?line.style_dotted:line.style_solid), border_width = 1))
             
get_prof(mp,tf)
