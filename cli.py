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

def cmd(c, t=3):
    try: return subprocess.run(c, capture_output=True, text=True, timeout=t)
    except: return None

def ts():
    r = cmd(['tailscale', '--socket=' + TAIL_SOCK, 'status'])
    if r and r.returncode == 0:
        for l in r.stdout.split('\n'):
            if '100.126' in l or 'titit-0' in l:
                return '🟢 ONLINE | ' + l.split()[0]
    return '🔴 OFFLINE'

def ssh():
    r = cmd(['pgrep', '-c', 'sshd'])
    n = int(r.stdout.strip() if r and r.stdout else 0)
    if n > 0:
        r2 = cmd(['ss', '-tlnp'])
        if r2 and ':2288' in r2.stdout: return '🟢 ' + str(n) + ' daemon | Port 2288'
    return '🔴 STOPPED'

def hb():
    r = cmd(['pgrep', '-f', 'daemon.py'])
    if r and r.stdout.strip():
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    d = json.load(f)
                    p = d.get('ping', {})
                    metrics = f"Min: [green]{p.get('min',0)}[/green] | Avg: [yellow]{p.get('avg',0)}[/yellow] | Max: [red]{p.get('max',0)}[/red] ms"
                    return f'🟢 RUNNING | {metrics}'
            return '🟢 RUNNING (Waiting for data...)'
        except:
            return '🟢 RUNNING'
    return '🔴 STOPPED'

def run_ts():
    r = cmd(['pgrep', 'tailscaled'])
    if r and r.stdout.strip():
        cmd(['pkill', 'tailscaled'])
        return '⏹️ Stopped'
    subprocess.Popen(['tailscaled', '-tun=userspace-networking', '-socks5-server=localhost:1055', '-state=/home/.z/tailscale/tailscaled.state', '-socket=' + TAIL_SOCK], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    cmd(['tailscale', '-socket=' + TAIL_SOCK, 'up', '-auth-key=' + os.environ.get('TAILSCALE_AUTH_KEY',''), '-hostname=' + os.environ.get('TAILSCALE_HOSTNAME','titit-0'), '-accept-dns=false'])
    return '▶️ Started'

def run_ssh():
    r = cmd(['pgrep', '-c', 'sshd'])
    if r and int(r.stdout.strip() or 0) > 0:
        cmd(['pkill', 'sshd'])
        return '⏹️ Stopped'
    subprocess.Popen(['/usr/sbin/sshd', '-D', '-p', '2288', '-o', 'HostKey=/etc/ssh/ssh_host_ed25519_key', '-o', 'ClientAliveInterval=10', '-o', 'TCPKeepAlive=yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return '▶️ Started'

def run_hb():
    r = cmd(['pgrep', '-f', 'daemon.py'])
    if r and r.stdout.strip():
        cmd(['pkill', '-f', 'daemon.py'])
        return '⏹️ Stopped'
    subprocess.Popen(['python3', '/home/workspace/heartbeat-monitor/daemon.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return '▶️ Started'

def generate_table():
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column('Service', style='cyan', width=12)
    table.add_column('Status', style='bold white', width=15)
    table.add_column('Metrics / Info', style='white')
    
    t_raw, s_raw, h_raw = ts(), ssh(), hb()
    
    t_status = '🟢 ONLINE' if '🟢' in t_raw else '🔴 OFFLINE'
    t_info = t_raw.replace('🟢','').replace('ONLINE','').replace('|','').strip() if '🟢' in t_raw else '-'
    table.add_row('Tailscale', t_status, t_info)
    
    s_status = '🟢 RUNNING' if '🟢' in s_raw else '🔴 STOPPED'
    s_info = s_raw.replace('🟢','').strip() if '🟢' in s_raw else '-'
    table.add_row('SSH', s_status, s_info)
    
    h_status = '🟢 RUNNING' if '🟢' in h_raw else '🔴 STOPPED'
    h_info = h_raw.split('|')[1].strip() if '|' in h_raw else '-'
    table.add_row('Heartbeat', h_status, h_info)
    
    return Panel(
        table, 
        title='[bold magenta]🔥 Heartbeat Monitor Dashboard[/bold magenta]', 
        subtitle='[white on blue] 1:TS | 2:SSH | 3:HB | Q:Quit [/white on blue]',
        border_style='blue'
    )

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    with Live(generate_table(), refresh_per_second=4, screen=True) as live:
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                live.update(generate_table())
                
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'q':
                        break
                    elif key == '1':
                        run_ts()
                    elif key == '2':
                        run_ssh()
                    elif key == '3':
                        run_hb()
                
                time.sleep(0.05)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    console.print('[bold green]Bye Bas![/bold green]')
