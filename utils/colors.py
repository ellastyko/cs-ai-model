def parse_to_rgba(color):
        """Преобразует цвет в формат RGBA"""
        if isinstance(color, str):
            color_map = {
                'red': (1.0, 0.0, 0.0, 1.0),
                'green': (0.0, 1.0, 0.0, 1.0),
                'blue': (0.0, 0.0, 1.0, 1.0),
                'yellow': (1.0, 1.0, 0.0, 1.0)
            }
            return color_map.get(color.lower(), (1.0, 1.0, 1.0, 1.0))
        elif len(color) == 3:
            return (color[0], color[1], color[2], 1.0)
        return color