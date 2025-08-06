from flask import Flask, render_template_string, redirect, url_for, jsonify
import json
import os
import subprocess
import threading
import time
import pandas as pd

app = Flask(__name__)
DATA_FILE = "/tmp/scan_results.json"
PROGRESS_FILE = "/tmp/scan_progress.json"
AUTOSCAN_FLAG = "/tmp/autoscan_enabled"
STOP_FLAG = "/tmp/stop_scan"
IP_FILE = "data/IP_List.xlsx"

# ------------------ Autoscan Thread ------------------
def autoscan_loop():
    while True:
        if os.path.exists(AUTOSCAN_FLAG):
            subprocess.Popen(["python", "scripts/daily_scan_docker.py"])
        time.sleep(900)  # 15 minutes
threading.Thread(target=autoscan_loop, daemon=True).start()

# ------------------ Helpers ------------------
def load_results():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
        results = data.get("results", [])
        timestamp = data.get("timestamp", "Unknown")
    else:
        results = []
        timestamp = "No scan data available"
    return results, timestamp

def count_ips():
    if os.path.exists(IP_FILE):
        try:
            df = pd.read_excel(IP_FILE)
            return len(df)
        except Exception:
            return 0
    return 0

# ------------------ Routes ------------------
@app.route('/')
def dashboard():
    results, timestamp = load_results()
    autoscan_status = "ON" if os.path.exists(AUTOSCAN_FLAG) else "OFF"
    ip_count = count_ips()
    source_path = os.path.abspath(IP_FILE)

    html = """
    <h1>Ping Dashboard (Docker)</h1>
    <p>Last Scan: """ + timestamp + """</p>
    <p>Total IPs in list: """ + str(ip_count) + """</p>
    <p>Data source: """ + source_path + """</p>
    <p>Autoscan: """ + autoscan_status + """ (every 15 minutes)</p>
    <form action='""" + url_for('start_scan') + """' method='post' style='display:inline;'>
        <button type='submit'>Start Scan</button>
    </form>
    <form action='""" + url_for('stop_scan') + """' method='post' style='display:inline;'>
        <button type='submit'>Stop Scan</button>
    </form>
    <form action='""" + url_for('toggle_autoscan') + """' method='post' style='display:inline;'>
        <button type='submit'>Toggle Autoscan</button>
    </form>
    <div id='progress' style="margin:10px 0; font-weight:bold;"></div>
    <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:10px;">
        <canvas id="statusChart" style="max-width: 200px; max-height: 200px;"></canvas>
        <div id="chartCounts" style="margin-top:5px; font-weight:bold;"></div>
    </div>
    <table id='results' border='1' style='margin:0 auto; border-collapse:collapse;'>
        <tr><th>Name</th><th>IP</th><th>Status</th></tr>
    </table>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <script>
    let pieChart;
    function fetchProgress() {
        fetch('/progress').then(res => res.json()).then(data => {
            let progressDiv = document.getElementById('progress');
            let table = document.getElementById('results');
            table.innerHTML = "<tr><th>Name</th><th>IP</th><th>Status</th></tr>";
            if (data.status === "running") {
                progressDiv.innerHTML = "Scanning... " + data.completed + "/" + data.total;
            } else if (data.status === "completed") {
                progressDiv.innerHTML = "Scan complete (" + data.total + " IPs)";
            } else if (data.status === "stopped") {
                progressDiv.innerHTML = "Scan stopped at " + data.completed + "/" + data.total;
            }
            let online = 0, offline = 0;
            data.results.forEach(r => {
                let color = r.status === "online" ? "green" : "red";
                table.innerHTML += "<tr><td>"+r.name+"</td><td>"+r.ip+"</td><td style='color:"+color+"'>"+r.status+"</td></tr>";
                if(r.status === "online") online++; else offline++;
            });
            // Update counts text
            document.getElementById('chartCounts').innerHTML = 
                "Online: " + online + " | Offline: " + offline;

            // Update pie chart
            const ctx = document.getElementById('statusChart').getContext('2d');
            if (!pieChart) {
                pieChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['Online', 'Offline'],
                        datasets: [{
                            data: [online, offline],
                            backgroundColor: ['green', 'red']
                        }]
                    },
                    options: {
                        plugins: {
                            datalabels: {
                                color: '#fff',
                                formatter: (value, ctx) => {
                                    let sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    let percentage = (value * 100 / sum).toFixed(0) + "%";
                                    return percentage;
                                }
                            }
                        }
                    },
                    plugins: [ChartDataLabels]
                });
            } else {
                pieChart.data.datasets[0].data = [online, offline];
                pieChart.update();
            }
        });
    }
    setInterval(fetchProgress, 1000);
    </script>
    """
    return render_template_string(html)

@app.route('/start', methods=['POST'])
def start_scan():
    # Clear old results before starting
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(STOP_FLAG):
        os.remove(STOP_FLAG)

    subprocess.Popen(["python", "scripts/daily_scan_docker.py"])
    return redirect(url_for('dashboard'))

@app.route('/stop', methods=['POST'])
def stop_scan():
    with open(STOP_FLAG, "w") as f:
        f.write("stop")
    return redirect(url_for('dashboard'))

@app.route('/toggle_autoscan', methods=['POST'])
def toggle_autoscan():
    if os.path.exists(AUTOSCAN_FLAG):
        os.remove(AUTOSCAN_FLAG)
    else:
        with open(AUTOSCAN_FLAG, "w") as f:
            f.write("enabled")
    return redirect(url_for('dashboard'))

@app.route('/progress')
def progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            data = json.load(f)
        if data.get("status") == "completed":
            data["results"] = sorted(data["results"], key=lambda x: x["status"] != "offline")
        return jsonify(data)
    else:
        return jsonify({"status": "idle", "completed": 0, "total": 0, "results": []})

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        subprocess.Popen(["python", "scripts/daily_scan_docker.py"])
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
