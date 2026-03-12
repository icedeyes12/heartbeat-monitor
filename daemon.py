#!/usr/bin/env python3
import subprocess, os, json, re
from datetime import datetime

LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    pings = []
    
    # Langsung panggil ping murni. Di Termux/Linux biasanya ping udah
    # lumayan line-buffered outputnya, jadi aman tanpa stdbuf.
    process = subprocess.Popen(
        ['ping', '1.1.1.1'],
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
                
                # Jaga history di 20 data terakhir
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

            elif "timeout" in line.lower() or "unreachable" in line.lower():
                status = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'last_ping': 'RTO',
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
    