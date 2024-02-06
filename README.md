**README - V2TRADING - Advanced Algorithmic Trading Platform**

**Overview**
Custom-built algorithmic trading platform for research, backtesting and automated trading. Trading engine capable of processing tick data, managing trades, and supporting backtesting in a highly accurate and efficient manner.

**Key Features**
- **Trading Engine**: At the core of the platform is a trading engine that processes tick data in real time. This engine is responsible for aggregating data and managing the execution of trades, ensuring precision and speed in trade placement and execution.

- **High-Fidelity Backtesting Environment**: ability to backtest strategies with 1:1 precision - meaning a tick-by-tick backtesting. This level of precision in backtesting, down to millisecond accuracy, mirrors live trading environments and is vital for developing and testing high-frequency trading strategies.

- **Custom Data Aggregation:** The platform includes a data aggregator that allows for custom aggregation rules. This flexibility supports a variety of data analysis approaches, including non-time based bars and other unique criteria.

- **Indicators** Contains inbuild [tulipy](https://tulipindicators.org/list) [ta-lib](https://ta-lib.github.io/ta-lib-python/) and templates for custom build multioutputs stateful indicators.

- **Machine Learning Integration:** Recently, the platform has expanded to incorporate machine learning capabilities. This includes modules for both training and inference, supporting the complete ML lifecycle. These ML models can be utilized within trading strategies for classification and exploiting statistical advantages.

**Technology Stack**
**Backend and API:** The backbone of the platform is built with Python, utilizing libraries such as FastAPI, NumPy, Keras, and JAX, ensuring high performance and scalability.
**Frontend:** The client-side is developed with Vanilla JavaScript and jQuery, employing LightweightCharts for charting purposes. Additional modules enhance the platform's functionality. The frontend is slated for a future refactoring to modern frameworks like Vue.js and Vuetify for a more robust user interface.

While the platform is fully functional and growing, ongoing development is planned, particularly in the realm of frontend enhancements and further integration of advanced machine learning techniques.

**Contributions**
Contributions to this project are welcome. Whether it's improving the frontend, enhancing the backend capabilities, or experimenting with new trading strategies and machine learning models, your input can help take this platform to the next level.

This repository represents a sophisticated and evolving tool for algorithmic traders, offering precision, speed, and a level of customization that is unparalleled in open-source systems. Join us in shaping the future of algorithmic trading.

<p align="center">
  Main screen with entry/exit points and stoploss lines<br>
  <img width="700" alt="Main screen with entry/exit points and stoploss lines" src="https://github.com/drew2323/v2trading/assets/28433232/751d5b0e-ef64-453f-8e76-89a39db679c5">
</p>

<p align="center">
  Main screen with tick based indicators<br>
  <img width="700" alt="Main screen with tick based indicators" src="https://github.com/drew2323/v2trading/assets/28433232/4bf6128c-9b36-4e88-9da1-5a33319976a1">
</p>

<p align="center">
  Indicator editor<br>
  <img width="700" alt="Indicator editor" src="https://github.com/drew2323/v2trading/assets/28433232/cc417393-7b88-4eea-afcb-3a00402d0a8d">
</p>

<p align="center">
  Strategy editor<br>
  <img width="700" alt="Strategy editor" src="https://github.com/drew2323/v2trading/assets/28433232/74f67e7a-1efc-4f63-b763-7827b2337b6a">
</p>

<p align="center">
  Strategy analytical tools<br>
  <img width="700" alt="Strategy analytical tools" src="https://github.com/drew2323/v2trading/assets/28433232/4bf8b3c3-e430-4250-831a-e5876bb6b743">
</p>


