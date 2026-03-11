import sqlite3
import os

def calculate_averages(db_files, table_name, columns):
    """
    Calculates the average of the absolute values of the specified columns
    across multiple database files.
    Formula: (|v1| + |v2| + ... + |vn|) / n
    """
    overall_sums = {col: 0.0 for col in columns}
    overall_counts = {col: 0 for col in columns}

    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"Warning: Database file '{db_file}' not found. Skipping.")
            continue

        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Constructing the query using ABS() to ensure negative numbers
            # are treated as positive as per user requirement.
            query_parts = []
            for col in columns:
                query_parts.append(f"SUM(ABS({col})), COUNT({col})")

            query = f"SELECT {', '.join(query_parts)} FROM {table_name}"
            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                for i, col in enumerate(columns):
                    col_abs_sum = result[i*2]
                    col_count = result[i*2 + 1]

                    if col_abs_sum is not None:
                        overall_sums[col] += col_abs_sum
                        overall_counts[col] += col_count

            conn.close()
        except sqlite3.Error as e:
            print(f"Error reading {db_file}: {e}")

    print("\n--- Average Values (using Absolute Values) across all databases ---")
    for col in columns:
        if overall_counts[col] > 0:
            avg = overall_sums[col] / overall_counts[col]
            print(f"Average of {col}: {avg:.2f}")
        else:
            print(f"Average of {col}: N/A (no data)")

if __name__ == "__main__":
    # Configuration
    databases = ['stock_summary06_03.db', 'stock_summary07_03.db']
    table = 'latest_stock_data'
    target_columns = [
        'day_cum_ce_oi_chg',
        'day_cum_pe_oi_chg',
        'day_total_ce_volume',
        'day_total_pe_volume'
    ]

    calculate_averages(databases, table, target_columns)
