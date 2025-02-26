import json

config_path = "config.json"

def get_config_details(key):
    with open(config_path) as f:
        config_data = json.load(f)
        return config_data[key]
