# วิเคราะห์ความแตกต่าง: Python vs SQL Views

## 📁 ไฟล์ที่เปรียบเทียบ
1. **Python:** `momentum_simulation_v2_debug.py` (Test 021)
2. **SQL FIXED:** `strategy_acceleration_score_FIXED.sql`
3. **SQL Aligned:** `strategy_acceleration_score_aligned.sql`

---

## 🔍 เปรียบเทียบทีละขั้นตอน

### 1️⃣ Data Fetching (ดึงข้อมูล)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Query** | `entry_time >= start_date AND entry_time < end_date` | `entry_time >= NOW() - INTERVAL '6 hours'` | `entry_time >= (window start)` |
| **Lookback** | ❌ ไม่มี (look-ahead bias!) | ✅ 6 hours | ✅ 6 hours (generate_series) |
| **Time Window** | Static (user-defined) | Dynamic (last 6h) | Dynamic (last 6h) |
| **Logic Match** | - | ⚠️ Fixed window | ✅ Exact window calculation |

**💡 ข้อแตกต่างสำคัญ:**
- Python Test 021 **ไม่มี lookback** → มีปัญหา look-ahead bias ในช่วงแรก
- SQL FIXED ใช้ `NOW() - 6h` → ถูกต้อง
- SQL Aligned ใช้ `generate_series` → แม่นยำที่สุด

---

### 2️⃣ Cumulative PNL Calculation (คำนวน PNL สะสม)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Method** | `df['pnl_value'].cumsum()` | `SUM() OVER (... UNBOUNDED PRECEDING)` | `SUM() OVER (ORDER BY hour)` |
| **Per Strategy** | ✅ Group by strategy_action | ✅ PARTITION BY strategy_action | ✅ PARTITION BY strategy_action |
| **Order** | ✅ By entry_time | ✅ By hour | ✅ By hour |
| **Logic Match** | Baseline | ✅ Same | ✅ Same |

**Python Code:**
```python
df_strat['cumulative_pnl'] = df_strat['pnl_value'].cumsum()
```

**SQL FIXED:**
```sql
SUM(pnl_value) OVER (
    PARTITION BY strategy_action 
    ORDER BY hour 
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

**SQL Aligned:**
```sql
SUM(hourly_change) OVER (
    PARTITION BY strategy_action
    ORDER BY hour
)
```

**💡 ทั้ง 3 แบบ ผลลัพธ์เหมือนกัน ✅**

---

### 3️⃣ Forward Fill Missing Hours (เติมข้อมูลช่วงว่าง)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Method** | `prev_pnl` logic (loop) | `LAST_VALUE()` + CROSS JOIN | `COALESCE(0)` in hourly_series |
| **Strategy** | Forward-fill last value | Forward-fill last value | Fill 0 for missing |
| **Logic Match** | Baseline | ✅ Same | ⚠️ Different (fills 0) |

**Python Code:**
```python
prev_pnl = 0
for hour in all_hours:
    if strategy not in hourly_pnl[hour]:
        hourly_pnl[hour][strategy] = prev_pnl
    else:
        prev_pnl = hourly_pnl[hour][strategy]
```

**SQL FIXED:**
```sql
COALESCE(
    cumulative_pnl,
    LAST_VALUE(cumulative_pnl) OVER (
        PARTITION BY strategy_action 
        ORDER BY hour 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ),
    0
)
```

**SQL Aligned:**
```sql
-- hourly_series fills 0 for missing hours
COALESCE(hc.hourly_change, 0) AS hourly_change
```

**💡 ความแตกต่างสำคัญ:**
- Python & FIXED: **Forward-fill** (เก็บค่าล่าสุด)
- Aligned: **Fill 0** (เติม 0 ในช่วงว่าง)
- **FIXED ตรงกับ Python มากกว่า** ✅

---

### 4️⃣ LAG for P1-P6 (ดึงค่าย้อนหลัง)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Method** | Index-based: `pnls[0-5]` | `LAG(filled_pnl, 0-5)` | `LAG(cumulative_pnl, 0-5)` |
| **Null Handling** | `pnls.append(0)` if out of range | `COALESCE(LAG(...), 0)` | `COALESCE(LAG(...), 0)` |
| **Logic Match** | Baseline | ✅ Same | ✅ Same |

**Python Code:**
```python
pnls = []
for i in range(6):
    lookback_idx = hour_idx - i
    if lookback_idx >= 0:
        pnls.append(hourly_pnl[all_hours[lookback_idx]].get(strategy, 0))
    else:
        pnls.append(0)
```

**SQL FIXED & Aligned (เหมือนกัน):**
```sql
p1 = filled_pnl (current hour)
p2 = COALESCE(LAG(filled_pnl, 1) OVER (...), 0)
p3 = COALESCE(LAG(filled_pnl, 2) OVER (...), 0)
p4 = COALESCE(LAG(filled_pnl, 3) OVER (...), 0)
p5 = COALESCE(LAG(filled_pnl, 4) OVER (...), 0)
p6 = COALESCE(LAG(filled_pnl, 5) OVER (...), 0)
```

**💡 ทั้ง 3 แบบ ผลลัพธ์เหมือนกัน ✅**

---

### 5️⃣ Momentum & Acceleration Score (คำนวนคะแนน)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Formula** | `5*max(m1,0) + 3*max(accel,0)` | `5.0*GREATEST(m1,0) + 3.0*GREATEST(accel,0)` | `5.0*GREATEST(m1,0) + 3.0*GREATEST(accel,0)` |
| **m1** | `p1 - p2` | `p1 - p2` | `p1 - p2` |
| **m2** | `p2 - p3` | `p2 - p3` | `p2 - p3` |
| **acceleration** | `m1 - m2` | `(p1-p2) - (p2-p3)` | `(p1-p2) - (p2-p3)` |
| **Logic Match** | Baseline | ✅ Same | ✅ Same |

**💡 ทั้ง 3 แบบ สูตรเหมือนกันทุกประการ ✅**

---

### 6️⃣ KPI Normalization (ปรับคะแนน)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **KPI** | `mean + stddev` | `AVG() + STDDEV()` | `AVG() + STDDEV_POP()` |
| **Stddev Type** | Sample (`np.std`) | Sample (`STDDEV`) | Population (`STDDEV_POP`) |
| **Null Handling** | Default to 1 if stddev=0 | No special handling | `COALESCE(..., 0)` |
| **Logic Match** | Baseline | ⚠️ Different stddev type | ⚠️ Different stddev type |

**Python Code:**
```python
recent_kpi = np.mean(recent_raws) + np.std(recent_raws) if np.std(recent_raws) > 0 else 1
```

**SQL FIXED:**
```sql
AVG(recent_raw) OVER () + STDDEV(recent_raw) OVER ()
```

**SQL Aligned:**
```sql
AVG(recent_raw) OVER () + COALESCE(STDDEV_POP(recent_raw) OVER (), 0)
```

**💡 ความแตกต่างสำคัญ:**
- Python: `np.std` = **Sample stddev** (ddof=0)
- FIXED: `STDDEV` = **Sample stddev** (N-1)
- Aligned: `STDDEV_POP` = **Population stddev** (N)
- **FIXED ใกล้เคียง Python มากกว่า** ✅

---

### 7️⃣ Latest Hour Selection (เลือกชั่วโมงล่าสุด)

| Aspect | Python Test 021 | SQL FIXED | SQL Aligned |
|--------|-----------------|-----------|-------------|
| **Method** | Loop all hours | `DISTINCT ON` + `ORDER BY DESC` | `DISTINCT ON` + `ORDER BY DESC` |
| **Result** | Calculate for all hours | Return only latest hour | Return only latest hour |
| **Logic Match** | Different purpose | ✅ Correct for VIEW | ✅ Correct for VIEW |

**💡 Python loop ทุกชั่วโมงเพื่อ simulation, SQL return เฉพาะชั่วโมงล่าสุด**

---

## 🎯 สรุปภาพรวม

### ✅ **SQL FIXED (strategy_acceleration_score_FIXED.sql)**

**จุดเด่น:**
- ✅ Forward-fill logic ตรงกับ Python
- ✅ STDDEV (sample) ใกล้เคียง Python
- ✅ ใช้ `LAST_VALUE()` เลียนแบบ `prev_pnl`
- ✅ มี comment อธิบายว่าเหมือน Python

**จุดอ่อน:**
- ⚠️ ซับซ้อน (หลาย CTE)
- ⚠️ CROSS JOIN + LAST_VALUE อาจช้า

**คะแนนความตรงกับ Python: 9/10** 🌟

---

### ✅ **SQL Aligned (strategy_acceleration_score_aligned.sql)**

**จุดเด่น:**
- ✅ ใช้ `generate_series` แม่นยำ
- ✅ Clean และ maintainable
- ✅ มี `COALESCE` ป้องกัน NULL
- ✅ STDDEV_POP แม่นยำทางคณิตศาสตร์

**จุดอ่อน:**
- ⚠️ Fill 0 แทน forward-fill (ต่างจาก Python)
- ⚠️ STDDEV_POP vs STDDEV (ต่างจาก Python)

**คะแนนความตรงกับ Python: 7.5/10** 🌟

---

### ⚠️ **Python Test 021 (momentum_simulation_v2_debug.py)**

**จุดเด่น:**
- ✅ Logic baseline ที่ถูกต้อง
- ✅ Debug mode ละเอียด
- ✅ Forward-fill clear

**จุดอ่อน:**
- ❌ **ไม่มี lookback → Look-ahead bias!**
- ❌ ช่วงแรก P1-P6 = [0,0,0,0,0,0]
- ❌ ควรใช้ Test 027 แทน (มี lookback 3h)

**คะแนน: 6/10** (มีปัญหา look-ahead bias)

---

## 🏆 คำแนะนำ

### ✅ **ใช้ SQL FIXED เป็น Production**

**เหตุผล:**
1. ✅ Logic ตรงกับ Python Test 027 มากที่สุด
2. ✅ Forward-fill ถูกต้อง
3. ✅ มี comment ชัดเจน
4. ✅ Lookback 6 hours ปลอดภัย

### 🔄 **SQL Aligned เป็น Alternative**

**เหตุผล:**
1. ✅ Clean และ maintainable
2. ⚠️ แต่ต่าง logic นิดหน่อย (fill 0)

---

## 📋 ตารางสรุป

| Feature | Python 021 | SQL FIXED | SQL Aligned | Winner |
|---------|------------|-----------|-------------|--------|
| **Lookback** | ❌ ไม่มี | ✅ 6h | ✅ 6h | SQL |
| **Cumulative PNL** | ✅ | ✅ | ✅ | All |
| **Forward Fill** | ✅ prev_pnl | ✅ LAST_VALUE | ❌ Fill 0 | FIXED |
| **LAG P1-P6** | ✅ | ✅ | ✅ | All |
| **Score Formula** | ✅ | ✅ | ✅ | All |
| **STDDEV** | Sample | Sample | Population | FIXED |
| **Code Quality** | Good | Complex | Clean | Aligned |
| **Overall Match** | Baseline | **9/10** | 7.5/10 | **FIXED** |

---

## 🎯 Final Recommendation

**ใช้ `strategy_acceleration_score_FIXED.sql` เป็น Production ครับ!**

เพราะ:
1. ✅ Logic ตรงกับ Python มากที่สุด (9/10)
2. ✅ มี lookback 6 hours (แก้ look-ahead bias)
3. ✅ Forward-fill ถูกต้อง
4. ✅ STDDEV ใกล้เคียง Python

**และควรใช้ Python Test 027 แทน Test 021** (เพราะมี lookback 3h)


