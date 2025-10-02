#!/bin/bash
# ========================================================================================================
# Deploy Strategy Score System to Production
# Description: Deploy view and cron job to production database server
# Author: AI Assistant
# Created: 2025-10-02
# Usage: bash deploy_to_production.sh
# ========================================================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST="45.77.46.180"
DB_PORT="5432"
DB_NAME="TradingView"
DB_USER="postgres"
DB_PASS="pwd@root99"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Deploy Strategy Score System${NC}"
echo -e "${BLUE}=======================================${NC}"

# Step 1: Test database connection
echo -e "\n${YELLOW}Step 1: Testing database connection...${NC}"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    exit 1
fi

# Step 2: Create view
echo -e "\n${YELLOW}Step 2: Creating materialized view...${NC}"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "database/strategy_score_acceleration_view.sql" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ View created successfully${NC}"
else
    echo -e "${RED}❌ View creation failed${NC}"
    exit 1
fi

# Step 3: Check view
echo -e "\n${YELLOW}Step 3: Verifying view...${NC}"
ROW_COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM strategy_score_acceleration;")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ View verified: $(echo $ROW_COUNT | tr -d ' ') records${NC}"
else
    echo -e "${RED}❌ View verification failed${NC}"
    exit 1
fi

# Step 4: Setup cron (Local machine only)
echo -e "\n${YELLOW}Step 4: Setting up local cron job...${NC}"
read -p "Do you want to setup cron job on this machine? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash database/setup_cron.sh
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Cron job setup complete${NC}"
    else
        echo -e "${RED}❌ Cron job setup failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipped cron setup${NC}"
    echo -e "${YELLOW}To setup later, run: bash database/setup_cron.sh${NC}"
fi

# Step 5: Display TOP 10 scores
echo -e "\n${YELLOW}Step 5: Displaying current TOP 10 scores...${NC}"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
SELECT 
    ROW_NUMBER() OVER (ORDER BY score DESC) as rank,
    strategy_action,
    ROUND(score, 2) as score,
    current_pnl,
    trade_count,
    win_count
FROM strategy_score_acceleration
WHERE current_hour = (SELECT MAX(current_hour) FROM strategy_score_acceleration)
ORDER BY score DESC
LIMIT 10;
EOF

# Summary
echo -e "\n${BLUE}=======================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}📊 View: strategy_score_acceleration${NC}"
echo -e "${GREEN}🔄 Refresh: Every hour at minute 0${NC}"
echo -e "${GREEN}📝 Logs: /var/log/trading/${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Query scores: psql -f database/query_current_scores.sql"
echo -e "2. Check logs: tail -f /var/log/trading/strategy_score_refresh.log"
echo -e "3. Manual refresh: bash database/refresh_strategy_score.sh"

