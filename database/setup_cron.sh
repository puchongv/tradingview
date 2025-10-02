#!/bin/bash
# ========================================================================================================
# Setup Cron Job for Strategy Score Refresh
# Description: Install cron job to refresh strategy score every hour
# Author: AI Assistant
# Created: 2025-10-02
# Usage: sudo bash setup_cron.sh
# ========================================================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setting up Strategy Score Cron Job${NC}"
echo -e "${GREEN}========================================${NC}"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REFRESH_SCRIPT="$SCRIPT_DIR/refresh_strategy_score.sh"

# Check if refresh script exists
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo -e "${RED}❌ Error: refresh_strategy_score.sh not found${NC}"
    exit 1
fi

# Make refresh script executable
chmod +x "$REFRESH_SCRIPT"
echo -e "${GREEN}✅ Made refresh script executable${NC}"

# Create cron job entry
CRON_ENTRY="0 * * * * $REFRESH_SCRIPT >> /var/log/trading/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$REFRESH_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry
        crontab -l 2>/dev/null | grep -v "$REFRESH_SCRIPT" | crontab -
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
    echo -e "${GREEN}Schedule: Every hour at minute 0${NC}"
    echo -e "${GREEN}Script: $REFRESH_SCRIPT${NC}"
else
    echo -e "${RED}❌ Error adding cron job${NC}"
    exit 1
fi

# Display current cron jobs
echo -e "\n${GREEN}Current cron jobs:${NC}"
crontab -l

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
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "📊 View will refresh every hour at minute 0"
echo -e "📝 Logs: /var/log/trading/strategy_score_refresh.log"
echo -e "🔍 Check cron logs: tail -f /var/log/trading/cron.log"

