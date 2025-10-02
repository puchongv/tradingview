#!/usr/bin/env python3
import sys
import os

# Change to test directory
os.chdir('/Users/puchong/tradingview/testlog/momentum_test-003')

# Read and execute the simulation script
with open('momentum_simulation_v1_dynamic.py', 'r') as f:
    code = f.read()

# Redirect output to file
sys.stdout = open('simulation_log.txt', 'w')
sys.stderr = sys.stdout

# Execute
exec(code)

# Close file
sys.stdout.close()

# Print confirmation to original stdout
sys.stdout = sys.__stdout__
print("✅ Test 003 completed! Check testlog/momentum_test-003/simulation_log.txt")


