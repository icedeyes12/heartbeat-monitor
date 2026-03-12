#!/usr/bin/env python3
import subprocess, time, os, json, sys, select, termios, tty
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live

console = Console()
LOG_DIR = '/home/workspace/heartbeat-monitor/logs'
STATUS_FILE = f'{LOG_DIR}/status.json'

def get_tailscale_status():
    try:
        r = subprocess.run(['tailscale', 'status'], capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            for line in r.stdout.split('\n'):
                if 'titit-0' in line or '100.126' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return f"{parts[0]} {parts[1] if len(parts) > 1 else ''}"
    except:
        pass
    return "🔴 OFFLINE"

def get_ssh_status():
    try:
        r = subprocess.run(['pgrep', '-c', 'sshd'], capture_output=True, text=True)
        if int(r.stdout.strip() or 0) > 0:
            r2 = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
            if ':2288' in r2.stdout:
                return f"🟢 {r.stdout.strip()} daemon"
    except:
        pass
    return "🔴 STOPPED"

def get_heartbeat_status():
    try:
        r = subprocess.run(['pgrep', '-f', 'heartbeat'], capture_output=True, text=True)
        if 'daemon.py' in r.stdout:
            try:
                with open(STATUS_FILE, 'r') as f:
                    d = json.load(f)
                    p = d.get('ping', {})
                    return f"🟢 RUNNING | avg:{p.get('avg',0)}ms min:{p.get('min',0)}ms max:{p.get('max',0)}ms"
            except:
                return "🟢 RUNNING (no stats)"
    except:
        pass
    return "🔴 STOPPED"

def is_daemon_running():
    try:
        r = subprocess.run(['pgrep', '-f', 'daemon.py'], capture_output=True, text=True)
        return 'daemon.py' in r.stdout
    except:
        return False

def start_daemon():
    if not is_daemon_running():
        subprocess.Popen(['python3', '/home/workspace/heartbeat-monitor/daemon.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)

def stop_daemon():
    subprocess.run(['pkill', '-f', 'daemon.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def toggle_tailscale():
    try:
        r = subprocess.run(['pgrep', 'tailscaled'], capture_output=True, text=True)
        if r.stdout.strip():
            subprocess.run(['pkill', 'tailscaled'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            return "Stopped"
        else:
            subprocess.Popen(['tailscaled', '-tun=userspace-networking', '-socks5-server=localhost:1055', '-state=/home/.z/tailscale/tailscaled.state', '-socket=/var/run/tailscale/tailscaled.sock'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            subprocess.run(['tailscale', '-socket=/var/run/tailscale/tailscaled.sock', 'up', '-auth-key=' + os.environ.get('TAILSCALE_AUTH_KEY', ''), '-hostname=' + os.environ.get('TAILSCALE_HOSTNAME', 'titit-0'), '-accept-dns=false'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Started"
    except:
        return "Error"

def toggle_ssh():
    try:
        r = subprocess.run(['pgrep', '-c', 'sshd'], capture_output=True, text=True)
        if int(r.stdout.strip() or 0) > 0:
            subprocess.run(['pkill', 'sshd'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Stopped"
        else:
            subprocess.Popen(['/usr/sbin/sshd', '-D', '-p', '2288', '-o', 'HostKey=/etc/ssh/ssh_host_ed25519_key', '-o', 'ClientAliveInterval=10', '-o', 'ClientAliveCountMax=3', '-o', 'TCPKeepAlive=yes', '-o', 'PermitRootLogin=prohibit-password'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Started"
    except:
        return "Error"

def build_ui(live_mode=False):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", width=12)
    table.add_column("Status", style="green", width=15)
    table.add_column("Info", style="yellow")
    
    ts = get_tailscale_status()
    ssh = get_ssh_status()
    hb = get_heartbeat_status()
    
    table.add_row("Tailscale", "🟢 ONLINE" if "100.126" in ts or "titit" in ts else "🔴 OFFLINE", ts)
    table.add_row("SSH", ssh.split()[0] if "🟢" in ssh else "🔴 STOPPED", ssh.replace("🟢", "").replace("daemon", "").strip() if "🟢" in ssh else ssh)
    table.add_row("Heartbeat", "🟢 RUNNING" if "🟢" in hb else "🔴 STOPPED", hb.replace("🟢 RUNNING", "").replace("|", "").strip() if "🟢" in hb else hb)
    
    mode = "[dim]Press keys: [1]Tailscale [2]SSH [3]Heartbeat [l]Live [q]Quit[/dim]"
    if live_mode:
        mode = "[bold yellow]🔴 LIVE MODE (press 'q' to quit)[/bold yellow]"
    
    return Panel(table, title="🔥 Heartbeat Monitor", subtitle=mode, border_style="blue")

def live_mode():
    try:
        with Live(build_ui(live_mode=True), refresh_per_second=1) as live:
            while True:
                time.sleep(1)
                live.update(build_ui(live_mode=True))
    except KeyboardInterrupt:
        pass

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    
    console.print("[dim]Press: [1]Tailscale [2]SSH [3]Heartbeat [l]Live [q]Quit[/dim]")
    
    with Live(build_ui(), refresh_per_second=1) as live:
        while True:
            live.update(build_ui())
            time.sleep(0.5)  # Refresh UI tiap 0.5 detik
            
            # Non-blocking input check
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1).lower()
                
                if key == 'q':
                    console.print("\n[bold green]Bye![/bold green]")
                    break
                elif key == 'l':
                    live.stop()
                    console.clear()
                    live_mode()
                    break
                elif key == '1':
                    result = toggle_tailscale()
                    console.print(f"[dim]Tailscale: {result}[/dim]")
                elif key == '2':
                    result = toggle_ssh()
                    console.print(f"[dim]SSH: {result}[/dim]")
                elif key == '3':
                    if is_daemon_running():
                        stop_daemon()
                        console.print("[dim]Heartbeat: Stopped[/dim]")
                    else:
                        start_daemon()
                        console.print("[dim]Heartbeat: Started[/dim]")

if __name__ == "__main__":
    # Setup terminal for non-blocking input
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        main()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
