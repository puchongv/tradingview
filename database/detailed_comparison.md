# 🔍 วิเคราะห์ละเอียด: Test 022 vs SQL FIXED vs SQL Aligned

## ❓ คำถามสำคัญ

**GPT-5 บอกว่า SQL Aligned เหมือนกว่า - จริงหรือไม่?**

---

## 🧪 Test 022 Python Logic (Baseline)

```python
# Step 1: Calculate cumulative PNL per strategy
df_strat = df[df['strategy_action'] == strategy].copy()
df_strat['cumulative_pnl'] = df_strat['pnl_value'].cumsum()

# Step 2: Group by hour, get last value
for hour, group in df_strat.groupby('hour'):
    hourly_pnl[hour][strategy] = group['cumulative_pnl'].iloc[-1]

# Step 3: Forward fill missing hours
prev_pnl = 0
for hour in all_hours:
    if strategy not in hourly_pnl[hour]:
        hourly_pnl[hour][strategy] = prev_pnl  # Keep last value
    else:
        prev_pnl = hourly_pnl[hour][strategy]
```

**Key Points:**
- ✅ Cumulative PNL from all trades
- ✅ Use `all_hours` (hours where ANY strategy has data)
- ✅ Forward-fill with last known value

---

## 🔴 SQL FIXED - มีปัญหาร้ายแรง!

### ปัญหาที่ 1: Hour Window ไม่ครบ

```sql
-- CROSS JOIN ใช้ hour ที่มีใน data เท่านั้น!
FROM (SELECT DISTINCT strategy_action FROM hourly_pnl) s
CROSS JOIN (SELECT DISTINCT hour FROM hourly_pnl) h  -- ❌ ไม่ครบทุกชั่วโมง!
```

**ปัญหา:**
- ถ้า strategy A มี data แค่ hour 1, 3, 5
- ถ้า strategy B มี data แค่ hour 2, 4, 6
- `DISTINCT hour FROM hourly_pnl` จะได้ 1,2,3,4,5,6
- **แต่ไม่ได้สร้าง COMPLETE series เช่น 0,1,2,3,4,5,6!**

### ปัญหาที่ 2: LAST_VALUE ใช้ไม่ถูก

```sql
LAST_VALUE(cumulative_pnl) OVER (
    PARTITION BY strategy_action 
    ORDER BY hour 
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

**ปัญหา:**
- `LAST_VALUE` กับ `UNBOUNDED PRECEDING AND CURRENT ROW` 
- จะ return ค่าปัจจุบัน (CURRENT ROW) ไม่ใช่ค่าก่อนหน้า!
- **ควรใช้ `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`**

### ปัญหาที่ 3: Cumulative PNL Calculation

```sql
cumulative_pnl AS (
    SELECT 
        strategy_action, hour,
        SUM(pnl_value) OVER (
            PARTITION BY strategy_action 
            ORDER BY hour 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as cumulative_pnl
    FROM hourly_trades  -- ❌ มีหลาย row ต่อ hour!
)
```

**ปัญหา:**
- `hourly_trades` มี multiple rows per hour (แต่ละ trade)
- SUM OVER จะสะสมทุก row
- ทำให้ได้ cumulative_pnl หลายค่าต่อ hour
- **ต้อง GROUP BY hour ก่อน!**

---

## 🟢 SQL Aligned - ถูกต้อง!

### 1. สร้าง Complete Hour Window

```sql
window_hours AS (
    SELECT generate_series(
        (SELECT end_hour FROM params) - INTERVAL '5 hours',
        (SELECT end_hour FROM params),
        INTERVAL '1 hour'
    ) AS hour  -- ✅ สร้างชั่วโมงครบ 0,1,2,3,4,5!
)
```

### 2. คำนวน Hourly Change ก่อน

```sql
hourly_changes AS (
    SELECT strategy_action, hour, 
           SUM(pnl_value) AS hourly_change  -- ✅ SUM ต่อชั่วโมง
    FROM raw_trades
    GROUP BY strategy_action, hour  -- ✅ GROUP BY ก่อน!
)
```

### 3. Fill Missing Hours with 0

```sql
hourly_series AS (
    SELECT sh.strategy_action, sh.hour,
           COALESCE(hc.hourly_change, 0) AS hourly_change  -- ✅ Fill 0
    FROM strategy_hours sh
    LEFT JOIN hourly_changes hc
           ON sh.strategy_action = hc.strategy_action
          AND sh.hour = hc.hour
)
```

### 4. Cumulative Sum

```sql
cumulative AS (
    SELECT strategy_action, hour,
           SUM(hourly_change) OVER (
               PARTITION BY strategy_action
               ORDER BY hour
           ) AS cumulative_pnl  -- ✅ Cumsum จาก hourly_change
    FROM hourly_series
)
```

---

## 📊 เปรียบเทียบทีละขั้นตอน

| Step | Python Test 022 | SQL FIXED | SQL Aligned |
|------|-----------------|-----------|-------------|
| **1. Hour Window** | `all_hours` (hours with data) | ❌ `DISTINCT hour` (incomplete) | ✅ `generate_series` (complete) |
| **2. PNL Aggregation** | `GROUP BY hour` implicit | ❌ No GROUP BY before SUM OVER | ✅ `GROUP BY` before cumsum |
| **3. Missing Hours** | Forward-fill with prev_pnl | ❌ `LAST_VALUE` ใช้ผิด | ✅ Fill 0 then cumsum |
| **4. Cumulative** | `cumsum()` | ❌ SUM OVER หลาย row | ✅ SUM OVER จาก hourly_change |

---

## 🤔 แต่ Python ก็ Forward-fill ไม่ใช่ Fill 0 นะ?

### ❗ นี่คือจุดสำคัญ!

**Python Test 022:**
```python
# Forward fill กับ all_hours (ชั่วโมงที่มี data)
for hour in all_hours:
    if strategy not in hourly_pnl[hour]:
        hourly_pnl[hour][strategy] = prev_pnl
```

**คำถาม:** `all_hours` คืออะไร?
- `all_hours = sorted(hourly_pnl.keys())`
- **มันคือชั่วโมงที่มี data อย่างน้อย 1 strategy!**
- **ไม่ใช่ทุกชั่วโมงในช่วงเวลา!**

**ตัวอย่าง:**
- ถ้าช่วง 00:00-06:00 แต่มี data แค่ 01:00, 03:00, 05:00
- `all_hours = [01:00, 03:00, 05:00]`
- **ไม่มี 00:00, 02:00, 04:00, 06:00!**

### 🎯 SQL Aligned ทำถูกต้อง!

```sql
window_hours AS (
    SELECT generate_series(...)  -- ครบทุกชั่วโมง 00:00-06:00
)
```

**เมื่อ Fill 0 for missing hours:**
- Hour 00:00: change = 0 → cumsum = 0
- Hour 01:00: change = +200 → cumsum = 200
- Hour 02:00: change = 0 → cumsum = 200  ← เหมือน forward-fill!
- Hour 03:00: change = -50 → cumsum = 150

**ผลลัพธ์ = เหมือน forward-fill!** ✅

---

## 🏆 สรุปขั้นสุดท้าย

### ✅ **SQL Aligned ถูกต้องกว่า!**

**เหตุผล:**
1. ✅ สร้าง complete hour window ด้วย `generate_series`
2. ✅ `GROUP BY hour` ก่อน cumulative sum
3. ✅ Fill 0 for missing hours แล้ว cumsum → ผลลัพธ์เหมือน forward-fill
4. ✅ ไม่มี LAST_VALUE ที่ใช้ผิด
5. ✅ Logic สะอาดและถูกต้อง

### ❌ **SQL FIXED มีปัญหา:**
1. ❌ ไม่ได้สร้าง complete hour series
2. ❌ `LAST_VALUE` ใช้ผิด (ควรใช้ `1 PRECEDING`)
3. ❌ SUM OVER หลาย row ต่อ hour (ไม่ GROUP BY ก่อน)
4. ❌ Logic ซับซ้อนและมีข้อผิดพลาด

---

## 🎯 คำตอบ

**GPT-5 ถูก! SQL Aligned เหมือน Test 022 มากกว่า!** ✅

**แต่ต้องเข้าใจว่า:**
- Fill 0 + Cumsum = Forward-fill (ผลลัพธ์เดียวกัน)
- SQL Aligned ใช้ `generate_series` ทำให้มี complete window
- SQL FIXED มีปัญหา technical หลายจุด

**Recommendation:** ใช้ **SQL Aligned** เป็น Production! 🏆

