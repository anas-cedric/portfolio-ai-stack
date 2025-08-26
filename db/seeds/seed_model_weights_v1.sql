-- Seed model weights for v1 across risk buckets
-- Safe to run multiple times (upserts on conflict)

-- Low risk
INSERT INTO model_weights (model_version, bucket, symbol, weight) VALUES
  ('v1','Low','BND',  0.45),
  ('v1','Low','BNDX', 0.25),
  ('v1','Low','VTI',  0.20),
  ('v1','Low','VEA',  0.05),
  ('v1','Low','VWO',  0.03),
  ('v1','Low','VNQ',  0.02)
ON CONFLICT (model_version, bucket, symbol) DO UPDATE SET weight = EXCLUDED.weight;

-- Below-Avg risk
INSERT INTO model_weights (model_version, bucket, symbol, weight) VALUES
  ('v1','Below-Avg','BND',  0.35),
  ('v1','Below-Avg','BNDX', 0.20),
  ('v1','Below-Avg','VTI',  0.30),
  ('v1','Below-Avg','VEA',  0.08),
  ('v1','Below-Avg','VWO',  0.05),
  ('v1','Below-Avg','VNQ',  0.02)
ON CONFLICT (model_version, bucket, symbol) DO UPDATE SET weight = EXCLUDED.weight;

-- Moderate risk
INSERT INTO model_weights (model_version, bucket, symbol, weight) VALUES
  ('v1','Moderate','BND',  0.25),
  ('v1','Moderate','BNDX', 0.15),
  ('v1','Moderate','VTI',  0.40),
  ('v1','Moderate','VEA',  0.10),
  ('v1','Moderate','VWO',  0.06),
  ('v1','Moderate','VNQ',  0.04)
ON CONFLICT (model_version, bucket, symbol) DO UPDATE SET weight = EXCLUDED.weight;

-- Above-Avg risk
INSERT INTO model_weights (model_version, bucket, symbol, weight) VALUES
  ('v1','Above-Avg','BND',  0.15),
  ('v1','Above-Avg','BNDX', 0.10),
  ('v1','Above-Avg','VTI',  0.50),
  ('v1','Above-Avg','VEA',  0.13),
  ('v1','Above-Avg','VWO',  0.08),
  ('v1','Above-Avg','VNQ',  0.04)
ON CONFLICT (model_version, bucket, symbol) DO UPDATE SET weight = EXCLUDED.weight;

-- High risk
INSERT INTO model_weights (model_version, bucket, symbol, weight) VALUES
  ('v1','High','BND',  0.05),
  ('v1','High','BNDX', 0.05),
  ('v1','High','VTI',  0.60),
  ('v1','High','VEA',  0.15),
  ('v1','High','VWO',  0.10),
  ('v1','High','VNQ',  0.05)
ON CONFLICT (model_version, bucket, symbol) DO UPDATE SET weight = EXCLUDED.weight;
