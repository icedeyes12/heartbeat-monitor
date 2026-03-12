#!/usr/bin/env python3
import subprocess, time, os, json
from datetime import datetime

LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'

def ping_once():
    try:
        r = subprocess.run(['ping','-c','1','-W','2','1.1.1.1'], capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            for line in r.stdout.split('\n'):
                if 'time=' in line:
                    return float(line.split('time=')[1].split()[0])
    except:
        pass
    return None

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    pings = []
    
    initial_status = {'timestamp': '--:--:--', 'ping': {'avg': 0, 'min': 0, 'max': 0, 'count': 0}}
    with open(STATUS_FILE, 'w') as f:
        json.dump(initial_status, f)
    
    while True:
        ms = ping_once()
        
        if ms is not None:
            pings.append(ms)
            if len(pings) > 20: 
                pings.pop(0)
            
            avg_val = round(sum(pings) / len(pings), 1)
            min_val = round(min(pings), 1)
            max_val = round(max(pings), 1)
            
            status = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'ping': {
                    'avg': avg_val,
                    'min': min_val,
                    'max': max_val,
                    'count': len(pings)
                }
            }
            
            try:
                with open(STATUS_FILE, 'w') as f:
                    json.dump(status, f)
            except:
                pass
        
        time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
