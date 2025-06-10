import json
import os

class Map:
    ASSETS_DIR = './map/maps/'

    def __init__(self):
        self.maps = [f for f in os.listdir(self.ASSETS_DIR) if os.path.isfile(os.path.join(self.ASSETS_DIR, f))]

    # Get list of maps
    def maplist(self):
        return self.maps

    # Get map resources
    def resources(self, map_name):
        # Открываем файл для чтения
        with open(f'{self.ASSETS_DIR + map_name}.json', 'r', encoding='utf-8') as file:
            return json.load(file) 

