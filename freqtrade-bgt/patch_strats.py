import os
import re

base_dir = '/Users/vitaliyr/dev/freqtrade-bgt/user_data/strategies'

strats = ['EMA_Cross.py', 'SuperTrend.py', 'VWAP_RSI.py', 'ATR_Breakout.py']

for s in strats:
    path = os.path.join(base_dir, s)
    if not os.path.exists(path): continue
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Patch stoploss
    content = re.sub(r'stoploss\s*=\s*-0\.\d+', 'stoploss = -0.01', content)
    
    # Patch minimal_roi (naive approach, replacing the dict)
    new_roi = 'minimal_roi = {"0": 0.02, "15": 0.01, "45": 0.001}'
    content = re.sub(r'minimal_roi\s*=\s*\{.*?\}', new_roi, content, flags=re.DOTALL)
    
    # Inject leverage method if not exists
    if 'def leverage' not in content:
        leverage_code = "\n    def leverage(self, step: int, config: dict, pair: str, **kwargs) -> float:\n        return 2.0\n"
        # Insert before populate_indicators
        content = content.replace("    def populate_indicators", leverage_code + "\n    def populate_indicators")
        
    # specific tweaks
    if s == 'EMA_Cross.py':
        content = content.replace('dataframe["adx"] > 20', 'dataframe["adx"] > 15')
        
    with open(path, 'w') as f:
        f.write(content)

print("Patching strategies done.")
