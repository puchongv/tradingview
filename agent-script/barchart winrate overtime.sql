-- Metabase param (optional):
-- {{interval_target}} (Text) -> '10min' | '30min' | '60min'

WITH base AS (
	SELECT strategy, action, '10min'::text AS interval_label, result_10min AS result_selected
	FROM public.tradingviewdata
	UNION ALL
	SELECT strategy, action, '30min'::text AS interval_label, result_30min AS result_selected
	FROM public.tradingviewdata
	UNION ALL
	SELECT strategy, action, '60min'::text AS interval_label, result_60min AS result_selected
	FROM public.tradingviewdata
),
filtered AS (
	SELECT *
	FROM base
	WHERE result_selected IN ('WIN','LOSE')
	[[AND interval_label = {{interval_target}} ]]
),
agg AS (
	SELECT
		(strategy || ' - ' || action) AS strategy_action,
		COUNT(*)                                      AS total_trades,
		COUNT(*) FILTER (WHERE result_selected='WIN') AS wins,
		COUNT(*) FILTER (WHERE result_selected='LOSE') AS losses
	FROM filtered
	GROUP BY 1
)
SELECT
	strategy_action,
	ROUND(100.0 * wins::numeric / NULLIF(total_trades,0), 1) AS win_rate_pct,
	total_trades,
	wins,
	losses,
	ROUND(100.0 * total_trades::numeric / NULLIF(MAX(total_trades) OVER (),0), 1) AS volume_norm_pct
FROM agg
ORDER BY win_rate_pct DESC NULLS LAST;