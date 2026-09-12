import sys
sys.path.insert(0, '/Volumes/External/dev/uz-market-bot')

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'r') as f:
    code = f.read()

# Fix the regex to use raw string properly
code = code.replace(
    "clean_query = re.sub(r'\\\\d+[\\\\s]*(?:\\\\$|сум|usd|у\\\\.е)', '', clean_query, flags=re.IGNORECASE)",
    "clean_query = re.sub(r'\\d+[\\s]*(?:\\$|\u0441\u0443\u043c|usd|\u0443\\.\u0435)', '', clean_query, flags=re.IGNORECASE)"
)

with open('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', 'w') as f:
    f.write(code)

import py_compile
py_compile.compile('/Volumes/External/dev/uz-market-bot/src/bot/market_bot.py', doraise=True)
print('✅ OK')
