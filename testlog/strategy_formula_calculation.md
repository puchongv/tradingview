# Strategy Formula Calculation - Momentum Scoring Methods

เอกสารนี้รวบรวมสูตรการคำนวนคะแนน Momentum ทั้งหมด 6 แบบ สำหรับระบบ Dynamic Strategy Selection

---

## 📋 สารบัญ

1. [Linear Momentum (Option B)](#1-linear-momentum-option-b)
2. [Exponential Weighting (Option C)](#2-exponential-weighting-option-c)
3. [Acceleration (Option D)](#3-acceleration-option-d)
4. [Rate of Growth (Option E)](#4-rate-of-growth-option-e)
5. [Hybrid (Option F)](#5-hybrid-option-f)
6. [Penalty for Negative Momentum (Option G)](#6-penalty-for-negative-momentum-option-g)

---

## 1. Linear Momentum (Option B)

### ชื่อเรียก
**Linear Momentum** หรือ **Baseline Momentum**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Momentum แต่ละชั่วโมง
M₁ = PNL₁ - PNL₂  (momentum ชั่วโมงล่าสุด)
M₂ = PNL₂ - PNL₃
M₃ = PNL₃ - PNL₄
M₄ = PNL₄ - PNL₅
M₅ = PNL₅ - PNL₆

ขั้นที่ 2: คำนวน Raw Score
RecentScore_raw = 5×max(M₁, 0) + 
                  4×max(M₂, 0) + 
                  3×max(M₃, 0) + 
                  2×max(M₄, 0) + 
                  1×max(M₅, 0)

ขั้นที่ 3: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### น้ำหนัก (Weights)
```
W = [5, 4, 3, 2, 1]  (Linear - ลดลงเป็นเส้นตรง)
```

### หลักการ
- วัด momentum (การเปลี่ยนแปลงของ PNL) ระหว่างชั่วโมง
- ให้น้ำหนักชั่วโมงล่าสุดมากกว่า แต่ลดลงแบบเส้นตรง
- นับเฉพาะ momentum ที่เป็นบวก (max(M, 0))

### ผลการทดสอบ
- **PNL:** $3,550
- **Trades:** 38
- **Strategy Changes:** 7
- **Performance:** Baseline (0%)

### ข้อดี
✅ เข้าใจง่าย สมดุล  
✅ Stable (เปลี่ยน strategy ไม่บ่อย)  
✅ เหมาะเป็น baseline สำหรับเปรียบเทียบ

### ข้อเสีย
❌ Performance ต่ำกว่าวิธีอื่น  
❌ ไม่ sensitive กับการเปลี่ยนแปลงเร็ว

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    m1 = p1 - p2
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    recent_raw = (5 * max(m1, 0) + 
                  4 * max(m2, 0) + 
                  3 * max(m3, 0) + 
                  2 * max(m4, 0) + 
                  1 * max(m5, 0))
    
    return recent_raw
```

---

## 2. Exponential Weighting (Option C)

### ชื่อเรียง
**Exponential Momentum** หรือ **Front-Heavy Momentum**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Momentum
M₁ = PNL₁ - PNL₂
M₂ = PNL₂ - PNL₃
M₃ = PNL₃ - PNL₄
M₄ = PNL₄ - PNL₅
M₅ = PNL₅ - PNL₆

ขั้นที่ 2: คำนวน Raw Score (Exponential Weights)
RecentScore_raw = 8.0×max(M₁, 0) + 
                  4.0×max(M₂, 0) + 
                  2.0×max(M₃, 0) + 
                  1.0×max(M₄, 0) + 
                  0.5×max(M₅, 0)

ขั้นที่ 3: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### น้ำหนัก (Weights)
```
W = [8, 4, 2, 1, 0.5]  (Exponential - แต่ละน้ำหนักลดลงครึ่งหนึ่ง)
Ratio: 16 : 8 : 4 : 2 : 1
```

### หลักการ
- เน้นชั่วโมงล่าสุดหนักมากๆ (น้ำหนัก 8)
- น้ำหนักลดลงแบบ exponential (หารครึ่ง)
- Responsive กับการเปลี่ยนแปลงเร็ว

### ผลการทดสอบ
- **PNL:** $4,650 (+31% vs Linear) 🔥
- **Trades:** 39
- **Strategy Changes:** 12
- **Performance:** +31% vs Baseline

### ข้อดี
✅ จับ momentum ชั่วโมงล่าสุดได้แม่นยำ  
✅ Responsive กับการเปลี่ยนแปลงเร็ว  
✅ Performance ดีกว่า Linear มาก

### ข้อเสีย
❌ เปลี่ยน strategy บ่อยพอสมควร (12 ครั้ง)  
❌ อาจ sensitive เกินไปในตลาดที่ volatile

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    m1 = p1 - p2
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    recent_raw = (8.0 * max(m1, 0) + 
                  4.0 * max(m2, 0) + 
                  2.0 * max(m3, 0) + 
                  1.0 * max(m4, 0) + 
                  0.5 * max(m5, 0))
    
    return recent_raw
```

---

## 3. Acceleration (Option D)

### ชื่อเรียก
**Acceleration Momentum** หรือ **Momentum of Momentum**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Momentum
M₁ = PNL₁ - PNL₂  (momentum ล่าสุด)
M₂ = PNL₂ - PNL₃

ขั้นที่ 2: คำนวน Acceleration (momentum ของ momentum)
Acceleration = M₁ - M₂

ขั้นที่ 3: คำนวน Raw Score
RecentScore_raw = 5×max(M₁, 0) + 3×max(Acceleration, 0)

ขั้นที่ 4: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### น้ำหนัก (Weights)
```
W_momentum = 5
W_acceleration = 3
```

### หลักการ
- วัด **momentum ของ momentum** (Acceleration)
- จับ strategies ที่ momentum กำลัง **เร่งตัวขึ้น**
- เน้นที่การเปลี่ยนแปลงของอัตราการเปลี่ยนแปลง

### ตัวอย่างการคำนวน
```
PNL: [300, 250, 150, 100, 50, 0]

M₁ = 300 - 250 = 50   (momentum ชั่วโมงล่าสุด)
M₂ = 250 - 150 = 100  (momentum ชั่วโมงก่อน)

Acceleration = 50 - 100 = -50  (momentum กำลังชะลอตัว)
→ max(Acceleration, 0) = 0

RecentScore_raw = 5×50 + 3×0 = 250
```

### ผลการทดสอบ
- **PNL:** $5,400 (+52% vs Linear) 🏆 **BEST!**
- **Trades:** 36
- **Strategy Changes:** 27
- **Performance:** +52% vs Baseline

### ข้อดี
✅ **PNL สูงสุด** จากทุก options  
✅ จับ strategies ที่กำลัง "เร่งตัวขึ้น" ได้แม่นยำ  
✅ เหมาะกับตลาดที่มี momentum แรง

### ข้อเสีย
❌ **Sensitive มาก** → เปลี่ยน strategy บ่อยที่สุด (27 ครั้ง)  
❌ Transaction costs อาจสูง  
❌ ต้องการระบบ execution ที่เร็ว

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Momentum
    m1 = p1 - p2
    m2 = p2 - p3
    
    # Acceleration (momentum ของ momentum)
    acceleration = m1 - m2
    
    # Score
    recent_raw = (5 * max(m1, 0) + 
                  3 * max(acceleration, 0))
    
    return recent_raw
```

---

## 4. Rate of Growth (Option E)

### ชื่อเรียก
**Percentage Growth Momentum** หรือ **Relative Growth**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Rate of Growth (% change)
Rate₁ = (PNL₁ - PNL₂) / max(|PNL₂|, 1)  × 100
Rate₂ = (PNL₂ - PNL₃) / max(|PNL₃|, 1)  × 100
Rate₃ = (PNL₃ - PNL₄) / max(|PNL₄|, 1)  × 100
Rate₄ = (PNL₄ - PNL₅) / max(|PNL₅|, 1)  × 100
Rate₅ = (PNL₅ - PNL₆) / max(|PNL₆|, 1)  × 100

ขั้นที่ 2: คำนวน Raw Score
RecentScore_raw = 5×max(Rate₁, 0) + 
                  4×max(Rate₂, 0) + 
                  3×max(Rate₃, 0) + 
                  2×max(Rate₄, 0) + 
                  1×max(Rate₅, 0)

ขั้นที่ 3: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### หลักการ
- วัด **% การเติบโต** แทนการเติบโตแบบ absolute
- ไม่ bias ต่อ strategies ที่มี PNL สูง
- เน้นที่ growth rate

### ตัวอย่างการคำนวน
```
PNL: [300, 200, 100, 50, 25, 0]

Rate₁ = (300 - 200) / 200 × 100 = 50%
Rate₂ = (200 - 100) / 100 × 100 = 100%
Rate₃ = (100 - 50) / 50 × 100 = 100%

RecentScore_raw = 5×50 + 4×100 + 3×100 = 950
```

### ผลการทดสอบ
- **PNL:** $1,600 (-55% vs Linear) ❌ **WORST!**
- **Trades:** 26
- **Strategy Changes:** 8
- **Performance:** -55% vs Baseline

### ข้อดี
✅ ไม่ bias ต่อ strategies ที่มี PNL สูง  
✅ เหมาะกับการเปรียบเทียบ strategies ที่มี scale ต่างกัน

### ข้อเสีย
❌ **Performance แย่ที่สุด**  
❌ % growth ไม่สะท้อนถึง absolute profit ที่ได้จริง  
❌ Strategies PNL ต่ำแต่ % growth สูง อาจได้คะแนนผิดพลาด

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Rate of growth (% change)
    rate1 = (p1 - p2) / max(abs(p2), 1) if p2 != 0 else (p1 - p2)
    rate2 = (p2 - p3) / max(abs(p3), 1) if p3 != 0 else (p2 - p3)
    rate3 = (p3 - p4) / max(abs(p4), 1) if p4 != 0 else (p3 - p4)
    rate4 = (p4 - p5) / max(abs(p5), 1) if p5 != 0 else (p4 - p5)
    rate5 = (p5 - p6) / max(abs(p6), 1) if p6 != 0 else (p5 - p6)
    
    # Scale by 100
    recent_raw = (5 * max(rate1, 0) * 100 + 
                  4 * max(rate2, 0) * 100 + 
                  3 * max(rate3, 0) * 100 + 
                  2 * max(rate4, 0) * 100 + 
                  1 * max(rate5, 0) * 100)
    
    return recent_raw
```

---

## 5. Hybrid (Option F)

### ชื่อเรียก
**Hybrid Momentum** หรือ **Balanced Momentum & Performance**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Momentum Score
M₁ = PNL₁ - PNL₂
M₂ = PNL₂ - PNL₃
M₃ = PNL₃ - PNL₄
M₄ = PNL₄ - PNL₅
M₅ = PNL₅ - PNL₆

Momentum_Score = 5×max(M₁, 0) + 
                 4×max(M₂, 0) + 
                 3×max(M₃, 0) + 
                 2×max(M₄, 0) + 
                 1×max(M₅, 0)

ขั้นที่ 2: คำนวน Absolute Performance Score
Absolute_Score = PNL₁ / 100  (normalize)

ขั้นที่ 3: คำนวน Hybrid Raw Score
RecentScore_raw = 0.7×Momentum_Score + 0.3×Absolute_Score

ขั้นที่ 4: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### น้ำหนัก (Weights)
```
W_momentum = 0.7  (70%)
W_absolute = 0.3  (30%)
```

### หลักการ
- Balance ระหว่าง **momentum** (กำลังพุ่ง) และ **absolute PNL** (กำไรจริง)
- ป้องกันการเลือก strategies ที่ momentum ดีแต่ PNL ต่ำ
- Tune ratio ได้ตามต้องการ

### ตัวอย่างการคำนวน
```
Momentum_Score = 250
PNL₁ = 300

Absolute_Score = 300 / 100 = 3
RecentScore_raw = 0.7×250 + 0.3×3 = 175 + 0.9 = 175.9
```

### ผลการทดสอบ
- **PNL:** $3,550 (0% vs Linear)
- **Trades:** 38
- **Strategy Changes:** 7
- **Performance:** เท่ากับ Baseline

### ข้อดี
✅ Balance ระหว่าง momentum และ absolute performance  
✅ Tune ratio ได้ตามต้องการ

### ข้อเสีย
❌ **ไม่ช่วยปรับปรุง performance**  
❌ อาจทำให้ performance แย่ลงถ้า tune ผิด  
❌ ซับซ้อนกว่าแต่ไม่ได้ผลดีกว่า

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Momentum
    m1 = p1 - p2
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    # Momentum score
    momentum_score = (5 * max(m1, 0) + 
                      4 * max(m2, 0) + 
                      3 * max(m3, 0) + 
                      2 * max(m4, 0) + 
                      1 * max(m5, 0))
    
    # Absolute performance score
    absolute_score = p1 / 100
    
    # Hybrid (70% momentum, 30% absolute)
    recent_raw = 0.7 * momentum_score + 0.3 * absolute_score
    
    return recent_raw
```

---

## 6. Penalty for Negative Momentum (Option G)

### ชื่อเรียก
**Penalty Momentum** หรือ **Risk-Adjusted Momentum**

### สูตรการคำนวน

```
ขั้นที่ 1: คำนวน Momentum
M₁ = PNL₁ - PNL₂
M₂ = PNL₂ - PNL₃
M₃ = PNL₃ - PNL₄
M₄ = PNL₄ - PNL₅
M₅ = PNL₅ - PNL₆

ขั้นที่ 2: คำนวน Raw Score (with Penalty)
RecentScore_raw = 5×max(M₁, 0) - 2.0×max(-M₁, 0) +    # Heavy penalty
                  4×max(M₂, 0) - 1.5×max(-M₂, 0) +    # Medium penalty
                  3×max(M₃, 0) - 1.0×max(-M₃, 0) +    # Light penalty
                  2×max(M₄, 0) + 
                  1×max(M₅, 0)

ขั้นที่ 3: Normalize Score
Recent_KPI = mean(RecentScore_raw) + std(RecentScore_raw)
RecentScore = min((RecentScore_raw / Recent_KPI) × 30, 30)
```

### น้ำหนัก (Weights)
```
Positive Momentum: [5, 4, 3, 2, 1]
Negative Penalty:  [-2, -1.5, -1, 0, 0]

Penalty Ratio:
M₁: -2.0 (40% of positive weight)
M₂: -1.5 (37.5% of positive weight)
M₃: -1.0 (33% of positive weight)
```

### หลักการ
- ให้คะแนนกับ positive momentum ตามปกติ
- **ลงโทษ** strategies ที่มี **negative momentum**
- Penalty หนักขึ้นสำหรับชั่วโมงล่าสุด
- หลีกเลี่ยง strategies ที่กำลังดิ่งลง

### ตัวอย่างการคำนวน
```
Case 1: Positive momentum
M₁ = 100, M₂ = 80, M₃ = 50
RecentScore_raw = 5×100 + 4×80 + 3×50 = 970

Case 2: Mixed momentum
M₁ = 100, M₂ = -50, M₃ = 30
RecentScore_raw = 5×100 - 1.5×50 + 3×30 = 500 - 75 + 90 = 515

Case 3: Negative momentum
M₁ = -100, M₂ = -50, M₃ = -30
RecentScore_raw = -2×100 - 1.5×50 - 1×30 = -305
```

### ผลการทดสอบ
- **PNL:** $4,450 (+25% vs Linear) 🔥
- **Trades:** 38
- **Strategy Changes:** 11
- **Performance:** +25% vs Baseline

### ข้อดี
✅ **หลีกเลี่ยง strategies ที่กำลังดิ่งลง**  
✅ Performance ดี (อันดับ 3)  
✅ **Balanced** - ไม่เปลี่ยน strategy บ่อยเกินไป  
✅ เหมาะกับ production (trade-off ระหว่าง PNL และ stability)

### ข้อเสีย
❌ อาจพลาด strategies ที่ "bounce back" จากขาดทุน  
❌ ต้อง tune penalty weights อย่างระมัดระวัง

### Python Implementation
```python
def calculate_momentum_score(pnls):
    p1, p2, p3, p4, p5, p6 = pnls
    
    # Momentum
    m1 = p1 - p2
    m2 = p2 - p3
    m3 = p3 - p4
    m4 = p4 - p5
    m5 = p5 - p6
    
    # Score with penalty for negative momentum
    recent_raw = (5 * max(m1, 0) - 2.0 * max(-m1, 0) +      # Heavy penalty
                  4 * max(m2, 0) - 1.5 * max(-m2, 0) +      # Medium penalty
                  3 * max(m3, 0) - 1.0 * max(-m3, 0) +      # Light penalty
                  2 * max(m4, 0) + 
                  1 * max(m5, 0))
    
    return recent_raw
```

---

## 📊 สรุปเปรียบเทียบ

| Option | ชื่อเรียก | PNL | Change | Performance | Complexity | Stability |
|--------|----------|-----|--------|-------------|------------|-----------|
| **D** | **Acceleration** | **$5,400** | 27 | **+52%** 🏆 | Medium | Low |
| **C** | **Exponential** | **$4,650** | 12 | **+31%** 🥈 | Low | Medium |
| **G** | **Penalty** | **$4,450** | 11 | **+25%** 🥉 | Medium | High |
| **B** | **Linear** | **$3,550** | 7 | Baseline | Low | High |
| **F** | **Hybrid** | **$3,550** | 7 | 0% | High | High |
| **E** | **Rate of Growth** | **$1,600** | 8 | **-55%** ❌ | Medium | Medium |

---

## 💡 คำแนะนำการเลือกใช้

### สำหรับ Production

**เลือก Acceleration (Option D)** หาก:
- 🎯 ต้องการ PNL สูงสุด
- 💰 ยอมรับ transaction costs สูง
- ⚡ มีระบบ execution ที่รวดเร็ว
- 📊 ตลาดมี momentum แรง

**เลือก Penalty (Option G)** หาก:
- ⚖️ ต้องการ balance ระหว่าง PNL และ stability
- 💵 ต้องการลด transaction costs
- 🛡️ ต้องการหลีกเลี่ยง risk จาก strategies ที่กำลังแย่ลง
- 🏭 เหมาะกับ production จริง

**เลือก Exponential (Option C)** หาก:
- 📈 ต้องการ responsive กับการเปลี่ยนแปลงเร็ว
- 💡 ไม่ต้องการซับซ้อน
- 🔥 ต้องการ performance ดีและ stability พอใช้

---

## 📝 หมายเหตุ

- ทุกสูตรใช้ **Dynamic Strategy Selection** (ไม่ fix strategies)
- การทดสอบใช้ข้อมูลวันที่ 29-30 กันยายน 2025
- Investment: $250/trade, Payout: 0.8
- Scan ทั้งหมด 22 strategies (11 base × 2 actions)

---

**Last Updated:** October 1, 2025  
**Test Period:** 2025-09-29 to 2025-10-01 (48 hours)

