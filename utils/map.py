import json
import os

ASSETS_DIR = './assets/maps/'

def get_map_list():
    return [
        os.path.splitext(f)[0]
        for f in os.listdir(ASSETS_DIR)
        if os.path.isfile(os.path.join(ASSETS_DIR, f)) and f.endswith('.json')
    ]

def get_map_resources(map_name):
    with open(f'{ASSETS_DIR}{map_name}.json', 'r', encoding='utf-8') as file:
        return json.load(file)