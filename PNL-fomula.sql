-- ================== PARAMS (ปรับตรงนี้จุดเดียว) ==================
WITH params AS (
  SELECT
    3::int AS hours,  -- ชั่วโมงย้อนหลัง
    0.80::numeric AS payout,           -- อัตราจ่ายเมื่อชนะ (0.80 = 80%)
    250::numeric  AS investment,       -- เงินต่อไม้
    1::numeric    AS martingale,       -- ตัวคูณเวลาทบ (2 = x2)

    -- ===== ตัวกรองหลัก (เปิด/ปิดได้) =====
    true::boolean AS enable_filter,    -- เปิดกรอง = true / ปิดกรอง = false
    60::numeric   AS min_winrate,      -- winrate ขั้นต่ำ (%)
    3::int        AS min_signals,      -- จำนวนสัญญาณขั้นต่ำ

    -- ===== ฟิลเตอร์ตามข้อจำกัด Binance =====
    true::boolean AS enable_loss_cap,  -- เปิด/ปิดกรองตามสตรีคแพ้
    3::int        AS max_loss_allowed, -- อนุญาตสตรีคแพ้ยาวสุด (แนะนำ <=3)

    -- ===== ฟิลเตอร์เลือก horizon เดียว =====
    true::boolean AS enable_horizon_lock, -- เปิด/ปิดล็อก horizon เดียว
    '10min'::text AS horizon_lock_value   -- ค่า horizon ที่ต้องการ (เช่น '10min')
),

-- ================== PIPELINE ดึงผลและคำนวณสตรีค ==================
raw AS (
  SELECT
    strategy, action, entry_time,
    result_10min, result_30min, result_60min
  FROM tradingviewdata, params
  WHERE entry_time >= NOW() - (params.hours || ' hours')::interval
),
long AS (
  SELECT strategy, action, entry_time, '10min' AS horizon, result_10min AS result
  FROM raw WHERE result_10min IN ('WIN','LOSE')
  UNION ALL
  SELECT strategy, action, entry_time, '30min', result_30min
  FROM raw WHERE result_30min IN ('WIN','LOSE')
  UNION ALL
  SELECT strategy, action, entry_time, '60min', result_60min
  FROM raw WHERE result_60min IN ('WIN','LOSE')
),
ordered AS (
  SELECT
    strategy, action, horizon, entry_time, result,
    LAG(result) OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS prev_result
  FROM long
),
islands AS (
  SELECT
    strategy, action, horizon, entry_time, result,
    SUM(CASE WHEN prev_result IS DISTINCT FROM result THEN 1 ELSE 0 END)
      OVER (PARTITION BY strategy, action, horizon ORDER BY entry_time) AS grp_id
  FROM ordered
),
runs AS (
  SELECT
    strategy, action, horizon, entry_time, result, grp_id,
    COUNT(*) OVER (PARTITION BY strategy, action, horizon, grp_id) AS run_len
  FROM islands
),
latest AS (
  SELECT DISTINCT ON (strategy, action, horizon)
    strategy, action, horizon, entry_time, result, grp_id, run_len
  FROM runs
  ORDER BY strategy, action, horizon, entry_time DESC
),
agg AS (
  SELECT
    strategy, action, horizon,
    COUNT(*)                                                   AS total_signals,
    SUM( (result='WIN')::int )                                 AS wins,
    ROUND(100.0*SUM( (result='WIN')::int )/NULLIF(COUNT(*),0),2) AS winrate_pct,
    COALESCE(MAX(CASE WHEN result='WIN'  THEN run_len END),0)  AS max_win_streak,
    COALESCE(MAX(CASE WHEN result='LOSE' THEN run_len END),0)  AS max_loss_streak
  FROM runs
  GROUP BY strategy, action, horizon
),

-- ================== FINAL (คำนวณ PnL) ==================
final AS (
SELECT
  a.strategy,
  a.action,
  a.horizon,
  a.total_signals,
  a.wins,
  (a.total_signals - a.wins) AS losses,
  a.winrate_pct,
  a.max_win_streak,
  a.max_loss_streak,
  l.result  AS current_result,
  l.run_len AS current_streak_len,

  /* 1) FLAT PnL (ไม่ทบ) */
  (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment AS pnl_flat,

  /* 2) BEST-CASE (คง L-run ยาว k อย่างน้อย 1 ก้อน ถ้า L>=k; ที่เหลือจับคู่ WL ทันที) */
  CASE
    WHEN params.martingale <= 1 THEN
      (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment
    ELSE
      (
        WITH consts AS (
          SELECT
            params.payout::numeric     AS p,
            params.investment::numeric AS I,
            params.martingale::numeric AS m,
            a.wins::int                AS W,
            (a.total_signals - a.wins)::int AS L,
            GREATEST(a.max_loss_streak, 0)::int AS k
        ),
        geoms AS (
          SELECT *,
            (p*m - 1) * I AS net1, -- กำไรต่อ 1 คู่ WL
            (p*I*POWER(m, k) - I * CASE WHEN m<>1 THEN (POWER(m,k)-1)/(m-1) ELSE k END) AS netk
          FROM consts
        )
        SELECT
          CASE
            WHEN k > 0 AND L >= k AND W >= 1 THEN
              /* (L - k) คู่ WL + 1 ก้อน k + W เดี่ยวที่เหลือ */
              (L - k) * net1
              + netk
              + GREATEST(W - (L - k) - 1, 0) * p * I
            ELSE
              /* ไม่มี k หรือ L < k → จับคู่ WL ให้หมด */
              LEAST(W, L) * net1 + GREATEST(W - L, 0) * p * I
          END
        FROM geoms
      )
  END AS pnl_best,

  /* 3) WORST-CASE (เลวสุดจริง: เคลียร์ r ถ้าจำเป็น, กันท้ายเป็นก้อน k ไม่เคลียร์, W ที่เหลือเป็นชนะเดี่ยว) */
  CASE
    WHEN params.martingale <= 1 THEN
      (params.payout * a.wins - (a.total_signals - a.wins)) * params.investment
    ELSE
      (
        WITH consts AS (
          SELECT
            params.payout::numeric     AS p,
            params.investment::numeric AS I,
            params.martingale::numeric AS m,
            a.wins::int                AS W,
            (a.total_signals - a.wins)::int AS L,
            GREATEST(a.max_loss_streak, 1)::int AS k
        ),
        derived AS (
          SELECT *,
            (L % k) AS r,
            CASE WHEN m <> 1 THEN (POWER(m, k) - 1) / (m - 1) ELSE k END AS gk,
            CASE WHEN m <> 1 THEN (POWER(m, (L % k)) - 1) / (m - 1) ELSE (L % k) END AS gr
          FROM consts
        ),
        step1 AS (  -- เคลียร์ก้อน r ก่อน (ถ้า L-r >= k และมี W)
          SELECT *,
            CASE WHEN r > 0 AND W > 0 AND (L - r) >= k THEN 1 ELSE 0 END AS clr_r
          FROM derived
        ),
        step2 AS (
          SELECT *,
            (W - clr_r)            AS W1,
            (L - clr_r * r)        AS L1,
            (p*I*POWER(m, r) - I*gr) AS net_r_val,
            (p*I*POWER(m, k) - I*gk) AS net_k_val
          FROM step1
        ),
        step3 AS (  -- กันท้ายเป็นก้อน tail_t (k ถ้าไหว ไม่งั้น L1 ทั้งหมด)
          SELECT *,
            CASE WHEN L1 >= k THEN k ELSE L1 END AS tail_t
          FROM step2
        ),
        step4 AS (
          SELECT *,
            CASE WHEN m <> 1 THEN (POWER(m, tail_t) - 1)/(m - 1) ELSE tail_t END AS gtail
          FROM step3
        ),
        step5 AS (
          SELECT *,
            - I*gtail AS tail_loss,
            (L1 - tail_t) AS L2
          FROM step4
        ),
        step6 AS (
          SELECT *,
            FLOOR(L2::numeric / NULLIF(k,0))::int AS full_k_blocks
          FROM step5
        ),
        step7 AS (
          SELECT *,
            LEAST(W1, full_k_blocks) AS c
          FROM step6
        ),
        step8 AS (
          SELECT *,
            c * net_k_val    AS net_k_total,
            (W1 - c)         AS W2
          FROM step7
        )
        SELECT
          (CASE WHEN clr_r = 1 THEN net_r_val ELSE 0 END)   -- เคลียร์ r ถ้าเลือกทำ
          + tail_loss                                       -- แพ้ก้อนท้าย (ไม่เคลียร์)
          + net_k_total                                     -- เคลียร์ก้อน k ที่ทำได้
          + (W2 * p * I)                                    -- ชนะเดี่ยวที่เหลือ
        FROM step8
      )
  END AS pnl_worst
FROM agg a
LEFT JOIN latest l
  ON l.strategy=a.strategy AND l.action=a.action AND l.horizon=a.horizon
CROSS JOIN params
WHERE
  (NOT params.enable_filter)
  OR (
       a.winrate_pct >= params.min_winrate
       AND a.total_signals >= params.min_signals
       AND (NOT params.enable_loss_cap OR a.max_loss_streak <= params.max_loss_allowed)
       AND (NOT params.enable_horizon_lock OR a.horizon = params.horizon_lock_value)
     )
)

-- ================== SELECT สุดท้าย ==================
SELECT
  final.*,
  /* Performance: (Best + Worst) / 2 */
  (final.pnl_best + final.pnl_worst) / 2.0 AS pnl_performance
FROM final
ORDER BY pnl_performance DESC, final.winrate_pct DESC limit {{ $('Position Param').item.json['Rank Limit'] }};
--ORDER BY pnl_performance ASC, final.winrate_pct DESC;