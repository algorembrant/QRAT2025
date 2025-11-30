
| Feature/Aspect                | Pine Script                                                                                       | Python                                                                                                      | MQL5                                                                                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**               | Domain-specific language for creating **trading indicators and strategies** on TradingView.       | General-purpose programming language used for **web development, data analysis, AI, automation**, and more. | Domain-specific, C++-like language for **automated trading, indicators and scripts** on MetaTrader 5 (EAs, custom indicators, tools).          |
| **Primary Use**               | Financial charting, indicators, alerts, backtesting strategies.                                   | Wide range: data analysis, AI/ML, web development, automation, finance, etc.                                | Automated trading (Expert Advisors), custom indicators, order management, and trading utilities.                                               |
| **Execution Model**           | Runs **bar by bar** on time series data; series variables track historical values automatically.  | Procedural, object-oriented, or functional execution; manual handling of time series required.              | **Event-driven**: `OnInit`/`OnDeinit`/`OnTick`/`OnTimer` etc.; executes per tick and can process bar data — ideal for live trading.            |
| **Data Handling**             | Built-in support for price series, OHLC data, and indicators.                                     | Requires libraries like Pandas or NumPy for structured data and time series.                                | Built-in market data functions (`CopyRates`, `CopyTicks`, series arrays); supports arrays, structures, and low-level access to history.        |
| **Plotting & Visualization**  | Limited to chart overlays, indicators, and shapes on TradingView.                                 | Full-featured plotting with libraries like Matplotlib, Plotly, Seaborn.                                     | Chart objects, graphical primitives and indicator buffers for on-chart visualization; less flexible than general plotting libraries.           |
| **External Integration**      | No direct access to files, APIs, or databases; restricted to TradingView.                         | Can integrate with databases, web APIs, files, cloud services, and more.                                    | Can read/write files, use `WebRequest` for HTTP, and call DLLs (subject to platform security settings); integration is possible but sandboxed. |
| **Libraries & Extensibility** | Cannot import external libraries; only built-in Pine functions.                                   | Vast ecosystem of libraries for almost any task.                                                            | Standard MQL5 library, user include files, and ability to call external DLLs for extended functionality (with caution).                        |
| **Backtesting & Strategy**    | Native support for strategy testing, alerts, and position sizing.                                 | Requires manual coding or external frameworks for backtesting and trading simulations.                      | Robust Strategy Tester with tick/real ticks simulation, optimization, multi-threading and walk-forward testing built into MT5.                 |
| **Variables & State**         | Series variables automatically track historical values; supports mutable and immutable variables. | Variables are mutable; history tracking must be implemented manually.                                       | Standard variables, static/global scope, object-oriented support (classes), and persistent storage via global variables/files.                 |
| **Loops & Control Flow**      | Limited support for loops; vectorized operations preferred.                                       | Full support for loops, recursion, comprehensions, and control structures.                                  | Full control flow and loops; supports structured, procedural and object-oriented paradigms (C++-like syntax).                                  |
| **Learning Curve**            | Easier for traders due to focused domain and simple syntax.                                       | Steeper learning curve but highly versatile; large community support.                                       | Steeper if you lack C/C++ experience; requires knowledge of trading concepts and platform specifics (order types, symbols, margins).           |
| **Performance**               | Optimized for chart calculations; efficient for time series.                                      | Performance depends on implementation and libraries; may require optimization for large datasets.           | Compiled to native code (high runtime performance), designed for real-time trading with low latency.                                           |
| **Limitations**               | Restricted to TradingView platform; cannot perform general computing tasks.                       | Not inherently designed for trading platforms; requires additional coding for finance-specific tasks.       | Tied to MetaTrader 5 platform and broker environment; some operations (DLLs, WebRequest) subject to security and broker settings.              |

---

## QAT-QuantitativeAlgorithmicTrading

    Pinescript Folder
    Python Folder    
    MQL5 Folder     
    Concepts and Topics Folder

## Pinescript Folder

|   View    |   Info    |   Status  |   Included Details    |   Language    |
|-|-|-|-|-|
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Sunstoic's charting tool 2025 | Finished    |   indicators, TPO profile, Volume profile  |   Pinescript  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|  89RS The 8-9pm Rangebreakout Stoporder Method. | Finished    |   indicators, an Opening Range Break (ORB) reference.  |   Pinescript  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Asia/manila Time Logic  | Finished    |  code layout |   Pinescript  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    1min 4CCP & 3min 6CBP Pattern Detector, 30minute bars (Asia/Manila) | Finished    |  indicator, plot boxes |   Pinescript  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Risk Manager and Position Sizing | Finished    |  indicator, dynamic risk reward ratio plotter with position sizing |   Pinescript  |

## Python Folder

|   View    |   Info    |   Status  |   Included Details    |   Language    |
|-|-|-|-|-|
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Broker Account Portfolio Identification | Finished    |   fetching data from mt5, chart plotting  |   Python  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Market Profile (volumedata ver), not TPO-based | Finished    |   chart plotting and vertical profiles |   Python  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Chart plotting | Finished    |  code layout |   Python  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    89RS Backtested in Python | Finished    |  chart plotting, trade executions, backtesting, statistics |   Python  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Design and Optimization of 1HRMRSSv1: 1H Range Median Reversion Stoporder Strategy| Finished    |   Deployed Python algorithmic trading bot, stoporder hedging, `126million hours Backtesting`, `Research Paper documentation` ![img](https://github.com/algorembrant/QAT-QuantitativeAlgorithmicTrading/blob/main/z.Images%20Folder/pasted-image%20(15).png?raw=true)|   Python  |


## MQL5 Folder

|   View    |   Info    |   Status  |   Included Details    |   Language    |
|-|-|-|-|-|
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Hedging Expert Advisor (EA) for MT5 | Finished    |   Deployed EA algorithmic trading bot, stoporder hedging, stoploss trailing, `4hour trial, six 1h, 12h finale (22hr+ duration tests)` `documented & research paper` `2 LiveTests 7hr &` ![img](https://github.com/algorembrant/QAT-QuantitativeAlgorithmicTrading/blob/main/z.Images%20Folder/pasted-image%20(12).png)|   MQL5  |

## Concepts and Topics Folder

|   View    |   Info    |   Status  |   Included Details    |   Language    |
|-|-|-|-|-|
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    The Law of Large Numbers | Finished    |   Showcases the theory using simulated outcome, 6 side die and 2 side coin examples |   Python  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Risk Management Formulas | Finished    |   mathematical formulas |   na  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    The three 30-min candle wickyoff pattern | Finished    |  entry model to have tighter stoploss to increase the R-multiple wihtout moving the TP target |   na  |
| **[*link*](https://github.com/algorembrant/Pinescript.TradingView-Indicators.and.Strategies/blob/main/Trading%20Indicators%2C%20Strategies%20%26%20Techniques/SCT%20Sunstoic's%20Charting%20Tool.ipynb)**|    Max Number of Losing Streak in Regards to Winrate | Finished    |   Showcases the theory using simulated outcome, monte carlo simulation |   Python  |









