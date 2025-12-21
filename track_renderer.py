import arcade


class TrackRenderer:
    def __init__(self, drivers_data):
        self.track = []
        self.track_cx = 0
        self.track_cy = 0
        self.track_scale = 1
        self.track_offset_x = 500
        self.track_offset_y = 360
        
        if drivers_data and 1 in drivers_data[0]["laps"]:
            self._initialize_track(drivers_data[0]["laps"][1])
    
    def _initialize_track(self, telemetry):
        xs, ys = telemetry["X"].values, telemetry["Y"].values
        
        x_range, y_range = xs.max() - xs.min(), ys.max() - ys.min()
        scale = min(650 / x_range if x_range > 0 else 1, 
                   550 / y_range if y_range > 0 else 1) * 0.55
        
        self.track_cx, self.track_cy = xs.mean(), ys.mean()
        self.track_scale = scale
        
        self.track = [(scale * (x - self.track_cx) + 500,
                      scale * (y - self.track_cy) + 360)
                     for x, y in zip(xs, ys)]
    
    def draw_track(self):
        if len(self.track) > 1:
            arcade.draw_line_strip(self.track, (80, 80, 100), 8)
            x, y = self.track[0]
            arcade.draw_line(x - 20, y, x + 20, y, arcade.color.WHITE, 4)
    
    def transform_position(self, x, y):
        screen_x = self.track_scale * (x - self.track_cx) + self.track_offset_x
        screen_y = self.track_scale * (y - self.track_cy) + self.track_offset_y
        return screen_x, screen_y
