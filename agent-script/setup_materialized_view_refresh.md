# MATERIALIZED VIEW Auto-Refresh Setup Guide

## ภาพรวม
MATERIALIZED VIEW `mv_strategy_metrics_hourly` ต้องการ refresh ทุก 1-3 ชั่วโมง เพื่อให้ข้อมูลเป็นปัจจุบัน

---

## 🎯 วิธีที่ 1: ใช้ pg_cron (แนะนำ - ดีที่สุด)

### ข้อดี:
- ทำงานภายใน PostgreSQL
- ไม่ต้องพึ่ง external cron job
- จัดการง่าย query ใน database

### ขั้นตอน:

#### 1. ติดตั้ง pg_cron extension
```sql
-- เช็คว่ามี pg_cron หรือยัง
SELECT * FROM pg_extension WHERE extname = 'pg_cron';

-- ถ้าไม่มี ให้ติดตั้ง (ต้องเป็น superuser)
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

#### 2. ตั้งค่า refresh ทุก 1 ชั่วโมง
```sql
-- Refresh ทุก 1 ชั่วโมง (ที่นาที 0)
SELECT cron.schedule(
    'refresh-strategy-metrics',           -- job name
    '0 * * * *',                          -- cron expression (every hour at minute 0)
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
);
```

#### 3. ตรวจสอบ cron jobs
```sql
-- ดู jobs ทั้งหมด
SELECT * FROM cron.job;

-- ดู job runs ล่าสุด
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;
```

#### 4. แก้ไข/ลบ job (ถ้าต้องการ)
```sql
-- ลบ job
SELECT cron.unschedule('refresh-strategy-metrics');

-- แก้ไขเวลา (ต้องลบแล้วสร้างใหม่)
SELECT cron.unschedule('refresh-strategy-metrics');
SELECT cron.schedule(
    'refresh-strategy-metrics',
    '0 */2 * * *',  -- ทุก 2 ชั่วโมง
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly$$
);
```

---

## 🎯 วิธีที่ 2: ใช้ System Cron Job (Linux/macOS)

### ข้อดี:
- ไม่ต้องติดตั้ง extension
- ใช้ได้กับ PostgreSQL version ไหนก็ได้

### ขั้นตอน:

#### 1. สร้าง script สำหรับ refresh
```bash
#!/bin/bash
# File: /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh

PGHOST="45.77.44.36"
PGPORT="5432"
PGDATABASE="tradingpatterns"
PGUSER="postgres"
PGPASSWORD="Baanpuchong2004"

export PGPASSWORD

psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;"

# Log result
echo "$(date): MATERIALIZED VIEW refreshed" >> /Users/puchong/tradingview/logs/mv_refresh.log
```

#### 2. ให้สิทธิ์ execute
```bash
chmod +x /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh
```

#### 3. เพิ่มใน crontab
```bash
# เปิด crontab editor
crontab -e

# เพิ่มบรรทัดนี้ (refresh ทุก 1 ชั่วโมง)
0 * * * * /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh

# หรือ refresh ทุก 2 ชั่วโมง
0 */2 * * * /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh

# หรือ refresh ทุก 3 ชั่วโมง
0 */3 * * * /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh
```

#### 4. ตรวจสอบ crontab
```bash
# ดู crontab ที่ตั้งไว้
crontab -l

# ดู log
tail -f /Users/puchong/tradingview/logs/mv_refresh.log
```

---

## 🎯 วิธีที่ 3: ใช้ Python Script + Cron

### ข้อดี:
- ควบคุมได้ดีกว่า
- สามารถเพิ่ม error handling, notification
- ส่ง alert ได้ถ้า refresh ล้มเหลว

### ขั้นตอน:

#### 1. สร้าง Python script
```python
# File: /Users/puchong/tradingview/agent-script/refresh_mv.py

import psycopg2
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    filename='/Users/puchong/tradingview/logs/mv_refresh.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def refresh_materialized_view():
    try:
        conn = psycopg2.connect(
            host="45.77.44.36",
            port=5432,
            database="tradingpatterns",
            user="postgres",
            password="Baanpuchong2004"
        )
        
        cursor = conn.cursor()
        
        logging.info("Starting MATERIALIZED VIEW refresh...")
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;")
        conn.commit()
        
        logging.info("MATERIALIZED VIEW refreshed successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error refreshing MATERIALIZED VIEW: {e}")
        return False

if __name__ == "__main__":
    success = refresh_materialized_view()
    exit(0 if success else 1)
```

#### 2. เพิ่มใน crontab
```bash
# Refresh ทุก 1 ชั่วโมง
0 * * * * cd /Users/puchong/tradingview && python3 agent-script/refresh_mv.py
```

---

## 📊 Cron Expression ที่ใช้บ่อย

```
# ทุก 1 ชั่วโมง (ที่นาที 0)
0 * * * *

# ทุก 2 ชั่วโมง
0 */2 * * *

# ทุก 3 ชั่วโมง
0 */3 * * *

# ทุก 30 นาที
*/30 * * * *

# ทุกวันเวลา 00:00
0 0 * * *

# ทุกวันจันทร์-ศุกร์ เวลา 09:00
0 9 * * 1-5
```

---

## 🔍 ตรวจสอบสถานะ MATERIALIZED VIEW

```sql
-- ดูเวลา refresh ล่าสุด
SELECT 
    schemaname,
    matviewname,
    last_refresh
FROM pg_matviews
WHERE matviewname = 'mv_strategy_metrics_hourly';

-- ตรวจสอบขนาดของ MATERIALIZED VIEW
SELECT 
    pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size;

-- นับจำนวน rows
SELECT COUNT(*) FROM mv_strategy_metrics_hourly;
```

---

## ⚠️ หมายเหตุสำคัญ

### 1. CONCURRENTLY vs ไม่ CONCURRENTLY
```sql
-- ✅ CONCURRENTLY (แนะนำ)
-- ไม่ lock table, query ยังใช้งานได้ระหว่าง refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;

-- ❌ ไม่ CONCURRENTLY
-- lock table, query อื่นต้องรอ
REFRESH MATERIALIZED VIEW mv_strategy_metrics_hourly;
```

### 2. ต้องมี UNIQUE INDEX สำหรับ CONCURRENTLY
ถ้ายังไม่มี ต้องสร้างก่อน:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);
```

### 3. Performance
- MATERIALIZED VIEW ใหญ่ = refresh ช้า
- ควรตั้งเวลา refresh ในช่วงที่ traffic น้อย
- ถ้า refresh เกิน 1 ชั่วโมง ควรลด frequency

---

## 🎯 สรุปคำแนะนำ

| วิธี | ความยาก | แนะนำ | เหมาะกับ |
|------|---------|-------|----------|
| pg_cron | ง่าย | ⭐⭐⭐⭐⭐ | Production, ใช้งานง่าย |
| System Cron | ปานกลาง | ⭐⭐⭐⭐ | ไม่มี pg_cron |
| Python + Cron | ยาก | ⭐⭐⭐ | ต้องการ custom logic |

**แนะนำ: ใช้ pg_cron ถ้าทำได้!**
