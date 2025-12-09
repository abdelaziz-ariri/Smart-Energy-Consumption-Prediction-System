# ⚡️ Intelligent System for Energy Consumption Prediction and Monitoring (SARIMAX & Flask)

This project describes the design and deployment of a comprehensive solution for **real-time electrical energy consumption prediction**, incorporating advanced **monitoring** and **alerting** capabilities. The system's primary goal is to anticipate energy demand, detect consumption anomalies, and provide continuous visibility into energy usage trends.

## ✨ Key Features

* **Prediction Models:** Integrates advanced time series models (**SARIMA, SARIMAX**) and Machine Learning algorithms (**XGBoost, Random Forest, LSTM, GRU**) to accurately predict hourly consumption.
* **Real-Time Monitoring:** Ensures continuous monitoring of energy data streams and visualizes trends and model performance via interactive dashboards.
* **Anomaly Detection & Alerts:** Features an intelligent module that analyzes deviations between predictions and observed values to automatically generate email notifications for operators in case of unexpected predictions or anomalies.
* **Robust Architecture:** Utilizes a modern, scalable architecture based on **Python/Flask** for the API and user interface, and **MongoDB** for flexible NoSQL storage of time series data.
* **User Interface:** Provides an operational web interface for authentication, dashboard viewing, launching predictions, and checking historical data and notifications.

---

## 🏗️ System Architecture
<img width="1536" height="1024" alt="ChatGPT Image 8 déc  2025, 02_56_51" src="https://github.com/user-attachments/assets/559ad3bd-c1cd-4c03-8c1f-a6c5f4f79dc4" />

The architecture is built upon a suite of modern technologies organized into a clear pipeline flow:

1.  **Data Sources:** Ingestion of historical hourly consumption data from the PJM Interconnection (2002-2018).
2.  **Storage (MongoDB):** Stores historical data, prediction results, and performance logs, offering flexibility for evolving data schemas.
3.  **Data Processing:** A Python pipeline handles initial loading, cleaning (interpolation of missing values, duplicate removal), and crucial feature engineering for time series modeling.
4.  **Prediction Models:** Development and optimization of models, including SARIMAX and ML approaches, to capture complex seasonalities (daily and weekly).
5.  **Dashboard and Visualization:** Dynamic visualization of current consumption, comparison between predictions and actual values, and trend analysis (potentially via Grafana, accessible through the Flask app).
6.  **Notifications:** An alert system triggered by significant deviations between predicted and real consumption, ensuring proactive management.



---

## 📊 Modeling Insights (SARIMAX)

Time series analysis revealed key characteristics that guided the model configuration:

| Characteristic | Observation/Tool | Parameter Indication |
| :--- | :--- | :--- |
| **Non-Stationarity** | Slow ACF decay | Non-seasonal differentiation $d=1$ |
| **Daily Seasonality** | Peaks every 24 lags in ACF/PACF | Seasonal differentiation $D=1$, Period $s=24$ |
| **Short-Term AR** | Clear cut-off at lag 1 in PACF | Non-seasonal AR $p=1$ |
| **Seasonal AR** | Clear peak at lag 24 in PACF | Seasonal AR $P=1$ |

**Resulting Recommended Model:** $\text{SARIMA}(1, 1, 0) \times (1, 1, 0)_{24}$ (further refined using AIC and diagnostics).

---

## 🛠️ Technologies Used

* **Backend & API:** Python, Flask
* **Database:** MongoDB Atlas (NoSQL, document-oriented)
* **Time Series Modeling:** SARIMA, SARIMAX (`statsmodels`)
* **Advanced ML Modeling:** XGBoost, Random Forest, LSTM, GRU
* **Visualization:** Grafana, Flask Web Interface
---

---

## 👤 Contributors

* M. ARIRI Abdelaziz
* M. EL ATTAR Fahd
* M. ETTAQAFI OSSAMA

---
