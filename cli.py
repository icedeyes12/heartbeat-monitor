#!/usr/bin/env python3
import subprocess, time, os, json, sys, select, tty, termios
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.live import Live

console = Console()

# --- Dynamic Path & Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
STATUS_FILE = os.path.join(LOG_DIR, 'status.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
DAEMON_PATH = os.path.join(BASE_DIR, 'daemon.py')
TAIL_SOCK = '/var/run/tailscale/tailscaled.sock'

# --- Service Checkers ---
def cmd(c, t=2):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=t)
    except: return None

def get_ts():
    r_pid = cmd(['pgrep', 'tailscaled'])
    pids = r_pid.stdout.strip().replace('\n', ',') if r_pid and r_pid.stdout else ""
    pid_text = f"[dim cyan][PID: {pids}][/] " if pids else ""
    
    r = cmd(['tailscale', '--socket=' + TAIL_SOCK, 'status'])
    if r and r.returncode == 0:
        for l in r.stdout.split('\n'):
            if '100.126' in l or 'titit-0' in l:
                return '🟢 ONLINE', pid_text + l.split()[0]
    return '🔴 OFFLINE', '-'

def get_ssh():
    r_pid = cmd(['pgrep', 'sshd'])
    pids = r_pid.stdout.strip().replace('\n', ',') if r_pid and r_pid.stdout else ""
    pid_text = f"[dim cyan][PID: {pids}][/] " if pids else ""
    
    n = len(pids.split(',')) if pids else 0
    if n > 0: 
        return '🟢 RUNNING', pid_text + f'{n} daemon | Port 2288'
    return '🔴 STOPPED', '-'

def get_hb():
    r_pid = cmd(['pgrep', '-f', 'daemon.py'])
    pids = r_pid.stdout.strip().replace('\n', ',') if r_pid and r_pid.stdout else ""
    pid_text = f"[dim cyan][PID: {pids}][/] " if pids else ""
    
    if pids:
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    d = json.load(f)
                    p = d.get('ping', {})
                    last = d.get('last_ping', 'Wait...') 
                    
                    color = "red" if "RTO" in str(last) else "green"
                    m = f"Last: [{color}]{last}[/] | Min: {p.get('min',0)} | Avg: {p.get('avg',0)} | Max: {p.get('max',0)} ms"
                    return '🟢 RUNNING', pid_text + m
        except: pass
        return '🟢 RUNNING', pid_text + 'Wait...'
    return '🔴 STOPPED', '-'

# --- Service Toggles ---
def run_svc(svc):
    if svc == 'ts':
        r = cmd(['pgrep', 'tailscaled'])
        if r and r.stdout.strip(): 
            cmd(['pkill', 'tailscaled'])
        else:
            subprocess.Popen(['tailscaled', '-tun=userspace-networking', '-socket=' + TAIL_SOCK], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            time.sleep(1)
            cmd(['tailscale', '-socket=' + TAIL_SOCK, 'up', '--hostname=titit-0', '--accept-dns=false'])
            
    elif svc == 'ssh':
        r = cmd(['pgrep', '-c', 'sshd'])
        if r and int(r.stdout.strip() or 0) > 0: 
            cmd(['pkill', 'sshd'])
        else: 
            subprocess.Popen(['/usr/sbin/sshd', '-D', '-p', '2288'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            
    elif svc == 'hb':
        r = cmd(['pgrep', '-f', 'daemon.py'])
        if r and r.stdout.strip(): 
            cmd(['pkill', '-f', 'daemon.py'])
        else: 
            subprocess.Popen(['python3', DAEMON_PATH], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

# --- UI Builder ---
def generate_ui():
    table = Table(box=box.ROUNDED, expand=True, border_style="blue")
    table.add_column('Service', style='cyan', width=16)
    table.add_column('Status', width=15)
    table.add_column('Metrics / Info', style='white')
    
    ts_s, ts_i = get_ts()
    ss_s, ss_i = get_ssh()
    hb_s, hb_i = get_hb()
    
    # Baca target saat ini buat ditampilin di layar
    target = "1.1.1.1"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                target = json.load(f).get('target', '1.1.1.1')
        except: pass
    
    table.add_row('Tailscale', ts_s, ts_i)
    table.add_row('SSH', ss_s, ss_i)
    table.add_row(f'Heartbeat\n[dim cyan]({target})[/]', hb_s, hb_i)
    
    return Panel(
        table, 
        title=' [bold white]Heartbeat Monitor[/] [dim]Dashboard[/]', 
        subtitle='[yellow]1[/]:TS [yellow]2[/]:SSH [yellow]3[/]:HB | [yellow]T[/]:Target | [red]Q[/]:Quit',
        border_style='magenta'
    )

# --- Main Logic ---
def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    while True:
        action = None
        
        # Pake transient=True biar pas layar ganti ke prompt input, tabel lamanya ilang sementara
        with Live(generate_ui(), refresh_per_second=10, transient=True) as live:
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                while True:
                    live.update(generate_ui())
                    
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        key = sys.stdin.read(1).lower()
                        if key == 'q': 
                            action = 'quit'
                            break
                        elif key == 't':
                            action = 'target'
                            break
                        elif key == '1': run_svc('ts')
                        elif key == '2': run_svc('ssh')
                        elif key == '3': run_svc('hb')
                    
                    time.sleep(0.05)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # --- Handle aksi setelah Live ditutup sementara ---
        if action == 'quit':
            break
            
        elif action == 'target':
            console.print("\n[bold cyan]=== Ganti Target Ping ===[/]")
            new_target = console.input("[bold]Masukkan IP/Domain (kosongkan untuk default 1.1.1.1): [/]").strip()
            if not new_target:
                new_target = "1.1.1.1"
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"target": new_target}, f)
            
            # Restart daemon kalau lagi jalan biar langsung ngefek
            r = cmd(['pgrep', '-f', 'daemon.py'])
            if r and r.stdout.strip():
                cmd(['pkill', '-f', 'daemon.py'])
                time.sleep(0.5)
                subprocess.Popen(['python3', DAEMON_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            
            console.print(f"[bold green]Target diubah ke {new_target}! Restarting dashboard...[/]")
            time.sleep(1)
            # Loop otomatis balik ke awal dan ngebuka tabel Live lagi

if __name__ == '__main__':
    console.print("[bold cyan] Heartbeat Monitor ready...[/] [dim i]by @icedeyes12[/dim i]")
    try: 
        main()
    except KeyboardInterrupt: 
        pass
    console.print("\n[bold green]CLI closed. Daemon running in background.[/]")
