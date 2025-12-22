# F1 Race Visualization

A Python application that visualizes Formula 1 race data using the FastF1 library and the Arcade game engine. The repo also includes a static, browser-based visualization powered by pre-exported JSON datasets for easy hosting (e.g., GitHub Pages).

## What It Does

This application loads historical F1 race data and creates an animated visualization showing:

- **Track Layout**: A visual representation of the F1 circuit
- **Driver Positions**: Real-time positions of all drivers on the track during the race
- **Race Dashboard**: Live leaderboard showing driver positions, lap times, and gaps
- **Playback Controls**: Play, pause, and adjust speed of the race replay

The visualization uses actual telemetry data from F1 races to accurately recreate driver positions lap-by-lap.

## Getting Started

Preview the static site locally:

```bash
git clone https://github.com/Tausif-Rahman/F1-Race-Visualization.git
cd F1-Race-Visualization
python3 -m http.server 8000
# Open http://localhost:8000/
```

## Requirements

- **Web visualization (static)**: Modern browser only (no backend needed)
- **Exporter / Desktop app**:
	- Python 3.12+
	- Packages in `requirements.txt`

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install project dependencies
pip install -r requirements.txt
```

## Usage

Choose one of the following modes.

### Web (Static Demo)

Preview locally with a simple HTTP server:

```bash
python3 -m http.server 8000
# Open http://localhost:8000/
```

### Desktop App (Arcade)

Run the desktop visualization window:

```bash
python3 run.py
# OR
python3 -m src
```

The first run will download and cache race data. Subsequent runs will use the cached data.

### Flask (Local API)

Serve a local API and a template-rendered homepage:

```bash
# (Optional) create/activate a venv
python3 -m venv .venv
source .venv/bin/activate

# Install project dependencies
pip install -r requirements.txt

# Start the local API + template server
python3 api.py

# Endpoints
# Home:        http://127.0.0.1:3000/
# Season API:  http://127.0.0.1:3000/api/season/2025
# Race API:    http://127.0.0.1:3000/api/race/2025/1/58
# Health:      http://127.0.0.1:3000/api/health
```

## Exporter & Commands

Export static datasets from the FastF1 cache:

```bash
# Export Australian GP (Round 1)
python3 -m src.export_static_json 2025 1

# Export additional rounds (examples)
python3 -m src.export_static_json 2025 2
python3 -m src.export_static_json 2025 3

# Preview the site with a local static server
python3 -m http.server 8080
# Open http://localhost:8080/
```

Outputs are written to `static/data/` and the dataset index (`static/data/index.json`) is automatically maintained.

## Controls

- **Space**: Play/Pause
- **Up/Down Arrow**: Adjust playback speed
- **Left/Right Arrow**: Skip forward/backward
- **Q**: Quit

## How It Works

- **Data Export**: Python exporter writes race telemetry + lap times to `static/data/*.json`.
- **Dataset Index**: `static/data/index.json` lists available datasets and is auto-maintained.
- **Client Visualization**: The browser loads JSON and animates drivers on a canvas with lap progression.
- **No Backend Required**: All data is fetched as static files; Flask is for local development only.

## Repository Overview

- **index.html**: Static site entry. Hosts the visualization and docs.
- **static/js/viz.js**: Canvas renderer and race animation. Loads static JSON datasets.
- **static/data/**: Pre-exported datasets and `index.json` list.
- **src/export_static_json.py**: Exporter producing the static JSON from FastF1 cache.
- **cache/**: FastF1 cache assets (timing, telemetry). Used by the exporter.
- **src/main.py** & **run.py**: Desktop visualization using the Arcade engine.
- **api.py** & **templates/index.html**: Dev-only Flask API + template.

## Data Source

Race data is provided by the [FastF1](https://github.com/theOehrly/Fast-F1) library, which accesses official timing data. Datasets are exported locally and served as static files for the web visualization.
