CREATE TABLE users (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	email VARCHAR(255) NOT NULL UNIQUE,
	phone_number VARCHAR(20) NOT NULL UNIQUE,
	role VARCHAR(15) NOT NULL CHECK (role IN ('Candidate', 'Employer', 'Admin')),
	password VARCHAR(255) NOT NULL,
	is_active BOOLEAN DEFAULT TRUE,
	is_staff BOOLEAN DEFAULT FALSE,
	is_superuser BOOLEAN DEFAULT FALSE,
	last_login TIMESTAMP NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies(	
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	description TEXT,
	website VARCHAR(255),
	industry VARCHAR(100),
	location VARCHAR(255),
	size VARCHAR(30),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	first_name VARCHAR(50),
	last_name VARCHAR(50),
	bio TEXT,
	experience_level VARCHAR CHECK (experience_level IN ('Intern', 'Entry level', 'Junior', 'Mid level', 'Senior', 'Lead', 'Expert')),

	CONSTRAINT candidates_user_id_unique UNIQUE (user_id)
);

CREATE TABLE employers(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
	first_name VARCHAR(50),
	last_name VARCHAR(50),
	position VARCHAR(100),

	CONSTRAINT employers_user_id_unique UNIQUE (user_id)
);

CREATE TABLE job_offers(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
	employer_id BIGINT REFERENCES employers(id) ON DELETE SET NULL,
	title VARCHAR(255) NOT NULL,
	description TEXT,
	requirements TEXT,
	responsibilities TEXT,
	location VARCHAR(255) NOT NULL,
	salary_min INTEGER NOT NULL,
	salary_max INTEGER NOT NULL,
	employment_type VARCHAR NOT NULL CHECK (employment_type IN ('Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship', 'Seasonal', 'Volunteer')),
	experience_level VARCHAR NOT NULL CHECK (experience_level IN ('Intern', 'Entry level', 'Junior', 'Mid level', 'Senior', 'Lead', 'Expert')),
	contract_type VARCHAR NOT NULL CHECK (contract_type IN ('B2b', 'Employment contract', 'Contract of mandate', 'Contract for specific work')),
	work_mode VARCHAR NOT NULL CHECK (work_mode IN ('Remote', 'Hybrid', 'Onsite')),
	status VARCHAR NOT NULL CHECK (status IN ('Draft', 'Active', 'Closed', 'Expired')),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	expires_at TIMESTAMP NOT NULL,

	CONSTRAINT salary_min_pos CHECK (salary_min >= 0),
	CONSTRAINT salary_max_pos CHECK (salary_max >= salary_min),
	CONSTRAINT expires_after_creation CHECK (expires_at > created_at)
);

CREATE TABLE cvs(
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE,
	file_url VARCHAR(500) NOT NULL,
	file_name VARCHAR(255) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE applications(
	job_offer_id BIGINT REFERENCES job_offers(id) ON DELETE CASCADE,
	candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE,
	cv_id BIGINT REFERENCES cvs(id) ON DELETE CASCADE,
	status VARCHAR NOT NULL CHECK (status IN ('Sent', 'Reviewed', 'Rejected', 'Accepted')),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT NULL,

	PRIMARY KEY (job_offer_id, candidate_id, cv_id)
);

CREATE TABLE saved_jobs(
	candidate_id BIGINT REFERENCES candidates(id) ON DELETE CASCADE, 
	job_offer_id BIGINT REFERENCES job_offers(id) ON DELETE CASCADE,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (candidate_id, job_offer_id)
);