# 🔄 MATERIALIZED VIEW Auto-Refresh - Quick Setup Guide

## เลือกวิธีที่เหมาะกับคุณ

### ⭐ วิธีที่ 1: pg_cron (แนะนำ - ง่ายที่สุด)

```bash
# 1. รัน SQL script นี้
psql -h 45.77.44.36 -p 5432 -U postgres -d tradingpatterns -f agent-script/setup_pg_cron.sql

# 2. เสร็จแล้ว! ตรวจสอบว่า job ทำงานหรือไม่
psql -h 45.77.44.36 -p 5432 -U postgres -d tradingpatterns -c "SELECT * FROM cron.job;"
```

---

### 🔧 วิธีที่ 2: Bash Script + System Cron

```bash
# 1. ทดสอบ script
./agent-script/refresh_materialized_view.sh

# 2. ดู log
tail -f logs/mv_refresh.log

# 3. เพิ่มใน crontab (refresh ทุก 1 ชั่วโมง)
crontab -e

# เพิ่มบรรทัดนี้:
0 * * * * /Users/puchong/tradingview/agent-script/refresh_materialized_view.sh

# 4. ตรวจสอบ crontab
crontab -l
```

---

### 🐍 วิธีที่ 3: Python Script + System Cron

```bash
# 1. ทดสอบ script
python3 agent-script/refresh_mv.py

# 2. ดู log
tail -f logs/mv_refresh.log

# 3. เพิ่มใน crontab (refresh ทุก 1 ชั่วโมง)
crontab -e

# เพิ่มบรรทัดนี้:
0 * * * * cd /Users/puchong/tradingview && python3 agent-script/refresh_mv.py

# 4. ตรวจสอบ crontab
crontab -l
```

---

## 📊 ตรวจสอบสถานะ

```sql
-- เช็คเวลา refresh ล่าสุด
SELECT 
    matviewname,
    last_refresh,
    NOW() - last_refresh AS time_since_refresh
FROM pg_matviews
WHERE matviewname = 'mv_strategy_metrics_hourly';

-- เช็คขนาดและจำนวน rows
SELECT 
    pg_size_pretty(pg_total_relation_size('mv_strategy_metrics_hourly')) AS size,
    COUNT(*) AS rows
FROM mv_strategy_metrics_hourly;
```

---

## ⏰ Cron Schedule ที่ใช้บ่อย

```bash
# ทุก 1 ชั่วโมง
0 * * * *

# ทุก 2 ชั่วโมง
0 */2 * * *

# ทุก 3 ชั่วโมง
0 */3 * * *

# ทุก 30 นาที
*/30 * * * *
```

---

## 🚨 Troubleshooting

### Problem: pg_cron ไม่มี
```sql
-- ต้องติดตั้งก่อน (ต้องเป็น superuser)
CREATE EXTENSION pg_cron;
```

### Problem: Cron job ไม่ทำงาน
```bash
# macOS - เช็คว่า cron service ทำงานหรือไม่
sudo launchctl list | grep cron

# ตรวจสอบ log
tail -f /var/log/system.log | grep cron

# ทดสอบรัน script manual
./agent-script/refresh_materialized_view.sh
```

### Problem: Permission denied
```bash
# ให้สิทธิ์ execute
chmod +x agent-script/refresh_materialized_view.sh
chmod +x agent-script/refresh_mv.py
```

---

## ✅ Checklist

- [ ] เลือกวิธีที่จะใช้
- [ ] ทดสอบ script manual ให้ทำงานก่อน
- [ ] ตั้งค่า cron job
- [ ] ตรวจสอบ log ว่า refresh สำเร็จ
- [ ] เช็ค last_refresh time ใน database

---

**💡 Tips:**
- ใช้ `CONCURRENTLY` เพื่อไม่ lock table
- ตั้งเวลา refresh ในช่วงที่ traffic น้อย
- Monitor log เป็นประจำ
- ถ้า refresh ช้า ให้ลด frequency
