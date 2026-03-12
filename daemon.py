#!/usr/bin/env python3
import subprocess, os, json, re
from datetime import datetime

# --- Dynamic Path Detection ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
STATUS_FILE = os.path.join(LOG_DIR, 'status.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    pings = []
    
    # Baca target dari config, kalau gak ada balik ke default 1.1.1.1
    target = "1.1.1.1"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                target = json.load(f).get('target', '1.1.1.1')
        except:
            pass
            
    # Eksekusi ping ke target yang udah diset
    process = subprocess.Popen(
        ['ping', target],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
                
            line = line.strip()
            match = re.search(r"time=([\d.]+)", line)
            
            if match:
                ms = float(match.group(1))
                pings.append(ms)
                
                if len(pings) > 20: 
                    pings.pop(0)
                
                avg_val = round(sum(pings) / len(pings), 1)
                min_val = round(min(pings), 1)
                max_val = round(max(pings), 1)
                
                status = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'last_ping': ms,
                    'ping': {
                        'avg': avg_val, 'min': min_val, 'max': max_val, 'count': len(pings)
                    }
                }
                
                try:
                    with open(STATUS_FILE, 'w') as f:
                        json.dump(status, f)
                        f.flush()
                        os.fsync(f.fileno())
                except:
                    pass

            elif "timeout" in line.lower() or "unreachable" in line.lower() or "cannot resolve" in line.lower():
                status = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'last_ping': 'RTO / Error',
                    'ping': {'avg': 0, 'min': 0, 'max': 0, 'count': 0}
                }
                try:
                    with open(STATUS_FILE, 'w') as f:
                        json.dump(status, f)
                        f.flush()
                        os.fsync(f.fileno())
                except:
                    pass

    except KeyboardInterrupt:
        process.terminate()

if __name__ == '__main__':
    main()
