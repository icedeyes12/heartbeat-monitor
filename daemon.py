#!/usr/bin/env python3
import subprocess, time, os, json, sys, re
from datetime import datetime

console = Console()
LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'
TAIL_SOCK = '/var/run/tailscale/tailscaled.sock'

def cmd(c, t=2):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=t)
    except: return None

def ping_once():
    r = cmd(['ping', '-c', '1', '-W', '2', '1.1.1.1'])
    if r and r.returncode == 0:
        m = re.search(r'time=([
[truncated]
')/len(ping_times)
        if d['ping']['avg'] < 30: color = 'green'
        elif d['ping']['avg'] < 100: color = 'yellow'
        else: color = 'red'
        
        d['msg'] = f"[bold {color}]Ping OK[/] | Min: {d['ping']['min']:.1f} | Avg: {d['ping']['avg']:.1f} | Max: {d['ping']['max']:.1f} ms"
        d['color'] = color
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(d, f)
    
    time.sleep(1)

if __name__ == '__main__':
    os.makedirs(LOG_DIR, exist_ok=True)
    console.print('[bold green]Daemon started[/]')
    try:
        main()
    except KeyboardInterrupt:
        pass
    console.print('[bold red]Daemon stopped[/]')
