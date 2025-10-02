#!/bin/bash
# ========================================================================================================
# Setup Cron Job for Strategy Acceleration Score Refresh
# Description: Install cron job to refresh strategy_acceleration_score every hour
# Usage: bash setup_cron_acceleration.sh
# ========================================================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setting up Strategy Acceleration Score Cron Job${NC}"
echo -e "${GREEN}========================================${NC}"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/refresh_acceleration_score.sh"

# Check if refresh script exists
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo -e "${RED}❌ Error: refresh_acceleration_score.sh not found${NC}"
    exit 1
fi

# Make refresh script executable
chmod +x "$REFRESH_SCRIPT"
echo -e "${GREEN}✅ Made refresh script executable${NC}"

# Create cron job entry (ทุก 1 ชั่วโมง ที่นาทีที่ 0)
CRON_ENTRY="0 * * * * $REFRESH_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "refresh_acceleration_score.sh"; then
    echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry
        crontab -l 2>/dev/null | grep -v "refresh_acceleration_score.sh" | crontab -
        echo -e "${GREEN}✅ Removed old cron job${NC}"
    else
        echo -e "${YELLOW}Skipping cron job setup${NC}"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Cron job added successfully${NC}"
    echo -e "${GREEN}📅 Schedule: Every hour at minute 0${NC}"
    echo -e "${GREEN}📂 Script: $REFRESH_SCRIPT${NC}"
else
    echo -e "${RED}❌ Error adding cron job${NC}"
    exit 1
fi

# Display current cron jobs
echo -e "\n${GREEN}Current cron jobs:${NC}"
crontab -l | grep -E "refresh_acceleration_score|#"

# Test run
echo -e "\n${YELLOW}Running test refresh...${NC}"
bash "$REFRESH_SCRIPT"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test refresh successful${NC}"
else
    echo -e "${RED}❌ Test refresh failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "📊 VIEW: strategy_acceleration_score"
echo -e "⏰ Schedule: Every hour (at :00)"
echo -e "📝 Logs: $SCRIPT_DIR/logs/acceleration_score_refresh.log"
echo -e ""
echo -e "🔍 Check logs:"
echo -e "   tail -f $SCRIPT_DIR/logs/acceleration_score_refresh.log"
echo -e ""
echo -e "📋 View current cron jobs:"
echo -e "   crontab -l"
echo -e ""
echo -e "🗑️  Remove cron job:"
echo -e "   crontab -l | grep -v refresh_acceleration_score.sh | crontab -"


