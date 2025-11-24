# Staff Code Reference Document

## Table 1: prod_users with Generated Staff Codes

| Full Name             | Email                      | Coordinator Code | Provider Code | Alt Provider Code |
| --------------------- | -------------------------- | ---------------- | ------------- | ----------------- |
| Ethel Antonio         | ethel@myhealthteam.org     | ANTET000         | Antonio, Ethel    | Antonio, Ethel    |
| Harpreet Cheema       | harpreet@myhealthteam.org  | CHEHA000         | Cheema, Harpreet | Cheema, Harpreet  |
| Eden Dabalus          | eden@myhealthteam.org      | DABED000         | Dabalus, Eden    | Dabalus, Eden     |
| Genevieve Davis       | genevieve@myhealthteam.org | DAVGE000         | Davis, Genevieve | Davis, Genevieve  |
| Albert Diaz           | albert@myhealthteam.org    | DIAAL000         | Diaz, Albert     | Diaz, Albert      |
| Jan Estomo            | jan@myhealthteam.org       | ESTJA000         | Estomo, Jan      | Estomo, Jan       |
| Hector Hernandez      | hector@myhealthteam.org    | HERHE000         | Hernandez, Hector| Hernandez, Hector |
| Anisha Jackson        | anisha@myhealthteam.org    | JACAN000         | Jackson, Anisha  | Jackson, Anisha   |
| Jaspreet Kaur         | jaspreet@myhealthteam.org  | KAUJA000         | Kaur, Jaspreet   | Kaur, Jaspreet    |
| Justin Malhotra MD    | admin@myhealthteam.org     | MALJU000         | Malhotra, Justin | Malhotra, Justin  |
| Sherwin Maningas      | sherwin@myhealthteam.org   | MANSH000         | Maningas, Sherwin| Maningas, Sherwin |
| Cindy Mariano         | cindy@myhealthteam.org     | MARCI000         | Mariano, Cindy   | Mariano, Cindy    |
| Dianela Medez         | dianela@myhealthteam.org   | MEDDI000         | Medez, Dianela   | Medez, Dianela    |
| Claudia Melara        | claudia@myhealthteam.org   | MELCL000         | Melara, Claudia  | Melara, Claudia   |
| Angela Otegbulu       | angela@myhealthteam.org    | OTEAN000         | Otegbulu, Angela | Otegbulu, Angela  |
| Jorge Perez           | jorge@myhealthteam.org     | PERJO000         | Perez, Jorge     | Perez, Jorge      |
| Manuel Rios           | manuel@myhealthteam.org    | RIOMA000         | Rios, Manuel     | Rios, Manuel      |
| Bianchi Sanchez       | bianchi@myhealthteam.org   | SANBI000         | Sanchez, Bianchi | Sanchez, Bianchi  |
| Laura Sumpay CC       | laura@myhealthteam.org     | SUMLA000         | Sumpay, Laura    | Sumpay, Laura     |
| Shirley Alter CC      | shirley@myhealthteam.org   | ALTSH000         | Alter, Shirley   | Alter, Shirley    |
| Jose Soberanis        | jose@myhealthteam.org      | SOBJO000         | Soberanis, Jose  | Soberanis, Jose   |
| Andrew Szalas NP      | andrews@myhealthteam.org   | SZAAN000         | Szalas, Andrew   | Szalas, Andrew    |
| Lourdes Villasenor NP | lourdesv@myhealthteam.org  | VILLO000         | Villasenor, Lourdes | Villasenor, Lourdes |

## Table 2: Actual Staff Codes from Source Data

| Staff Code | Source Table              | Type                 | Potential Match         |
| ---------- | ------------------------- | -------------------- | ----------------------- |
| ChaZu000   | coordinator_tasks_history | Coordinator          | No match found          |
| EstJa000   | coordinator_tasks_history | Coordinator          | ✓ Jan Estomo            |
| HerHe000   | coordinator_tasks_history | Coordinator          | ✓ Hector Hernandez      |
| LopJu000   | coordinator_tasks_history | Coordinator          | No match found          |
| LumJa000   | coordinator_tasks_history | Coordinator          | No match found          |
| MalJu000   | coordinator_tasks_history | Coordinator          | ✓ Justin Malhotra MD    |
| MalMe000   | coordinator_tasks_history | Coordinator          | No match found          |
| ManSh000   | coordinator_tasks_history | Coordinator          | ✓ Sherwin Maningas      |
| MarCi000   | coordinator_tasks_history | Coordinator          | ✓ Cindy Mariano         |
| PerJo000   | coordinator_tasks_history | Coordinator          | ✓ Jorge Perez           |
| RioMa000   | coordinator_tasks_history | Coordinator          | ✓ Manuel Rios           |
| RubAn000   | coordinator_tasks_history | Coordinator          | No match found          |
| SanBi000   | coordinator_tasks_history | Coordinator          | ✓ Bianchi Sanchez       |
| SanMa000   | coordinator_tasks_history | Coordinator          | No match found          |
| SanRa000   | coordinator_tasks_history | Coordinator          | No match found          |
| SobJo000   | coordinator_tasks_history | Coordinator          | ✓ Jose Soberanis        |
| SobMa000   | coordinator_tasks_history | Coordinator          | No match found          |
| ZEN-SZA    | coordinator_tasks_history | Provider/Coordinator | ✓ Andrew Szalas NP      |
| ZEN-VIL    | coordinator_tasks_history | Provider/Coordinator | ✓ Lourdes Villasenor NP |
| ZEN-ANE    | provider_tasks_history    | Provider             | ✓ Ethel Antonio         |
| ZEN-DIA    | provider_tasks_history    | Provider             | ✓ Albert Diaz           |
| ZEN-JAA    | provider_tasks_history    | Provider             | ✓ Anisha Jackson        |
| ZEN-KAJ    | provider_tasks_history    | Provider             | ✓ Jaspreet Kaur         |

## Table 3: Code Pattern Analysis

| Pattern               | Example            | Count | Notes                             |
| --------------------- | ------------------ | ----- | --------------------------------- |
| [Last3][First2]000    | EstJa000           | 17    | Standard coordinator pattern      |
| ZEN-[Last3]           | ZEN-DIA            | 4     | Provider pattern, some dual-role  |
| Unmatched Coordinator | ChaZu000, LopJu000 | 7     | Former staff or data entry errors |
| Unmatched Provider    | ZEN-ANE            | 1     | Needs investigation               |

---

## Table 4: Unmatched Staff Codes (No User Found)

### Coordinator Codes

| Staff Code | Source Table              | Type        | Notes                                  |
| ---------- | ------------------------- | ----------- | -------------------------------------- |
| AteDi000   | coordinator_tasks_history | Coordinator | New coordinator found in recent import |
| ChaZu000   | coordinator_tasks_history | Coordinator | Possible former staff member           |
| LopJu000   | coordinator_tasks_history | Coordinator | Possible former staff member           |
| LumJa000   | coordinator_tasks_history | Coordinator | Possible former staff member           |
| SanMa000   | coordinator_tasks_history | Coordinator | Possible former staff member           |
| SanRa000   | coordinator_tasks_history | Coordinator | Possible former staff member           |
| SobMa000   | coordinator_tasks_history | Coordinator | Possible former staff member           |

### Provider Codes

| Staff Code | Source Table           | Type     | Notes                               |
| ---------- | ---------------------- | -------- | ----------------------------------- |
| ZEN-DAG    | provider_tasks_history | Provider | New provider found in recent import |
| ZEN-JAA    | provider_tasks_history | Provider | New provider found in recent import |
| ZEN-KAJ    | provider_tasks_history | Provider | New provider found in recent import |
| ZEN-MEC    | provider_tasks_history | Provider | New provider found in recent import |

**Total Unmatched Codes: 11** (7 Coordinators + 4 Providers)

---

## Summary

- **Total prod_users**: 21 users
- **Coordinator codes in use**: 19 codes
- **Provider codes in use**: 2 codes
- **Total unique staff codes in source data**: 21 codes
- **Matched codes**: 12 codes
- **Unmatched codes**: 9 codes

### Pattern Analysis

- Most coordinator codes follow the [First3LastName][First2FirstName]000 pattern with variations
- Provider codes consistently follow the ZEN-[First3LastName] pattern
- Some codes like ZEN-SZA and ZEN-VIL appear in coordinator data, suggesting dual roles

### Mapping Opportunities

- Several coordinator codes can be mapped to existing prod_users based on name patterns
- Provider codes ZEN-DIA and ZEN-ANE need investigation for proper user mapping
- Some coordinator codes (ChaZu000, LopJu000, etc.) may represent former staff or require further investigation
