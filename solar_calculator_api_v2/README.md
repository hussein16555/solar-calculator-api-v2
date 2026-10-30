# Solar Energy Prediction & Equipment Sizing API v2

This version adds schedule-based hourly prediction (00:00–23:00), peak-hour detection, chart visualization, and a `/api/predict-hourly` endpoint.

Run:
`python -m venv .venv`
` .venv\\Scripts\\activate` on Windows
`pip install -r requirements.txt`
`uvicorn main:app --reload`

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

The current prediction is a deterministic schedule forecast. A future ML version can use historical hourly smart-meter/IoT data, temperature, weekday, occupancy, and solar generation to train XGBoost, Random Forest, Prophet, or LSTM.
