-- Krishi Setu Database Schema
-- Generated from SQLAlchemy models

CREATE TABLE farmer_profiles (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	phone VARCHAR(15), 
	aadhaar_hash VARCHAR(64), 
	state VARCHAR(100), 
	district VARCHAR(100), 
	land_holding_acres FLOAT, 
	caste VARCHAR(50), 
	annual_income INTEGER, 
	age INTEGER, 
	gender VARCHAR(20), 
	is_bpl BOOLEAN, 
	has_kisan_credit_card BOOLEAN, 
	primary_crop VARCHAR(100), 
	irrigation_type VARCHAR(50), 
	password_hash VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (phone), 
	UNIQUE (aadhaar_hash)
);

CREATE TABLE jobs (
	id BIGSERIAL NOT NULL, 
	job_type VARCHAR(100) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	payload JSON NOT NULL, 
	attempts INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	last_error TEXT, 
	celery_task_id VARCHAR(255), 
	run_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id)
);

CREATE TABLE ministries (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	name_hindi VARCHAR(255), 
	acronym VARCHAR(50), 
	website_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE schemes (
	id SERIAL NOT NULL, 
	ministry_id INTEGER, 
	name VARCHAR(500) NOT NULL, 
	name_hindi VARCHAR(500), 
	slug VARCHAR(255) NOT NULL, 
	description TEXT, 
	description_hindi TEXT, 
	eligibility_criteria JSON, 
	benefits JSON, 
	application_url VARCHAR(500), 
	source_url VARCHAR(500), 
	search_synonyms JSON, 
	url_hash VARCHAR(64), 
	content_hash VARCHAR(64), 
	is_active BOOLEAN NOT NULL, 
	last_updated_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(ministry_id) REFERENCES ministries (id) ON DELETE SET NULL, 
	UNIQUE (slug)
);

CREATE TABLE search_logs (
	id BIGSERIAL NOT NULL, 
	farmer_id INTEGER, 
	query_raw TEXT NOT NULL, 
	query_normalized TEXT, 
	results_count INTEGER NOT NULL, 
	top_scheme_ids JSON, 
	session_id VARCHAR(255), 
	response_time_ms INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(farmer_id) REFERENCES farmer_profiles (id) ON DELETE SET NULL
);

CREATE TABLE sources (
	id SERIAL NOT NULL, 
	ministry_id INTEGER, 
	name VARCHAR(255) NOT NULL, 
	base_url VARCHAR(500) NOT NULL, 
	format sourceformat NOT NULL, 
	crawl_interval_hours INTEGER NOT NULL, 
	max_depth INTEGER NOT NULL, 
	rate_limit_rps FLOAT NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	respect_robots_txt BOOLEAN NOT NULL, 
	last_crawled_at TIMESTAMP WITH TIME ZONE, 
	next_crawl_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(ministry_id) REFERENCES ministries (id) ON DELETE SET NULL, 
	UNIQUE (base_url)
);

CREATE TABLE crawl_jobs (
	id BIGSERIAL NOT NULL, 
	source_id INTEGER NOT NULL, 
	status crawljobstatus NOT NULL, 
	job_type crawljobtype NOT NULL, 
	urls_discovered INTEGER NOT NULL, 
	urls_crawled INTEGER NOT NULL, 
	schemes_upserted INTEGER NOT NULL, 
	errors_count INTEGER NOT NULL, 
	attempts INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	last_error TEXT, 
	celery_task_id VARCHAR(255), 
	scheduled_at TIMESTAMP WITH TIME ZONE, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_id) REFERENCES sources (id) ON DELETE CASCADE
);

CREATE TABLE eligibility_records (
	id BIGSERIAL NOT NULL, 
	farmer_id INTEGER NOT NULL, 
	scheme_id INTEGER NOT NULL, 
	overall_result eligibilityresult NOT NULL, 
	criteria_results JSON NOT NULL, 
	summary TEXT, 
	checked_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_eligibility_farmer_scheme UNIQUE (farmer_id, scheme_id), 
	FOREIGN KEY(farmer_id) REFERENCES farmer_profiles (id) ON DELETE CASCADE, 
	FOREIGN KEY(scheme_id) REFERENCES schemes (id) ON DELETE CASCADE
);

