import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

PLOT_DIR = Path("plots")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

def plot_bar(results, result_type):
    df = pd.DataFrame(results)

    if result_type not in df.columns:
        raise ValueError(f"{result_type} not found in results")

    df["is_baseline"] = df["scenario"].str.contains("baseline")
    df = df.sort_values(by="is_baseline", ascending=False).reset_index(drop=True)

    colors = [
        "red" if t == "baseline" else "blue"
        for t in df["type"]
    ]

    labels = {
        "duration_mean": "Average Duration",
        "waiting_mean": "Average Waiting Time",
        "time_loss_mean": "Average Time Loss",
        "count": "Vehicle Count"
    }

    titles = {
        "duration_mean": "Average Trip Duration Comparison",
        "waiting_mean": "Average Waiting Time Comparison",
        "time_loss_mean": "Average Time Loss Comparison",
        "count": "Vehicle Count Comparison"
    }

    plt.figure()

    plt.bar(df["scenario"], df[result_type], color=colors, edgecolor="black")

    plt.xticks(rotation=45)
    plt.xlabel("Scenario")
    plt.ylabel(labels.get(result_type, result_type))
    plt.title(titles.get(result_type, result_type))

    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{result_type}.png")
    plt.show()

def plot_difference(results, result_type):
    df = pd.DataFrame(results)

    if result_type not in df.columns:
        raise ValueError(f"{result_type} not found")

    baseline_row = df[df["type"] == "baseline"]
    if baseline_row.empty:
        raise ValueError("No baseline found")

    baseline_value = baseline_row[result_type].values[0]

    df["delta"] = df[result_type] - baseline_value

    df_plot = df[df["type"] != "baseline"].reset_index(drop=True)

    colors = ["red" if d > 0 else "green" for d in df_plot["delta"]]

    plt.figure()

    plt.bar(
        df_plot["scenario"],
        df_plot["delta"],
        color=colors,
        edgecolor="black"
    )

    plt.axhline(0, linestyle="--", linewidth=1)

    plt.xticks(rotation=45)
    plt.xlabel("Scenario")
    plt.ylabel(f"Delta {result_type}")
    plt.title(f"Difference to Baseline ({result_type})")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{result_type}_difference.png")
    plt.show()

def plot_histogram(data, label):
    plt.figure()

    plt.hist(data, bins="fd", density=True)

    plt.xlabel(label)
    plt.ylabel("Density")
    plt.title(f"Distribution of {label}")


    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{label}_hist.png")
    plt.show()

def plot_all_metrics(results):
    df = pd.DataFrame(results)

    metrics = ["duration_mean", "waiting_mean", "time_loss_mean"]

    fig, axes = plt.subplots(len(metrics), 1, figsize=(8, 10))

    for i, metric in enumerate(metrics):
        axes[i].bar(df["scenario"], df[metric])
        axes[i].set_title(metric)
        axes[i].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "all_metrics.png")
    plt.show()