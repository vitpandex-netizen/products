import os
import json

base_dir = '/Users/vitaliyr/dev/freqtrade-bgt/user_data'

# Update configs
for conf_name in ['config_ema.json', 'config_supertrend.json', 'config_vwap.json']:
    path = os.path.join(base_dir, conf_name)
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        
        data['max_open_trades'] = 10
        if 'freqtrade-ema-cross' in data.get('bot_name', ''):
            data['max_open_trades'] = 10
            
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

print("Patching configs done.")
