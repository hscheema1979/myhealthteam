-- Standardized Patient ID Normalization Pattern
-- Use this pattern consistently across all transformation scripts
-- 
-- This normalization handles:
-- 1. Removes 'ZEN-' prefixes from patient IDs
-- 2. Converts comma-space (', ') to single space (' ')
-- 3. Converts standalone commas (',') to single space (' ')
-- 4. Trims leading/trailing whitespace
-- 5. Handles multiple consecutive spaces by reducing to single space
--
-- Usage: Replace [SOURCE_COLUMN] with the actual column name containing patient ID

-- STANDARD PATIENT ID NORMALIZATION PATTERN:
TRIM(
    REPLACE(
        REPLACE(
            REPLACE(
                TRIM(REPLACE([SOURCE_COLUMN], 'ZEN-', '')),
                ', ',
                ' '
            ),
            ',',
            ' '
        ),
        '  ',
        ' '
    )
) AS patient_id

-- Example usage in transformation scripts:
-- For SOURCE_PSL_TASKS tables:
-- TRIM(
--     REPLACE(
--         REPLACE(
--             REPLACE(
--                 TRIM(REPLACE(t.[Patient Last, First DOB], 'ZEN-', '')),
--                 ', ',
--                 ' '
--             ),
--             ',',
--             ' '
--         ),
--         '  ',
--         ' '
--     )
-- ) AS patient_id

-- For SOURCE_CM_TASKS tables:
-- TRIM(
--     REPLACE(
--         REPLACE(
--             REPLACE(
--                 TRIM(REPLACE(t.[Pt Name], 'ZEN-', '')),
--                 ', ',
--                 ' '
--             ),
--             ',',
--             ' '
--         ),
--         '  ',
--         ' '
--     )
-- ) AS patient_id

-- Test cases this pattern handles:
-- Input: 'ALHUSARI, MOHAMMED 10/20/1959' -> Output: 'ALHUSARI MOHAMMED 10/20/1959'
-- Input: 'ZEN-SMITH, JOHN 01/01/1980' -> Output: 'SMITH JOHN 01/01/1980'
-- Input: 'JONES,MARY 12/25/1975' -> Output: 'JONES MARY 12/25/1975'
-- Input: 'BROWN  DAVID  05/15/1990' -> Output: 'BROWN DAVID 05/15/1990'