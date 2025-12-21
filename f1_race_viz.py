import arcade
import fastf1 as ff1
import warnings

ff1.Cache.enable_cache("cache")


def load_race_simple(year, race_num, num_laps=10):
    """Load minimal race data quickly"""
    print(f"\nLoading {year} Race {race_num} (first {num_laps} laps)...")

    session = ff1.get_session(year, race_num, "R")
    session.load()

    print(f"✓ {session.event['EventName']}")

    drivers_data = []
    laps = session.laps

    for drv in session.drivers:  # All drivers
        drv_laps = laps.pick_driver(drv)
        if len(drv_laps) == 0:
            continue

        driver_info = session.get_driver(drv)

        # Get telemetry for laps with time data
        lap_data = {}
        lap_times = {}
        for lap_num in range(1, num_laps + 1):
            lap = drv_laps[drv_laps["LapNumber"] == lap_num]
            if len(lap) > 0:
                try:
                    tel = lap.iloc[0].get_pos_data()
                    if tel is not None and len(tel) > 0:
                        lap_data[lap_num] = tel[["X", "Y", "Time"]].copy()
                        # Store lap time for ordering (check for valid time)
                        lap_time = lap.iloc[0]["LapTime"]
                        if lap_time is not None and hasattr(lap_time, "total_seconds"):
                            lap_time_seconds = lap_time.total_seconds()
                            # Check for NaN
                            import math

                            if not math.isnan(lap_time_seconds):
                                lap_times[lap_num] = lap_time_seconds
                except Exception as e:
                    pass

        if len(lap_data) > 0:
            color = driver_info.get("TeamColor", "FFFFFF")
            if not color.startswith("#"):
                color = f"#{color}"

            drivers_data.append(
                {
                    "code": drv,
                    "abbr": driver_info.get("Abbreviation", drv),
                    "full_name": driver_info.get("FullName", drv),
                    "team": driver_info.get("TeamName", "Unknown"),
                    "color": color,
                    "laps": lap_data,
                    "lap_times": lap_times,
                }
            )
            print(
                f"  ✓ {drv} ({driver_info.get('Abbreviation', drv)}) - {len(lap_data)} laps"
            )

    print(f"✓ Loaded {len(drivers_data)} drivers\n")
    return drivers_data, num_laps


class SimpleRaceViz(arcade.Window):
    """Simple race visualization"""

    def __init__(self, drivers_data, max_laps):
        super().__init__(1280, 720, "F1 Race Viz")
        arcade.set_background_color((20, 20, 30))

        self.drivers = drivers_data
        self.max_laps = max_laps
        self.current_lap = 1
        self.progress = 0.0
        self.speed = 0.003
        self.paused = False

        # Driver positions with change tracking and animation
        self.driver_positions = {
            d["code"]: {
                "x": 0,
                "y": 0,
                "pos": i + 1,
                "dist": 0,
                "lap_time": "--:--",
                "changed_frame": 0,
            }
            for i, d in enumerate(self.drivers)
        }
        self.previous_positions = {d["code"]: i + 1 for i, d in enumerate(self.drivers)}
        self.frame_counter = 0

        # Dashboard animation
        self.dashboard_y_positions = {
            d["code"]: 0.0 for d in self.drivers
        }  # Smooth animated Y positions
        self.dashboard_target_y = {
            d["code"]: 0.0 for d in self.drivers
        }  # Target Y positions

        # Initialize dashboard positions
        dashboard_start_y = 640  # self.height - 80
        row_height = 28  # Smaller rows for more drivers
        for i, d in enumerate(self.drivers):
            initial_y = dashboard_start_y - i * row_height
            self.dashboard_y_positions[d["code"]] = initial_y
            self.dashboard_target_y[d["code"]] = initial_y

        # Build track from first driver and store transformation
        if len(self.drivers) > 0 and 1 in self.drivers[0]["laps"]:
            tel = self.drivers[0]["laps"][1]
            xs = tel["X"].values
            ys = tel["Y"].values

            # Calculate track bounds for proper scaling
            x_range = xs.max() - xs.min()
            y_range = ys.max() - ys.min()

            # Scale to fit in window with dashboard (1280x720)
            available_width = 650  # Space for track
            available_height = 550  # Height for track

            scale_x = available_width / x_range if x_range > 0 else 1
            scale_y = available_height / y_range if y_range > 0 else 1

            # Use smaller scale to ensure track fits
            self.track_scale = min(scale_x, scale_y) * 0.55

            # Center track (shifted left to make room for dashboard)
            self.track_cx = xs.mean()
            self.track_cy = ys.mean()
            self.track_offset_x = 500  # Shifted left for dashboard
            self.track_offset_y = 360  # Center vertically

            self.track = [
                (
                    self.track_scale * (x - self.track_cx) + self.track_offset_x,
                    self.track_scale * (y - self.track_cy) + self.track_offset_y,
                )
                for x, y in zip(xs, ys)
            ]
        else:
            self.track = []
            self.track_cx = 0
            self.track_cy = 0
            self.track_scale = 1
            self.track_offset_x = 500
            self.track_offset_y = 360

        print("✓ Visualization ready!")
        print("\nControls:")
        print("  [SPACE] - Pause/Resume")
        print("  [R] - Restart")
        print("  [↑/↓] - Speed up/down")
        print("  [Q] - Quit\n")

        # Calculate initial positions
        self.calculate_positions()
        self.update_dashboard_positions()

    def calculate_positions(self):
        """Calculate driver positions based on cumulative time and progress"""
        positions = []

        for driver in self.drivers:
            if self.current_lap not in driver["laps"]:
                positions.append(
                    (driver["code"], 999999, 0, 0)
                )  # Put at end if no data
                continue

            tel = driver["laps"][self.current_lap]
            idx = int(self.progress * (len(tel) - 1))
            idx = max(0, min(idx, len(tel) - 1))

            # Calculate cumulative time (sum of all previous lap times + current lap progress)
            cumulative_time = 0.0
            for lap_num in range(1, self.current_lap):
                if lap_num in driver["lap_times"]:
                    cumulative_time += driver["lap_times"][lap_num]

            # Add progress through current lap
            if self.current_lap in driver["lap_times"]:
                cumulative_time += driver["lap_times"][self.current_lap] * self.progress
            else:
                # Estimate based on previous lap if current lap time not available
                if (self.current_lap - 1) in driver["lap_times"]:
                    cumulative_time += (
                        driver["lap_times"][self.current_lap - 1] * self.progress
                    )

            row = tel.iloc[idx]
            positions.append((driver["code"], cumulative_time, row["X"], row["Y"]))

        # Sort by cumulative time (ascending = leading, lower time is better)
        positions.sort(key=lambda x: x[1])

        # Update positions and detect overtakes
        for i, (code, time, x, y) in enumerate(positions):
            new_pos = i + 1
            old_pos = self.previous_positions.get(code, new_pos)

            # Get current lap time
            driver = next(d for d in self.drivers if d["code"] == code)
            lap_time_str = "--:--"
            if self.current_lap in driver["lap_times"]:
                lap_time = driver["lap_times"][self.current_lap]
                # Check for valid lap time (not NaN)
                try:
                    if lap_time and not (
                        isinstance(lap_time, float) and lap_time != lap_time
                    ):  # Check for NaN
                        mins = int(lap_time // 60)
                        secs = lap_time % 60
                        lap_time_str = f"{mins}:{secs:05.2f}"
                except (ValueError, TypeError):
                    lap_time_str = "--:--"

            self.driver_positions[code] = {
                "x": x,
                "y": y,
                "pos": new_pos,
                "dist": time,
                "lap_time": lap_time_str,
                "changed_frame": (
                    self.frame_counter
                    if new_pos != old_pos
                    else self.driver_positions[code].get("changed_frame", 0)
                ),
            }

            # Track position changes (no popup notifications)
            if new_pos != old_pos:
                driver_abbr = next(d["abbr"] for d in self.drivers if d["code"] == code)
                if new_pos < old_pos:
                    print(f"⬆️  {driver_abbr}: P{old_pos} → P{new_pos}")
                else:
                    print(f"⬇️  {driver_abbr}: P{old_pos} → P{new_pos}")

            self.previous_positions[code] = new_pos

    def update_dashboard_positions(self):
        """Smoothly animate dashboard positions"""
        dashboard_start_y = self.height - 80
        row_height = 28  # Smaller rows for more drivers

        # Update target positions based on race position
        for driver in self.drivers:
            code = driver["code"]
            pos = self.driver_positions[code]["pos"]
            target_y = dashboard_start_y - (pos - 1) * row_height
            self.dashboard_target_y[code] = target_y

            # Smooth interpolation
            current_y = self.dashboard_y_positions.get(code, target_y)
            diff = target_y - current_y
            self.dashboard_y_positions[code] = current_y + diff * 0.15  # Smooth easing

    def on_update(self, dt):
        """Update animation - called automatically by Arcade"""
        if self.paused or self.current_lap > self.max_laps:
            return

        self.frame_counter += 1
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 0.0
            self.current_lap += 1
            if self.current_lap <= self.max_laps:
                print(f"LAP {self.current_lap}/{self.max_laps}")

        self.calculate_positions()
        self.update_dashboard_positions()

    def on_draw(self):
        self.clear()

        # Draw track
        if len(self.track) > 1:
            arcade.draw_line_strip(self.track, (80, 80, 100), 8)

            # Draw start/finish line
            if len(self.track) > 0:
                x, y = self.track[0]
                arcade.draw_line(x - 20, y, x + 20, y, arcade.color.WHITE, 4)

        # Draw drivers on track
        sorted_drivers = sorted(
            self.drivers, key=lambda d: self.driver_positions[d["code"]]["pos"]
        )

        for driver in sorted_drivers:
            pos_data = self.driver_positions[driver["code"]]

            if pos_data["dist"] < 0:  # No data for this lap
                continue

            # Use same transformation as track
            x = self.track_scale * (pos_data["x"] - self.track_cx) + self.track_offset_x
            y = self.track_scale * (pos_data["y"] - self.track_cy) + self.track_offset_y

            # Draw driver circle
            try:
                color_hex = driver["color"].lstrip("#")
                color = tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))
            except:
                color = (255, 255, 255)

            arcade.draw_circle_filled(x, y, 14, color)
            arcade.draw_circle_outline(x, y, 14, arcade.color.WHITE, 2)

            # Position number on driver
            arcade.draw_text(
                str(pos_data["pos"]),
                x,
                y - 3,
                arcade.color.BLACK,
                12,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )

            # Driver abbreviation above
            arcade.draw_text(
                driver["abbr"],
                x,
                y + 20,
                arcade.color.WHITE,
                11,
                anchor_x="center",
                bold=True,
            )

        # Draw UI elements
        self.draw_header()
        self.draw_dashboard()
        self.draw_controls()

    def draw_dashboard(self):
        """Draw animated positions dashboard"""
        dashboard_x = 980  # Adjusted for 1280px width
        panel_width = 280

        # Draw dashboard background
        arcade.draw_lrbt_rectangle_filled(
            dashboard_x - 10, self.width - 10, 20, self.height - 60, (30, 30, 45, 230)
        )

        # Dashboard title
        arcade.draw_text(
            "LIVE STANDINGS",
            dashboard_x + 160,
            self.height - 75,
            arcade.color.WHITE,
            14,
            anchor_x="center",
            bold=True,
        )

        # Draw separator line
        arcade.draw_line(
            dashboard_x,
            self.height - 85,
            self.width - 20,
            self.height - 85,
            (80, 80, 100),
            2,
        )

        # Sort drivers by current position for proper rendering order
        sorted_drivers = sorted(
            self.drivers, key=lambda d: self.driver_positions[d["code"]]["pos"]
        )

        for driver in sorted_drivers:
            code = driver["code"]
            pos_data = self.driver_positions[code]

            # Get smooth Y position
            y = self.dashboard_y_positions.get(code, self.height - 100)

            # Skip if off screen
            if y < 10 or y > self.height - 80:
                continue

            # Team color
            try:
                color_hex = driver["color"].lstrip("#")
                color = tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))
            except:
                color = (255, 255, 255)

            # Check if position recently changed
            frames_since_change = self.frame_counter - pos_data["changed_frame"]
            highlight = frames_since_change < 60  # Highlight for 1 second (60 frames)

            # Background highlight for position changes
            if highlight:
                pulse = 1.0 - (frames_since_change / 60.0)
                highlight_alpha = int(100 * pulse)
                arcade.draw_lrbt_rectangle_filled(
                    dashboard_x - 5,
                    self.width - 15,
                    y - 12,
                    y + 12,
                    (*color, highlight_alpha),
                )

            # Position number with background (smaller)
            pos_bg_color = color if pos_data["pos"] <= 3 else (60, 60, 80)
            arcade.draw_circle_filled(dashboard_x + 18, y, 11, pos_bg_color)
            arcade.draw_circle_outline(dashboard_x + 18, y, 11, (255, 255, 255, 150), 2)

            arcade.draw_text(
                str(pos_data["pos"]),
                dashboard_x + 18,
                y - 3,
                arcade.color.WHITE,
                10,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )

            # Driver abbreviation with team color bar (smaller)
            arcade.draw_lrbt_rectangle_filled(
                dashboard_x + 35, dashboard_x + 40, y - 10, y + 10, color
            )

            arcade.draw_text(
                driver["abbr"],
                dashboard_x + 48,
                y - 3,
                arcade.color.WHITE,
                11,
                anchor_x="left",
                anchor_y="center",
                bold=True,
            )

            # Team name (smaller)
            arcade.draw_text(
                driver["team"][:15],
                dashboard_x + 100,
                y - 3,
                (180, 180, 200),
                8,
                anchor_x="left",
                anchor_y="center",
            )

            # Lap time
            arcade.draw_text(
                pos_data["lap_time"],
                self.width - 30,
                y - 3,
                (255, 255, 100),
                9,
                anchor_x="right",
                anchor_y="center",
                bold=True,
            )

    def draw_header(self):
        """Draw race information header"""
        # Title
        arcade.draw_text(
            "F1 RACE REPLAY",
            self.width // 2,
            self.height - 25,
            arcade.color.WHITE,
            20,
            anchor_x="center",
            bold=True,
        )

        # Lap counter with progress bar
        lap_text = f"LAP {self.current_lap}/{self.max_laps}"
        arcade.draw_text(
            lap_text,
            self.width - 180,
            self.height - 25,
            arcade.color.YELLOW,
            18,
            bold=True,
        )

        # Progress bar
        bar_x = self.width - 180
        bar_y = self.height - 50
        bar_width = 150
        arcade.draw_lrbt_rectangle_outline(
            bar_x, bar_x + bar_width, bar_y - 5, bar_y + 5, arcade.color.WHITE, 2
        )
        if self.progress > 0:
            filled_width = bar_width * self.progress
            arcade.draw_lrbt_rectangle_filled(
                bar_x, bar_x + filled_width, bar_y - 4, bar_y + 4, arcade.color.YELLOW
            )

    def draw_controls(self):
        arcade.draw_text(
            "[SPACE] Pause  [R] Restart  [↑/↓] Speed  [Q] Quit",
            self.width // 2,
            15,
            (120, 120, 140),
            10,
            anchor_x="center",
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.paused = not self.paused
            print("⏸ PAUSED" if self.paused else "▶ RESUMED")
        elif key == arcade.key.R:
            self.current_lap = 1
            self.progress = 0.0
            self.paused = False
            self.previous_positions = {
                d["code"]: i + 1 for i, d in enumerate(self.drivers)
            }
            print("\n🔄 RESTARTED\n")
        elif key == arcade.key.Q:
            arcade.close_window()
        elif key == arcade.key.UP:
            self.speed = min(0.02, self.speed * 1.5)
            print(f"⏩ Speed: {self.speed:.4f}")
        elif key == arcade.key.DOWN:
            self.speed = max(0.0005, self.speed / 1.5)
            print(f"⏪ Speed: {self.speed:.4f}")


def main():
    print("\n" + "=" * 60)
    print("F1 RACE VISUALIZATION - ENHANCED VERSION")
    print("=" * 60)

    # Load data BEFORE window
    try:
        drivers, laps = load_race_simple(2025, 1, 58)  # 2025 Australia GP
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return

    if len(drivers) == 0:
        print("\n✗ No driver data loaded")
        return

    # Create window AFTER loading
    print("\nCreating window...\n")
    window = SimpleRaceViz(drivers, laps)
    arcade.run()


if __name__ == "__main__":
    main()
