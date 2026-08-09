import xml.etree.ElementTree as ET
import numpy as np

def load_tripinfo(filename):
    durations = []
    waiting_times = []
    time_losses = []

    for event, elem in ET.iterparse(filename, events=("end",)):
        if elem.tag == "tripinfo":
            durations.append(float(elem.get("duration")))
            waiting_times.append(float(elem.get("waitingTime")))
            time_losses.append(float(elem.get("timeLoss")))
            elem.clear()

    return durations, waiting_times, time_losses


def compute_statistics(data):
    return {
        "mean": np.mean(data),
        "variance": np.var(data),
        "std": np.std(data),
        "min": np.min(data),
        "max": np.max(data),
        "count": len(data)
    }

def analyse_tripinfo(filename):
    durations, waiting_times, time_losses = load_tripinfo(filename)
    return {
        "duration": compute_statistics(durations),
        "waiting_time": compute_statistics(waiting_times),
        "time_loss": compute_statistics(time_losses)
    }