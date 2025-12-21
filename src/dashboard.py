import arcade
from .driver_renderer import DriverRenderer


class Dashboard:
    def __init__(self, drivers, window_height):
        self.drivers = drivers
        self.window_height = window_height
        self.y_positions = {}
        self.row_height = 28
        self._initialize_positions()
    
    def _initialize_positions(self):
        start_y = 640
        for i, d in enumerate(self.drivers):
            y = start_y - i * self.row_height
            self.y_positions[d["code"]] = {"current": y, "target": y}
    
    def update_positions(self, driver_positions):
        for driver in self.drivers:
            code = driver["code"]
            pos = driver_positions[code]["pos"]
            target = (self.window_height - 80) - (pos - 1) * self.row_height
            
            current = self.y_positions[code]["current"]
            self.y_positions[code]["target"] = target
            self.y_positions[code]["current"] = current + (target - current) * 0.15
    
    def draw(self, window_width, driver_positions, frame_counter):
        dashboard_x = 980

        arcade.draw_lrbt_rectangle_filled(dashboard_x - 10, window_width - 10, 20, 
                                         self.window_height - 60, (30, 30, 45, 230))
        arcade.draw_text("LIVE STANDINGS", dashboard_x + 160, self.window_height - 75,
                        arcade.color.WHITE, 14, anchor_x="center", bold=True)
        arcade.draw_line(dashboard_x, self.window_height - 85, window_width - 20, 
                        self.window_height - 85, (80, 80, 100), 2)

        sorted_drivers = sorted(self.drivers, 
                               key=lambda d: driver_positions[d["code"]]["pos"])

        for driver in sorted_drivers:
            code = driver["code"]
            pos_data = driver_positions[code]
            y = self.y_positions[code]["current"]

            if y < 10 or y > self.window_height - 80:
                continue

            color = DriverRenderer.get_color(driver["color"])
            
            frames_since_change = frame_counter - pos_data["changed_frame"]
            if frames_since_change < 60:
                pulse = 1.0 - (frames_since_change / 60.0)
                arcade.draw_lrbt_rectangle_filled(dashboard_x - 5, window_width - 15,
                    y - 12, y + 12, (*color, int(100 * pulse)))

            pos_bg = color if pos_data["pos"] <= 3 else (60, 60, 80)
            arcade.draw_circle_filled(dashboard_x + 18, y, 11, pos_bg)
            arcade.draw_circle_outline(dashboard_x + 18, y, 11, (255, 255, 255, 150), 2)
            arcade.draw_text(str(pos_data["pos"]), dashboard_x + 18, y - 3,
                           arcade.color.WHITE, 10, anchor_x="center", 
                           anchor_y="center", bold=True)

            arcade.draw_lrbt_rectangle_filled(dashboard_x + 35, dashboard_x + 40, 
                                             y - 10, y + 10, color)
            arcade.draw_text(driver["abbr"], dashboard_x + 48, y - 3,
                           arcade.color.WHITE, 11, anchor_x="left", 
                           anchor_y="center", bold=True)
            arcade.draw_text(driver["team"][:15], dashboard_x + 100, y - 3,
                           (180, 180, 200), 8, anchor_x="left", anchor_y="center")
            arcade.draw_text(pos_data["lap_time"], window_width - 30, y - 3,
                           (255, 255, 100), 9, anchor_x="right", 
                           anchor_y="center", bold=True)
