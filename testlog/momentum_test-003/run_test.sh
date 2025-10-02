#!/bin/bash
cd /Users/puchong/tradingview/testlog/momentum_test-003
python3 momentum_simulation_v1_dynamic.py > simulation_log.txt 2>&1
echo "✅ Test 003 completed!"
tail -30 simulation_log.txt

