# Staff Code Reference Document

## Table 1: prod_users with Generated Staff Codes

| Full Name             | Email                      | Coordinator Code | Provider Code | Alt Provider Code |
| --------------------- | -------------------------- | ---------------- | ------------- | ----------------- |
| Ethel Antonio         | ethel@myhealthteam.org     | ANTET000         | ZEN-ANT       | ZEN-ANE           |
| Harpreet Cheema       | harpreet@myhealthteam.org  | CHEHA000         | ZEN-CHE       | ZEN-CHH           |
| Eden Dabalus          | eden@myhealthteam.org      | DABED000         | ZEN-DAB       | ZEN-DAE           |
| Genevieve Davis       | genevieve@myhealthteam.org | DAVGE000         | ZEN-DAV       | ZEN-DAG           |
| Albert Diaz           | albert@myhealthteam.org    | DIAAL000         | ZEN-DIA       | ZEN-DIA           |
| Jan Estomo            | jan@myhealthteam.org       | ESTJA000         | ZEN-EST       | ZEN-ESJ           |
| Hector Hernandez      | hector@myhealthteam.org    | HERHE000         | ZEN-HER       | ZEN-HEH           |
| Anisha Jackson        | anisha@myhealthteam.org    | JACAN000         | ZEN-JAA       | ZEN-JAA           |
| Jaspreet Kaur         | jaspreet@myhealthteam.org  | KAUJA000         | ZEN-KAJ       | ZEN-KAJ           |
| Justin Malhotra MD    | admin@myhealthteam.org     | MALJU000         | ZEN-MAL       | ZEN-MAJ           |
| Sherwin Maningas      | sherwin@myhealthteam.org   | MANSH000         | ZEN-MAN       | ZEN-MAS           |
| Cindy Mariano         | cindy@myhealthteam.org     | MARCI000         | ZEN-MAR       | ZEN-MAC           |
| Dianela Medez         | dianela@myhealthteam.org   | MEDDI000         | ZEN-MED       | ZEN-MED           |
| Claudia Melara        | claudia@myhealthteam.org   | MELCL000         | ZEN-MEL       | ZEN-MEC           |
| Angela Otegbulu       | angela@myhealthteam.org    | OTEAN000         | ZEN-OTE       | ZEN-OTA           |
| Jorge Perez           | jorge@myhealthteam.org     | PERJO000         | ZEN-PER       | ZEN-PEJ           |
| Manuel Rios           | manuel@myhealthteam.org    | RIOMA000         | ZEN-RIO       | ZEN-RIM           |
| Bianchi Sanchez       | bianchi@myhealthteam.org   | SANBI000         | ZEN-SAN       | ZEN-SAB           |
| Jose Soberanis        | jose@myhealthteam.org      | SOBJO000         | ZEN-SOB       | ZEN-SOJ           |
| Andrew Szalas NP      | andrews@myhealthteam.org   | SZAAN000         | ZEN-SZA       | ZEN-SZA           |
| Lourdes Villasenor NP | lourdesv@myhealthteam.org  | VILLO000         | ZEN-VIL       | ZEN-VIL           |

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
