CREATE OR REPLACE FUNCTION check_application_cv() RETURNS TRIGGER AS $$
DECLARE
	candidate_cv BIGINT;
BEGIN 
	SELECT c.candidate_id INTO candidate_cv
		FROM cvs c
		WHERE c.id = NEW.cv_id;

	IF candidate_cv IS DISTINCT FROM NEW.candidate_id
	THEN 
		RAISE EXCEPTION
            'CV with id % does not belong to candidate %',
            NEW.cv_id,
            NEW.candidate_id;
    END IF;

	RETURN NEW;
END $$ LANGUAGE plpgsql;


CREATE TRIGGER application_tg 
BEFORE INSERT ON applications 
FOR EACH ROW 
EXECUTE PROCEDURE check_application_cv();

CREATE OR REPLACE FUNCTION check_employer_company() RETURNS TRIGGER AS $$
DECLARE
	employer_company BIGINT;
BEGIN
	SELECT e.company_id INTO employer_company
		FROM employers e
		WHERE e.id = NEW.employer_id;

	IF employer_company IS DISTINCT FROM NEW.company_id
	THEN 
		RAISE EXCEPTION
            'Employer with id % does not belong to company %',
            NEW.employer_id,
            NEW.company_id;
    END IF;

	RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER offer_tg
BEFORE INSERT OR UPDATE OF employer_id, company_id ON job_offers
FOR EACH ROW
EXECUTE FUNCTION check_employer_company();