WITH monthly AS (
    SELECT SUBSTR(invoice_date, 1, 7) AS month,
           SUM(quantity * unit_price) AS net_line_value_gbp
    FROM transactions
    GROUP BY SUBSTR(invoice_date, 1, 7)
)
SELECT month,
       ROUND(net_line_value_gbp, 2) AS net_line_value_gbp,
       ROUND(SUM(net_line_value_gbp) OVER (
           ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ), 2) AS cumulative_net_line_value_gbp
FROM monthly
ORDER BY month;
