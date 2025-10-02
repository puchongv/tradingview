# Test Log - Momentum-based Strategy Scoring Simulation

## 📁 Folder Purpose
เก็บ software simulation และผลทดสอบระบบการให้คะแนน strategy ด้วย Momentum-based Recent Performance Score

## 📄 Files

### 1. `momentum_simulation_v1.py`
Python script สำหรับทดสอบระบบ Momentum-based scoring

**Features:**
- เชื่อมต่อ PostgreSQL database เพื่อดึงข้อมูลจริง
- คำนวณ Momentum Score แบบ real-time ทุกชั่วโมง
- Simulate การเลือก strategy ตาม score สูงสุด
- Track PNL และการเปลี่ยน strategy

**Usage:**
```bash
cd /Users/puchong/tradingview/testlog
python3 momentum_simulation_v1.py
```

**Output:**
- Hourly log แสดง PNL, Score, Status ของทุก strategy
- Final Total PNL
- จำนวน trades และการเปลี่ยน strategy

### 2. `simulation_log.txt`
ผลการทดสอบ Momentum-based scoring กับข้อมูลจริง

**Test Period:** 20/09 01:00 - 21/09 23:00 (47 ชั่วโมง)  
**Result:** **+$11,100** (จากเงินลงทุน $250/trade, payout 0.8)

---

## 🧮 Scoring Formula

### Momentum-based Recent Performance Score

**Step 1: Calculate Momentum (การเปลี่ยนแปลง PNL)**
```
M₁ = PNL₁ - PNL₂  (1 hour ago vs 2 hours ago)
M₂ = PNL₂ - PNL₃  (2 hours ago vs 3 hours ago)
M₃ = PNL₃ - PNL₄
M₄ = PNL₄ - PNL₅
M₅ = PNL₅ - PNL₆
```

**Step 2: Calculate Raw Score (weighted by recency)**
```
RecentScore_raw = 5×max(M₁,0) + 4×max(M₂,0) + 3×max(M₃,0) + 2×max(M₄,0) + 1×max(M₅,0)
```

**Step 3: Calculate KPI**
```
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
```

**Step 4: Normalize Score (max 30 points)**
```
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

---

## 💡 Key Insights

### ทำไมต้องใช้ Momentum แทน Absolute PNL?

**ปัญหาของสูตรเดิม (PNL₁ - PNL₂):**
- ให้คะแนนสูงกับ strategy ที่ "bounce back from loss"
- เช่น: PNL₁ = 150, PNL₂ = -400 → Score = 550 (สูงมาก!)
- แต่จริงๆ strategy นี้กำลัง "recover จากขาดทุน" ไม่ใช่ "กำลังพุ่ง"

**ข้อดีของสูตรใหม่ (Momentum):**
- วัดการเปลี่ยนแปลงระหว่างชั่วโมง (slope/อัตราเร่ง)
- ให้คะแนนสูงกับ strategy ที่มี "momentum" จริงๆ
- เช่น: PNL เปลี่ยนจาก 100 → 150 → 200 → 250 (momentum สม่ำเสมอ = ดี)
- ไม่ให้คะแนนกับ strategy ที่ PNL กระโดด -400 → 150 (แค่ recover)

---

## 📊 Trading Rules

- **Investment:** $250 per trade
- **Payout:** 0.8
  - WIN: +$200
  - LOSE: -$250
- **Strategy Selection:** เลือก strategy ที่มี Recent Performance Score สูงสุดในแต่ละชั่วโมง
- **Evaluation Frequency:** ทุก 1 ชั่วโมง (00:00, 01:00, 02:00, ...)

---

## 🎯 Next Steps

1. ✅ Verify ว่าสูตร Momentum ทำงานได้ตามที่คาดหวัง
2. ⏳ สร้าง SQL V2.1 โดยใช้สูตร Momentum-based scoring
3. ⏳ ทดสอบ V2.1 ใน Metabase
4. ⏳ อัพเดท `Score Evalucation.md` ให้สอดคล้องกับสูตรใหม่

---

**Last Updated:** 2025-10-01

