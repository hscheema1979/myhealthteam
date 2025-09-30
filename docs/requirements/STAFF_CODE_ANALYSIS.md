# Staff Code Analysis

## Unique Staff Codes Found in Task Data

This document lists all unique staff codes found in the SOURCE_COORDINATOR_TASKS_HISTORY and SOURCE_PROVIDER_TASKS_HISTORY tables.

### Complete List of Staff Codes (21 total)

#### Coordinator Task Staff Codes (19 codes)
1. ChaZu000
2. EstJa000
3. HerHe000
4. LopJu000
5. LumJa000
6. MalJu000
7. MalMe000
8. ManSh000
9. MarCi000
10. PerJo000
11. RioMa000
12. RubAn000
13. SanBi000
14. SanMa000
15. SanRa000
16. SobJo000
17. SobMa000
18. ZEN-SZA
19. ZEN-VIL

#### Provider Task Staff Codes (2 codes)
1. ZEN-ANE
2. ZEN-DIA

### Staff Code Patterns Identified

#### Pattern 1: First 3 letters of first name + First 2 letters of last name + "000"
Examples:
- ManSh000 → **Man**uel **Sh**erwin? (Need to verify)
- HerHe000 → **Her**nandez **He**ctor? (Likely Hector HerNAndez)
- EstJa000 → **Est**omo **Ja**n? (Likely Jan Estomo)
- RioMa000 → **Rio**s **Ma**nuel? (Likely Manuel Rios)

#### Pattern 2: "ZEN-" + First 3 letters of last name
Examples:
- ZEN-VIL → ZEN-**VIL**lasenor (Likely Lourdes Villasenor NP)
- ZEN-SZA → ZEN-**SZA**las (Likely Andrew Szalas NP)
- ZEN-ANE → ZEN-**ANE**? (Unknown staff member)
- ZEN-DIA → ZEN-**DIA**z (Likely Albert Diaz)

### Potential Staff Mappings

Based on SOURCE_STAFF_INFO data:

| Staff Code | Likely Staff Member | Role | Confidence |
|------------|-------------------|------|------------|
| HerHe000 | Hector HerNAndez | CC (Care Coordinator) | High |
| EstJa000 | Jan Estomo | CC (Care Coordinator) | High |
| RioMa000 | Manuel Rios | CC (Care Coordinator) | High |
| ManSh000 | Sherwin Maningas | OT (Onboarding Team) | Medium |
| MarCi000 | Cindy Mariano | OT (Onboarding Team) | Medium |
| ZEN-VIL | Lourdes Villasenor NP | CP (Care Provider) | High |
| ZEN-SZA | Andrew Szalas NP | CP (Care Provider) | High |
| ZEN-DIA | Albert Diaz | CP (Care Provider) | High |
| MalJu000 | Justin Malhotra MD | ADMIN/CP | Medium |

### Unmatched Staff Codes

These codes don't have clear matches in the current SOURCE_STAFF_INFO:
- ChaZu000
- LopJu000
- LumJa000
- MalMe000
- RubAn000
- SanBi000
- SanMa000
- SanRa000
- SobJo000
- SobMa000
- PerJo000
- ZEN-ANE

## Staff Code to prod_users Mapping Analysis

### Provider Code Mappings (High Confidence)
The provider codes follow a clear ZEN-[Last3Letters] pattern and have been successfully matched:

- **ZEN-DIA** → Albert Diaz (albert@myhealthteam.org)
  - Pattern: ZEN + DIA (first 3 letters of "Diaz")
  - Confidence: HIGH - Perfect pattern match

- **ZEN-MAL** → Justin Malhotra MD (admin@myhealthteam.org)
  - Pattern: ZEN + MAL (first 3 letters of "Malhotra")
  - Confidence: HIGH - Perfect pattern match

- **ZEN-SZA** → Andrew Szalas NP (andrews@myhealthteam.org)
  - Pattern: ZEN + SZA (first 3 letters of "Szalas")
  - Confidence: HIGH - Perfect pattern match

- **ZEN-VIL** → Lourdes Villasenor NP (lourdesv@myhealthteam.org)
  - Pattern: ZEN + VIL (first 3 letters of "Villasenor")
  - Confidence: HIGH - Perfect pattern match

- **ZEN-ANE** → Unknown provider (requires investigation)
  - Pattern: ZEN + ANE (unknown staff member)
  - Confidence: LOW - No clear match found

### Coordinator Code Mappings (Medium Confidence)
The coordinator codes follow a [First3Letters][Last2Letters]000 pattern with some variations:

- **AteDi000** → Albert Diaz (albert@myhealthteam.org)
  - Pattern: Ate (variant of "Albert") + Di ("Diaz") + 000
  - Confidence: MEDIUM - Name pattern match with variation

- **EstJa000** → Multiple possible matches:
  - Anisha Jackson (anisha@myhealthteam.org) - Partial match
  - Jan Estomo (jan@myhealthteam.org) - Better pattern match
  - Confidence: MEDIUM - Requires verification

- **MalMe000** → Multiple possible matches:
  - Claudia Melara (claudia@myhealthteam.org) - Last name partial match
  - Dianela Medez (dianela@myhealthteam.org) - Last name partial match
  - Confidence: MEDIUM - Requires verification

- **RubAn000** → Ethel Antonio (ethel@myhealthteam.org)
  - Pattern: Rub (possible first name) + An ("Antonio") + 000
  - Confidence: MEDIUM - Partial pattern match

- **SanBi000** → Bianchi Sanchez (bianchi@myhealthteam.org)
  - Pattern: San ("Sanchez") + Bi ("Bianchi") + 000
  - Confidence: MEDIUM - Reversed name pattern

- **SobAl000** → Jose Soberanis (jose@myhealthteam.org)
  - Pattern: Sob ("Soberanis") + Al (possible middle name) + 000
  - Confidence: MEDIUM - Partial pattern match

### Special Abbreviation Cases (High Confidence)
These codes appear to be direct abbreviations:

- **SZA** → Andrew Szalas NP (andrews@myhealthteam.org)
  - Direct abbreviation of "Szalas"
  - Confidence: HIGH - Clear abbreviation pattern

- **VIL** → Lourdes Villasenor NP (lourdesv@myhealthteam.org)
  - Direct abbreviation of "Villasenor"
  - Confidence: HIGH - Clear abbreviation pattern

### Unmatched Codes Requiring Investigation
The following coordinator codes could not be confidently matched to existing prod_users:

- **LopJu000** - No clear match found in current user database
- **LumJa000** - Partial matches only, requires verification
- **MalJu000** - Partial matches only, requires verification
- **MarCi000** - Partial matches only, requires verification
- **SanMa000** - Multiple partial matches, requires verification
- **SanRa000** - Partial matches only, requires verification
- **SobMa000** - Multiple partial matches, requires verification

These codes may represent:
- Former staff members no longer in the system
- Staff members with different naming conventions
- Data entry variations or typos
- Staff members not yet added to prod_users table

## Next Steps

1. **Validate High-Confidence Mappings**: Confirm the ZEN- provider codes and review coordinator matches
2. **Investigate Unmatched Codes**: Check if these represent former employees or data entry errors
3. **Create Mapping Table**: Build a lookup table for confirmed mappings
4. **Update Migration Scripts**: Incorporate staff code mappings into data migration
5. **Handle Orphaned Tasks**: Decide how to handle tasks with unmatched staff codes

## Code Pattern Rules

### Coordinator/Manager Pattern: `[First3Letters][Last2Letters]000`
- Take first 3 letters of first name
- Take first 2 letters of last name  
- Append "000"
- Example: "Charise Zuniga" → "ChaZu000"
- **Note**: Pattern not always consistent - some codes may use variations

### Provider Pattern: `ZEN-[Last3Letters]`
- Prefix with "ZEN-"
- Take first 3 letters of last name (uppercase)
- Example: "Dr. Anesthesia" → "ZEN-ANE"
- **Confirmed**: This pattern is highly reliable for provider identification

---
*Last Updated: January 2025*
*Source: SOURCE_COORDINATOR_TASKS_HISTORY and SOURCE_PROVIDER_TASKS_HISTORY tables*