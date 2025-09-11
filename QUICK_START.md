# Quick Start Guide - Trading Signal Analysis

## สำหรับ Agent ใหม่
เมื่อคุณเปิด Cursor บนเครื่องอื่น ให้อ่านไฟล์นี้ก่อน!

## เป้าหมายหลัก
- สร้าง **Pattern Analysis Charts** สำหรับ Trading Signals
- เน้นการแสดง **รูปแบบ (Pattern)** ของข้อมูล
- มองเห็น pattern ที่ส่งผลต่อ win rate
- **ไม่ใช่ Performance Metrics** - เน้นการวิเคราะห์รูปแบบ

## ข้อมูลสำคัญ
- **Data File**: `Result Last 120HR.csv`
- **Chart Config**: `metabase_chart_details.json`
- **SQL Queries**: `metabase_queries.sql`
- **Setup Guide**: `metabase_dashboard_guide.md`

## สิ่งที่ทำไปแล้ว
1. ✅ สร้างไฟล์ configuration สำหรับ Metabase
2. ✅ สร้างตัวอย่าง charts
3. ✅ สร้าง dashboard layout
4. ✅ Push ขึ้น GitHub แล้ว

## สิ่งที่ต้องทำต่อ
1. **Pattern Analysis Charts** - สร้าง charts ที่แสดงรูปแบบของข้อมูล
2. **Visual Pattern Recognition** - มองเห็น pattern ที่ส่งผลต่อ win rate
3. **Pattern Detection Visualization** - visualization สำหรับ pattern detection

## วิธีใช้
1. อ่าน `CONVERSATION_CONTEXT.md` เพื่อดูประวัติการคุย
2. ดู `metabase_dashboard_guide.md` เพื่อเข้าใจ setup
3. ดู `metabase_chart_details.json` เพื่อเข้าใจ chart configuration
4. เริ่มสร้าง Pattern Analysis Charts

## คำถามที่พบบ่อย
- **Q**: Chart แสดงอะไร? **A**: แสดงรูปแบบ (Pattern) ของข้อมูล ไม่ใช่ performance
- **Q**: เป้าหมายคืออะไร? **A**: มองเห็น pattern ที่ส่งผลต่อ win rate
- **Q**: ใช้ข้อมูลอะไร? **A**: `Result Last 120HR.csv`

## ไฟล์สำคัญ
- `CONVERSATION_CONTEXT.md` - ประวัติการคุย
- `metabase_chart_details.json` - Chart configuration
- `metabase_queries.sql` - SQL queries
- `Result Last 120HR.csv` - Trading data
