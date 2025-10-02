# Codex Playbook System v1.0

## 1. Objective
วิเคราะห์สัญญาณจาก `public.tradingviewdata` (interval 10 นาที) เพื่อตัดสินใจเลือกสัญญาณที่มี Momentum + Stability สูงสุด พร้อมควบคุมความเสี่ยงตามกติกา Binance Event Contract (ลงทุนสูงสุด $250/ไม้, เปิดพร้อมกัน ≤5 ไม้, ปิดเมื่อครบ 10 นาที) ด้วยทุนเริ่ม $2,000

## 2. Data & Prerequisites
- ตาราง `public.tradingviewdata`
  - คอลัมน์ที่ใช้: `strategy`, `action`, `entry_time`, `result_10min`
  - แปลง `entry_time` เป็น UTC timezone-naive ก่อนคำนวณ
  - แปลงผลลัพธ์เป็น "unit": `WIN → +0.8`, `LOSE → -1.0`
- ต้องดึงข้อมูลย้อนหลังอย่างน้อย 1 วันเพื่อให้ครบหน้าต่างการคำนวณ
- ระบบคำนวณใหม่ทุกชั่วโมง (00 นาทีของทุกชั่วโมง)

## 3. Rolling Metrics
สำหรับทุกสัญญาณ `(strategy, action)` คำนวณค่าต่อไปนี้จากผลเทรดย้อนหลัง 3 หน้าต่าง

| Window | ช่วงเวลา | ขั้นต่ำต่อสัญญาณ |
| --- | --- | --- |
| 1 ชั่วโมง (1h) | 60 นาทีล่าสุด | ≥ 3 เทรด |
| 3 ชั่วโมง (3h) | 180 นาทีล่าสุด | ≥ 6 เทรด |
| 1 วัน (1d) | 24 ชั่วโมงล่าสุด | ≥ 15 เทรด |

ค่าสถิติในแต่ละหน้าต่าง
- `avg_unit_window` : ค่าเฉลี่ยหน่วยกำไร/เทรด
- `total_units_window` : ผลรวมหน่วยกำไร
- `std_unit_1h` : ส่วนเบี่ยงเบนมาตรฐานใน 1 ชั่วโมง (ถ้า < 2 เทรด → 0)
- `samples_window` : จำนวนเทรดในหน้าต่าง
- `loss_streak_window` : ความยาวแพ้ติดสูงสุดในหน้าต่าง (จากผล WIN/LOSE)
- `drawdown_1d` : Maximum drawdown ของ cumulative sum ภายใน 1 วัน
- `momentum_delta = avg_unit_1h – avg_unit_3h`
- `day_delta = avg_unit_3h – avg_unit_1d`

## 4. Scoring
ให้คะแนน 0–10 โดย normalize ตัวแปรแต่ละตัวด้วย percentile rank แล้วนำมาคิดน้ำหนัก

```
Performance = 0.6 * pct(avg_unit_1d) + 0.4 * pct(total_units_1d)
Momentum    = 0.5 * pct(avg_unit_1h) + 0.3 * pct(momentum_delta) + 0.2 * pct(day_delta)
Stability   = 0.5 * (1 - pct(std_unit_1h))
            + 0.3 * (1 - pct(loss_streak_1h))
            + 0.2 * pct(samples_1d)
score_raw   = 0.4 * Performance + 0.4 * Momentum + 0.2 * Stability
score       = clip(score_raw * 10, 0, 10)
```
เมื่อข้อมูลน้อย (ทุกค่าคงที่) จะให้ percentile = 0.5 เพื่อลด bias

## 5. Stake & Position Rules
- Stake mapping
  - `score ≥ 8` → $250
  - `6 ≤ score < 8` → $100
  - `4 ≤ score < 6` → $10
  - `score < 4` → งดเข้า
- กำหนดตำแหน่งพร้อมกันต่อสัญญาณ
  - `score ≥ 10` → สูงสุด 3 ไม้
  - `8 ≤ score < 10` → 2 ไม้
  - `6 ≤ score < 8` → 1 ไม้
  - อื่น ๆ → 0–1 ไม้ ตาม stake
- ข้อจำกัดความเสี่ยง
  - `signal_loss_streak >= 4` → งดเข้า (จนชนะใหม่)
  - `global_loss_streak >= 12` → งดเข้าเรื่อย ๆ จนกว่าชนะ
  - `daily_realized <= -600` (ต่อวัน) → งดเข้า, รอ reset
  - Cooldown 15 นาที หลัง loss ของสัญญาณเดียวกัน
  - เปิดพร้อมกันทั้งระบบ ≤ 5 ไม้

## 6. Workflow (พร้อมต่อ n8n)
1. **Data Refresh (ทุกชั่วโมง)**
   - คิวรีข้อมูลจนถึงเวลาปัจจุบัน
   - คำนวณ rolling metrics + score ตามสูตรด้านบน
   - บันทึก score table สำหรับการ lookup เมื่อมีสัญญาณเข้าใหม่

2. **Signal Handling (ทุกครั้งที่ได้รับ TradingView webhook)**
   - ตรวจสอบข้อจำกัดระบบ (daily stop, global loss streak, cash, max positions)
   - Lookup score ของสัญญาณจากตารางล่าสุด
   - ใช้ stake mapping + ตรวจ loss streak ของสัญญาณนั้น
   - ถ้าอนุญาต → เปิด position (reserve cash, log entry)

3. **Position Exit (ครบ 10 นาที)**
   - ปิด position, คำนวณ PnL (WIN → +stake*0.8, LOSE → -stake)
   - อัปเดต equity, cash, daily pnl, loss streak, global loss streak
   - บันทึก log

## 7. Simulation Engine
สคริปต์ `python` (ดูผลใน `report/codex_playbook_backtest_summary.md`) ทำงานดังนี้
- ดึงข้อมูล 1–20 ก.ย. 2025 จัดเรียงตามเวลา
- สร้าง event (entry/exit) ทุก 10 นาที, คำนวณ score ใหม่ทุกชั่วโมง
- ใช้กฎ stake & risk ข้างต้น, เปิด/ปิด position, อัปเดต state, log ไม้
- ผลลัพธ์สรุป (ทุน $2,000):
  - Equity สิ้นสุด $2,334 → PnL +$334
  - เทรด 41 ไม้ (ชนะ 25, แพ้ 16, win rate ~60.98%)
  - Max drawdown $164
  - รายละเอียดรายวันดูที่ `report/codex_playbook_backtest_summary.md`
  - รายละเอียดไม้ทั้งหมดใน `report/codex_playbook_backtest.csv`

## 8. Deployment Notes
- โมดูลคำนวณ score สามารถทำเป็น SQL (ใช้ window function) หรือ Python scheduler ก็ได้
- ควรทำ endpoint/ webhook ใน n8n ที่เรียกใช้ score ล่าสุดและดำเนินการเปิด order เมื่อ TradingView ส่งสัญญาณ
- เก็บ state ความเสี่ยง (loss streak, daily pnl, cash) ไว้ใน storage (database หรือ workflow variables)
- ก่อนนำไปใช้จริงควร backtest ช่วงเพิ่มเติม + ปรับพารามิเตอร์เพื่อให้ผลลัพธ์เหมาะกับตลาดปัจจุบัน
