-- Get Average Trading Volume Per Sto
SELECT symbol, AVG(volume) AS avg_volume
FROM stock_data_table
GROUP BY symbol;