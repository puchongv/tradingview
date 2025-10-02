#!/bin/bash
# ============================================================================
# VPS System Cron Setup Script
# ============================================================================
# Purpose: Setup System Cron for MATERIALIZED VIEW auto-refresh
# VPS: 45.77.46.180
# ============================================================================

set -e

VPS_HOST="45.77.46.180"
VPS_USER="root"
VPS_PASS="3J_rFj4CKhpL2@FD"

echo "============================================================================"
echo "🚀 VPS System Cron Setup"
echo "============================================================================"
echo ""

echo "📋 Step 1: Creating directories on VPS..."
echo "   Command: mkdir -p /opt/tradingview/scripts /opt/tradingview/logs"
echo ""

echo "📋 Step 2: Upload refresh script to VPS..."
echo "   File: vps_refresh_mv.sh → /opt/tradingview/scripts/"
echo ""

echo "📋 Step 3: Create unique index in database..."
echo "   Index: idx_mv_strategy_metrics_unique"
echo ""

echo "📋 Step 4: Setup crontab (refresh every 1 hour)..."
echo "   Schedule: 0 * * * * (every hour at minute 0)"
echo ""

echo "📋 Step 5: Perform initial refresh..."
echo ""

echo "============================================================================"
echo "⚠️  Manual Steps Required:"
echo "============================================================================"
echo ""
echo "คุณต้อง SSH เข้า VPS และรันคำสั่งต่อไปนี้:"
echo ""
echo "# 1. SSH เข้า VPS"
echo "ssh root@45.77.46.180"
echo "# Password: 3J_rFj4CKhpL2@FD"
echo ""
echo "# 2. สร้าง directory"
echo "mkdir -p /opt/tradingview/scripts /opt/tradingview/logs"
echo ""
echo "# 3. สร้างไฟล์ refresh script"
echo "cat > /opt/tradingview/scripts/refresh_mv.sh << 'EOFSCRIPT'"
echo "#!/bin/bash"
echo "PGHOST=\"45.77.46.180\""
echo "PGPORT=\"5432\""
echo "PGDATABASE=\"TradingView\""
echo "PGUSER=\"postgres\""
echo "PGPASSWORD=\"pwd@root99\""
echo "LOG_FILE=\"/opt/tradingview/logs/mv_refresh.log\""
echo "export PGPASSWORD"
echo "echo \"========================================\" >> \"\$LOG_FILE\""
echo "echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Starting refresh...\" >> \"\$LOG_FILE\""
echo "if psql -h \"\$PGHOST\" -p \"\$PGPORT\" -U \"\$PGUSER\" -d \"\$PGDATABASE\" -c \"REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;\" >> \"\$LOG_FILE\" 2>&1; then"
echo "    echo \"\$(date '+%Y-%m-%d %H:%M:%S') - ✅ Success!\" >> \"\$LOG_FILE\""
echo "else"
echo "    echo \"\$(date '+%Y-%m-%d %H:%M:%S') - ❌ Failed!\" >> \"\$LOG_FILE\""
echo "fi"
echo "EOFSCRIPT"
echo ""
echo "# 4. ให้สิทธิ์ execute"
echo "chmod +x /opt/tradingview/scripts/refresh_mv.sh"
echo ""
echo "# 5. สร้าง unique index (ถ้ายังไม่มี)"
echo "PGPASSWORD='pwd@root99' psql -h 45.77.46.180 -U postgres -d TradingView -c \"CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);\""
echo ""
echo "# 6. ทดสอบ script"
echo "/opt/tradingview/scripts/refresh_mv.sh"
echo ""
echo "# 7. ดู log"
echo "tail -f /opt/tradingview/logs/mv_refresh.log"
echo ""
echo "# 8. เพิ่มใน crontab"
echo "crontab -e"
echo "# เพิ่มบรรทัดนี้:"
echo "0 * * * * /opt/tradingview/scripts/refresh_mv.sh"
echo ""
echo "# 9. ตรวจสอบ crontab"
echo "crontab -l"
echo ""
echo "============================================================================"
echo ""

# Create a comprehensive setup file
cat > /tmp/vps_setup_commands.txt << 'EOF'
# ============================================================================
# VPS Setup Commands - Copy & Paste ทีละ section
# ============================================================================

# SECTION 1: SSH เข้า VPS
ssh root@45.77.46.180
# Password: 3J_rFj4CKhpL2@FD

# SECTION 2: สร้าง directories
mkdir -p /opt/tradingview/scripts /opt/tradingview/logs

# SECTION 3: สร้าง refresh script
cat > /opt/tradingview/scripts/refresh_mv.sh << 'EOFSCRIPT'
#!/bin/bash
PGHOST="45.77.46.180"
PGPORT="5432"
PGDATABASE="TradingView"
PGUSER="postgres"
PGPASSWORD="pwd@root99"
LOG_FILE="/opt/tradingview/logs/mv_refresh.log"
export PGPASSWORD
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting refresh..." >> "$LOG_FILE"
if psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_strategy_metrics_hourly;" >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Success!" >> "$LOG_FILE"
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -tAc "SELECT '$(date '+%Y-%m-%d %H:%M:%S') - Stats: ' || COUNT(*) || ' rows' FROM mv_strategy_metrics_hourly;" >> "$LOG_FILE" 2>&1
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ Failed!" >> "$LOG_FILE"
fi
EOFSCRIPT

# SECTION 4: ให้สิทธิ์
chmod +x /opt/tradingview/scripts/refresh_mv.sh

# SECTION 5: สร้าง unique index
PGPASSWORD='pwd@root99' psql -h 45.77.46.180 -U postgres -d TradingView << 'EOFSQL'
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_strategy_metrics_unique 
ON mv_strategy_metrics_hourly (strategy, action, symbol, window_hours);

SELECT 'Index created' AS status;
EOFSQL

# SECTION 6: ทดสอบ refresh (ครั้งแรก)
/opt/tradingview/scripts/refresh_mv.sh

# SECTION 7: ดู log
tail -20 /opt/tradingview/logs/mv_refresh.log

# SECTION 8: ตั้งค่า crontab
crontab -e
# กด 'i' เพื่อ insert mode
# เพิ่มบรรทัดนี้:
0 * * * * /opt/tradingview/scripts/refresh_mv.sh
# กด Esc แล้วพิมพ์ :wq เพื่อ save

# SECTION 9: ตรวจสอบ crontab
crontab -l

# SECTION 10: ตรวจสอบว่า cron service ทำงาน
service cron status

# เสร็จแล้ว! Exit จาก VPS
exit

# ============================================================================
# หลังจาก setup เสร็จ - ตรวจสอบจาก Mac
# ============================================================================

# เช็ค last refresh time
PGPASSWORD='pwd@root99' psql -h 45.77.46.180 -U postgres -d TradingView -c "SELECT matviewname, last_refresh, NOW() - last_refresh AS time_since FROM pg_matviews WHERE matviewname = 'mv_strategy_metrics_hourly';"

# ดู log จากระยะไกล
ssh root@45.77.46.180 "tail -20 /opt/tradingview/logs/mv_refresh.log"

EOF

echo "✅ Created setup instructions file: /tmp/vps_setup_commands.txt"
echo ""
echo "📖 ดูคำสั่งทั้งหมด:"
echo "   cat /tmp/vps_setup_commands.txt"
echo ""
echo "📋 หรือ copy commands จาก terminal output ด้านบน"
echo ""
