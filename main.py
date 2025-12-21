import arcade
import warnings
from data_loader import load_race_data
from race_window import RaceWindow

warnings.filterwarnings('ignore')


def main():
    try:
        drivers, laps, event_info = load_race_data(2025, 1, 58)
        if drivers:
            window = RaceWindow(drivers, laps, event_info)
            arcade.run()
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
