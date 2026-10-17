SELECT country, COUNT(*) AS transaction_lines,
       SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END) AS negative_quantity_lines,
       ROUND(SUM(quantity * unit_price), 2) AS net_line_value_gbp
FROM transactions
GROUP BY country
ORDER BY net_line_value_gbp DESC;
