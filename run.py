#!/usr/bin/env python3
"""
F1 Race Visualization Launcher
Simple entry point to start the visualization
"""

import subprocess
import sys

def main():
    print("\n" + "="*60)
    print("F1 RACE VISUALIZATION")
    print("="*60)
    print("\nStarting visualization...")
    print("Controls:")
    print("  [SPACE] - Pause/Resume")
    print("  [R] - Restart race")
    print("  [↑/↓] - Adjust speed")
    print("  [Q] - Quit")
    print("\n" + "="*60 + "\n")
    
    try:
        subprocess.run([sys.executable, "f1_race_viz.py"])
    except KeyboardInterrupt:
        print("\n\nVisualization stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure you have installed dependencies: pip install fastf1 arcade")

if __name__ == "__main__":
    main()
