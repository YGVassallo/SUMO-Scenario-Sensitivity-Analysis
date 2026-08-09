import subprocess
import shutil
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def get_sumo_home():
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        raise EnvironmentError("SUMO_HOME is not set")
    return Path(sumo_home)

def count_trips(trip_file):
    count = 0
    for event, elem in ET.iterparse(trip_file, events=("end",)):
        if elem.tag == "trip":
            count += 1
        elem.clear()
    return count

def generate_trips(trafficMult, simulation_time, net_file, trip_file, newTripFile):
    if trafficMult == 1:
        tree = ET.parse(trip_file)
        root = tree.getroot()

        new_root = ET.Element(root.tag, root.attrib)

        for elem in root:
            if elem.tag == "trip":
                if elem.get("from") and elem.get("to"):
                    depart = float(elem.get("depart", 0))
                    if depart <= simulation_time:
                        new_root.append(ET.fromstring(ET.tostring(elem)))

        new_root = sort_trips_by_depart(new_root)

        ET.ElementTree(new_root).write(newTripFile, encoding="utf-8", xml_declaration=True)

    elif trafficMult < 1:
        total_trips = count_trips(trip_file)
        target_count = int(total_trips * trafficMult)

        for event, elem in ET.iterparse(trip_file, events=("start",)):
            root_tag = elem.tag
            root_attrib = elem.attrib
            break

        new_root = ET.Element(root_tag, root_attrib)

        count = 0
        for event, elem in ET.iterparse(trip_file, events=("end",)):
            if count >= target_count:
                break

            if elem.tag == "trip":
                if elem.get("from") and elem.get("to"):
                    depart = float(elem.get("depart", 0))
                    if depart <= simulation_time:
                        new_root.append(ET.fromstring(ET.tostring(elem)))
                        count += 1

            elem.clear()

        new_root = sort_trips_by_depart(new_root)

        ET.ElementTree(new_root).write(newTripFile, encoding="utf-8", xml_declaration=True)

    else:
        total_trips = count_trips(trip_file)
        extra_trips = max(1, int(total_trips * (trafficMult - 1)))

        sumo_home = get_sumo_home()
        randomTrips = sumo_home / "tools" / "randomTrips.py"

        subprocess.run([
            sys.executable, randomTrips,
            "-n", str(net_file),
            "-o", str(newTripFile),
            "-e", str(simulation_time),
            "-p", str(max(1, int(simulation_time / extra_trips))),
            "--prefix", "new_"
        ], check=True)

        tree = ET.parse(newTripFile)
        root = tree.getroot()

        for event, elem in ET.iterparse(trip_file, events=("end",)):
            if elem.tag == "trip":
                if elem.get("from") and elem.get("to"):
                    depart = float(elem.get("depart", 0))
                    if depart <= simulation_time:
                        root.append(ET.fromstring(ET.tostring(elem)))

            elem.clear()

        root = sort_trips_by_depart(root)

        ET.ElementTree(root).write(newTripFile, encoding="utf-8", xml_declaration=True)

def sort_trips_by_depart(root):
    trips = []

    for trip in root.findall("trip"):
        depart = float(trip.get("depart", "0"))
        trips.append((depart, trip))

    trips.sort(key=lambda x: x[0])

    new_root = ET.Element(root.tag, root.attrib)

    for _, trip in trips:
        new_root.append(trip)

    return new_root

    
def generate_scenario(sample, sim_folder, net_file, trip_file):
    print("generate_scenario")
    name=sample["scenario"]
    sumo_home=get_sumo_home()
    print(sumo_home)
    scenario_folder = sim_folder / "scenarios" / name
    scenario_folder.mkdir(parents=True, exist_ok=True)
    new_net_file = scenario_folder / f"{name}.net.xml"
    netconvert = sumo_home / "bin" / "netconvert"
    if sample.get("closed_roads"):
        edges=",".join(sample["closed_roads"])
        subprocess.run ([
            str(netconvert),
            "-s", str(net_file),
            "--remove-edges", edges,
            "-o", str(new_net_file)
        ],check=True)
    else:
        subprocess.run ([
            str(netconvert),
            "-s", str(net_file),
            "-o", str(new_net_file)
        ],check=True)
    new_trips_file=scenario_folder / f"{name}.trips.xml"
    traffic_mult=sample["traffic_multiplier"]
    simulation_time=sample["simulation_time"]
    generate_trips(traffic_mult, simulation_time, new_net_file, trip_file, new_trips_file)
    new_route_file = scenario_folder / f"{name}.rou.xml"
    duarouter = sumo_home / "bin" / "duarouter"
    routing = sample["routing_algorithm"]
    extra_args=[]
    if routing not in ["fastest", "shortest"]:
        routing = "fastest"
    if routing == "shortest":
        extra_args += ["--weight-attribute", "length"]
    extra_args += [
        "--ignore-errors",
        "--remove-loops"
    ]
    subprocess.run([
        str(duarouter),
        "-n", str(new_net_file),
        "-r", str(new_trips_file),
        "-o", str(new_route_file),
        *extra_args
    ], check=True)
    
    root=ET.Element("configuration")
    input_tag=ET.SubElement(root, "input")
    ET.SubElement(input_tag,"net-file",value=str(new_net_file))
    ET.SubElement(input_tag,"route-files",value=str(new_route_file))
    time_tag=ET.SubElement(root,"time")
    ET.SubElement(time_tag,"begin",value="0")
    ET.SubElement(time_tag,"end",value=str(simulation_time))
    output_tag=ET.SubElement(root,"output")
    ET.SubElement(output_tag,"tripinfo-output",value=f"tripinfo_{name}.xml")
    new_sumocfg_file=scenario_folder / f"{name}.sumocfg"
    ET.ElementTree(root).write(new_sumocfg_file,encoding="utf-8",xml_declaration=True)
    return {
        "net": new_net_file,
        "trips": new_trips_file,
        "routes": new_route_file,
        "sumocfg": new_sumocfg_file,
        "tripinfo": scenario_folder / f"tripinfo_{name}.xml",
        "folder": scenario_folder
    }