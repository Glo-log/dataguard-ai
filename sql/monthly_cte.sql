WITH monthly AS (
    SELECT SUBSTR(invoice_date, 1, 7) AS month,
           COUNT(*) AS transaction_lines,
           SUM(quantity * unit_price) AS net_line_value_gbp
    FROM transactions
    GROUP BY SUBSTR(invoice_date, 1, 7)
)
SELECT month, transaction_lines, ROUND(net_line_value_gbp, 2) AS net_line_value_gbp
FROM monthly
ORDER BY month;
