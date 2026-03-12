#!/usr/bin/env python3
import subprocess, os, json, sys, re
from datetime import datetime

LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    pings = []
    
    process = subprocess.Popen(
        ['ping', '1.1.1.1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    try:
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            match = re.search(r"time=([\d.]+)", line)
            
            if match:
                ms = float(match.group(1))
                pings.append(ms)
                if len(pings) > 20: pings.pop(0)
                
                avg_val = round(sum(pings) / len(pings), 1)
                min_val = round(min(pings), 1)
                max_val = round(max(pings), 1)
                
                status = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'last_ping': ms,
                    'ping': {'avg': avg_val, 'min': min_val, 'max': max_val, 'count': len(pings)}
                }
            elif "timeout" in line.lower() or "unreachable" in line.lower():
                status = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'last_ping': 'RTO',
                    'ping': {'avg': 0, 'min': 0, 'max': 0, 'count': 0}
                }
            else:
                continue
                
            with open(STATUS_FILE, 'w') as f:
                json.dump(status, f)
    except KeyboardInterrupt:
        process.terminate()

if __name__ == '__main__':
    main()
