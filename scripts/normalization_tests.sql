-- Normalization SQL test harness
-- Creates a small test corpus and validates the standardized patient_id normalization expression.
-- Usage:
--   sqlite3 production.db ".read scripts/normalization_tests.sql"

PRAGMA foreign_keys = OFF;

-- Test corpus
DROP TABLE IF EXISTS normalization_test_cases;
CREATE TABLE normalization_test_cases (
  name_dob_raw TEXT NOT NULL,
  expected_patient_id TEXT NOT NULL
);

INSERT INTO normalization_test_cases (name_dob_raw, expected_patient_id) VALUES
  ('SMITH, JOHN 01/15/1980', 'SMITH JOHN 01/15/1980'),
  ('ZEN-DOE, JANE 03/10/1990', 'DOE JANE 03/10/1990'),
  ('PM-JONES,MARY 12/25/1975', 'JONES MARY 12/25/1975'),
  ('BLESSEDCARE-ALPHA, BOB 06/20/1985', 'ALPHA BOB 06/20/1985'),
  ('3PR BROWN  MIKE 06/20/1985', 'BROWN MIKE 06/20/1985');

-- Canonical normalization expression (derived from src/sql/patient_id_normalization_standard.sql)
WITH normalized AS (
  SELECT
    name_dob_raw,
    expected_patient_id,
    -- Base normalization: strip known prefixes; replace commas with spaces; trim
    TRIM(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(
              REPLACE(
                REPLACE(
                  REPLACE(
                    REPLACE(
                      REPLACE(
                        REPLACE(
                          TRIM(name_dob_raw),
                          'ZEN-', ''
                        ),
                        'PM-', ''
                      ),
                      'ZMN-', ''
                    ),
                    'BLESSEDCARE-', ''
                  ),
                  'BLEESSEDCARE-', ''
                ),
                '3PR-', ''
              ),
              'BLESSEDCARE ', ''
            ),
            'BLEESSEDCARE ', ''
          ),
          '3PR ', ''
        ),
        ', ', ' '
      )
    ) AS base_norm
  FROM normalization_test_cases
), collapsed AS (
  -- Collapse multiple spaces to a single space (apply REPLACE several times)
  SELECT
    name_dob_raw,
    expected_patient_id,
    TRIM(REPLACE(REPLACE(REPLACE(base_norm, '  ', ' '), '  ', ' '), '  ', ' ')) AS normalized_patient_id
  FROM normalized
)
SELECT
  name_dob_raw,
  expected_patient_id,
  normalized_patient_id,
  CASE WHEN normalized_patient_id = expected_patient_id THEN 'OK' ELSE 'MISMATCH' END AS status
FROM collapsed;

-- Summary: count mismatches
SELECT COUNT(*) AS mismatch_count
FROM (
  SELECT CASE WHEN normalized_patient_id = expected_patient_id THEN 0 ELSE 1 END AS is_mismatch
  FROM collapsed
) t
WHERE t.is_mismatch = 1;