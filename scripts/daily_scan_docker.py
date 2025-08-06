import subprocess
import platform
import json
import os
import pandas as pd
from datetime import datetime

IP_FILE = os.path.join("data", "IP_List.xlsx")
DATA_FILE = "/tmp/scan_results.json"
PROGRESS_FILE = "/tmp/scan_progress.json"
STOP_FLAG = "/tmp/stop_scan"

def load_ips():
    if not os.path.exists(IP_FILE):
        raise FileNotFoundError(f"IP list file not found: {IP_FILE}")

    df = pd.read_excel(IP_FILE)
    df.columns = [c.strip().lower() for c in df.columns]

    name_col = None
    ip_col = None
    for col in df.columns:
        if "name" in col:
            name_col = col
        if "ip" in col:
            ip_col = col

    if not name_col or not ip_col:
        raise ValueError(f"Expected columns containing 'Name' and 'IP' in {IP_FILE}")

    ips = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        ip = str(row[ip_col]).strip()
        if name and ip:
            ips.append({"name": name, "ip": ip})

    if not ips:
        raise ValueError(f"No valid IPs found in {IP_FILE}")

    return ips

def ping(host, retries=4, timeout=1):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"

    for _ in range(retries):
        command = ["ping", param, "1", timeout_param, str(timeout), host]
        if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return True
    return False

def run_scan():
    # Clear stop flag
    if os.path.exists(STOP_FLAG):
        os.remove(STOP_FLAG)

    ips = load_ips()
    total = len(ips)
    results = []

    # Initialize progress
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"status": "running", "completed": 0, "total": total, "results": []}, f)

    for idx, item in enumerate(ips, start=1):
        # Stop if STOP_FLAG exists
        if os.path.exists(STOP_FLAG):
            with open(PROGRESS_FILE, "w") as f:
                json.dump({"status": "stopped", "completed": idx-1, "total": total, "results": results}, f)
            return

        status = "online" if ping(item["ip"]) else "offline"
        results.append({
            "name": item["name"],
            "ip": item["ip"],
            "status": status
        })

        # Update progress file incrementally
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"status": "running", "completed": idx, "total": total, "results": results}, f)

    # Finalize results
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    with open(PROGRESS_FILE, "w") as f:
        json.dump({"status": "completed", "completed": total, "total": total, "results": results}, f)

if __name__ == "__main__":
    run_scan()
