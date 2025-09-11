# Binary Options Trading Patterns
## รูปแบบการเทรดที่พบจากการวิเคราะห์ข้อมูล 120 ชั่วโมง

---

## 1. PRE-LOSS STREAK PATTERN (สัญญาณที่ชัดเจนที่สุด)

### สิ่งที่พบ:
- **เมื่อแพ้ 1 ครั้งติด** จะมี win rate ตกลง **30-57%**
- **MWP-25**: 63.8% → 23.9% (ตกลง 39.9%)
- **MWP-27**: 66.1% → 25.6% (ตกลง 40.6%)
- **MWP-30**: 72.5% → 14.8% (ตกลง 57.6%)

### เงื่อนไข:
- **หยุดสัญญาณเดิมทันทีเมื่อแพ้ ≥1 ครั้ง**
- **ห้ามใช้ strategy เดิมต่อ** หลังจากแพ้ 1 ครั้ง

### ใช้เมื่อไหร่:
- ตรวจสอบก่อนเทรดทุกครั้ง
- ถ้าแพ้ 1 ครั้ง = หยุด strategy นั้นทันที

---

## 2. TIME ZONE PATTERN (สัญญาณที่สำคัญมาก)

### โซนดี (Win Rate ≥ 60%):
- **00:00-06:00**: 00:00, 04:00, 06:00, 08:00
- **10:00-11:00**: 10:00, 11:00
- **14:00-16:00**: 14:00, 15:00, 16:00
- **22:00**: 22:00

### โซนแย่ (Win Rate ≤ 40%):
- **12:00**: 12:00
- **17:00-19:00**: 17:00, 18:00, 19:00
- **03:00**: 03:00

### เงื่อนไข:
- **เทรดเฉพาะชั่วโมงดี**
- **หลีกเลี่ยงชั่วโมงแย่**

### ใช้เมื่อไหร่:
- ตรวจสอบเวลาก่อนเทรด
- ถ้าเป็นชั่วโมงแย่ = หยุดเทรด

---

## 3. WINNING STREAK PATTERN (สัญญาณที่สำคัญมาก)

### สิ่งที่พบ:
- **เมื่อชนะ 1 ครั้ง** = มีโอกาส 79-85% ชนะต่อ
- **เมื่อชนะ 2-4 ครั้ง** = มีโอกาส 80-87% ชนะต่อ
- **เมื่อชนะ 5+ ครั้ง** = เริ่มมีโอกาสแพ้มากขึ้น

### เงื่อนไข:
- **เมื่อชนะ 1-4 ครั้ง** = ต่อเทรดได้
- **เมื่อชนะ 5+ ครั้ง** = ระวัง เริ่มมีโอกาสแพ้

### ใช้เมื่อไหร่:
- ตรวจสอบ winning streak ปัจจุบัน
- ถ้า 1-4 ครั้ง = ต่อได้
- ถ้า 5+ ครั้ง = ระวัง

---

## 4. STRATEGY ROTATION PATTERN (สัญญาณที่สำคัญ)

### Strategy ที่ดีที่สุด:
- **10min**: Range FRAMA3 (61.0% win rate)
- **30min**: Range FRAMA3 (56.2% win rate), MWP-30 (52.1% win rate)
- **60min**: Range FRAMA3 (54.3% win rate), MWP-30 (51.6% win rate)

### Strategy ที่หมุนเวียน:
- **Range FRAMA3**: ดีใน 10min
- **MWP-30**: ดีใน 30min, 60min
- **Strategy หมุนเวียนกัน** - ไม่มี strategy ไหนดีตลอด

### เงื่อนไข:
- **เปลี่ยน strategy ตาม timeframe**
- **เปลี่ยน strategy ตามเวลา** (12 ชั่วโมง)

### ใช้เมื่อไหร่:
- เลือก strategy ตาม timeframe
- เปลี่ยน strategy ทุก 12 ชั่วโมง

---

## 5. PRICE MOMENTUM PATTERN (สัญญาณ reversal)

### สิ่งที่พบ:
- **Negative Momentum**: 63.0% win rate (10min) - **สัญญาณ reversal!**
- **Positive Momentum**: 60.9% win rate (10min)
- **Neutral Momentum**: 51.2% win rate (10min)

### Price Volatility:
- **Low Volatility**: 55.5% win rate (10min) - **ดีที่สุด**
- **Medium Volatility**: 52.4% win rate (10min)
- **High Volatility**: 47.0% win rate (10min) - **แย่ที่สุด**

### เงื่อนไข:
- **เมื่อ price momentum เป็นลบ** = มีโอกาสชนะสูง (reversal)
- **เมื่อ volatility ต่ำ** = มีโอกาสชนะสูง

### ใช้เมื่อไหร่:
- ตรวจสอบ price momentum ก่อนเทรด
- เลือกเทรดเมื่อ momentum เป็นลบ
- หลีกเลี่ยงเมื่อ volatility สูง

---

## 6. ACTION PATTERN (สัญญาณที่ชัดเจน)

### Action Sequence ที่ดีที่สุด:
- **Sell -> FlowTrend Bullish + Buy**: 100.0% win rate
- **Buy -> FlowTrend Bearish + Sell+**: 100.0% win rate
- **FlowTrend Bearish + Sell -> Sell**: 63.2% win rate

### Best Action per Hour:
- **00:00-06:00**: FlowTrend Bullish + Buy/Buy+ (100% win rate)
- **06:00-12:00**: Buy (55-80% win rate)
- **12:00-18:00**: FlowTrend Bearish + Sell (60-100% win rate)
- **18:00-00:00**: FlowTrend Bullish + Buy (60-100% win rate)

### เงื่อนไข:
- **เลือก action ตามเวลา**
- **ใช้ action sequence ที่ดี**

### ใช้เมื่อไหร่:
- ตรวจสอบเวลาก่อนเลือก action
- ใช้ action sequence ที่มี win rate สูง

---

## 7. MARKET CONDITION PATTERN (สัญญาณที่ชัดเจน)

### Market Condition ที่ดี:
- **Strong Up**: 61.5% win rate (10min) - **ดีที่สุด**
- **Sideways**: 54.1% win rate (10min)
- **Down**: 53.3% win rate (10min)
- **Strong Down**: 50.5% win rate (10min)

### Best Strategy per Market Condition:
- **Strong Down**: MWP-20 (63.6% win rate)
- **Sideways**: Range FRAMA3 (69.0% win rate)
- **Strong Up**: Range FRAMA3 (71.4% win rate)

### เงื่อนไข:
- **เลือก strategy ตาม market condition**
- **Strong Up = ดีที่สุด**

### ใช้เมื่อไหร่:
- ตรวจสอบ market condition ก่อนเทรด
- เลือก strategy ที่เหมาะกับ market condition

---

## 8. DAILY STABILITY PATTERN (สัญญาณเสถียรภาพ)

### Strategy ที่เสถียร (CV ≤ 20%):
- **10min**: MWP-20, MWP-25, MWP-27, Range FRAMA3, UT-BOT2-10
- **30min**: MWP-20, MWP-25, MWP-27, UT-BOT2-10
- **60min**: Range FRAMA3, UT-BOT2-10

### Strategy ที่ไม่เสถียร (CV > 20%):
- **10min**: MWP-30, Range Filter5
- **30min**: MWP-30, Range FRAMA3, Range FRAMA3-99, Range Filter5
- **60min**: MWP-20, MWP-25, MWP-27, MWP-30, Range FRAMA3-99, Range Filter5

### เงื่อนไข:
- **เลือก strategy ที่เสถียร**
- **หลีกเลี่ยง strategy ที่ไม่เสถียร**

### ใช้เมื่อไหร่:
- เลือก strategy ที่มี CV ≤ 20%
- หลีกเลี่ยง strategy ที่มี CV > 20%

---

## 9. MAX LOSS STREAK PATTERN (สัญญาณความเสี่ยง)

### Strategy ที่ปลอดภัย (Max Streak ≤ 3):
- **Range FRAMA3**: Max streak 3-4 ครั้ง (ปลอดภัยที่สุด)

### Strategy ที่เสี่ยงมาก (Max Streak > 3):
- **MWP-20, MWP-25, MWP-27, MWP-30**: Max streak 6-17 ครั้ง

### เงื่อนไข:
- **เลือก strategy ที่ปลอดภัย**
- **หลีกเลี่ยง strategy ที่เสี่ยง**

### ใช้เมื่อไหร่:
- เลือก strategy ที่มี max streak ≤ 3
- หลีกเลี่ยง strategy ที่มี max streak > 3

---

## 10. LOOKBACK PERFORMANCE PATTERN (สัญญาณ reversal)

### สิ่งที่พบ:
- **10min**: Low Performance = 81.0% win rate (สัญญาณ reversal!)
- **30min**: High Performance = 53.9% win rate
- **60min**: Low Performance = 69.2% win rate (สัญญาณ reversal!)

### เงื่อนไข:
- **เมื่อ performance ต่ำใน 12 ชั่วโมงที่ผ่านมา** = มีโอกาสชนะสูง (reversal)
- **เมื่อ performance สูงใน 12 ชั่วโมงที่ผ่านมา** = มีโอกาสแพ้สูง

### ใช้เมื่อไหร่:
- ตรวจสอบ performance ใน 12 ชั่วโมงที่ผ่านมา
- เลือกเทรดเมื่อ performance ต่ำ (reversal effect)

---

## สรุป Pattern ที่สำคัญที่สุด:

### 1. **Pre-Loss Streak Signal** (ชัดเจน 100%)
- หยุดสัญญาณเดิมทันทีเมื่อแพ้ ≥1 ครั้ง

### 2. **Winning Streak Signal** (ชัดเจน 100%)
- เมื่อชนะ 1-4 ครั้ง = ต่อได้
- เมื่อชนะ 5+ ครั้ง = ระวัง

### 3. **Time Zone Signal** (ชัดเจน 100%)
- เทรดเฉพาะชั่วโมงดี (00:00-06:00, 10:00-11:00, 14:00-16:00, 22:00)
- หลีกเลี่ยงชั่วโมงแย่ (12:00, 17:00-19:00, 03:00)

### 4. **Price Momentum Signal** (ชัดเจน 100%)
- Negative Momentum = 63.0% win rate (reversal effect)
- Low Volatility = 55.5% win rate (ดีที่สุด)

### 5. **Strategy Rotation Signal** (ชัดเจน 100%)
- Range FRAMA3 ดีใน 10min
- MWP-30 ดีใน 30min, 60min
- Strategy หมุนเวียนกัน - ต้องเปลี่ยนตามเวลา

---

## วิธีการใช้ Pattern เหล่านี้:

### Step 1: Screen เบื้องต้น (Behavior Observation)
1. ตรวจสอบเวลา (Time Zone Signal)
2. ตรวจสอบ market condition
3. ตรวจสอบ price momentum
4. ตรวจสอบ performance ใน 12 ชั่วโมงที่ผ่านมา
5. เลือก strategy ที่เหมาะสม

### Step 2: Manage ด้วย Action Logic
1. ตรวจสอบ pre-loss streak
2. ตรวจสอบ winning streak
3. ตรวจสอบ volatility
4. ใช้ action sequence ที่ดี
5. หยุดเมื่อมีสัญญาณอันตราย

### Step 3: เปลี่ยน Strategy
1. เปลี่ยน strategy ทุก 12 ชั่วโมง
2. เปลี่ยน strategy ตาม market condition
3. เปลี่ยน strategy ตาม timeframe

---

## หมายเหตุ:
- Pattern เหล่านี้มาจากการวิเคราะห์ข้อมูล 120 ชั่วโมง
- ข้อมูล 12 ชั่วโมงย้อนหลังมี 99.7% (เกือบจริง)
- ควรทดสอบ pattern เหล่านี้กับข้อมูลใหม่ก่อนใช้จริง
- ควรมี fallback logic เมื่อ pattern ไม่ทำงาน
