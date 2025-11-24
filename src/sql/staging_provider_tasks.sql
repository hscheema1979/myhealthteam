-- Staging provider tasks: canonical patient_id (LASTNAME FIRSTNAME MM/DD/YYYY)
DROP TABLE IF EXISTS staging.staging_provider_tasks;
CREATE TABLE staging.staging_provider_tasks AS WITH input AS (
  SELECT "Prov" AS provider_code,
    "Patient Last, First DOB" AS patient_name_raw,
    TRIM("Service") AS service,
    TRIM("Coding") AS billing_code,
    "Minutes" AS minutes_raw,
    "DOS" AS DOS
  FROM SOURCE_PROVIDER_TASKS_HISTORY
),
clean AS (
  SELECT provider_code,
    -- strip vendor/facility prefixes but KEEP comma for splitting
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
                          REPLACE(
                            REPLACE(patient_name_raw, 'ZEN-', ''),
                            'PM-',
                            ''
                          ),
                          'ZMN-',
                          ''
                        ),
                        'BlessedCare-',
                        ''
                      ),
                      'BLESSEDCARE-',
                      ''
                    ),
                    'BleessedCare-',
                    ''
                  ),
                  'BLEESSEDCARE-',
                  ''
                ),
                '3PR-',
                ''
              ),
              '3PR -',
              ''
            ),
            'BLESSEDCARE ',
            ''
          ),
          'BLEESSEDCARE ',
          ''
        ),
        '3PR ',
        ''
      )
    ) AS patient_name_clean,
    service,
    billing_code,
    minutes_raw,
    DOS
  FROM input
)
SELECT provider_code,
  patient_name_clean AS patient_name_raw,
  CASE
    WHEN INSTR(patient_name_clean, ',') > 0 THEN -- LASTNAME FIRSTNAME MM/DD/YYYY (uppercase, no internal spaces in names)
    UPPER(
      TRIM(
        SUBSTR(
          patient_name_clean,
          1,
          INSTR(patient_name_clean, ',') - 1
        )
      )
    ) || ' ' || UPPER(
      TRIM(
        REPLACE(
          SUBSTR(
            patient_name_clean,
            INSTR(patient_name_clean, ',') + 1
          ),
          CASE
            WHEN SUBSTR(
              patient_name_clean,
              LENGTH(patient_name_clean) - 9,
              10
            ) GLOB '??/??/????' THEN SUBSTR(
              patient_name_clean,
              LENGTH(patient_name_clean) - 9,
              10
            )
            WHEN SUBSTR(
              patient_name_clean,
              LENGTH(patient_name_clean) - 7,
              8
            ) GLOB '??/??/??' THEN SUBSTR(
              patient_name_clean,
              LENGTH(patient_name_clean) - 7,
              8
            )
            ELSE ''
          END,
          ''
        )
      )
    ) || ' ' || CASE
      WHEN SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 9,
        10
      ) GLOB '??/??/????' THEN SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 9,
        10
      )
      WHEN SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 7,
        8
      ) GLOB '??/??/??' THEN SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 7,
        2
      ) || '/' || SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 4,
        2
      ) || '/20' || SUBSTR(
        patient_name_clean,
        LENGTH(patient_name_clean) - 1,
        2
      )
      ELSE NULL
    END
    ELSE NULL
  END AS patient_id,
  service,
  billing_code,
  minutes_raw,
  CASE
    WHEN DOS GLOB '??/??/????' THEN substr(DOS, 7, 4) || '-' || printf('%02d', CAST(substr(DOS, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(DOS, 4, 2) AS INTEGER))
    WHEN DOS GLOB '??/??/??' THEN '20' || substr(DOS, 7, 2) || '-' || printf('%02d', CAST(substr(DOS, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(DOS, 4, 2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  CASE
    WHEN DOS IS NOT NULL THEN CASE
      WHEN DOS GLOB '??/??/????' THEN substr(DOS, 7, 4) || '_' || printf('%02d', CAST(substr(DOS, 1, 2) AS INTEGER))
      WHEN DOS GLOB '??/??/??' THEN '20' || substr(DOS, 7, 2) || '_' || printf('%02d', CAST(substr(DOS, 1, 2) AS INTEGER))
      ELSE NULL
    END
    ELSE NULL
  END AS year_month
FROM clean;
CREATE INDEX IF NOT EXISTS staging.idx_staging_provider_year_month ON staging_provider_tasks(year_month);
CREATE INDEX IF NOT EXISTS staging.idx_staging_provider_activity_date ON staging_provider_tasks(activity_date);
CREATE INDEX IF NOT EXISTS staging.idx_staging_provider_patient_id ON staging_provider_tasks(patient_id);