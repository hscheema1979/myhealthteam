import pandas as pd
import sqlite3


<parameter name="StartLine">4

# Find missing
csv_emails = set(csv_df['email_lower'])
db_emails = set(db_df['email_lower'])
missing_emails = csv_emails - db_emails

print(f"\nUsers in CSV but NOT in DB: {len(missing_emails)}")
if missing_emails:
    missing_df = csv_df[csv_df['email_lower'].isin(missing_emails)]
    for _, row in missing_df.iterrows():
        print(f"  {row['First Name [Required]']} {row['Last Name [Required]']} - {row['Email Address [Required]']}")

# Also check for name mismatches (like Medez vs Atencio)
print("\n\nChecking for name mismatches...")
print("DB users:")
for _, row in db_df.head(25).iterrows():
    print(f"  {row['full_name']} - {row['email']}")
