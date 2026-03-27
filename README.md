# pi-rodactyl

This is the public repo for the Aerodactyl's drone team for the UAS4STEM competition in 2025.

# How to Setup

## GIT BASH

Setup the venv:<br />

```bash
cd ui && python -m venv venv && ./venv/Scripts/pip install -r api/requirements.txt
```

(be inside the pi-rodactyl directory)<br />
Run the mavproxy:<br />

```bash
mavproxy --master=COM3 --baudrate 57600 --out 127.0.0.1:14551 --out 127.0.0.1:14552
```

Run the gui:<br />

```bash
cd ui && npm run next-dev
```

Run the state machine:<br />

```bash
cd ui && ./venv/Scripts/python api/index.py
```

## COMMAND PROMPT

Setup the venv:<br />

```bash
cd ui && python -m venv venv && venv\Scripts\pip install -r api\requirements.txt
```

(be inside the pi-rodactyl directory)<br />
Run the mavproxy:<br />

```bash
mavproxy --master=COM3 --baudrate 57600 --out 127.0.0.1:14551 --out 127.0.0.1:14552
```

Run the gui:<br />

```bash
cd ui && npm run next-dev
```

Run the state machine:<br />

```bash
cd ui && venv\Scripts\python api\index.py
```

# Credits

Written by: [Chandu Peddada (Chanadu)](https://github.com/Chanadu), osirais, UnityGranted, and [Lucas Lyubenko (Luc215)](https://github.com/Luc215)
