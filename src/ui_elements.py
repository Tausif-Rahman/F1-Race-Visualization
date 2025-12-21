import arcade


class UIElements:
    @staticmethod
    def draw_header(window_width, window_height, current_lap, max_laps, progress, event_info=None):
        if event_info:
            arcade.draw_text(event_info["name"].upper(), window_width // 2, window_height - 20,
                            arcade.color.WHITE, 18, anchor_x="center", bold=True)
            arcade.draw_text(event_info["date"], window_width // 2, window_height - 40,
                            (180, 180, 200), 11, anchor_x="center")
        else:
            arcade.draw_text("F1 RACE REPLAY", window_width // 2, window_height - 25,
                            arcade.color.WHITE, 20, anchor_x="center", bold=True)
        
        lap_text = f"LAP {current_lap}/{max_laps}"
        arcade.draw_text(lap_text, window_width - 180, window_height - 25,
                        arcade.color.YELLOW, 18, bold=True)
        
        bar_x, bar_y, bar_width = window_width - 180, window_height - 50, 150
        arcade.draw_lrbt_rectangle_outline(bar_x, bar_x + bar_width, bar_y - 5, 
                                          bar_y + 5, arcade.color.WHITE, 2)
        if progress > 0:
            arcade.draw_lrbt_rectangle_filled(bar_x, bar_x + bar_width * progress,
                                             bar_y - 4, bar_y + 4, arcade.color.YELLOW)
    
    @staticmethod
    def draw_controls(window_width):
        arcade.draw_text("[SPACE] Pause  [R] Restart  [↑/↓] Speed  [Q] Quit",
                        window_width // 2, 15, (120, 120, 140), 10, anchor_x="center")
