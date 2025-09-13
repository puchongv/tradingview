# 🎯 DASHBOARD PATTERNS LIST
## เทพสุด - เรียงตาม Win Rate

**Generated**: 2025-09-14 00:30:01  
**Total Patterns**: 12  
**Min Sample Size**: 50  
**Min Win Rate Deviation**: 5.0%

---

## 🏆 **TOP GOOD PATTERNS (Win Rate > 50%)**

### 🔥 **#1 After WIN** - 78.9%

- **Category**: MOMENTUM
- **Description**: หลังจากชนะ 1 ไม้ → ไม้ต่อไป
- **Win Rate**: **78.9%**
- **Sample Size**: 2,089
- **P-value**: 0.0000
- **Pattern Strength**: 604.5
- **Action**: เพิ่มความมั่นใจ
- **Dashboard Filter**: `previous_trade_result = 'WIN'`

### 💎 **#2 Hour 21:00** - 63.5%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 21:00-21:59
- **Win Rate**: **63.5%**
- **Sample Size**: 181
- **P-value**: 0.0003
- **Pattern Strength**: 24.5
- **Action**: เทรดในชั่วโมงนี้
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 21`

### 💎 **#3 Hour 08:00** - 62.5%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 08:00-08:59
- **Win Rate**: **62.5%**
- **Sample Size**: 136
- **P-value**: 0.0045
- **Pattern Strength**: 17.0
- **Action**: เทรดในชั่วโมงนี้
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 8`

### 💎 **#4 Hour 15:00** - 61.6%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 15:00-15:59
- **Win Rate**: **61.6%**
- **Sample Size**: 151
- **P-value**: 0.0055
- **Pattern Strength**: 17.5
- **Action**: เทรดในชั่วโมงนี้
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 15`

### ⭐ **#5 Tuesday** - 59.9%

- **Category**: TIME_DAY
- **Description**: เทรดในวันTuesday
- **Win Rate**: **59.9%**
- **Sample Size**: 349
- **P-value**: 0.0003
- **Pattern Strength**: 34.5
- **Action**: เทรดในวันTuesday
- **Dashboard Filter**: `EXTRACT(DOW FROM entry_time) = 2`

### ⭐ **#6 Hour 10:00** - 58.9%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 10:00-10:59
- **Win Rate**: **58.9%**
- **Sample Size**: 168
- **P-value**: 0.0250
- **Pattern Strength**: 15.0
- **Action**: เทรดในชั่วโมงนี้
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 10`



---

## ☠️ **TOP BAD PATTERNS (Win Rate < 50%) - AVOID!**

### 💀 **#1 After LOSS** - 21.3%

- **Category**: MOMENTUM
- **Description**: หลังจากแพ้ 1 ไม้ → ไม้ต่อไป
- **Win Rate**: **21.3%** ⚠️
- **Sample Size**: 2,062
- **P-value**: 0.0000
- **Action**: **ระวัง/หลีกเลี่ยง**
- **Dashboard Filter**: `previous_trade_result = 'LOSS'`

### ⚠️ **#2 Hour 19:00** - 36.6%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 19:00-19:59
- **Win Rate**: **36.6%** ⚠️
- **Sample Size**: 235
- **P-value**: 0.0000
- **Action**: **หลีกเลี่ยงชั่วโมงนี้**
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 19`

### ⚠️ **#3 Hour 17:00** - 38.3%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 17:00-17:59
- **Win Rate**: **38.3%** ⚠️
- **Sample Size**: 175
- **P-value**: 0.0024
- **Action**: **หลีกเลี่ยงชั่วโมงนี้**
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 17`

### ⚠️ **#4 Hour 23:00** - 38.6%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 23:00-23:59
- **Win Rate**: **38.6%** ⚠️
- **Sample Size**: 153
- **P-value**: 0.0058
- **Action**: **หลีกเลี่ยงชั่วโมงนี้**
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 23`

### 🔴 **#5 Hour 03:00** - 40.9%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 03:00-03:59
- **Win Rate**: **40.9%** ⚠️
- **Sample Size**: 164
- **P-value**: 0.0232
- **Action**: **หลีกเลี่ยงชั่วโมงนี้**
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 3`

### 🔴 **#6 Hour 12:00** - 41.9%

- **Category**: TIME_HOUR
- **Description**: เทรดในชั่วโมง 12:00-12:59
- **Win Rate**: **41.9%** ⚠️
- **Sample Size**: 179
- **P-value**: 0.0361
- **Action**: **หลีกเลี่ยงชั่วโมงนี้**
- **Dashboard Filter**: `EXTRACT(HOUR FROM entry_time) = 12`



---

## 📊 **DASHBOARD IMPLEMENTATION**

### **📈 Metabase Dashboard Setup:**

**1. Create Pattern Performance Chart:**
```sql
SELECT 
  pattern_name,
  win_rate,
  sample_size,
  category
FROM pattern_analysis_results 
ORDER BY win_rate DESC;
```

**2. Time-based Pattern Visualization:**
```sql
SELECT 
  EXTRACT(HOUR FROM entry_time) as hour,
  COUNT(*) as total_trades,
  AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate
FROM tradingviewdata 
GROUP BY EXTRACT(HOUR FROM entry_time)
ORDER BY hour;
```

**3. Pattern Performance Heatmap:**
```sql
SELECT 
  EXTRACT(DOW FROM entry_time) as day_of_week,
  EXTRACT(HOUR FROM entry_time) as hour,
  COUNT(*) as trades,
  AVG(CASE WHEN result_60min = 'WIN' THEN 1 ELSE 0 END) as win_rate
FROM tradingviewdata 
GROUP BY day_of_week, hour
HAVING COUNT(*) >= 10;
```

**4. Best Pattern Combinations:**
- Tuesday + Hour 21 
- After WIN + Good Hours
- Morning Block + Reliable Signals


---

## 🔥 **PATTERN CATEGORIES SUMMARY**

**MOMENTUM**: 2 patterns, Avg Win Rate: 50.1%
**TIME_HOUR**: 9 patterns, Avg Win Rate: 49.2%
**TIME_DAY**: 1 patterns, Avg Win Rate: 59.9%

