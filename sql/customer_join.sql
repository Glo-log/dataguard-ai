-- LEFT JOIN retains transactions whose customer identifier is missing.
SELECT t.row_position, t.invoice_no, t.customer_id,
       COALESCE(c.customer_status, 'unknown customer identifier') AS customer_status,
       ROUND(t.quantity * t.unit_price, 2) AS net_line_value_gbp
FROM transactions AS t
LEFT JOIN customers AS c ON t.customer_id = c.customer_id
ORDER BY t.row_position
LIMIT 100;
