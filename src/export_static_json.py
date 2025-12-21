import os
import json
import re
from typing import Optional

from .data_loader import load_race_data


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return s


def export_race_json(year: int, race_num: int, num_laps: Optional[int] = None, out_dir: str = None) -> str:
    """
    Export race telemetry and lap times to a static JSON file for GitHub Pages.

    Returns the output file path.
    """
    drivers, max_laps, event_info = load_race_data(year, race_num, num_laps or 10)

    serialized_drivers = []
    for driver in drivers:
        serialized_laps = {}
        for lap_num, lap_df in driver["laps"].items():
            laps_list = []
            for _, row in lap_df.iterrows():
                time_val = row["Time"]
                if hasattr(time_val, "total_seconds"):
                    time_ms = int(time_val.total_seconds() * 1000)
                else:
                    # Some telemetry returns integer-like Time already
                    try:
                        time_ms = int(float(time_val))
                    except Exception:
                        time_ms = 0
                laps_list.append({
                    "X": float(row["X"]),
                    "Y": float(row["Y"]),
                    "Time": time_ms
                })
            serialized_laps[str(lap_num)] = laps_list

        serialized_drivers.append({
            "code": driver["code"],
            "abbr": driver["abbr"],
            "team": driver["team"],
            "color": driver["color"],
            "laps": serialized_laps,
            "lap_times": {str(k): float(v) for k, v in driver["lap_times"].items()}
        })

    payload = {
        "drivers": serialized_drivers,
        "max_laps": max_laps,
        "event_info": event_info,
        "source": {
            "year": year,
            "race_num": race_num
        }
    }

    race_name = slugify(event_info.get("name", f"Race_{race_num}"))
    fname = f"{year}_{race_num}_{race_name}.json"
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, fname)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    # Maintain a simple index.json list of datasets
    index_path = os.path.join(out_dir, "index.json")
    try:
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                idx = json.load(f)
            if isinstance(idx, list):
                if fname not in idx:
                    idx.append(fname)
            else:
                idx = [fname]
        else:
            idx = [fname]
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(idx, f)
    except Exception:
        # Non-fatal
        pass

    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export F1 race data to static JSON")
    parser.add_argument("year", type=int, help="Season year, e.g., 2025")
    parser.add_argument("race_num", type=int, help="Round number, e.g., 1")
    parser.add_argument("--laps", type=int, default=None, help="Optional max laps to attempt")
    parser.add_argument("--out", type=str, default=None, help="Output directory (defaults to static/data)")
    args = parser.parse_args()
    path = export_race_json(args.year, args.race_num, args.laps, args.out)
    print(f"Wrote: {path}")
