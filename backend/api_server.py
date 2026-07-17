
"""
Predictive Maintenance API - serves live sensor simulation + model predictions
Run after simulate_and_train.py has generated data/model.pkl
"""

import threading
import time
import json
import random
import pickle
from collections import deque
from typing import Dict, List

import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

NUM_MACHINES = 5
WINDOW = 20
TICK_SECONDS = 0.3

state_lock = threading.Lock()
machine_state: Dict[int, Dict] = {}

with open("data/model.pkl", "rb") as f:
    MODEL = pickle.load(f)


class MachineSimulator:
    """Live streaming simulator per machine, feeding a rolling window into
    the trained RandomForest model for real-time failure-risk prediction."""

    def __init__(self, mid: int):
        self.mid = mid
        self.will_fail = mid % 2 == 0
        self.t = 0
        self.degrade_start = random.randint(150, 220)
        self.base_vibration = random.uniform(1.5, 2.5)
        self.base_temp = random.uniform(60, 70)
        self.base_current = random.uniform(10, 14)
        self.vib_hist = deque(maxlen=WINDOW)
        self.temp_hist = deque(maxlen=WINDOW)
        self.curr_hist = deque(maxlen=WINDOW)

    def step(self):
        degrade_factor = 0.0
        if self.will_fail and self.t > self.degrade_start:
            progress = min(1.0, (self.t - self.degrade_start) / 150)
            degrade_factor = progress ** 2

        vibration = self.base_vibration + degrade_factor * 6 + random.gauss(0, 0.15)
        temperature = self.base_temp + degrade_factor * 25 + random.gauss(0, 0.8)
        current = self.base_current + degrade_factor * 5 + random.gauss(0, 0.3)

        self.vib_hist.append(vibration)
        self.temp_hist.append(temperature)
        self.curr_hist.append(current)
        self.t += 1

        risk = None
        if len(self.vib_hist) == WINDOW:
            def slope(vals):
                xs = np.arange(len(vals))
                return float(np.polyfit(xs, vals, 1)[0])

            feat = np.array([[
                np.mean(self.vib_hist), np.std(self.vib_hist), slope(list(self.vib_hist)),
                np.mean(self.temp_hist), np.std(self.temp_hist), slope(list(self.temp_hist)),
                np.mean(self.curr_hist), np.std(self.curr_hist), slope(list(self.curr_hist)),
            ]])
            proba = MODEL.predict_proba(feat)[0]
            risk = float(proba[1]) if len(proba) > 1 else 0.0

        with state_lock:
            machine_state[self.mid] = {
                "id": self.mid,
                "vibration": round(vibration, 2),
                "temperature": round(temperature, 2),
                "current": round(current, 2),
                "risk": round(risk, 3) if risk is not None else 0.0,
                "status": "CRITICAL" if (risk or 0) > 0.7 else ("WARNING" if (risk or 0) > 0.4 else "NORMAL"),
            }


def start_machines():
    sims = [MachineSimulator(i) for i in range(NUM_MACHINES)]

    def loop():
        while True:
            for s in sims:
                s.step()
            time.sleep(TICK_SECONDS)

    threading.Thread(target=loop, daemon=True).start()


app = FastAPI(title="Predictive Maintenance API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/machines")
def get_machines():
    with state_lock:
        return list(machine_state.values())


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    import asyncio
    try:
        while True:
            with state_lock:
                payload = json.dumps(list(machine_state.values()))
            await websocket.send_text(payload)
            await asyncio.sleep(TICK_SECONDS)
    except Exception:
        pass


@app.on_event("startup")
def on_startup():
    start_machines()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
