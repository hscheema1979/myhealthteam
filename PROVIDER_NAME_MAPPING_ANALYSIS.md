# ZMO Provider Name to Users Table Mapping

## ZMO Provider Names → Users Table

Based on actual data:

### ZMO → Users Mapping
```
"Szalas NP, Andrew"         → "Szalas NP, Andrew"  (user_id: 2)
"Antonio NP, Ethel"         → "Antonio, Ethel"     (user_id: 10)
"Jackson PA, Anisha"        → "Jackson, Anisha"    (user_id: 4)
"Dabalus NP, Eden"          → "Dabalus, Eden"      (user_id: 9)
"Malhotra MD, Justinder"    → "Malhotra MD, Justin" (user_id: 18)
"Villasenor NP, Lourdes"    → "Villasenor NP, Lourdes" (user_id: 19)
"Kaur NP, Jaspreet"         → "Kaur, Jaspreet"     (user_id: 15)
"Otebulu NP, Angela"        → "Otegbulu, Angela"   (user_id: 3)
"Melara ZZ, Claudia"        → "Melara, Claudia"    (user_id: 7)
"Davis NP, Genevieve"       → "Davis, Genevieve"   (user_id: 11)
```

## The Problem
ZMO uses full names with titles (NP, PA, MD) but users table has inconsistent format:
- Some have titles in last_name: "Szalas NP"
- Some don't: "Antonio", "Jackson"

## Solution
Need to create a fuzzy name matcher that:
1. Strips titles (NP, PA, MD, ZZ)
2. Matches on last name + first name
3. Handles typos (Otebulu vs Otegbulu, Justinder vs Justin)
