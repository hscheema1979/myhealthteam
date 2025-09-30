import pandas as pd
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def split_cmlog_by_month():
    # Define input and output paths
    input_file = "downloads/cmlog.csv"
    output_folder = "downloads/monthly_CM"
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")
    
    # Read the CSV file
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Display basic info about the data
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Check the date format in the "Date Only" column
    print("\nSample dates from 'Date Only' column:")
    print(df['Date Only'].head(10))
    
    # Function to parse dates with multiple formats
    def parse_date(date_str):
        if pd.isna(date_str):
            return None
        
        # Clean the date string
        date_str = str(date_str).strip()
        
        # Handle 2-digit years specially
        if '/' in date_str and len(date_str.split('/')[-1]) == 2:
            parts = date_str.split('/')
            month, day, year = parts[0], parts[1], parts[2]
            
            # Convert 2-digit year to 4-digit year
            # Assuming 00-29 are 2000-2029 and 30-99 are 1930-1999
            # But based on the data, 99 should be 2099
            year_int = int(year)
            if year_int >= 30:
                year_4digit = 1900 + year_int
            else:
                year_4digit = 2000 + year_int
                
            # Special case for 99 -> 2099 based on the data pattern
            if year_int == 99:
                year_4digit = 2099
                
            # Try to parse with the corrected year
            try:
                return datetime(year_4digit, int(month), int(day))
            except ValueError:
                pass
        
        # Try different date formats
        formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    # Parse dates and create a new column with normalized dates
    print("\nParsing dates...")
    df['Parsed_Date'] = df['Date Only'].apply(parse_date)
    
    # Check for rows with invalid dates
    invalid_dates = df[df['Parsed_Date'].isna()]
    if len(invalid_dates) > 0:
        print(f"Warning: {len(invalid_dates)} rows have invalid dates")
        # Show some examples of invalid dates
        print("Sample invalid dates:")
        print(invalid_dates['Date Only'].head())
    
    # Remove rows with invalid dates
    valid_df = df.dropna(subset=['Parsed_Date'])
    print(f"Rows with valid dates: {len(valid_df)}")
    
    # Add normalized date column in YYYY-MM-DD format
    valid_df['Normalized_Date'] = valid_df['Parsed_Date'].dt.strftime('%Y-%m-%d')
    
    # Update the Date Only column with normalized dates
    valid_df['Date Only'] = valid_df['Normalized_Date']
    
    # Group by year and month
    valid_df['Year_Month'] = valid_df['Parsed_Date'].dt.to_period('M')
    
    # Create separate files for each month
    print("\nSplitting data by month...")
    grouped = valid_df.groupby('Year_Month')
    
    for month, group in grouped:
        # Create filename
        year = month.year
        month_num = month.month
        filename = f"coordinator_tasks_{year}_{month_num:02d}.csv"
        filepath = os.path.join(output_folder, filename)
        
        # Remove temporary columns before saving
        group_to_save = group.drop(['Parsed_Date', 'Normalized_Date', 'Year_Month'], axis=1)
        
        # Save to CSV
        group_to_save.to_csv(filepath, index=False)
        print(f"Saved {len(group)} rows to {filepath}")
    
    print(f"\nProcessing complete! Files saved in {output_folder} folder.")

if __name__ == "__main__":
    split_cmlog_by_month()