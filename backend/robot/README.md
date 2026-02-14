# Robot (Raspberry Pi)

## Two separate processes

### 1. Robot Listener (API server)

Runs on the Raspberry Pi. Controls Arduino (motors, servo) and camera.

```bash
# On the Pi:
cd backend/robot
pip install -r requirements_pi.txt
python robot_listener.py
# or: uvicorn robot_listener:app --host 0.0.0.0 --port 8080
```

Access: `http://<pi-ip>:8080/control`

### 2. Autonomous mode (separate script)

Runs as a **different process**. Talks to the robot listener over HTTP. Use YOLO to find a target object, turn toward it, and approach until it fills 50% of the frame.

**Prerequisite:** Robot listener must be running (see above).

```bash
# On the Pi or on your PC (set --pi-url to the Pi’s address):
pip install -r requirements_pi.txt   # includes ultralytics, requests
python run_autonomous.py --target bottle
python run_autonomous.py --target cup --pi-url http://192.168.1.100:8080
```

- `--target` – COCO class name (e.g. `bottle`, `person`, `cup`)
- `--pi-url` – Base URL of the robot listener (default: `http://127.0.0.1:8080` or `ROBOT_PI_URL`)
- `--scan-only` – Only scan left/center/right and report; no turn or approach
- `--list-classes` – List available COCO class names

Stop autonomous mode: **Ctrl+C**.

## Summary

| Process            | File                 | Run how                          |
|--------------------|----------------------|-----------------------------------|
| API + hardware     | `robot_listener.py`  | `python robot_listener.py`        |
| Autonomous search  | `run_autonomous.py`  | `python run_autonomous.py --target bottle` |

Both run **differently** (separate processes). Start the listener first, then run autonomous when needed.
