-- Seed glide path data from existing Python allocations
-- This imports the existing 5-bucket system (Low, Below-Avg, Moderate, Above-Avg, High)

-- Clear existing data
TRUNCATE TABLE model_glidepath CASCADE;
TRUNCATE TABLE model_portfolio CASCADE;
TRUNCATE TABLE model_holdings CASCADE;

-- Insert glide paths for each risk bucket and age range
-- Data extracted from src/data/glide_path_allocations.py

-- Low Risk Bucket
INSERT INTO model_glidepath (bucket, age_from, age_to, equity_pct, intl_equity_pct, bond_pct, tips_pct, cash_pct) VALUES
('Low', 18, 22, 60.0, 40.0, 23.0, 12.0, 5.0),
('Low', 23, 27, 55.0, 40.0, 28.0, 12.0, 5.0),
('Low', 28, 32, 50.0, 40.0, 33.0, 12.0, 5.0),
('Low', 33, 37, 45.0, 40.0, 38.0, 12.0, 5.0),
('Low', 38, 42, 40.0, 40.0, 43.0, 12.0, 5.0),
('Low', 43, 47, 35.0, 40.0, 52.0, 8.0, 5.0),
('Low', 48, 52, 30.0, 40.0, 57.0, 8.0, 5.0),
('Low', 53, 57, 25.0, 40.0, 62.0, 8.0, 5.0),
('Low', 58, 62, 20.0, 40.0, 68.0, 6.0, 6.0),
('Low', 63, 67, 15.0, 40.0, 73.0, 6.0, 6.0),
('Low', 68, 72, 10.0, 40.0, 78.0, 6.0, 6.0);

-- Below-Avg Risk Bucket
INSERT INTO model_glidepath (bucket, age_from, age_to, equity_pct, intl_equity_pct, bond_pct, tips_pct, cash_pct) VALUES
('Below-Avg', 18, 22, 70.0, 40.0, 14.0, 12.0, 4.0),
('Below-Avg', 23, 27, 65.0, 40.0, 19.0, 12.0, 4.0),
('Below-Avg', 28, 32, 60.0, 40.0, 24.0, 12.0, 4.0),
('Below-Avg', 33, 37, 55.0, 40.0, 29.0, 12.0, 4.0),
('Below-Avg', 38, 42, 50.0, 40.0, 34.0, 12.0, 4.0),
('Below-Avg', 43, 47, 45.0, 40.0, 43.0, 8.0, 4.0),
('Below-Avg', 48, 52, 40.0, 40.0, 48.0, 8.0, 4.0),
('Below-Avg', 53, 57, 35.0, 40.0, 53.0, 8.0, 4.0),
('Below-Avg', 58, 62, 30.0, 40.0, 59.0, 6.0, 5.0),
('Below-Avg', 63, 67, 25.0, 40.0, 64.0, 6.0, 5.0),
('Below-Avg', 68, 72, 20.0, 40.0, 69.0, 6.0, 5.0);

-- Moderate Risk Bucket
INSERT INTO model_glidepath (bucket, age_from, age_to, equity_pct, intl_equity_pct, bond_pct, tips_pct, cash_pct) VALUES
('Moderate', 18, 22, 80.0, 40.0, 5.0, 12.0, 3.0),
('Moderate', 23, 27, 75.0, 40.0, 10.0, 12.0, 3.0),
('Moderate', 28, 32, 70.0, 40.0, 15.0, 12.0, 3.0),
('Moderate', 33, 37, 65.0, 40.0, 20.0, 12.0, 3.0),
('Moderate', 38, 42, 60.0, 40.0, 25.0, 12.0, 3.0),
('Moderate', 43, 47, 55.0, 40.0, 34.0, 8.0, 3.0),
('Moderate', 48, 52, 50.0, 40.0, 39.0, 8.0, 3.0),
('Moderate', 53, 57, 45.0, 40.0, 44.0, 8.0, 3.0),
('Moderate', 58, 62, 40.0, 40.0, 50.0, 6.0, 4.0),
('Moderate', 63, 67, 35.0, 40.0, 55.0, 6.0, 4.0),
('Moderate', 68, 72, 30.0, 40.0, 60.0, 6.0, 4.0);

-- Above-Avg Risk Bucket
INSERT INTO model_glidepath (bucket, age_from, age_to, equity_pct, intl_equity_pct, bond_pct, tips_pct, cash_pct) VALUES
('Above-Avg', 18, 22, 85.0, 45.0, 1.0, 12.0, 2.0),
('Above-Avg', 23, 27, 85.0, 45.0, 1.0, 12.0, 2.0),
('Above-Avg', 28, 32, 80.0, 45.0, 6.0, 12.0, 2.0),
('Above-Avg', 33, 37, 75.0, 45.0, 11.0, 12.0, 2.0),
('Above-Avg', 38, 42, 70.0, 45.0, 16.0, 12.0, 2.0),
('Above-Avg', 43, 47, 65.0, 45.0, 25.0, 8.0, 2.0),
('Above-Avg', 48, 52, 55.0, 45.0, 35.0, 8.0, 2.0),
('Above-Avg', 53, 57, 50.0, 45.0, 40.0, 8.0, 2.0),
('Above-Avg', 58, 62, 45.0, 45.0, 46.0, 6.0, 3.0),
('Above-Avg', 63, 67, 40.0, 45.0, 51.0, 6.0, 3.0),
('Above-Avg', 68, 72, 35.0, 45.0, 56.0, 6.0, 3.0);

-- High Risk Bucket
INSERT INTO model_glidepath (bucket, age_from, age_to, equity_pct, intl_equity_pct, bond_pct, tips_pct, cash_pct) VALUES
('High', 18, 22, 90.0, 50.0, 0.0, 9.0, 1.0),
('High', 23, 27, 90.0, 50.0, 0.0, 9.0, 1.0),
('High', 28, 32, 85.0, 50.0, 2.0, 12.0, 1.0),
('High', 33, 37, 80.0, 50.0, 7.0, 12.0, 1.0),
('High', 38, 42, 75.0, 50.0, 12.0, 12.0, 1.0),
('High', 43, 47, 70.0, 50.0, 21.0, 8.0, 1.0),
('High', 48, 52, 60.0, 50.0, 31.0, 8.0, 1.0),
('High', 53, 57, 55.0, 50.0, 36.0, 8.0, 1.0),
('High', 58, 62, 50.0, 50.0, 42.0, 6.0, 2.0),
('High', 63, 67, 45.0, 50.0, 47.0, 6.0, 2.0),
('High', 68, 72, 40.0, 50.0, 52.0, 6.0, 2.0);

-- Create base model portfolios for each risk bucket
INSERT INTO model_portfolio (name, bucket) VALUES
('Low Risk Portfolio', 'Low'),
('Below Average Risk Portfolio', 'Below-Avg'),
('Moderate Risk Portfolio', 'Moderate'),
('Above Average Risk Portfolio', 'Above-Avg'),
('High Risk Portfolio', 'High');

-- Add holdings for Moderate Risk Portfolio (age 33-37) as an example
-- In production, you'd generate these dynamically based on the glide path
WITH moderate_portfolio AS (
    SELECT id FROM model_portfolio WHERE bucket = 'Moderate' LIMIT 1
)
INSERT INTO model_holdings (model_id, symbol, target_weight)
SELECT 
    mp.id,
    etf.symbol,
    etf.weight
FROM moderate_portfolio mp,
(VALUES
    ('VTI', 46.4),    -- US Total Market (65% * 60% US portion)
    ('VEA', 32.5),    -- International Developed
    ('VSS', 10.8),    -- International Small Cap
    ('VWO', 21.7),    -- Emerging Markets
    ('VBR', 9.3),     -- US Small Value
    ('VUG', 9.3),     -- US Growth
    ('BND', 10.0),    -- US Bonds
    ('BNDX', 6.0),    -- International Bonds
    ('VNQ', 7.2),     -- US Real Estate
    ('VNQI', 4.8),    -- International Real Estate
    ('VTIP', 4.0)     -- Treasury Inflation-Protected
) AS etf(symbol, weight);

-- Insert some sample agreement versions
INSERT INTO agreement_version (kind, version, url, effective_at) VALUES
('terms', '1.0', '/legal/terms-v1.pdf', '2025-01-01'),
('privacy', '1.0', '/legal/privacy-v1.pdf', '2025-01-01'),
('advisory', '1.0', '/legal/advisory-v1.pdf', '2025-01-01'),
('esign', '1.0', '/legal/esign-v1.pdf', '2025-01-01');