# Heartbeat Monitor

Monitor dashboard untuk Tailscale, SSH, dan heartbeat ping.

## Files
- `daemon.py` - Ping ke 100.126.125.89 tiap 30 detik
- `cli.py` - Dashboard interaktif
- `logs/` - Auto-create, git-ignored

## Usage

```bash
python3 daemon.py &
python3 cli.py
```

## Keys
| Key | Action |
|-----|--------|
| 1 | Restart Tailscale |
| 2 | Restart SSH |
| 3 | Toggle Heartbeat |
| l | Live Mode |
| q | Quit |

## Auto-start

Add to `.zshrc`:
```bash
if ! pgrep -f heartbeat-monitor/daemon.py > /dev/null; then
    nohup python3 /home/workspace/heartbeat-monitor/daemon.py > /dev/null 2>&1 &
fi
alias hb='python3 /home/workspace/heartbeat-monitor/cli.py'
```
