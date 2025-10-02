# Strategy Score System - Acceleration Formula

## 📊 Overview

Real-time strategy scoring system using **Acceleration Formula** (5×M₁ + 3×Acceleration).

The system automatically refreshes scores every hour via PostgreSQL materialized view and cron job.

---

## 🗂️ Files

```
database/
├── strategy_score_acceleration_view.sql  # Main view definition
├── refresh_strategy_score.sh             # Refresh script
├── setup_cron.sh                         # Cron setup script
├── query_current_scores.sql              # Query examples
└── README.md                             # This file
```

---

## 🚀 Installation

### 1. Create View (One-time setup)

```bash
# Connect to database
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView

# Execute view creation
\i database/strategy_score_acceleration_view.sql
```

### 2. Setup Cron Job (One-time setup)

**On Database Server (45.77.46.180):**

```bash
# Copy scripts to server
scp database/*.sh root@45.77.46.180:/root/trading/

# SSH to server
ssh root@45.77.46.180

# Run setup
cd /root/trading/
chmod +x setup_cron.sh
sudo bash setup_cron.sh
```

---

## 📋 Cron Schedule

**Schedule:** Every hour at minute 0 (00:00, 01:00, 02:00, ...)

```cron
0 * * * * /path/to/refresh_strategy_score.sh >> /var/log/trading/cron.log 2>&1
```

---

## 🔍 Usage

### Query Current Scores

```bash
# Option 1: Using psql
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView -f database/query_current_scores.sql

# Option 2: Direct query
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView -c "
SELECT * FROM strategy_score_acceleration 
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
ORDER BY score DESC LIMIT 10;
"
```

### Manual Refresh

```bash
# On server
/root/trading/refresh_strategy_score.sh

# Or via psql
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView -c "
REFRESH MATERIALIZED VIEW strategy_score_acceleration;
"
```

---

## 📊 View Schema

| Column | Type | Description |
|--------|------|-------------|
| `strategy_action` | TEXT | Strategy + Action (e.g., "MWP10-1m \| Buy") |
| `strategy` | TEXT | Strategy name only |
| `action` | TEXT | Action (Buy/Sell) |
| `current_hour` | TIMESTAMP | Hour timestamp |
| `current_pnl` | NUMERIC | Current cumulative PNL (P1) |
| `momentum` | NUMERIC | M₁ = P1 - P2 |
| `acceleration` | NUMERIC | M₁ - M₂ |
| `recent_raw` | NUMERIC | Raw score (5×M₁ + 3×Acceleration) |
| `recent_kpi` | NUMERIC | Normalization KPI (mean + stddev) |
| `score` | NUMERIC | Normalized score (0-30) |
| `trade_count` | INTEGER | Number of trades in hour |
| `win_count` | INTEGER | Number of winning trades |
| `win_rate` | NUMERIC | Win percentage |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

## 🔧 Monitoring

### Check Logs

```bash
# Refresh logs
tail -f /var/log/trading/strategy_score_refresh.log

# Cron logs
tail -f /var/log/trading/cron.log

# System cron logs
grep CRON /var/log/syslog | tail -20
```

### Check Cron Status

```bash
# List all cron jobs
crontab -l

# Check if cron service is running
systemctl status cron
```

### Verify View

```sql
-- Check last update
SELECT MAX(updated_at) as last_update FROM strategy_score_acceleration;

-- Check data freshness
SELECT 
    MAX(current_hour) as latest_hour,
    COUNT(*) as record_count,
    MAX(updated_at) as last_refresh
FROM strategy_score_acceleration;
```

---

## 🐛 Troubleshooting

### View Not Refreshing

```bash
# Check cron is running
systemctl status cron

# Check cron logs
tail -f /var/log/trading/cron.log

# Manual test
bash /root/trading/refresh_strategy_score.sh
```

### Permission Issues

```bash
# Make scripts executable
chmod +x /root/trading/*.sh

# Check log directory permissions
mkdir -p /var/log/trading
chmod 755 /var/log/trading
```

### Database Connection Issues

```bash
# Test connection
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView -c "SELECT 1;"

# Check if view exists
psql -h 45.77.46.180 -p 5432 -U postgres -d TradingView -c "
SELECT * FROM pg_matviews WHERE matviewname = 'strategy_score_acceleration';
"
```

---

## 📈 Performance

- **View Size:** ~500-1000 rows (24 hours × 20-40 strategies)
- **Refresh Time:** ~2-5 seconds
- **Query Time:** <100ms (with indexes)
- **Storage:** ~100KB per 24 hours

---

## 🔄 Maintenance

### Clean Old Data

View automatically keeps only last 30 days of source data and 24 hours of scores.

To adjust retention:

```sql
-- Edit view definition
-- Change: WHERE entry_time >= NOW() - INTERVAL '30 days'
-- To: WHERE entry_time >= NOW() - INTERVAL '60 days'
```

### Rebuild View

```sql
DROP MATERIALIZED VIEW IF EXISTS strategy_score_acceleration CASCADE;
\i database/strategy_score_acceleration_view.sql
```

---

## 📞 Support

For issues or questions, check:
1. Logs: `/var/log/trading/`
2. Cron status: `crontab -l`
3. Database connection: Test with psql

---

**Last Updated:** 2025-10-02
**Version:** 1.0

