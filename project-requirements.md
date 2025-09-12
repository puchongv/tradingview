# Project Requirements
## Binary Options Trading Pattern Analysis Project

### 📅 Last Update: 2025-01-27
### 🎯 Project Status: Machine Learning Analysis Complete

---

## 🎯 Project Overview
**Binary Options Trading Pattern Analysis Dashboard**

### Mission
สร้าง Metabase Dashboard สำหรับวิเคราะห์ **รูปแบบ (Pattern)** ของ Trading Signals เพื่อให้มองเห็น pattern ที่ส่งผลต่อ win rate

### Vision
- เน้นการแสดง **รูปแบบ (Pattern)** ของข้อมูล
- มองเห็น pattern ที่ส่งผลต่อ win rate
- **ไม่ใช่ Performance Metrics** - เน้นการวิเคราะห์รูปแบบ

---

## 📊 Project Details

### Data Sources
- **Primary File**: `Result Last 120HR.csv` (1,745 records)
- **Additional File**: `Result 2568-09-11 22-54-00.csv` (737 records)
- **Total Records**: 2,482 trading signals
- **Time Range**: 2025-09-03 to 2025-09-11
- **Symbol**: BTCUSDT

### Strategies Available
- MWP-20, MWP-25, MWP-27, MWP-30
- Range FRAMA3, Range FRAMA3-99, Range Filter5
- UT-BOT2-10

### Actions Available
- Buy, Sell
- FlowTrend Bullish + Buy
- FlowTrend Bearish + Sell+

### Timeframes
- 10min, 30min, 60min

## 🎨 Chart Requirements

### Pattern Analysis Charts Only
- **Heatmaps** - สำหรับ time-based patterns
- **Scatter Plots** - สำหรับ correlation patterns
- **Box Plots** - สำหรับ distribution patterns
- **Violin Plots** - สำหรับ density patterns
- **Network Graphs** - สำหรับ relationship patterns

### Avoid Basic Charts
- ❌ Simple bar charts
- ❌ Basic line charts
- ❌ Pie charts
- ❌ Number cards

## 🔍 Pattern Analysis Focus

### 1. Time Pattern Analysis
- **ชั่วโมงไหน** ที่แต่ละ strategy ทำงานได้ดี
- **วันไหน** ที่แต่ละ strategy ทำงานได้ดี
- **ช่วงเวลาไหน** ที่ควรหลีกเลี่ยง

### 2. Price Movement Pattern
- **ราคาแบบไหน** ที่ส่งผลต่อ win rate
- **Price range** ที่เหมาะสมสำหรับแต่ละ strategy
- **Price volatility** ที่ส่งผลต่อผลลัพธ์

### 3. Strategy Behavior Pattern
- **Strategy ไหน** ที่มี pattern ชัดเจน
- **Action ไหน** ที่เหมาะสมกับแต่ละ strategy
- **Combination ไหน** ที่มี pattern ที่ดี

### 4. Win/Loss Streak Pattern
- **แพ้แล้วจะแพ้ต่อไหม** (Losing Streak)
- **ชนะแล้วจะชนะต่อไหม** (Winning Streak)
- **Pattern ของการแพ้/ชนะ**

### 5. Market Condition Pattern
- **ตลาดแบบไหน** ที่ส่งผลต่อ win rate
- **Volatility pattern** ที่ส่งผลต่อผลลัพธ์
- **Trend pattern** ที่ส่งผลต่อ win rate

## 🎯 Objectives

### Primary Objectives
1. **Pattern Recognition** - ระบุรูปแบบที่ชัดเจน
2. **Visual Analysis** - สร้าง visualization ที่แสดง pattern
3. **Pattern Detection** - ระบบตรวจจับ pattern อัตโนมัติ
4. **Pattern Insights** - ข้อมูลเชิงลึกจาก pattern

### Secondary Objectives
1. **Dashboard Creation** - สร้าง Metabase Dashboard
2. **Data Integration** - เชื่อมต่อข้อมูลกับ Metabase
3. **User Interface** - สร้าง UI ที่ใช้งานง่าย
4. **Documentation** - เอกสารการใช้งาน

## 📋 Functional Requirements

### Core Functions
1. **Pattern Detection Engine** - ระบบตรวจจับ pattern
2. **Visualization Generator** - สร้าง charts แสดง pattern
3. **Pattern Analysis Report** - รายงานการวิเคราะห์ pattern
4. **Pattern Alerts** - เตือนเมื่อเจอ pattern ที่น่าสนใจ

### Data Functions
1. **Data Loading** - โหลดข้อมูลจาก CSV
2. **Data Processing** - ประมวลผลข้อมูล
3. **Pattern Calculation** - คำนวณ pattern
4. **Result Export** - ส่งออกผลลัพธ์

### UI Functions
1. **Dashboard Display** - แสดง dashboard
2. **Chart Interaction** - ปฏิสัมพันธ์กับ charts
3. **Filter Controls** - ตัวกรองข้อมูล
4. **Export Options** - ตัวเลือกการส่งออก

## 🚫 Non-Requirements

### Avoid These
- ❌ Performance metrics focus
- ❌ Basic win rate charts
- ❌ Simple bar/line charts
- ❌ Generic dashboard layouts
- ❌ Standard BI reports

### Not Priority
- Real-time data updates
- Advanced analytics
- Machine learning models
- Complex algorithms

## 📊 Success Criteria

### Technical Success
- ✅ Pattern recognition charts created
- ✅ Visual pattern analysis working
- ✅ Metabase dashboard functional
- ✅ Data integration complete

### User Success
- ✅ User can identify patterns easily
- ✅ User can make decisions based on patterns
- ✅ User can understand pattern insights
- ✅ User can use dashboard effectively

## 🔧 Technical Requirements

### Technology Stack
- **Database**: PostgreSQL (via Metabase)
- **Visualization**: Metabase Charts
- **Data Processing**: Python
- **File Format**: CSV, JSON

### Performance Requirements
- **Response Time**: < 5 seconds
- **Data Volume**: 1,747 rows
- **Concurrent Users**: 1-5 users
- **Availability**: 99% uptime

---

## 📁 File Structure

### Core Analysis Files
- **`simple_ml_analysis.py`** - Main ML analysis script → [Link](./simple_ml_analysis.py)
- **`comprehensive_factor_analysis.py`** - Comprehensive analysis → [Link](./comprehensive_factor_analysis.py)
- **`agent_resume_system.py`** - Agent resume system → [Link](./agent_resume_system.py)

### Analysis Results
- **`simple_ml_insights.json`** - ML analysis results → [Link](./simple_ml_insights.json)
- **`significant_patterns.json`** - Significant patterns found → [Link](./significant_patterns.json)
- **`factors_analysis.json`** - Factors analysis results → [Link](./factors_analysis.json)

### Dashboard Files
- **`metabase_dashboard_config.json`** - Dashboard configuration → [Link](./metabase_dashboard_config.json)
- **`metabase_queries.sql`** - SQL queries for Metabase → [Link](./metabase_queries.sql)

### Report Files
- **`ML_ANALYSIS_REPORT.md`** - Main analysis report → [Link](./ML_ANALYSIS_REPORT.md)
- **`COMPREHENSIVE_ANALYSIS_REPORT.md`** - Comprehensive report → [Link](./COMPREHENSIVE_ANALYSIS_REPORT.md)
- **`AGENT_RESUME_GUIDE.md`** - Agent resume guide → [Link](./AGENT_RESUME_GUIDE.md)

### Context Files
- **`agent-conversation-context.md`** - Conversation context → [Link](./agent-conversation-context.md)
- **`project-requirements.md`** - Project requirements (this file)

---

## 🔗 Cross-References

### Related Reports
- **ML Analysis Report** → [ML_ANALYSIS_REPORT.md](./ML_ANALYSIS_REPORT.md)
- **Comprehensive Analysis** → [COMPREHENSIVE_ANALYSIS_REPORT.md](./COMPREHENSIVE_ANALYSIS_REPORT.md)
- **Agent Resume Guide** → [AGENT_RESUME_GUIDE.md](./AGENT_RESUME_GUIDE.md)

### Related Analysis
- **ML Insights** → [simple_ml_insights.json](./simple_ml_insights.json)
- **Significant Patterns** → [significant_patterns.json](./significant_patterns.json)
- **Factors Analysis** → [factors_analysis.json](./factors_analysis.json)

### Related Documentation
- **Conversation Context** → [agent-conversation-context.md](./agent-conversation-context.md)
- **Dashboard Config** → [metabase_dashboard_config.json](./metabase_dashboard_config.json)
- **SQL Queries** → [metabase_queries.sql](./metabase_queries.sql)

---

## 📊 Key Findings Summary

### Significant Patterns Found
1. **Time Patterns**: 02:00 (69.1% win rate), 17:00 (23.9% win rate)
2. **Volatility Patterns**: Level 2 = 0% win rate (100% loss)
3. **Combination Patterns**: MWP-27_FlowTrend Bearish + Sell = 27.3% win rate

### Top Features (Correlation with win_60min)
1. **win_streak** (0.72) - Win streak มีความสัมพันธ์สูงมาก
2. **loss_streak** (-0.65) - Loss streak มีความสัมพันธ์สูงมาก
3. **rolling_win_rate_10** (0.32) - Win rate 10 ครั้งล่าสุด
4. **rolling_win_rate_20** (0.25) - Win rate 20 ครั้งล่าสุด

### Prediction Rules
- **Rule 1**: IF volatility_level = 2 THEN PREDICT LOSE (Confidence: 100.0%)

---

## 📝 Documentation Requirements

### Required Documents
1. **User Manual** - คู่มือการใช้งาน
2. **Technical Documentation** - เอกสารเทคนิค
3. **API Documentation** - เอกสาร API
4. **Troubleshooting Guide** - คู่มือแก้ปัญหา

### Update Frequency
- **Daily**: Context files
- **Weekly**: Progress reports
- **Monthly**: Full documentation review

---

**Remember: Focus on Pattern Analysis, not Performance Metrics!**
