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

# VTR–DMag System — Detailed Formula Walkthrough

This document is a structured Markdown version of the full detailed explanation (Sections 1–18) of the system shown in the image. It covers **Volume Gate, Volume Boom, VTR, True Range, Directional Movement (+DM/−DM), DI, DX, and DMag (ADX)**, including formulas, logic flow, implementation notes, pitfalls, and example usage.

---

## 1. Notation & Preliminaries

* Time index: `t` = current bar, `t-1` = previous bar
* Price:

  * `High_t`, `Low_t`, `Close_t`, `Open_t`
* Volume: `Vol_t`
* Parameters:

  * `m`, `l` → VTR scaling parameters
  * `L` → Volume Gate lookback
  * `n = 14` → Wilder smoothing period

---

## 2. Volume Gate (VG)

**Formula:**

```
Vol_t ≥ VG
```

**Typical implementation:**

```
VG_t = mean(Vol_{t-L...t-1}) × factor
```

**Logic:**

* Blocks low-volume noise
* Only allows trades during sufficient participation

**Notes:**

* Use `L = 20–50`
* Use `factor = 1.0–2.0`
* Requires `min_periods = L`

---

## 3. Volume Boom

**Image Formula:**

```
Vol_t ≥ 2 × Σ_{i=1}^{10} Vol_{t-i}
```

**Interpretation:**

* Current volume must exceed twice the **sum of the previous 10 bars**
* This detects extreme participation surges

---

## 4. True Range (TR)

**Standard Formula:**

```
TR_t = max(
    High_t − Low_t,
    |High_t − Close_{t-1}|,
    |Low_t − Close_{t-1}|
)
```

**Purpose:**

* Measures real price expansion per bar

---

## 5. VTR — Volatility True Range

**General Formula:**

```
VTR_t = m × (1/l) × Σ_{i=0}^{l-1} TR_{t-i}
```

**Image Parameters:**

* `VTR(3,12)` → medium volatility
* `VTR(10,1)` → instant spike
* `VTR(11,2)` → ultra-short range

**Unit:** Same as price

---

## 6. Market Bias Rules (VTR vs Price)

Let `Price_t = Close_t`

**Bullish Condition:**

```
VTR_1 > Price_t AND
VTR_2 > Price_t AND
VTR_3 > Price_t
```

**Bearish Condition:**

```
VTR_1 < Price_t AND
VTR_2 < Price_t AND
VTR_3 < Price_t
```

**No Trade:**

```
Otherwise (mixed signals)
```

---

## 7. Directional Movement (+DM / −DM)

Let:

```
upMove   = High_t − High_{t-1}
downMove = Low_{t-1} − Low_t
```

**Formulas:**

```
+DM_t = upMove   if upMove > downMove and upMove > 0 else 0
−DM_t = downMove if downMove > upMove and downMove > 0 else 0
```

---

## 8. Wilder Smoothing (for TR, +DM, −DM)

**Initial value:**

```
Smoothed_0 = Σ raw[0...n-1]
```

**Recursive formula:**

```
Smoothed_t = Smoothed_{t-1} − (Smoothed_{t-1} / n) + raw_t
```

Applied to:

* `TR`
* `+DM`
* `−DM`

---

## 9. Directional Indicators (+DI / −DI)

**Formulas:**

```
+DI_t = 100 × ( +DM_smooth_t / TR_smooth_t )
−DI_t = 100 × ( −DM_smooth_t / TR_smooth_t )
```

---

## 10. DX — Directional Index

**Formula:**

```
DX_t = 100 × |+DI_t − −DI_t| / ( +DI_t + −DI_t )
```

Range: `0–100`

---

## 11. DMag (ADX via Wilder)

**Initial Average (Image shows):**

```
DMag_14 = (1/14) × Σ DX
```

**Wilder Recursion:**

```
DMag_t = ((n − 1) × DMag_{t-1} + DX_t) / n
```

Purpose:

* Detects **trend strength only**, not direction

---

## 12. Signal Strength Filter

**Image Rule:**

```
DMag > 20 AND DMag > DMag[1]
```

Meaning:

* Trend must be **stronger than 20**
* Trend must be **accelerating**

---

## 13. Full Decision Logic

### Bullish Signal

```
VolumeBoom AND
VolumeGate AND
VTR_Bullish AND
DMag > 20 AND
DMag Rising
```

### Bearish Signal

```
VolumeBoom AND
VolumeGate AND
VTR_Bearish AND
DMag > 20 AND
DMag Rising
```

---

## 14. Practical MT5 Notes

* Prefer `real_volume` if broker provides it
* Use `shift(1)` carefully
* Use strict `min_periods`
* Protect against division by zero in DI & DX

---

## 15. Mini Numeric Example

Example bar:

```
High_t  = 103
Low_t   = 100
Close_t = 102
Close_{t-1} = 100
```

TR:

```
max(3, 3, 0) = 3
```

VTR(10,1):

```
10 × 3 = 30
```

Comparison:

```
30 < 102 → bearish zone
```

---

## 16. Pitfalls

* Comparing raw price to VTR assumes scale compatibility
* Weak volume sessions distort Volume Boom
* Early-bar smoothing instability
* ADX must be Wilder-smoothed, not EMA

---

## 17. Pseudocode Summary

```
for each bar t:
    compute TR
    compute VTRs
    compute VolumeGate
    compute VolumeBoom
    compute +DM, -DM
    wilder_smooth(TR, +DM, -DM)
    compute +DI, -DI
    compute DX
    compute DMag (ADX)

    if all bullish conditions:
        place bullish dot
    if all bearish conditions:
        place bearish dot
```

---

## 18. Recommended Parameter Ranges

| Parameter          | Suggested Range |
| ------------------ | --------------- |
| VG Lookback        | 20–100          |
| VG Multiplier      | 1.0–2.0         |
| Volume Boom Window | 10–20           |
| VTR Multipliers    | 2–12            |
| ADX Period         | 14 (standard)   |
| ADX Threshold      | 20–25           |

---

**End of System Documentation**

