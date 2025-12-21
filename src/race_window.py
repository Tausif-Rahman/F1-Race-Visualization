import arcade
from track_renderer import TrackRenderer
from driver_renderer import DriverRenderer
from position_calculator import PositionCalculator
from dashboard import Dashboard
from ui_elements import UIElements


class RaceWindow(arcade.Window):
    def __init__(self, drivers_data, max_laps, event_info=None):
        super().__init__(1280, 720, "F1 Race Visualization")
        arcade.set_background_color((20, 20, 30))

        self.drivers = drivers_data
        self.max_laps = max_laps
        self.event_info = event_info
        self.current_lap = 1
        self.progress = 0.0
        self.speed = 0.003
        self.paused = False
        self.frame_counter = 0

        self.driver_positions = {d["code"]: {"x": 0, "y": 0, "pos": i + 1, "dist": 0, 
                                              "lap_time": "--:--", "changed_frame": 0}
                                 for i, d in enumerate(self.drivers)}
        self.previous_positions = {d["code"]: i + 1 for i, d in enumerate(self.drivers)}
        
        self.track_renderer = TrackRenderer(drivers_data)
        self.dashboard = Dashboard(drivers_data, self.height)
        
        self._update_positions()
        self.dashboard.update_positions(self.driver_positions)

    def _update_positions(self):
        positions = PositionCalculator.calculate_race_positions(
            self.drivers, self.current_lap, self.progress
        )

        for i, (code, time, x, y) in enumerate(positions):
            new_pos = i + 1
            old_pos = self.previous_positions[code]
            
            lap_time_str = PositionCalculator.format_lap_time(
                self.drivers, code, self.current_lap
            )
            
            self.driver_positions[code] = {
                "x": x, "y": y, "pos": new_pos, "dist": time, "lap_time": lap_time_str,
                "changed_frame": self.frame_counter if new_pos != old_pos 
                                else self.driver_positions[code]["changed_frame"]
            }
            self.previous_positions[code] = new_pos

    def on_update(self, dt):
        if self.paused or self.current_lap > self.max_laps:
            return

        self.frame_counter += 1
        self.progress += self.speed
        
        if self.progress >= 1.0:
            self.progress = 0.0
            self.current_lap += 1

        self._update_positions()
        self.dashboard.update_positions(self.driver_positions)

    def on_draw(self):
        self.clear()
        self.track_renderer.draw_track()
        self._draw_drivers()
        UIElements.draw_header(self.width, self.height, self.current_lap, 
                              self.max_laps, self.progress, self.event_info)
        self.dashboard.draw(self.width, self.driver_positions, self.frame_counter)
        UIElements.draw_controls(self.width)

    def _draw_drivers(self):
        sorted_drivers = sorted(self.drivers, 
                               key=lambda d: self.driver_positions[d["code"]]["pos"])

        for driver in sorted_drivers:
            pos_data = self.driver_positions[driver["code"]]
            if pos_data["dist"] < 0:
                continue

            x, y = self.track_renderer.transform_position(pos_data["x"], pos_data["y"])
            DriverRenderer.draw_driver(x, y, pos_data["pos"], driver["abbr"], driver["color"])

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.paused = not self.paused
        elif key == arcade.key.R:
            self.current_lap = 1
            self.progress = 0.0
            self.paused = False
            self.previous_positions = {d["code"]: i + 1 for i, d in enumerate(self.drivers)}
        elif key == arcade.key.Q:
            arcade.close_window()
        elif key == arcade.key.UP:
            self.speed = min(0.02, self.speed * 1.5)
        elif key == arcade.key.DOWN:
            self.speed = max(0.0005, self.speed / 1.5)
