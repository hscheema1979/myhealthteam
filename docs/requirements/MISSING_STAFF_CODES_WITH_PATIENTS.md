# Missing Staff Codes Documentation

## Unmatched Coordinator Staff Codes with Real Patient Examples

Based on SOURCE_COORDINATOR_TASKS_HISTORY table data:

### High Activity Unmatched Staff (Likely Current Employees)

**RubAn000**

- Real Patient Example: KNAPPIK, OLGA 07/22/1936
- Activity Level: 21,617 total tasks, 386 unique patients
- Date Range: 01/01/22 - 12/30/Thu
- Status: HIGHLY ACTIVE - needs immediate mapping

**MalMe000**

- Real Patient Example: WELLER, DONALD 07/31/1953
- Activity Level: 18,546 total tasks, 351 unique patients
- Date Range: 02/01/2024 - 12/30/Thu
- Status: HIGHLY ACTIVE - needs immediate mapping

**SobMa000**

- Real Patient Example: MARLER, ANGELA 08/19/1954
- Activity Level: 3,937 total tasks, 465 unique patients
- Date Range: 01/08/2025 - 12/30/Thu
- Status: ACTIVE - needs mapping

### Medium Activity Unmatched Staff (Former Employees - Short Term)

**ChaZu000**

- Real Patient Example: ACOSTA, MARIA 02/03/1991
- Activity Level: 3,752 total tasks, 366 unique patients
- Date Range: 02/01/2024 - 04/30/2024
- Status: FORMER EMPLOYEE (3-month period)

**LopJu000**

- Real Patient Example: FROST, MICHELLE 09/15/1966
- Activity Level: 2,689 total tasks, 256 unique patients
- Date Range: [Invalid date] - 04/29/2024
- Status: FORMER EMPLOYEE

**LumJa000**

- Real Patient Example: AGUILAR, ANGELICA 03/09/1983
- Activity Level: 2,032 total tasks, 287 unique patients
- Date Range: 02/01/2024 - 04/25/2024
- Status: FORMER EMPLOYEE (3-month period)

### Low Activity Unmatched Staff (Former Employees)

**SanMa000**

- Real Patient Example: GOVANI, KANTA 03/19/1940
- Activity Level: Data not available in previous query
- Status: FORMER EMPLOYEE - low activity

**SanRa000**

- Real Patient Example: ACOSTA, FIDELIA 03/30/1939
- Activity Level: 1,119 total tasks, 154 unique patients
- Date Range: [Invalid date] - 04/29/2024
- Status: FORMER EMPLOYEE

## Unmatched Provider Staff Codes

### Provider Codes Needing Investigation

**ZEN-DAG**

- Real Patient Example: [No patient data found in query]
- Pattern: ZEN-**DAG** (likely last name starts with "Dag")
- Status: NEW PROVIDER - needs user mapping

**ZEN-JAA**

- Real Patient Example: [No patient data found in query]
- Pattern: ZEN-**JAA** (likely last name starts with "Jaa")
- Status: NEW PROVIDER - needs user mapping

**ZEN-KAJ**

- Real Patient Example: [No patient data found in query]
- Pattern: ZEN-**KAJ** (likely last name starts with "Kaj")
- Status: NEW PROVIDER - needs user mapping

**ZEN-MEC**

- Real Patient Example: [No patient data found in query]
- Pattern: ZEN-**MEC** (likely last name starts with "Mec")
- Status: NEW PROVIDER - needs user mapping

## Action Items by Priority

### Immediate Action Required (High Activity)

1. **RubAn000** - 21K+ tasks, needs immediate user mapping
2. **MalMe000** - 18K+ tasks, needs immediate user mapping
3. **SobMa000** - 3K+ tasks, active through 2025

### Documentation Only (Former Employees)

4. **ChaZu000, LopJu000, LumJa000, SanRa000** - Short-term employees (Feb-Apr 2024)
5. **SanMa000** - Low activity former employee

### Investigation Required (New Providers)

6. **ZEN-DAG, ZEN-JAA, ZEN-KAJ, ZEN-MEC** - New provider codes need staff identification

## Pattern Analysis

### Coordinator Pattern: [Last3][First2]000

- **RubAn000**: Rub??? + An??? + 000
- **MalMe000**: Mal??? + Me??? + 000 (could be Melara?)
- **SobMa000**: Sob??? + Ma??? + 000 (could be Soberanis variant?)

### Provider Pattern: ZEN-[Last3]

- **ZEN-DAG**: Unknown provider with last name starting "Dag"
- **ZEN-JAA**: Unknown provider with last name starting "Jaa"
- **ZEN-KAJ**: Unknown provider with last name starting "Kaj"
- **ZEN-MEC**: Unknown provider with last name starting "Mec"

---

_Generated: September 21, 2025_
_Source: SOURCE_COORDINATOR_TASKS_HISTORY and SOURCE_PROVIDER_TASKS_HISTORY_
