import arcade


class DriverRenderer:
    @staticmethod
    def get_color(color_hex):
        try:
            color_hex = color_hex.lstrip("#")
            return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        except:
            return (255, 255, 255)
    
    @staticmethod
    def draw_driver(x, y, position, abbreviation, color_hex):
        color = DriverRenderer.get_color(color_hex)
        arcade.draw_circle_filled(x, y, 14, color)
        arcade.draw_circle_outline(x, y, 14, arcade.color.WHITE, 2)
        
        arcade.draw_text(str(position), x, y - 3, arcade.color.BLACK, 12,
                       anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(abbreviation, x, y + 20, arcade.color.WHITE, 11,
                       anchor_x="center", bold=True)
