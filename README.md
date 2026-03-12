# Heartbeat Monitor

Keepalive daemon untuk Zo Computer + rich CLI dashboard.

## Files

| File | Purpose |
|------|---------|
| `daemon.py` | Background process, auto-restart services |
| `cli.py` | Rich TUI dashboard |

## Usage

```bash
# Start daemon (background)
nohup python3 /home/workspace/heartbeat-monitor/daemon.py > /dev/null 2>&1 &

# Open dashboard (anytime)
python3 /home/workspace/heartbeat-monitor/cli.py
```

## Auto-start

Add to `.zshrc`:
```zsh
# Auto-start heartbeat daemon
if ! pgrep -f "daemon.py" > /dev/null; then
  nohup python3 /home/workspace/heartbeat-monitor/daemon.py > /dev/null 2>&1 &
fi
alias hb='python3 /home/workspace/heartbeat-monitor/cli.py'
```

## Features

- Auto-restart Tailscale & SSH if down
- Ping statistics (Avg/Min/Max ms)
- Real-time rich UI
- Multiple clients can connect
- JSON state file at `/tmp/heartbeat.json`
