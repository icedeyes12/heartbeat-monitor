#!/usr/bin/env python3
import subprocess, time, os, json, sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

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
            with open(STATUS_FILE) as f:
                d = json.load(f)
                p = d.get('ping', {})
                return '🟢 RUNNING | avg:' + str(p.get('avg',0)) + 'ms'
        except: return '🟢 RUNNING'
    return '🔴 STOPPED'

def run_ts():
    r = cmd(['pgrep', 'tailscaled'])
    if r and r.stdout.strip():
        cmd(['pkill', 'tailscaled']); return '⏹️  Stopped'
    subprocess.Popen(['tailscaled', '-tun=userspace-networking', '-socks5-server=localhost:1055', '-state=/home/.z/tailscale/tailscaled.state', '-socket=' + TAIL_SOCK], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    cmd(['tailscale', '-socket=' + TAIL_SOCK, 'up', '-auth-key=' + os.environ.get('TAILSCALE_AUTH_KEY',''), '-hostname=' + os.environ.get('TAILSCALE_HOSTNAME','titit-0'), '-accept-dns=false'])
    return '▶️  Started'

def run_ssh():
    r = cmd(['pgrep', '-c', 'sshd'])
    if r and int(r.stdout.strip() or 0) > 0:
        cmd(['pkill', 'sshd']); return '⏹️  Stopped'
    subprocess.Popen(['/usr/sbin/sshd', '-D', '-p', '2288', '-o', 'HostKey=/etc/ssh/ssh_host_ed25519_key', '-o', 'ClientAliveInterval=10', '-o', 'TCPKeepAlive=yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return '▶️  Started'

def run_hb():
    r = cmd(['pgrep', '-f', 'daemon.py'])
    if r and r.stdout.strip():
        cmd(['pkill', '-f', 'daemon.py']); return '⏹️  Stopped'
    subprocess.Popen(['python3', '/home/workspace/heartbeat-monitor/daemon.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return '▶️  Started'

def show():
    table = Table(box=box.ROUNDED)
    table.add_column('Service', style='cyan', width=12)
    table.add_column('Status', style='green', width=15)
    table.add_column('Info', style='yellow')
    t, s, h = ts(), ssh(), hb()
    t_ok, s_ok, h_ok = '🟢' in t, '🟢' in s, '🟢' in h
    table.add_row('Tailscale', '🟢 ONLINE' if t_ok else '🔴 OFFLINE', t.replace('🟢','').replace('ONLINE','').strip() if t_ok else t)
    table.add_row('SSH', '🟢 RUNNING' if s_ok else '🔴 STOPPED', s.replace('🟢','').strip() if s_ok else s)
    table.add_row('Heartbeat', '🟢 RUNNING' if h_ok else '🔴 STOPPED', h.replace('🟢 RUNNING |','').strip() if h_ok else h)
    console.print(Panel(table, title='🔥 Heartbeat Monitor', subtitle='[1]Tailscale [2]SSH [3]Heartbeat [r]Refresh [l]Live [q]Quit', border_style='blue'))

def live():
    try:
        while True:
            console.clear(); show()
            console.print('\n[dim]Live: auto-refresh 2s | Ctrl+C to stop[/dim]')
            time.sleep(2)
    except KeyboardInterrupt:
        console.print('\n[bold]Stopped.[/bold]')

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    while True:
        console.clear(); show()
        try:
            k = console.input('\n[bold]Pilih: [/bold]').strip().lower()
        except EOFError:
            break
        if k == 'q': break
        elif k == 'r': continue
        elif k == 'l': live(); continue
        elif k == '1': console.print('[dim]Tailscale: ' + run_ts() + '[/dim]'); time.sleep(1)
        elif k == '2': console.print('[dim]SSH: ' + run_ssh() + '[/dim]'); time.sleep(1)
        elif k == '3': console.print('[dim]Heartbeat: ' + run_hb() + '[/dim]'); time.sleep(1)
    console.print('[bold green]Bye![/bold green]')

if __name__ == '__main__':
    main()
