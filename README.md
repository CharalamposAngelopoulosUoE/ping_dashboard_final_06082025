# Ping Dashboard Docker (Final Version)

A Dockerized dashboard to monitor IP addresses (online/offline) with real-time updates and automatic rescans.

---

## Features

- Real-time progress updates during scan
- Pie chart with **percentages** and **counts** (Online/Offline)
- **Start / Stop** manual scans
- **Autoscan toggle** (every 15 minutes)
- Offline-first sorting after completion
- Shows total IPs and source file path (`data/IP_List.xlsx`)
- **Volume mount support** — edit Excel file without rebuilding image

---

## Quick Start



```powershell
 1. Clone the Repository
    git clone https://github.com/CharalamposAngelopoulosUoE/ping_dashboard_final_06082025.git
    cd ping_dashboard_final_06082025

2. Build Docker Image
    docker build -t ping_dashboard .
    
3. Run Container (with volume mount)   
    docker run -p 5000:5000 -v ${PWD}/data/IP_List.xlsx:/app/data/IP_List.xlsx ping_dashboard