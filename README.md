# Predictive Maintenance for Mining Equipment (No Hardware Required)

A software-only predictive maintenance system that simulates sensor telemetry
(vibration, temperature, current draw) from multiple mining machines,
trains a machine learning model to predict impending failures, and serves
live risk predictions through a real-time dashboard.

This mirrors real AI-based predictive maintenance systems used in mining
equipment (e.g. BEML's AI-based Big Data analytics for equipment health
monitoring) but runs entirely on your laptop - no FPGA or physical sensors needed.

## Architecture

1. **`backend/simulate_and_train.py`**
   - Simulates 5 "machines" as independent Python threads, each generating
     a stream of vibration/temperature/current readings (mirrors multiple
     equipment telemetry channels feeding a central monitoring system)
   - Half the machines are programmed to gradually "degrade" toward failure
   - Extracts rolling-window statistical features (mean, std, slope) per sensor
   - Trains a RandomForestClassifier to predict "failure_soon" from these features
   - Saves the trained model to `data/model.pkl` and metrics to `data/metrics.json`

2. **`backend/api_server.py`**
   - FastAPI server that simulates live telemetry (same generator logic)
   - Feeds each new reading through the trained model in real time
   - Streams machine status (NORMAL / WARNING / CRITICAL) + failure-risk %
     to the frontend via WebSocket

3. **`frontend/page.tsx`**
   - Next.js dashboard showing a live card per machine: current sensor
     readings, failure-risk percentage, color-coded status, and a mini
     risk-history sparkline chart

## Running it

### Step 1: Simulate data and train the model
```
cd backend
pip install -r requirements.txt
python simulate_and_train.py
```
This generates `data/sensor_stream.csv`, `data/model.pkl`, `data/metrics.json`.
Takes about 1-2 minutes (simulates 10,000 sensor readings across 5 threads).

### Step 2: Start the live API server
```
python api_server.py
```
Runs on http://localhost:8001, WebSocket at ws://localhost:8001/ws/telemetry

### Step 3: Start the frontend
```
cd ../frontend
npx create-next-app@latest . --typescript --app --no-tailwind --no-eslint
# replace app/page.tsx with the provided page.tsx
npm run dev
```
Open http://localhost:3000 - you will see 5 machine cards updating live,
with 2-3 gradually turning from green -> yellow -> red as they "degrade".

## Key concepts demonstrated

- Multithreaded sensor simulation (Python threading, mirrors POSIX thread
  concepts you already know from C) - each machine is an independent
  producer thread with shared-state writes protected by a lock.
- Feature engineering on time-series telemetry (rolling window statistics).
- Supervised ML classification (RandomForest) for failure prediction.
- Real-time WebSocket streaming from a concurrent Python backend to React.
- End-to-end AI pipeline: data generation -> training -> live inference -> dashboard.

## Resume framing

"Built an end-to-end predictive maintenance system for simulated mining
equipment: multithreaded sensor telemetry generation, feature engineering,
and a RandomForest classifier achieving over 90% test accuracy in predicting
equipment failure risk, served via a real-time React dashboard streaming
live risk scores over WebSocket."

## Extending it

1. Swap RandomForest for an LSTM/GRU (better suited to true time-series patterns).
2. Add a maintenance-scheduling optimizer that recommends which machine to
   service first based on risk score + downtime cost.
3. Replace the simulated sensor data with a public dataset (e.g. NASA
   bearing dataset, CWRU bearing fault dataset) for a more rigorous demo.
4. Add anomaly detection (isolation forest) as a second, unsupervised layer.
