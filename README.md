# F1 Race Visualization

A Python application that visualizes Formula 1 race data in real-time using the FastF1 library and Arcade game engine.

## What It Does

This application loads historical F1 race data and creates an animated visualization showing:

- **Track Layout**: A visual representation of the F1 circuit
- **Driver Positions**: Real-time positions of all drivers on the track during the race
- **Race Dashboard**: Live leaderboard showing driver positions, lap times, and gaps
- **Playback Controls**: Play, pause, and adjust speed of the race replay

The visualization uses actual telemetry data from F1 races to accurately recreate driver positions lap-by-lap.

## Requirements

- Python 3.12+
- fastf1
- arcade

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install fastf1 arcade
```

## Usage

Run the application from the project root:

```bash
python3 src/main.py
```

The first run will download and cache race data. Subsequent runs will use the cached data.

## Controls

- **Space**: Play/Pause
- **Up/Down Arrow**: Adjust playback speed
- **Left/Right Arrow**: Skip forward/backward

## Data Source

Race data is provided by the [FastF1](https://github.com/theOehrly/Fast-F1) library, which accesses the official F1 timing data.
