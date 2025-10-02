#!/bin/bash
# Deploy 3-Hour Version of strategy_acceleration_score

echo "========================================"
echo "🚀 Deploying 3-Hour Strategy Acceleration Score VIEW"
echo "========================================"

# Database config
DB_HOST="45.77.46.180"
DB_PORT="5432"
DB_NAME="TradingView"
DB_USER="postgres"

export PGPASSWORD="pwd@root99"

echo ""
echo "📋 Step 1: Backup current VIEW definition..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT pg_get_viewdef('strategy_acceleration_score'::regclass);" > /tmp/view_backup_$(date +%Y%m%d_%H%M%S).sql

echo ""
echo "📋 Step 2: Deploy new 3-hour VIEW..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f strategy_acceleration_score_3h.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deploy successful!"
    echo ""
    echo "📊 Step 3: Verify VIEW..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT 
        strategy, 
        action, 
        score, 
        pnl_1h, 
        pnl_2h, 
        pnl_3h 
    FROM strategy_acceleration_score 
    WHERE score >= 25 
    ORDER BY score DESC 
    LIMIT 5;
    "
    
    echo ""
    echo "✅ Done! VIEW is now using 3-hour lookback (matched with Simulation)"
else
    echo ""
    echo "❌ Deploy failed! Check error messages above."
    exit 1
fi

unset PGPASSWORD

