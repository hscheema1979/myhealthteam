import csv
import os

def sum_september_minutes():
    file_path = "downloads/monthly_CM/coordinator_tasks_2025_09.csv"

    total_minutes = 0.0
    row_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            # Skip header
            header = next(reader)

            for row in reader:
                if len(row) > 12:  # Make sure we have enough columns
                    try:
                        # Total Mins is in column 12 (0-indexed)
                        mins_str = row[12].strip()
                        if mins_str and mins_str != 'Total Mins':  # Skip header if present
                            # Remove any commas and convert to float
                            mins_clean = mins_str.replace(',', '')
                            if mins_clean:
                                minutes = float(mins_clean)
                                total_minutes += minutes
                                row_count += 1
                    except (ValueError, IndexError) as e:
                        # Skip rows that can't be parsed
                        continue

        print(f"Processed {row_count} rows")
        print(f"Total minutes for September 2025: {total_minutes:.2f}")

        return total_minutes

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"Error reading file: {e}")
        return 0

if __name__ == "__main__":
    result = sum_september_minutes()
    print(f"\nFinal result: {result:.2f} total minutes for September 2025 CM logs")