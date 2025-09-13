# Project Requirements
## Binary Options Trading Pattern Analysis Project

### 📅 Last Update: 2025-09-13
### 🎯 Project Status: Advanced Deep Pattern Analysis Complete - TOP Certainty Patterns Found

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
- **Primary Database**: PostgreSQL TradingView Database
- **Table**: `tradingviewdata`
- **Total Records**: 4,383 trading signals (เพิ่มขึ้น 1,901 records!)
- **Time Range**: 2025-08-28 to 2025-09-13
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
- **`advanced_deep_analysis.py`** - Advanced deep pattern analysis script → [Link](./advanced_deep_analysis.py)
- **`database_connection.py`** - Database connection and exploration → [Link](./database_connection.py)
- **`simple_ml_analysis.py`** - Previous ML analysis script → [Link](./simple_ml_analysis.py)
- **`comprehensive_factor_analysis.py`** - Comprehensive analysis → [Link](./comprehensive_factor_analysis.py)

### Analysis Results  
- **`advanced_deep_analysis_20250913_224955.json`** - Complete advanced analysis results → [Link](./advanced_deep_analysis_20250913_224955.json)
- **`simple_ml_insights.json`** - Previous ML analysis results → [Link](./simple_ml_insights.json)
- **`significant_patterns.json`** - Significant patterns found → [Link](./significant_patterns.json)
- **`factors_analysis.json`** - Factors analysis results → [Link](./factors_analysis.json)

### Dashboard Files
- **`metabase_dashboard_config.json`** - Dashboard configuration → [Link](./metabase_dashboard_config.json)
- **`metabase_queries.sql`** - SQL queries for Metabase → [Link](./metabase_queries.sql)

### Report Files
- **`ADVANCED_DEEP_ANALYSIS_REPORT.md`** - Advanced deep analysis report → [Link](./ADVANCED_DEEP_ANALYSIS_REPORT.md)
- **`TOP_CERTAINTY_PATTERNS_RANKED.md`** - TOP patterns ranked by certainty → [Link](./TOP_CERTAINTY_PATTERNS_RANKED.md)
- **`ML_ANALYSIS_REPORT.md`** - Previous ML analysis report → [Link](./ML_ANALYSIS_REPORT.md)
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

## 🏆 TOP CERTAINTY PATTERNS ที่พบ (เรียงตามความ "ชัว")

### 🥇 #1 ชัวที่สุด - WIN STREAK PATTERN
- **ML Importance**: 40.85% (GradientBoosting accuracy 98.7%)
- **กฎ**: Win streak สูง → โอกาสชนะต่อสูงมาก
- **Sample**: ทั้งหมด 4,383 records
- **ความชัว**: ⭐⭐⭐⭐⭐ (100%)

### 🥈 #2 ชัวมาก - DEATH ZONES (หลีกเลี่ยง 100%)
- **MWP-30 + Hour 22**: 0% win rate (แพ้ 8/8 ครั้ง)
- **Range FRAMA3 + Hour 14 + High volatility**: 0% win rate (แพ้ 18/18)
- **UT-BOT2-10 + Hour 22 + High volatility**: 0% win rate (แพ้ 29/29)

### 🥉 #3 ชัวสูง - GOLDEN TIME HOUR 21
- **Win Rate**: 62.3% (+14.9% จากค่าเฉลี่ย)
- **P-value**: 0.00006 (มีนัยสำคัญสูงมาก!)
- **Sample**: 183 signals

### 🏅 #4 ชัวสูง - GOLDEN COMBOS
- **MWP-30 + Hour 21**: 87.5% win rate (16 signals)
- **MWP-27 + Hour 8**: 84.6% win rate (13 signals)
- **MWP-27 + Hour 10**: 84.2% win rate (19 signals)

### 🏅 #5 ชัวดี - DANGER ZONES
- **Hour 19:00**: 35.7% win rate (p=0.0002, 244 signals)
- **Hour 23:00**: 35.5% win rate (p=0.003, 155 signals)
- **MWP-30 + Hour 19**: 18.2% win rate (33 signals)

### Statistical Significance Results
- **24 significant hour patterns** พบ
- **27 strategy-time interaction patterns** พบ
- **9 consecutive patterns** พบ
- **5 clustering configurations** วิเคราะห์
- **3 ML models tested** (GradientBoosting = best 98.7% accuracy)

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
