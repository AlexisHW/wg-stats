#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from datetime import datetime

# Configuration - customize these
WG_CONTAINER = os.environ.get("WG_CONTAINER", "wg-easy")  # Docker container name
WG_INTERFACE = os.environ.get("WG_INTERFACE", "wg0")       # WireGuard interface name
DATA_DIR = os.environ.get("WG_DATA_DIR", "/var/opt/wg-stats")  # Directory to store data
period_env = os.environ.get("PERIOD", "daily,weekly,monthly,lastcheck")
periods = [p.strip() for p in period_env.split(",")]

def run_wg_show():
    """Run 'wg show <interface> dump' inside the Docker container and return output lines."""
    try:
        cmd = ["docker", "exec", WG_CONTAINER, "wg", "show", WG_INTERFACE, "dump"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error running wg show: {e}", file=sys.stderr)
        sys.exit(1)

def parse_wg_dump(lines):
    peers = {}
    # Skip first line if it's the interface header (optional)
    for line in lines:
        parts = line.split('\t')
        if len(parts) < 7:
            continue
        allowed_ips = parts[3]
        try:
            transfer_rx = int(parts[5])
            transfer_tx = int(parts[6])
        except ValueError:
            transfer_rx = 0
            transfer_tx = 0
        peers[allowed_ips] = {"rx": transfer_rx, "tx": transfer_tx}
    return peers

def human_readable_bytes(num):
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"

def get_period_key(period):
    now = datetime.now()
    if period == "daily":
        return now.strftime("%Y-%m-%d")
    elif period == "weekly":
        return now.strftime("%Y-W%W")
    elif period == "monthly":
        return now.strftime("%Y-%m")
    else:
        return "lastcheck"

def load_period_data(filename):
    if not os.path.exists(filename):
        return {"period_key": None, "stats": {}}
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return {"period_key": None, "stats": {}}

def save_period_data(filename, period_key, stats):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump({"period_key": period_key, "stats": stats}, f)

def print_period_stats(period, current_stats, previous_stats):
    print(f"\n=== {period.capitalize()} stats ===")
    if not current_stats:
        print("No data.")
        return

    for peer, stats in current_stats.items():
        prev = previous_stats.get(peer, {"rx": 0, "tx": 0})
        delta_rx = stats["rx"] - prev.get("rx", 0)
        delta_tx = stats["tx"] - prev.get("tx", 0)

        # Handle counter reset (negative delta)
        if delta_rx < 0:
            delta_rx = stats["rx"]
        if delta_tx < 0:
            delta_tx = stats["tx"]

        print(f"Peer: {peer}")
        print(f"  RX: {human_readable_bytes(stats['rx'])} (Total), +{human_readable_bytes(delta_rx)} since last check")
        print(f"  TX: {human_readable_bytes(stats['tx'])} (Total), +{human_readable_bytes(delta_tx)} since last check\n")

def main():
    lines = run_wg_show()
    current_stats = parse_wg_dump(lines)

    period_files = {p: os.path.join(DATA_DIR, f"{WG_CONTAINER}_{WG_INTERFACE}_{p}.json") for p in periods}
    
    now = datetime.now().strftime("%d %B %Y %H:%M:%S")
    print(f"WireGuard Traffic Report ({WG_CONTAINER}:{WG_INTERFACE})")
    print(f"Timestamp: {now}\n")

    for period in periods:
        period_key = get_period_key(period)
        period_data = load_period_data(period_files[period])
        prev_key = period_data.get("period_key")
        prev_stats = period_data.get("stats", {})

        # Reset stats if period changed (except for lastcheck)
        if period != "lastcheck" and prev_key != period_key:
            prev_stats = {}

        print_period_stats(period, current_stats, prev_stats)

        # Save current stats for next run
        save_period_data(period_files[period], period_key, current_stats)

if __name__ == "__main__":
    main()
