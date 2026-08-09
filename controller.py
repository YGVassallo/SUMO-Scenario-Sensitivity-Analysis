import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import pandas as pd

from collections import Counter
from pathlib import Path 

from generate_scenario import generate_scenario
from run_scenario import run_scenario
from generate_sample import * 
from analyse_tripinfo import *
from plot_results import *

def check_file_writable(file_path):
    try:
        with open(file_path, "a"):
            pass
    except PermissionError:
        raise RuntimeError(f"File is open or locked: {file_path}")


file_path = Path(__file__).resolve()
folder_path = file_path.parent

config = load_config(folder_path / "config.json")

files_to_check = [
    "results.xlsx",
    "plots/all_metrics.png",
    "plots/duration_mean_difference.png",
    "plots/duration_mean.png",
    "plots/time_loss_mean_difference.png",
    "plots/time_loss_mean.png",
    "plots/waiting_mean.png",
    "plots/waiting_mean_difference.png"
]
for f in files_to_check:
    try:
        check_file_writable(folder_path / f)
    except RuntimeError:
        print(f"Please close file: {f}")
        sys.exit(1)
    
sim_folder = Path(config["sim_folder"])
net_file = config["net_file"]
trip_file = config["trip_file"]

num_samples = config["sampling"]["num_samples"]

results = []

baseline = config["baseline"]
baseline_scenario = generate_scenario(baseline, sim_folder, net_file, trip_file)
baseline_folder = baseline_scenario["folder"]
baseline_tripinfo = run_scenario(baseline_folder, baseline["scenario"], baseline["simulation_time"])
baseline_stats = analyse_tripinfo(baseline_tripinfo)

baseline_duration = baseline_stats["duration"]["mean"]
baseline_waiting = baseline_stats["waiting_time"]["mean"]
baseline_time_loss = baseline_stats["time_loss"]["mean"]
baseline_count = baseline_stats["duration"]["count"]

results.append({
    "scenario": baseline["scenario"],
    "type": "baseline",  

    "closed_roads": baseline["closed_roads"],
    "traffic_multiplier": baseline["traffic_multiplier"],
    "routing": baseline["routing_algorithm"],

    "duration_mean": baseline_duration,
    "waiting_mean": baseline_waiting,
    "time_loss_mean": baseline_time_loss,
    "count": baseline_count,

    "delta_duration": 0,
    "delta_waiting": 0,
    "delta_time_loss": 0,
    "delta_count": 0
})


for i in range(num_samples):
    sample = generate_sample(config, i)
    scenario = generate_scenario(sample, sim_folder, net_file, trip_file)
    scenario_folder = scenario["folder"]
    tripinfo = run_scenario(scenario_folder, sample["scenario"], sample["simulation_time"])

    stats = analyse_tripinfo(tripinfo)

    delta_duration = stats["duration"]["mean"] - baseline_duration
    delta_waiting = stats["waiting_time"]["mean"] - baseline_waiting
    delta_time_loss = stats["time_loss"]["mean"] - baseline_time_loss
    delta_count = stats["duration"]["count"] - baseline_count

    results.append({
        "scenario": sample["scenario"],
        "type": "scenario",

        "closed_roads": sample["closed_roads"],
        "traffic_multiplier": sample["traffic_multiplier"],
        "routing": sample["routing_algorithm"],

        "duration_mean": stats["duration"]["mean"],
        "waiting_mean": stats["waiting_time"]["mean"],
        "time_loss_mean": stats["time_loss"]["mean"],
        "count": stats["duration"]["count"],

        "delta_duration": delta_duration,
        "delta_waiting": delta_waiting,
        "delta_time_loss": delta_time_loss,
        "delta_count": delta_count
    })


df = pd.DataFrame(results)


if "closed_roads" in df.columns:

    max_roads = df["closed_roads"].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    ).max()

    for i in range(max_roads):
        df[f"closed_road_{i+1}"] = df["closed_roads"].apply(
            lambda x: x[i] if isinstance(x, list) and len(x) > i else ""
        )

    df = df.drop(columns=["closed_roads"])


df = df.sort_values(by="delta_duration", ascending=False)


print("\n===== SCENARIO RESULTS =====\n")
print(df.to_string(index=False))


bad_scenarios = df[df["delta_duration"] > 0]
road_columns = [col for col in df.columns if col.startswith("closed_road_")]

road_counter = Counter()

for _, row in bad_scenarios.iterrows():
    for col in road_columns:
        road = row[col]
        if road:
            road_counter[road] += 1

print("\n===== CRITICAL ROADS =====\n")
for road, count in road_counter.most_common(10):
    print(f"{road}: {count}")

good_scenarios = df[df["delta_duration"] < 0]

good_road_counter = Counter()

for _, row in good_scenarios.iterrows():
    for col in road_columns:
        road = row[col]
        if road:
            good_road_counter[road] += 1

print("\n===== BENEFICIAL ROADS =====\n")
for road, count in good_road_counter.most_common(10):
    print(f"{road}: {count}")


road_score = {}

for road, count in road_counter.items():
    road_score[road] = road_score.get(road, 0) - count

for road, count in good_road_counter.items():
    road_score[road] = road_score.get(road, 0) + count

print("\n===== ROAD IMPACT SCORE =====\n")
for road, score in sorted(road_score.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{road}: {score}")


output_path = "results.xlsx"
df.to_excel(output_path, index=False)

print(f"\nResults saved to: {output_path}")

# ===== PLOTS =====
plot_bar(results, "duration_mean")
plot_bar(results, "waiting_mean")
plot_bar(results, "time_loss_mean")

plot_difference(results, "duration_mean")
plot_difference(results, "waiting_mean")
plot_difference(results, "time_loss_mean")

plot_all_metrics(results)