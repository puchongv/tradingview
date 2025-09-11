# Project Requirements

## 🎯 Project Overview
**Trading Signal Pattern Analysis Dashboard**

### Mission
สร้าง Metabase Dashboard สำหรับวิเคราะห์ **รูปแบบ (Pattern)** ของ Trading Signals เพื่อให้มองเห็น pattern ที่ส่งผลต่อ win rate

### Vision
- เน้นการแสดง **รูปแบบ (Pattern)** ของข้อมูล
- มองเห็น pattern ที่ส่งผลต่อ win rate
- **ไม่ใช่ Performance Metrics** - เน้นการวิเคราะห์รูปแบบ

## 📊 Project Details

### Data Source
- **File**: `Result Last 120HR.csv`
- **Rows**: 1,747 trading signals
- **Time Range**: Last 120 hours
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
