-- Minimal EOD prices to enable portfolio valuation
-- Safe to run multiple times (upserts on conflict)

INSERT INTO mkt_price (symbol, date, close) VALUES
  ('VTI',  '2025-01-02', 260.12),
  ('VEA',  '2025-01-02',  51.42),
  ('VWO',  '2025-01-02',  42.18),
  ('BND',  '2025-01-02',  74.33),
  ('BNDX', '2025-01-02',  49.21),
  ('VNQ',  '2025-01-02',  87.77)
ON CONFLICT (symbol, date) DO UPDATE SET close = EXCLUDED.close;
