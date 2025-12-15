from transform_production_data_v3 import build_provider_map, normalize_name_key

def test_mapping():
    # ... (setup code)

    print("\nTesting Normalization Logic:")
    test_cases = [
        ("Szalas NP, Andrew", "SZALAS ANDREW"),
        ("Antonio NP, Ethel", "ANTONIO ETHEL"),
        ("Jackson PA, Anisha", "JACKSON ANISHA"),
    ]
    
    for input_name, expected in test_cases:
        normalized = normalize_name_key(input_name)
        print(f"  '{input_name}' -> '{normalized}' [{'MATCH' if normalized == expected else 'FAIL'}]")
        
    # (Rest of the script)
    conn = sqlite3.connect('production.db')
    
    # 1. Build map
    print("Building provider map...")
    provider_map, _ = build_provider_map(conn)
    
    # 2. Check key keys
    print(f"\nMap size: {len(provider_map)}")
    keys_sample = list(provider_map.keys())[:20]
    print(f"Sample keys: {keys_sample}")
    
    # 3. Test explicit keys we expect
    test_keys = [
        "SZALAS NP, ANDREW", 
        "ANTONIO NP, ETHEL", 
        "JACKSON PA, ANISHA",
        "SZA",
        "ANT",
        "JAC"
    ] 
    
    print("\nChecking expected ZMO keys:")
    for key in test_keys:
        val = provider_map.get(key)
        print(f"  '{key}': {val}")
        
    # 4. Read ZMO and test top values
    print("\nReading ZMO...")
    zmo = pd.read_csv('downloads/ZMO_MAIN.csv')
    
    # Correct column name with space
    col_name = 'Assigned \nReg Prov'
    if col_name not in zmo.columns:
        print(f"ERROR: Column '{col_name}' not found!")
        print("Columns found:", zmo.columns.tolist())
        return

    top_provs = zmo[col_name].value_counts().head(10)
    print("\nTesting Top 10 ZMO Providers:")
    for name, count in top_provs.items():
        name_clean = str(name).strip().upper()
        
        # Test direct map
        uid = provider_map.get(name_clean)
        
        # Test fallback (first 3 chars)
        uid_fallback = None
        if not uid and len(name_clean) >= 3:
            uid_fallback = provider_map.get(name_clean[:3])
            
        status = "✅ MATCH" if uid else ("⚠️ FALLBACK MATCH" if uid_fallback else "❌ FAIL")
        resolved_id = uid or uid_fallback
        
        print(f"  {count:3d} | '{name_clean}' -> ID: {resolved_id} ({status})")

if __name__ == "__main__":
    test_mapping()
