from pathlib import Path
import subprocess
import os

def get_sumo_home():
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        raise EnvironmentError("SUMO_HOME is not set")
    return Path(sumo_home)

def run_scenario(scenario_folder, name, simulation_time):
    sumocfg_file = scenario_folder / (name + ".sumocfg")

    sumoExe = get_sumo_home() / "bin" / "sumo.exe"

    subprocess.run([
        str(sumoExe),          
        "-c", str(sumocfg_file),
        "--end", str(simulation_time),
        "--no-step-log",
        "--time-to-teleport", "-1"
    ], cwd=scenario_folder, check=True)

    return scenario_folder / f"tripinfo_{name}.xml"