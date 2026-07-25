CREATE INDEX IF NOT EXISTS idx_companies_name
ON companies (name);

CREATE INDEX IF NOT EXISTS idx_job_offers_title
ON job_offers (title);

CREATE INDEX IF NOT EXISTS idx_job_offers_status_created_at
ON job_offers (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_job_offers_experience_level
ON job_offers (experience_level);

CREATE INDEX IF NOT EXISTS idx_applications_offer_candidate_updated
ON applications (job_offer_id, candidate_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_applications_candidate_offer_created
ON applications (candidate_id, job_offer_id, created_at DESC);