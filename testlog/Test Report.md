**momentum_test-001**
สูตรที่เทสมา: Option B (Momentum-based) ✅
RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₂−PNL₃,0) + 3×max(PNL₃−PNL₄,0) + 2×max(PNL₄−PNL₅,0) + 1×max(PNL₅−PNL₆,0)
✅ วัด momentum (การเปลี่ยนแปลงระหว่างชั่วโมง)
✅ ให้คะแนนกับ strategy ที่มี "slope" ชัน (กำลังพุ่ง)
✅ น้ำหนักล่าสุดมากกว่า (5, 4, 3, 2, 1)
✅ ผลทดสอบ: +$11,100 (47 ชั่วโมง)
💰 FINAL Total PNL: $11100

------------------------------------------------------------------------------------------

**momentum_test-002**
สูตรที่เทสมา: Option B (Momentum-based) ✅
RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₂−PNL₃,0) + 3×max(PNL₃−PNL₄,0) + 2×max(PNL₄−PNL₅,0) + 1×max(PNL₅−PNL₆,0)
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
📈 Strategies: MWP10-1m, MWP20-3m, MWP-27, MWP-31, SuperTrend10
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$4,000
📊 Total Trades: 38
🔄 Strategy Changes: 8
💰 FINAL Total PNL: $4000
📁 Software: testlog/momentum_testV1.0_002/momentum_simulation_v1.py
📄 Log: testlog/momentum_testV1.0_002/simulation_log.txt (525 lines)

------------------------------------------------------------------------------------------

**momentum_test-003**
สูตรที่เทสมา: Option B (Momentum-based) - Dynamic TOP 6 Selection ✅
RecentScore_raw = 5×max(PNL₁−PNL₂,0) + 4×max(PNL₂−PNL₃,0) + 3×max(PNL₃−PNL₄,0) + 2×max(PNL₄−PNL₅,0) + 1×max(PNL₅−PNL₆,0)
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
📈 Available Strategies: 11 base strategies × 2 actions = 22 total
    - MWP10-1m, MWP20-3m, MWP-27, MWP-30, MWP-31
    - Range Filter5, Range FRAMA100-3, Rang Fillter WR
    - SuperTrend10, SuperTrend9, UTBOT2-5
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$3,550
📊 Total Trades: 38
🔄 Strategy Changes: 7
💰 FINAL Total PNL: $3550
📁 Software: testlog/momentum_test-003/momentum_simulation_v1_dynamic.py
📄 Log: testlog/momentum_test-003/simulation_log.txt

**เปรียบเทียบ Test 002 vs 003:**
- Test 002 (Fixed 5 strategies): $4,000 PNL
- Test 003 (Dynamic TOP 6 from 11 strategies): $3,550 PNL
- Observation: Fixed strategy set outperformed dynamic selection ในช่วงนี้

------------------------------------------------------------------------------------------

**momentum_test-004**
สูตรที่เทสมา: Option C (Exponential Weighting) 🔥
RecentScore_raw = 8×max(M₁,0) + 4×max(M₂,0) + 2×max(M₃,0) + 1×max(M₄,0) + 0.5×max(M₅,0)
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
⚖️  Weights: 8, 4, 2, 1, 0.5 (Exponential - เน้นชั่วโมงล่าสุดหนักมาก)
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$4,650
📊 Total Trades: 39
🔄 Strategy Changes: 12
💰 FINAL Total PNL: $4650
📁 Software: testlog/momentum_test-004/momentum_simulation_v1_optionC.py

------------------------------------------------------------------------------------------

**momentum_test-005**
สูตรที่เทสมา: Option D (Acceleration) 🏆 **BEST!**
RecentScore_raw = 5×max(M₁,0) + 3×max(Acceleration,0)
- Acceleration = M₁ - M₂ (momentum ของ momentum)
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
⚙️  Formula: จับ strategies ที่ momentum กำลังเร่งตัวขึ้น
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$5,400 🏆
📊 Total Trades: 36
🔄 Strategy Changes: 27 (เปลี่ยนบ่อย - sensitive)
💰 FINAL Total PNL: $5400
📁 Software: testlog/momentum_test-005/momentum_simulation_v1_optionD.py

------------------------------------------------------------------------------------------

**momentum_test-006**
สูตรที่เทสมา: Option E (Rate of Growth) ❌
RecentScore_raw = 5×max(Rate₁,0) + 4×max(Rate₂,0) + ...
- Rate = % change in PNL
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
📈 Formula: ดู % growth rate
💰 Investment: $250/trade, Payout: 0.8
❌ ผลทดสอบ: +$1,600 (แย่ที่สุด)
📊 Total Trades: 26
🔄 Strategy Changes: 8
💰 FINAL Total PNL: $1600
📁 Software: testlog/momentum_test-006/momentum_simulation_v1_optionE.py
📝 Note: % growth ไม่เหมาะกับการจับ momentum

------------------------------------------------------------------------------------------

**momentum_test-007**
สูตรที่เทสมา: Option F (Hybrid: Momentum + Absolute)
RecentScore_raw = 0.7×Momentum_Score + 0.3×(PNL₁/100)
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
⚖️  Formula: Balance ระหว่าง momentum และ absolute PNL
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$3,550
📊 Total Trades: 38
🔄 Strategy Changes: 7
💰 FINAL Total PNL: $3550
📁 Software: testlog/momentum_test-007/momentum_simulation_v1_optionF.py
📝 Note: เท่ากับ Test 003 - Hybrid ไม่ช่วยปรับปรุง

------------------------------------------------------------------------------------------

**momentum_test-008**
สูตรที่เทสมา: Option G (Penalty for Negative Momentum) 🔥
RecentScore_raw = 5×max(M₁,0) - 2×max(-M₁,0) + 4×max(M₂,0) - 1.5×max(-M₂,0) + ...
📅 Period: 2025-09-29 00:00:00 to 2025-10-01 00:00:00 (48 ชั่วโมง)
🔍 Mode: Scan ALL strategies, select TOP 6 every hour (DYNAMIC)
⚠️  Penalty: ลงโทษ strategies ที่กำลังดิ่งลง
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$4,450
📊 Total Trades: 38
🔄 Strategy Changes: 11
💰 FINAL Total PNL: $4450
📁 Software: testlog/momentum_test-008/momentum_simulation_v1_optionG.py

------------------------------------------------------------------------------------------

## 📊 สรุปผลการทดสอบทั้งหมด (เรียงตาม PNL)

| Rank | Test | Formula | PNL | Trades | Changes | Note |
|------|------|---------|-----|--------|---------|------|
| 🥇 | **005** | **Acceleration** | **$5,400** | 36 | 27 | จับ momentum ที่เร่งตัวขึ้น (sensitive) |
| 🥈 | **004** | **Exponential** | **$4,650** | 39 | 12 | เน้นชั่วโมงล่าสุดหนักมาก |
| 🥉 | **008** | **Penalty** | **$4,450** | 38 | 11 | ลงโทษ negative momentum |
| 4 | **002** | **Linear (Fixed)** | **$4,000** | 38 | 8 | Baseline - Fixed 5 strategies |
| 5 | **003** | **Linear (Dynamic)** | **$3,550** | 38 | 7 | Baseline - Dynamic scan all |
| 5 | **007** | **Hybrid** | **$3,550** | 38 | 7 | 0.7×Momentum + 0.3×Absolute |
| 7 | **006** | **Rate of Growth** | **$1,600** | 26 | 8 | % change - ไม่เหมาะ |

---

## 🎯 สรุปและข้อเสนอแนะ

### ผู้ชนะ: **Test 005 (Acceleration)** 🏆
- **PNL: $5,400** (+35% จาก baseline Test 002)
- **Formula**: 5×M₁ + 3×Acceleration
- **จุดเด่น**: จับ strategies ที่ momentum กำลัง "เร่งตัวขึ้น" ได้แม่นยำ
- **จุดอ่อน**: Sensitive มาก → เปลี่ยน strategy บ่อย (27 ครั้ง)

### Runner-up: **Test 004 (Exponential)** 🥈
- **PNL: $4,650** (+16% จาก baseline)
- **Formula**: 8, 4, 2, 1, 0.5 (Exponential weights)
- **จุดเด่น**: เน้นชั่วโมงล่าสุดหนักมาก → responsive
- **จุดอ่อน**: เปลี่ยนบ่อยพอสมควร (12 ครั้ง)

### Third: **Test 008 (Penalty)** 🥉
- **PNL: $4,450** (+11% จาก baseline)
- **Formula**: Momentum + Penalty for negative
- **จุดเด่น**: หลีกเลี่ยง strategies ที่กำลังดิ่งลง
- **Balanced**: เปลี่ยนไม่บ่อยมาก (11 ครั้ง)

### ผู้แพ้: **Test 006 (Rate of Growth)** ❌
- **PNL: $1,600** (-60% จาก baseline)
- **% growth ไม่เหมาะ** กับการจับ momentum

---

## 💡 คำแนะนำสำหรับ Production

**แนะนำ Test 005 (Acceleration)** หาก:
- ต้องการ PNL สูงสุด
- ยอมรับ transaction costs จากการเปลี่ยน strategy บ่อย
- มีระบบที่ execute เร็ว

**แนะนำ Test 008 (Penalty)** หาก:
- ต้องการ balance ระหว่าง PNL และ stability
- ต้องการลด transaction costs
- ต้องการหลีกเลี่ยง strategies ที่กำลังแย่ลง

**Next Steps:**
1. ทดสอบ Test 005 กับข้อมูลช่วงอื่นๆ (out-of-sample testing)
2. วิเคราะห์ว่า 27 strategy changes ของ Test 005 มี transaction cost เท่าไหร่
3. พิจารณา calibrate Test 008 เพิ่มเติม (tune penalty weights)

------------------------------------------------------------------------------------------


## 🆕 Tests 009-014: Dynamic Strategy & Action (1-30 Sep 2025)

**Test 009: Linear (Option B)**
PNL: $50,950 | Trades: 662 | Changes: 227

**Test 010: Exponential (Option C)** 🔥  
PNL: $77,250 | Trades: 672 | Changes: 308

**Test 011: Acceleration (Option D)** 🏆 **BEST!**  
PNL: $115,800 | Trades: 651 | Changes: 595 (very sensitive)

**Test 012: Rate of Growth (Option E)** ❌  
PNL: $35,000 | Trades: 373 | Changes: 229 (WORST)

**Test 013: Hybrid (Option F)**  
PNL: $51,350 | Trades: 664 | Changes: 228

**Test 014: Penalty (Option G)** 🔥  
PNL: $73,550 | Trades: 613 | Changes: 281

---

## 📊 Ranking (Dynamic Tests 009-014):

| Rank | Test | PNL | vs Baseline |
|------|------|-----|-------------|
| 🥇 | 011 (Acceleration) | $115,800 | +127% |
| 🥈 | 010 (Exponential) | $77,250 | +52% |
| 🥉 | 014 (Penalty) | $73,550 | +44% |
| 4 | 013 (Hybrid) | $51,350 | +1% |
| 5 | 009 (Linear) | $50,950 | Baseline |
| 6 | 012 (Rate of Growth) | $35,000 | -31% |

**Period:** 1-30 September 2025 (30 วัน, ~720 ชั่วโมง)  
**Mode:** Dynamic - Scan ALL strategies & actions (no hard-code)  
**Combinations:** ~41 strategy-action pairs (6 actions)

---

## 🎯 Winner: Test 011 (Acceleration) 🏆

- **PNL: $115,800** (สูงที่สุด!)
- Formula: 5×M₁ + 3×Acceleration
- แต่ sensitive มาก (595 changes)
- เหมาะกับ high-frequency trading

---

## 🔄 Hard-code Buy/Sell Tests (016-017)

**momentum_test-016**
สูตรที่เทสมา: Acceleration (Option D) - Hard-code Buy/Sell only ✅
RecentScore_raw = 5×M₁ + 3×Acceleration (where M₁=PNL₁−PNL₂, Acceleration=M₁−M₂)
📅 Period: 2025-09-01 00:00:00 to 2025-09-30 23:59:59 (30 days)
🎯 Actions: Buy/Sell ONLY (no FlowTrend)
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$124,600 🥇 (Best performer!)
📊 Total Trades: 704
🔄 Strategy Changes: 593
📁 Software: testlog/momentum_test-016/momentum_simulation_v2.py
📄 Log: testlog/momentum_test-016/simulation_log.txt

🔍 **Key Discovery:**
- Hard-code Buy/Sell outperforms Dynamic All Actions by +$8,800 (+7.6%)
- FlowTrend actions add noise rather than value
- Simple is better: 22 combinations vs 45 combinations

------------------------------------------------------------------------------------------

**momentum_test-017**
สูตรที่เทสมา: Acceleration (Option D) - Hard-code Buy/Sell only ✅
RecentScore_raw = 5×M₁ + 3×Acceleration (where M₁=PNL₁−PNL₂, Acceleration=M₁−M₂)
📅 Period: 2025-09-22 00:00:00 to 2025-09-30 23:59:59 (8-9 days)
🎯 Actions: Buy/Sell ONLY (no FlowTrend)
💰 Investment: $250/trade, Payout: 0.8
✅ ผลทดสอบ: +$41,650
📊 Total Trades: 242
🔄 Strategy Changes: 176
📁 Software: testlog/momentum_test-017/momentum_simulation_v2.py
📄 Log: testlog/momentum_test-017/simulation_log.txt

🔍 **Performance Analysis:**
- 8-9 days = ~$41,650 
- Average: ~$4,628/day
- Extrapolated to 30 days: ~$138,840 (slightly better than test 016)
- Top performers: MWP10-1m, MWP-30, MWP-27, Range FRAMA100-3

------------------------------------------------------------------------------------------

### 📊 Hard-code Buy/Sell Comparison

| Period | Test | Days | PNL | Daily Avg | Notes |
|--------|------|------|-----|-----------|-------|
| 1-30 Sep | 016 | 30 | $124,600 | $4,153 | Full month |
| 22-30 Sep | 017 | 8-9 | $41,650 | $4,628 | Recent period |

**💡 Insight:** ช่วง 22-30 Sep มี performance สูงกว่าค่าเฉลี่ย (~+11.4%)

---

## 🧪 TEST 028: Acceleration Extended + 4-Hour Lookback

**📅 Period:** 01-30 Sep 2025 (30 วัน)  
**🔄 Formula:** `5×M₁ + 3×Accel₁ + 2×Accel₂` (เพิ่ม M3 เข้าไป)  
**📊 Lookback:** 4 hours (ลดจาก 7 วัน)  
**🎯 Actions:** Buy/Sell ONLY (hard-code)  
**💰 Final PNL:** $111,850  
**📈 Daily Average:** $3,728/day  
**🎯 Trades:** 719 | Strategy Changes: 485

🔍 **Key Changes:**
- เพิ่ม M3 (momentum ก่อนหน้า 2) เข้าไปในสูตร
- คำนวน Acceleration ย้อนหลัง (accel2 = m2 - m3)
- ใช้ lookback 4 ชั่วโมง (แทน 7 วัน) เพื่อให้ P1-P4 มีค่าจริง
- น้ำหนัก: 5×m1 + 3×accel1 + 2×accel2

🔍 **Performance vs Test 016:**
- Test 016 (Original Acceleration): $124,600 | $4,153/day
- Test 028 (Extended Acceleration): $111,850 | $3,728/day
- **Difference:** -$12,750 (-10.2%)

**💡 Insight:** การเพิ่ม M3 และ Accel2 ทำให้ PNL ลดลง 10.2% เมื่อเทียบกับสูตรเดิม (Test 016) ซึ่งอาจเกิดจาก:
1. Lag มากขึ้น (ดูข้อมูลย้อนหลังลึกถึง P4)
2. Accel2 น้ำหนัก 2 อาจไม่เพียงพอในการชดเชย lag
3. Strategy เปลี่ยนบ่อยขึ้น (485 ครั้ง vs ?)

------------------------------------------------------------------------------------------

