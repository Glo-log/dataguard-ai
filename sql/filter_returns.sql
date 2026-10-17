SELECT row_position, invoice_no, country, quantity, unit_price
FROM transactions
WHERE quantity < 0 AND country = :country
ORDER BY row_position
LIMIT 500;
