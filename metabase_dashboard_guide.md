# Metabase Dashboard Guide
## สร้าง Dashboard แสดง Performance ของทุกสัญญาณ

---

## **1. Dashboard Layout ที่แนะนำ**

### **Dashboard 1: Strategy Performance Overview**
```
┌─────────────────┬─────────────────┬─────────────────┐
│   Strategy      │   Win Rate      │   Total Trades  │
│   Performance   │   (Bar Chart)   │   (Number)      │
│   (Table)       │   10min/30min   │   Today         │
├─────────────────┼─────────────────┼─────────────────┤
│   Time Pattern  │   Risk          │   Recent        │
│   (Line Chart)  │   Assessment    │   Performance   │
│   Win Rate      │   (Table)       │   (Line Chart)  │
│   by Hour       │                 │   PnL Trend     │
└─────────────────┴─────────────────┴─────────────────┘
```

### **Dashboard 2: Signal Analysis**
```
┌─────────────────┬─────────────────┬─────────────────┐
│   Strategy +    │   Action +      │   Best          │
│   Time Heatmap  │   Time Heatmap  │   Combinations  │
│   (Heatmap)     │   (Heatmap)     │   (Table)       │
├─────────────────┼─────────────────┼─────────────────┤
│   Pre-Loss      │   Price         │   Risk          │
│   Streak        │   Movement      │   Assessment    │
│   Analysis      │   Analysis      │   (Table)       │
│   (Bar Chart)   │   (Bar Chart)   │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

---

## **2. ขั้นตอนการสร้าง Dashboard**

### **Step 1: สร้าง Questions (Queries)**

**1.1 Strategy Performance Overview:**
- ใช้ Query #1 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Table**
- Columns: strategy, action, timeframe, total_trades, win_rate_10min, win_rate_30min, win_rate_60min

**1.2 Win Rate by Strategy:**
- ใช้ Query #1 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Bar Chart**
- X-axis: strategy
- Y-axis: win_rate_10min

**1.3 Time Pattern Analysis:**
- ใช้ Query #2 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Line Chart**
- X-axis: hour
- Y-axis: win_rate_10min

**1.4 Strategy + Time Heatmap:**
- ใช้ Query #3 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Heatmap**
- X-axis: hour
- Y-axis: strategy
- Color: win_rate_10min

**1.5 Action + Time Heatmap:**
- ใช้ Query #4 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Heatmap**
- X-axis: hour
- Y-axis: action
- Color: win_rate_10min

**1.6 Pre-Loss Streak Analysis:**
- ใช้ Query #5 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Bar Chart**
- X-axis: strategy
- Y-axis: win_rate
- Group by: is_after_loss

**1.7 Price Movement Analysis:**
- ใช้ Query #7 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Bar Chart**
- X-axis: price_movement
- Y-axis: win_rate

**1.8 Risk Assessment:**
- ใช้ Query #8 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Table**
- Columns: strategy, action, win_rate, max_consecutive_losses, risk_level

**1.9 Best Combinations:**
- ใช้ Query #9 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Table**
- Columns: strategy, action, hour, win_rate_10min, win_rate_30min, win_rate_60min

**1.10 Recent Performance:**
- ใช้ Query #10 จากไฟล์ `metabase_queries.sql`
- Chart Type: **Line Chart**
- X-axis: strategy
- Y-axis: win_rate_10min

### **Step 2: สร้าง Dashboard**

**2.1 สร้าง Dashboard ใหม่:**
- ไปที่ Metabase → Dashboards → New Dashboard
- ตั้งชื่อ: "Trading Signal Analysis"

**2.2 เพิ่ม Charts:**
- ลาก Questions ที่สร้างไว้มาใส่ใน Dashboard
- จัดเรียงตาม Layout ที่แนะนำ

**2.3 ตั้งค่า Filters:**
- เพิ่ม Dashboard Filter
- ตั้งค่า Filter สำหรับ:
  - Strategy (Dropdown)
  - Action (Dropdown)
  - Time Range (Date Range)
  - Timeframe (Dropdown)

### **Step 3: ตั้งค่า Filters**

**3.1 Strategy Filter:**
- Type: Dropdown
- Source: Query #1
- Column: strategy

**3.2 Action Filter:**
- Type: Dropdown
- Source: Query #1
- Column: action

**3.3 Time Range Filter:**
- Type: Date Range
- Source: tradingviewdata
- Column: entry_time

**3.4 Timeframe Filter:**
- Type: Dropdown
- Source: Query #1
- Column: tf

---

## **3. การใช้งาน Dashboard**

### **3.1 ดู Performance ของทุกสัญญาณ:**
- ดู Table แรก (Strategy Performance Overview)
- ดู Bar Chart (Win Rate by Strategy)
- ดู Line Chart (Time Pattern Analysis)

### **3.2 หาสัญญาณที่ดี:**
- ใช้ Heatmap (Strategy + Time, Action + Time)
- ดู Best Combinations Table
- ดู Recent Performance

### **3.3 สังเกตปัจจัยที่ส่งผลต่อ Win Rate:**
- ดู Pre-Loss Streak Analysis
- ดู Price Movement Analysis
- ดู Risk Assessment

### **3.4 ใช้ Filters:**
- เลือก Strategy ที่ต้องการ
- เลือก Action ที่ต้องการ
- เลือกช่วงเวลา
- เลือก Timeframe

---

## **4. Tips การใช้งาน**

### **4.1 หาสัญญาณที่ดี:**
- ดู Heatmap สีเขียว (Win Rate สูง)
- ดู Best Combinations Table
- ดู Recent Performance

### **4.2 สังเกต Pattern:**
- ดู Time Pattern (ชั่วโมงไหนดี)
- ดู Pre-Loss Streak (แพ้แล้วจะแพ้ต่อไหม)
- ดู Price Movement (ราคาแบบไหนชนะบ่อย)

### **4.3 หลีกเลี่ยงความเสี่ยง:**
- ดู Risk Assessment (High Risk = หลีกเลี่ยง)
- ดู Pre-Loss Streak (แพ้แล้ว = หยุด)
- ดู Time Pattern (ชั่วโมงแย่ = หลีกเลี่ยง)

---

## **5. การอัพเดท Dashboard**

### **5.1 Real-time Updates:**
- Dashboard จะอัพเดทอัตโนมัติเมื่อมีข้อมูลใหม่
- ใช้ Recent Performance เพื่อดูข้อมูลล่าสุด

### **5.2 การปรับแต่ง:**
- เพิ่ม/ลด Charts ตามต้องการ
- เปลี่ยน Chart Type ตามความเหมาะสม
- เพิ่ม Filters ตามความต้องการ

---

## **6. ไฟล์ที่ต้องใช้**

1. **metabase_queries.sql** - SQL Queries สำหรับสร้าง Questions
2. **metabase_dashboard_guide.md** - คู่มือการสร้าง Dashboard (ไฟล์นี้)

---

## **7. ขั้นตอนการสร้าง (สรุป)**

1. **สร้าง Questions** - ใช้ SQL Queries จากไฟล์ `metabase_queries.sql`
2. **สร้าง Dashboard** - สร้าง Dashboard ใหม่ใน Metabase
3. **เพิ่ม Charts** - ลาก Questions มาใส่ใน Dashboard
4. **ตั้งค่า Filters** - ตั้งค่า Dashboard Filters
5. **ทดสอบ** - ทดสอบการใช้งาน Dashboard
6. **ปรับแต่ง** - ปรับแต่งตามความต้องการ

---

## **8. คำถามที่ Dashboard จะตอบได้**

- **Strategy ไหนดีที่สุด?** → ดู Strategy Performance Table
- **เวลาไหนควรเทรด?** → ดู Time Pattern Chart
- **Action ไหนดีที่สุด?** → ดู Action + Time Heatmap
- **ความเสี่ยงเท่าไหร่?** → ดู Risk Assessment Table
- **แพ้แล้วจะแพ้ต่อไหม?** → ดู Pre-Loss Streak Analysis
- **ราคาแบบไหนชนะบ่อย?** → ดู Price Movement Analysis
- **Combination ไหนดีที่สุด?** → ดู Best Combinations Table
