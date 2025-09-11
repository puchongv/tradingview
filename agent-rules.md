# agent rules - Universal Context System

## 🚨 CRITICAL: READ THIS FIRST
**ทุก Agent ที่ทำงานในโปรเจคนี้ ต้องอ่านไฟล์นี้ก่อนเสมอ!**

## 📋 MANDATORY CHECKLIST
ก่อนเริ่มทำงาน ให้ทำตามลำดับนี้:

### 1. อ่านไฟล์ Context (บังคับ)
```
1. อ่าน QUICK_START.md
2. อ่าน CONVERSATION_CONTEXT.md  
3. อ่าน PATTERN_ANALYSIS_REQUIREMENTS.md
4. อ่าน agent-rules.md (ไฟล์นี้)
```

### 2. ตรวจสอบสถานะปัจจุบัน
- ดู `git log --oneline -5` เพื่อดูงานล่าสุด
- ดู `ls -la *.md` เพื่อดูไฟล์เอกสาร
- ดู `ls -la *.py` เพื่อดูไฟล์โค้ด

### 3. อัพเดท Context (ถ้าจำเป็น)
- อัพเดท `conversation_context.md` ถ้ามีการเปลี่ยนแปลง
- อัพเดท `quick_start.md` ถ้ามีข้อมูลใหม่
- Commit และ push การเปลี่ยนแปลง

## 🎯 PROJECT MISSION
**สร้าง Pattern Analysis Charts สำหรับ Trading Signals**
- เน้นการแสดง **รูปแบบ (Pattern)** ของข้อมูล
- มองเห็น pattern ที่ส่งผลต่อ win rate
- **ไม่ใช่ Performance Metrics** - เน้นการวิเคราะห์รูปแบบ

## 📊 CURRENT STATUS
- **Phase**: Pattern Analysis Development
- **Priority**: Pattern Detection over Performance
- **Data**: `Result Last 120HR.csv` (1,747 rows)
- **Target**: Metabase Dashboard with Pattern Charts

## ✅ COMPLETED TASKS
1. ✅ Metabase configuration files
2. ✅ Sample charts and visualizations
3. ✅ Dashboard layout examples
4. ✅ SQL queries for charts
5. ✅ Context documentation system

## 🔄 IN PROGRESS
- Pattern Analysis Charts development
- Visual Pattern Recognition
- Pattern Detection Visualization

## 📁 KEY FILES
- `Result Last 120HR.csv` - Trading data
- `metabase_chart_details.json` - Chart configuration
- `metabase_queries.sql` - SQL queries
- `conversation_context.md` - Full context
- `pattern_analysis_requirements.md` - Requirements

## 🚫 AVOID THESE
- ❌ Performance metrics focus
- ❌ Basic win rate charts
- ❌ Simple bar/line charts
- ❌ Generic dashboard layouts

## ✅ FOCUS ON THESE
- ✅ Pattern recognition
- ✅ Visual pattern analysis
- ✅ Time-based patterns
- ✅ Price movement patterns
- ✅ Strategy behavior patterns
- ✅ Win/loss streak patterns

## 🔧 WORKFLOW RULES

### Before Starting Work:
1. **Read Context Files** (บังคับ)
2. **Check Git Status** - `git status`
3. **Understand Current Phase** - Pattern Analysis
4. **Identify Next Steps** - จาก requirements

### During Work:
1. **Update Context** - ถ้ามีการเปลี่ยนแปลง
2. **Follow Pattern Focus** - เน้น pattern analysis
3. **Create Visualizations** - ที่แสดงรูปแบบ
4. **Document Changes** - ใน context files

### After Work:
1. **Update Context Files** - อัพเดทสถานะ
2. **Commit Changes** - พร้อมข้อความชัดเจน
3. **Push to GitHub** - เพื่อ sync กับเครื่องอื่น
4. **Update Status** - ใน conversation_context.md

## 📝 COMMUNICATION RULES

### When User Asks:
1. **Check Context First** - อ่านไฟล์ context
2. **Understand Phase** - ดูว่าอยู่ phase ไหน
3. **Answer Based on Context** - ใช้ข้อมูลจาก context
4. **Update Context** - ถ้ามีข้อมูลใหม่

### When User Gives New Requirements:
1. **Update Requirements** - ใน pattern_analysis_requirements.md
2. **Update Context** - ใน conversation_context.md
3. **Plan Implementation** - ตาม requirements ใหม่
4. **Execute and Document** - ทำและบันทึก

## 🎨 CHART CREATION RULES

### Pattern Analysis Charts Only:
- **Heatmaps** - สำหรับ time-based patterns
- **Scatter Plots** - สำหรับ correlation patterns
- **Box Plots** - สำหรับ distribution patterns
- **Violin Plots** - สำหรับ density patterns
- **Network Graphs** - สำหรับ relationship patterns

### Avoid Basic Charts:
- ❌ Simple bar charts
- ❌ Basic line charts
- ❌ Pie charts
- ❌ Number cards

## 🔄 CONTEXT UPDATE RULES

### Always Update These Files:
1. **conversation_context.md** - เมื่อมีการคุยใหม่
2. **quick_start.md** - เมื่อมีข้อมูลใหม่
3. **agent-rules.md** - เมื่อมี rule ใหม่

### Update Format:
```markdown
## Last Update: [DATE]
## Status: [CURRENT_STATUS]
## Next Steps: [NEXT_ACTIONS]
```

## 🚨 EMERGENCY RULES

### If Context is Lost:
1. **Read All .md Files** - เริ่มจาก quick_start.md
2. **Check Git History** - `git log --oneline -10`
3. **Ask User** - "อ่าน context files แล้ว ต้องการทำอะไรต่อ?"
4. **Rebuild Context** - ถ้าจำเป็น

### If User is Confused:
1. **Show Current Status** - จาก context files
2. **Explain Phase** - Pattern Analysis
3. **Show Progress** - จาก git history
4. **Ask for Direction** - ต้องการทำอะไรต่อ

## 📋 DAILY CHECKLIST

### Morning (First Work):
- [ ] Read context files
- [ ] Check git status
- [ ] Understand current phase
- [ ] Plan day's work

### During Work:
- [ ] Focus on pattern analysis
- [ ] Create visualizations
- [ ] Update context files
- [ ] Document changes

### End of Day:
- [ ] Update all context files
- [ ] Commit and push changes
- [ ] Update status
- [ ] Plan next steps

## 🎯 SUCCESS METRICS
- ✅ Pattern recognition charts created
- ✅ Visual pattern analysis working
- ✅ Context maintained across machines
- ✅ User can continue work seamlessly

---

## 📞 CONTACT INFO
- **Repository**: https://github.com/puchongv/tradingview
- **Main Context**: conversation_context.md
- **Quick Start**: quick_start.md
- **Requirements**: pattern_analysis_requirements.md

**Remember: Always read context files first!**
