# Detailed Analysis of the Trading System (From Image)

This document provides a full technical explanation of the formulas,
logic, and signal construction shown in the reference image. It covers
Volume Conditions, VTR logic, Directional Movement (DM), DI, DX, and
DMag (ADX), including how everything connects into a complete trading
signal framework.

------------------------------------------------------------------------

## 1. Notation & Preliminaries

-   `t` : current candle index\
-   `t-1`, `t-i` : previous candles\
-   `High_t`, `Low_t`, `Close_t`, `Open_t` : OHLC values\
-   `Vol_t` : current volume (tick or real volume)\
-   `TR_t` : True Range\
-   `VTR(m,l)` : Volatility Threshold Range

All calculations are performed bar-by-bar with proper shifting.

------------------------------------------------------------------------

## 2. Volume Gate (VG)

**Condition:**

    Vol_t ≥ VG

Where:

    VG = mean(Vol_{t-L} ... Vol_{t-1}) × factor

This ensures the current candle trades with sufficient participation.

------------------------------------------------------------------------

## 3. Volume Boom Condition

**Formula from Image:**

    Vol_t ≥ 2 × Σ Vol_{t-i}, i = 1..10

This requires the current volume to be at least double the total volume
of the last 10 candles.

------------------------------------------------------------------------

## 4. True Range (TR)

    TR_t = max(
        High_t - Low_t,
        |High_t - Close_{t-1}|,
        |Low_t - Close_{t-1}|
    )

This captures raw price volatility including gaps.

------------------------------------------------------------------------

## 5. VTR (Volatility Threshold Range)

    VTR_t = m × (1/l) × Σ TR_{t-i}, i = 0..(l-1)

Image uses:

-   VTR(3,12)
-   VTR(10,1)
-   VTR(11,2)

Each VTR scales volatility across different horizons.

------------------------------------------------------------------------

## 6. Market Bias from VTR

**Bullish Bias:**

    VTR1 > Price_t ∧ VTR2 > Price_t ∧ VTR3 > Price_t

**Bearish Bias:**

    VTR1 < Price_t ∧ VTR2 < Price_t ∧ VTR3 < Price_t

Otherwise: No-trade zone.

------------------------------------------------------------------------

## 7. Directional Movement (+DM / -DM)

    UpMove   = High_t - High_{t-1}
    DownMove = Low_{t-1} - Low_t

    +DM_t = UpMove   if UpMove > DownMove and UpMove > 0 else 0
    -DM_t = DownMove if DownMove > UpMove and DownMove > 0 else 0

------------------------------------------------------------------------

## 8. Wilder Smoothing (14 Periods)

    Smooth_t = Smooth_{t-1} - (Smooth_{t-1}/14) + Raw_t

Applied to:

-   TR
-   +DM
-   -DM

------------------------------------------------------------------------

## 9. Directional Indicators

    +DI = 100 × (+DM_smooth / TR_smooth)
    -DI = 100 × (-DM_smooth / TR_smooth)

------------------------------------------------------------------------

## 10. Directional Index DX

    DX = 100 × |+DI - -DI| / (+DI + -DI)

------------------------------------------------------------------------

## 11. DMag (ADX)

Initial:

    ADX_14 = mean(DX[0..13])

Then:

    ADX_t = ((13 × ADX_{t-1}) + DX_t) / 14

------------------------------------------------------------------------

## 12. DMag Filter

    DMag > 20 ∧ DMag > DMag[1]

Confirms strong and strengthening trend.

------------------------------------------------------------------------

## 13. Final Signal Logic

**Bullish Signal:**

    Volume Boom
    ∧ Volume Gate
    ∧ VTR Bullish Bias
    ∧ ADX > 20 and rising

**Bearish Signal:**

    Volume Boom
    ∧ Volume Gate
    ∧ VTR Bearish Bias
    ∧ ADX > 20 and rising

Dots are placed on the chart where these conditions occur.

------------------------------------------------------------------------

## 14. Algorithm Flow Summary

1.  Compute TR
2.  Compute VTRs
3.  Check Volume Gate
4.  Check Volume Boom
5.  Compute +DM / -DM
6.  Wilder smooth TR & DM
7.  Compute +DI, -DI
8.  Compute DX
9.  Compute DMag (ADX)
10. Apply DMag filter
11. Apply VTR bias
12. Generate signal
13. Plot signal dots

------------------------------------------------------------------------

This MD file represents a direct systematic breakdown of the entire
strategy logic from the image.
