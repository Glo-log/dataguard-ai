SELECT row_position, invoice_no, stock_code, country, quantity, unit_price,
       ROUND(quantity * unit_price, 2) AS net_line_value_gbp
FROM transactions
ORDER BY row_position
LIMIT 100;
