# Pattern Analysis Requirements

## เป้าหมาย
สร้าง Charts ที่แสดง **รูปแบบ (Pattern)** ของข้อมูลแต่ละสัญญาณ เพื่อให้มองเห็น pattern ที่ส่งผลต่อ win rate

## Pattern ที่ต้องวิเคราะห์

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

## Chart Types ที่ต้องสร้าง

### 1. Pattern Detection Charts
- **Heatmap** - แสดง pattern ตามเวลา
- **Scatter Plot** - แสดงความสัมพันธ์ระหว่าง variables
- **Box Plot** - แสดง distribution ของข้อมูล
- **Violin Plot** - แสดง density ของข้อมูล

### 2. Time Series Pattern Charts
- **Line Chart** - แสดง pattern ตามเวลา
- **Area Chart** - แสดง trend pattern
- **Candlestick Chart** - แสดง price pattern

### 3. Distribution Pattern Charts
- **Histogram** - แสดง distribution ของ win rate
- **Density Plot** - แสดง density ของข้อมูล
- **Q-Q Plot** - แสดง distribution comparison

### 4. Correlation Pattern Charts
- **Correlation Matrix** - แสดงความสัมพันธ์ระหว่าง variables
- **Network Graph** - แสดงความสัมพันธ์ระหว่าง strategies
- **Chord Diagram** - แสดงความสัมพันธ์ระหว่าง actions

## ข้อมูลที่ต้องใช้
- **entry_time** - เวลาเข้าสัญญาณ
- **entry_price** - ราคาเข้าสัญญาณ
- **price_10min, price_30min, price_60min** - ราคาตามเวลา
- **result_10min, result_30min, result_60min** - ผลลัพธ์
- **strategy** - กลยุทธ์
- **action** - การกระทำ
- **pnl** - กำไร/ขาดทุน

## Output ที่ต้องการ
1. **Pattern Recognition Charts** - แสดงรูปแบบที่ชัดเจน
2. **Pattern Analysis Report** - รายงานการวิเคราะห์ pattern
3. **Pattern Recommendations** - คำแนะนำจาก pattern
4. **Pattern Alerts** - เตือนเมื่อเจอ pattern ที่น่าสนใจ

## ตัวอย่าง Pattern ที่ต้องหา
- **Golden Hour Pattern** - ชั่วโมงทองที่ win rate สูง
- **Danger Zone Pattern** - ช่วงเวลาที่ควรหลีกเลี่ยง
- **Price Sweet Spot** - ราคาที่เหมาะสมสำหรับแต่ละ strategy
- **Winning Streak Pattern** - รูปแบบการชนะต่อเนื่อง
- **Losing Streak Pattern** - รูปแบบการแพ้ต่อเนื่อง
