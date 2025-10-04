.headers on
.mode table

SELECT patient_id, first_name, last_name, date_of_birth 
FROM patients 
WHERE first_name LIKE '%TEST%' OR last_name LIKE '%TEST%' OR first_name LIKE '%Test%' OR last_name LIKE '%Test%';