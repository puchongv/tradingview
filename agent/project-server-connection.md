# Project Server Connection Details
## Binary Options Trading Pattern Analysis Project

### 📅 Last Update: 2024-12-19
### 🔒 Connection Status: Ready to Connect

---

## 🗄️ Database Connection

### PostgreSQL Database
- **Host**: 45.77.46.180
- **Port**: 5432
- **Database**: TradingView
- **User**: postgres
- **Password**: pwd@root99
- **Type**: PostgreSQL

### Connection String Format:
```
postgresql://postgres:pwd@root99@45.77.46.180:5432/TradingView
```

### Python Connection Example:
```python
import psycopg2
import pandas as pd

# Database connection parameters
DB_CONFIG = {
    'host': '45.77.46.180',
    'port': 5432,
    'database': 'TradingView',
    'user': 'postgres',
    'password': 'pwd@root99'
}

# Create connection
conn = psycopg2.connect(**DB_CONFIG)
```

---

## 📊 Expected Data Structure

### Trading Signals Table
Based on CSV analysis, expected columns:
- `id` - Signal ID
- `action` - Buy/Sell action
- `symbol` - Trading symbol (BTCUSDT)
- `strategy` - Strategy name (MWP-20, MWP-25, etc.)
- `entry_time` - Signal timestamp
- `entry_price` - Entry price
- `result_10min` - 10-minute result (WIN/LOSE)
- `result_30min` - 30-minute result (WIN/LOSE)
- `result_60min` - 60-minute result (WIN/LOSE)
- `pnl` - Profit/Loss amount

---

## 🛠️ Tools & Access

### Database Management Tools
- **pgAdmin** - PostgreSQL administration
- **DBeaver** - Universal database tool
- **Metabase** - Business intelligence platform

### Security Notes
- Connection requires authentication
- No SSL certificates configured
- Direct connection (no SSH tunnel)

---

## 📋 Connection Checklist

### Before Connecting:
- [ ] Verify network access to 45.77.46.180:5432
- [ ] Confirm database credentials
- [ ] Install required Python packages (psycopg2)
- [ ] Test connection

### After Connecting:
- [ ] Explore database schema
- [ ] Identify tables and structure
- [ ] Verify data matches CSV files
- [ ] Set up Metabase connection

---

## 🚨 Security Considerations

- **Password**: Stored in plain text (consider environment variables)
- **Network**: Direct connection (no VPN/tunnel required)
- **Access**: Full postgres user privileges
- **Backup**: Ensure regular backups are in place

---

**Status**: Ready for database connection and data exploration
