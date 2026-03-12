#!/usr/bin/env python3
import subprocess, time, os, json, sys, select, tty, termios
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.live import Live

console = Console()
LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'
TAIL_SOCK = '/var/run/tailscale/tailscaled.sock'

# --- Service Checkers ---
def cmd(c, t=2):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=t)
    except: return None

def get_ts():
    r = cmd(['tailscale', '--socket=' + TAIL_SOCK, 'status'])
    if r and r.returncode == 0:
        for l in r.stdout.split('\n'):
            if '100.126' in l or 'titit-0' in l:
                return '🟢 ONLINE', l.split()[0]
    return '🔴 OFFLINE', '-'

def get_ssh():
    r = cmd(['pgrep', '-c', 'sshd'])
    n = int(r.stdout.strip() if r and r.stdout else 0)
    if n > 0: return '🟢 RUNNING', f'{n} daemon | Port 2288'
    return '🔴 STOPPED', '-'

def get_hb():
    r = cmd(['pgrep', '-f', 'daemon.py'])
    if r and r.stdout.strip():
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    d = json.load(f)
                    p = d.get('ping', {})
                    # Kasih fallback "Wait..." kalau daemon belum sempet nulis key last_ping
                    last = d.get('last_ping', 'Wait...') 
                    
                    color = "red" if last == "RTO" else "cyan"
                    m = f"Last: [{color}]{last}[/] | Min: {p.get('min',0)} | Avg: {p.get('avg',0)} | Max: {p.get('max',0)} ms"
                    return '🟢 RUNNING', m
        except: pass
        return '🟢 RUNNING', 'Loading...'
    return '🔴 STOPPED', '-'

# --- Service Toggles ---
def run_svc(svc):
    if svc == 'ts':
        r = cmd(['pgrep', 'tailscaled'])
        if r and r.stdout.strip(): 
            cmd(['pkill', 'tailscaled'])
        else:
            subprocess.Popen(['tailscaled', '-tun=userspace-networking', '-socket=' + TAIL_SOCK], stdout=subprocess.DEVNULL)
            time.sleep(1)
            cmd(['tailscale', '-socket=' + TAIL_SOCK, 'up', '--hostname=titit-0', '--accept-dns=false'])
    elif svc == 'ssh':
        r = cmd(['pgrep', '-c', 'sshd'])
        if r and int(r.stdout.strip() or 0) > 0: 
            cmd(['pkill', 'sshd'])
        else: 
            subprocess.Popen(['/usr/sbin/sshd', '-D', '-p', '2288'], stdout=subprocess.DEVNULL)
    elif svc == 'hb':
        r = cmd(['pgrep', '-f', 'daemon.py'])
        if r and r.stdout.strip(): 
            cmd(['pkill', '-f', 'daemon.py'])
        else: 
            subprocess.Popen(['python3', '/home/workspace/heartbeat-monitor/daemon.py'], stdout=subprocess.DEVNULL)

# --- UI Builder ---
def generate_ui():
    table = Table(box=box.ROUNDED, expand=True, border_style="blue")
    table.add_column('Service', style='cyan', width=12)
    table.add_column('Status', width=15)
    table.add_column('Metrics / Info', style='white')
    
    ts_s, ts_i = get_ts()
    ss_s, ss_i = get_ssh()
    hb_s, hb_i = get_hb()
    
    table.add_row('Tailscale', ts_s, ts_i)
    table.add_row('SSH', ss_s, ss_i)
    table.add_row('Heartbeat', hb_s, hb_i)
    
    return Panel(
        table, 
        title='🔥 [bold white]Heartbeat Monitor[/] [dim]Dashboard[/]', 
        subtitle='[yellow]1[/]:TS [yellow]2[/]:SSH [yellow]3[/]:HB | [red]Q[/]:Quit',
        border_style='magenta'
    )

# --- Main Logic ---
def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Refresh rate di 10 biar mulus
    with Live(generate_ui(), refresh_per_second=10, transient=False) as live:
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                live.update(generate_ui())
                
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'q': break
                    elif key == '1': run_svc('ts')
                    elif key == '2': run_svc('ssh')
                    elif key == '3': run_svc('hb')
                
                time.sleep(0.05)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == '__main__':
    console.print("[bold cyan]Welcome Bas, Heartbeat system ready...[/]")
    try: 
        main()
    except KeyboardInterrupt: 
        pass
    console.print("\n[bold green]Selesai![/]")
