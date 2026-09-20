#!/bin/bash
PASS="bgt_secure_ag_2026"
USER="admin"
PORTS=(18091 18092 18093 18094)
NAMES=("EMA_Cross" "SuperTrend" "VWAP_RSI" "ATR_Breakout")
IP="100.84.223.96"

for i in ${!PORTS[@]}; do
  PORT=${PORTS[$i]}
  NAME=${NAMES[$i]}
  
  PROFIT=$(curl -s -u $USER:$PASS http://$IP:$PORT/api/v1/profit)
  
  if [ -n "$PROFIT" ] && [[ "$PROFIT" != *"detail"* ]]; then
    TOTAL_TRADES=$(echo "$PROFIT" | jq -r ".trade_count")
    WIN_COUNT=$(echo "$PROFIT" | jq -r ".winning_trades")
    LOSE_COUNT=$(echo "$PROFIT" | jq -r ".losing_trades")
    ABS_PROFIT=$(echo "$PROFIT" | jq -r ".profit_all_coin")
    REL_PROFIT=$(echo "$PROFIT" | jq -r ".profit_all_percent")
    
    echo "$NAME: Trades: $TOTAL_TRADES ($WIN_COUNT W / $LOSE_COUNT L) | Profit: $ABS_PROFIT USDT ($REL_PROFIT %)"
  else
    echo "$NAME: Failed to fetch profit on port $PORT"
  fi
done
