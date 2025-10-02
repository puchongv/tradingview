# Backtest Scenarios (2025-09-01 to 2025-09-20)

| Scenario | Interval | Trades | Win% | Final Equity | PnL ($) | ROI % | Max Drawdown | Note |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| trend_quantile | 10m | 98 | 50.0% | 90.00 | -1910.00 | -95.5% | 2330.00 |  |
| reversion_quantile | 30m | 51 | 45.1% | 80.00 | -1920.00 | -96.0% | 1920.00 |  |
| balanced_std | 60m | 79 | 35.4% | 1192.00 | -808.00 | -40.4% | 928.00 | Best |
| dynamic_leader | 10m | 133 | 51.1% | 70.00 | -1930.00 | -96.5% | 2610.00 |  |

## Scenario Details

### trend_quantile

Interval 10m. Rolling 12 trades. Trade when winrate >= global 75th percentile and rolling profit >=0; stake 250 if also >=90th percentile else 100. Cooldown 20m after a loss.

- Trades: 98 (Wins 49, Losses 49)
- Win rate: 50.0%
- Final equity: $90.00 (PnL $-1910.00)
- ROI: -95.5%
- Max drawdown: $2330.00

- Mode breakdown:
  - trend: trades 98, win% 50.0, pnl $-1910.00
- Top contributing strategies:
  - Range FRAMA3-99 | Buy: trades 20, win% 60.0, pnl $520.00
  - MWP-25 | Sell: trades 7, win% 57.1, pnl $110.00
  - MWP-25 | Buy: trades 1, win% 100.0, pnl $80.00
  - Range Filter5 | Buy: trades 1, win% 100.0, pnl $80.00
  - MWP-30 | FlowTrend Bullish + Buy+: trades 2, win% 50.0, pnl $-20.00
- Worst contributing strategies:
  - UT-BOT2-10 | Sell: trades 4, win% 25.0, pnl $-520.00
  - Range FRAMA3 | Buy: trades 10, win% 40.0, pnl $-490.00
  - MWP-27 | Sell: trades 5, win% 20.0, pnl $-350.00
  - MWP-25 | FlowTrend Bullish + Buy+: trades 3, win% 33.3, pnl $-270.00
  - MWP-30 | Buy: trades 3, win% 33.3, pnl $-270.00
- Daily PnL snapshots:
  - 2025-09-01: $-430.00
  - 2025-09-02: $650.00
  - 2025-09-03: $-2130.00

### reversion_quantile

Interval 30m. Rolling 14 trades. Trade contra when winrate <=25th percentile, loss streak >=3, rolling profit below global 25th; stake 100, boost to 250 for worst 10%. Cooldown 25m.

- Trades: 51 (Wins 23, Losses 28)
- Win rate: 45.1%
- Final equity: $80.00 (PnL $-1920.00)
- ROI: -96.0%
- Max drawdown: $1920.00

- Mode breakdown:
  - contrarian: trades 51, win% 45.1, pnl $-1920.00
- Top contributing strategies:
  - Range Filter5 | Sell: trades 7, win% 85.7, pnl $830.00
  - Range FRAMA3-99 | Buy: trades 3, win% 66.7, pnl $60.00
  - MWP-20 | FlowTrend Bearish + Sell: trades 2, win% 50.0, pnl $-50.00
  - MWP-27 | FlowTrend Bearish + Sell+: trades 2, win% 50.0, pnl $-50.00
  - UT-BOT2-10 | Sell: trades 10, win% 50.0, pnl $-70.00
- Worst contributing strategies:
  - MWP-20 | Buy: trades 3, win% 0.0, pnl $-600.00
  - UT-BOT2-10 | Buy: trades 8, win% 37.5, pnl $-560.00
  - MWP-20 | Sell: trades 4, win% 25.0, pnl $-520.00
  - MWP-20 | FlowTrend Bullish + Buy: trades 1, win% 0.0, pnl $-250.00
  - Range FRAMA3 | Sell: trades 2, win% 50.0, pnl $-170.00
- Daily PnL snapshots:
  - 2025-09-01: $-800.00
  - 2025-09-02: $-240.00
  - 2025-09-03: $-310.00
  - 2025-09-04: $940.00
  - 2025-09-05: $-1120.00
  - 2025-09-06: $-140.00
  - 2025-09-07: $-250.00

### balanced_std

Interval 60m. Score = 0.6*winrate + 0.4*momentum vs global mean ±0.5σ. Above -> trend stake 100. Below -> contrarian stake 100. Reduce stake to 10 when drawdown >$600.

- Trades: 79 (Wins 28, Losses 51)
- Win rate: 35.4%
- Final equity: $1192.00 (PnL $-808.00)
- ROI: -40.4%
- Max drawdown: $928.00

- Mode breakdown:
  - trend: trades 44, win% 40.9, pnl $-512.00
  - contrarian: trades 35, win% 28.6, pnl $-296.00
- Top contributing strategies:
  - Range FRAMA3-99 | Buy: trades 8, win% 62.5, pnl $10.00
  - Range FRAMA3 | Buy: trades 1, win% 100.0, pnl $8.00
  - MWP-27 | Sell: trades 1, win% 0.0, pnl $-10.00
  - MWP-25 | Buy: trades 2, win% 0.0, pnl $-20.00
  - MWP-25 | Sell: trades 4, win% 25.0, pnl $-22.00
- Worst contributing strategies:
  - UT-BOT2-10 | Sell: trades 22, win% 27.3, pnl $-328.00
  - Range FRAMA3-99 | Sell: trades 7, win% 28.6, pnl $-214.00
  - MWP-20 | Buy: trades 7, win% 42.9, pnl $-106.00
  - UT-BOT2-10 | Buy: trades 16, win% 37.5, pnl $-88.00
  - MWP-20 | Sell: trades 11, win% 36.4, pnl $-38.00
- Daily PnL snapshots:
  - 2025-09-01: $-660.00
  - 2025-09-02: $-148.00

### dynamic_leader

Interval 10m. Hourly refresh leaderboard from cumulative profit per trade (>=15 trades). Trade only if current strategy in top-6 and rolling winrate >=55%. Top-3 stake 250, others 100. Cooldown 15m.

- Trades: 133 (Wins 68, Losses 65)
- Win rate: 51.1%
- Final equity: $70.00 (PnL $-1930.00)
- ROI: -96.5%
- Max drawdown: $2610.00

- Mode breakdown:
  - trend: trades 133, win% 51.1, pnl $-1930.00
- Top contributing strategies:
  - Range FRAMA3-99 | Buy: trades 33, win% 63.6, pnl $480.00
  - MWP-30 | Sell: trades 11, win% 63.6, pnl $160.00
  - MWP-30 | FlowTrend Bearish + Sell+: trades 3, win% 66.7, pnl $60.00
  - MWP-25 | FlowTrend Bullish + Buy+: trades 5, win% 60.0, pnl $40.00
  - MWP-27 | FlowTrend Bullish + Buy+: trades 4, win% 50.0, pnl $-40.00
- Worst contributing strategies:
  - Range FRAMA3-99 | Sell: trades 5, win% 20.0, pnl $-620.00
  - UT-BOT2-10 | Buy: trades 28, win% 53.6, pnl $-550.00
  - MWP-27 | Sell: trades 8, win% 25.0, pnl $-440.00
  - MWP-25 | Sell: trades 6, win% 33.3, pnl $-240.00
  - MWP-25 | Buy: trades 2, win% 0.0, pnl $-200.00
- Daily PnL snapshots:
  - 2025-09-01: $-240.00
  - 2025-09-02: $-910.00
  - 2025-09-03: $-340.00
  - 2025-09-04: $180.00
  - 2025-09-05: $-620.00
