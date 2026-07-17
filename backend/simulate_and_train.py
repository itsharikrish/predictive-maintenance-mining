
"""
Predictive Maintenance for Mining Equipment - Data Simulation + Model Training
No FPGA required - runs entirely in software using simulated sensor streams
(vibration, temperature, current draw) from multiple "machines" (threads),
mimicking multi-sensor telemetry from mining equipment like excavators/dumpers.
"""

import threading
import time
import random
import csv
import math
import json
import pickle
from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# ------------------------- SENSOR SIMULATION -------------------------

NUM_MACHINES = 5
SAMPLES_PER_MACHINE = 2000
DATA_LOCK = threading.Lock()
RAW_ROWS: List[Dict] = []


def simulate_machine(machine_id: int, n_samples: int):
    """Simulates a mining machine's sensor stream (vibration, temp, current).
    Each machine runs on its own thread - mirrors independent equipment
    telemetry channels feeding a central monitoring system."""

    degrade_start = random.randint(int(n_samples * 0.6), int(n_samples * 0.85))
    fail_point = n_samples  # failure happens near the end for degrading machines
    will_fail = machine_id % 2 == 0  # half the machines degrade towards failure

    base_vibration = random.uniform(1.5, 2.5)
    base_temp = random.uniform(60, 70)
    base_current = random.uniform(10, 14)

    local_rows = []
    for t in range(n_samples):
        degrade_factor = 0.0
        if will_fail and t > degrade_start:
            progress = (t - degrade_start) / max(1, (fail_point - degrade_start))
            degrade_factor = progress ** 2

        vibration = base_vibration + degrade_factor * 6 + random.gauss(0, 0.15)
        temperature = base_temp + degrade_factor * 25 + random.gauss(0, 0.8)
        current = base_current + degrade_factor * 5 + random.gauss(0, 0.3)

        failure_soon = 1 if (will_fail and t > degrade_start + (fail_point - degrade_start) * 0.5) else 0

        row = {
            "machine_id": machine_id,
            "t": t,
            "vibration": round(vibration, 3),
            "temperature": round(temperature, 3),
            "current": round(current, 3),
            "failure_soon": failure_soon,
        }
        local_rows.append(row)
        time.sleep(0.0005)  # simulate streaming delay

    with DATA_LOCK:
        RAW_ROWS.extend(local_rows)
    print(f"Machine {machine_id} simulation complete ({'degrading' if will_fail else 'healthy'}).")


def run_simulation():
    threads = []
    for m in range(NUM_MACHINES):
        th = threading.Thread(target=simulate_machine, args=(m, SAMPLES_PER_MACHINE))
        threads.append(th)
        th.start()
    for th in threads:
        th.join()

    RAW_ROWS.sort(key=lambda r: (r["machine_id"], r["t"]))

    with open("data/sensor_stream.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["machine_id", "t", "vibration", "temperature", "current", "failure_soon"])
        writer.writeheader()
        writer.writerows(RAW_ROWS)

    print(f"Simulation done. {len(RAW_ROWS)} rows written to data/sensor_stream.csv")


# ------------------------- FEATURE ENGINEERING -------------------------

def build_features(rows: List[Dict], window: int = 20):
    """Rolling-window features per machine: mean/std/slope of each sensor,
    mirrors real predictive-maintenance feature engineering on telemetry."""
    from collections import defaultdict
    by_machine = defaultdict(list)
    for r in rows:
        by_machine[r["machine_id"]].append(r)

    X, y = [], []
    for mid, series in by_machine.items():
        series.sort(key=lambda r: r["t"])
        vib = [r["vibration"] for r in series]
        temp = [r["temperature"] for r in series]
        curr = [r["current"] for r in series]
        labels = [r["failure_soon"] for r in series]

        for i in range(window, len(series)):
            v_win = vib[i-window:i]
            t_win = temp[i-window:i]
            c_win = curr[i-window:i]

            def slope(vals):
                xs = np.arange(len(vals))
                return float(np.polyfit(xs, vals, 1)[0])

            feat = [
                np.mean(v_win), np.std(v_win), slope(v_win),
                np.mean(t_win), np.std(t_win), slope(t_win),
                np.mean(c_win), np.std(c_win), slope(c_win),
            ]
            X.append(feat)
            y.append(labels[i])

    return np.array(X), np.array(y)


def train_model():
    with open("data/sensor_stream.csv") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append({
                "machine_id": int(r["machine_id"]),
                "t": int(r["t"]),
                "vibration": float(r["vibration"]),
                "temperature": float(r["temperature"]),
                "current": float(r["current"]),
                "failure_soon": int(r["failure_soon"]),
            })

    X, y = build_features(rows)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    print(f"Test accuracy: {acc:.3f}")
    print(classification_report(y_test, y_pred))

    with open("data/model.pkl", "wb") as f:
        pickle.dump(clf, f)

    with open("data/metrics.json", "w") as f:
        json.dump({"accuracy": acc, "report": report}, f, indent=2)

    print("Model saved to data/model.pkl")


if __name__ == "__main__":
    run_simulation()
    train_model()
