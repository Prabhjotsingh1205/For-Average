import sqlite3
import os

def process_stock_data(source_db_files, output_db_file, table_name, columns):
    """
    Consolidated tool to:
    1. Calculate global averages of absolute values.
    2. Create a new database with per-stock averages of absolute values.
    """
    print(f"--- Starting Stock Data Processing ---\n")

    # Storage for global aggregation
    global_sums = {col: 0.0 for col in columns}
    global_counts = {col: 0 for col in columns}

    # Storage for per-stock aggregation
    # { 'SYMBOL': { 'col1': [abs_v1, abs_v2], ... } }
    stock_data = {}

    # 1. Load data from source databases
    for db_file in source_db_files:
        if not os.path.exists(db_file):
            print(f"Warning: Database file '{db_file}' not found. Skipping.")
            continue

        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Use ABS() to treat negative numbers as positive as per user requirement
            abs_cols_str = ", ".join([f"ABS({col})" for col in columns])
            query = f"SELECT symbol, {abs_cols_str} FROM {table_name}"
            cursor.execute(query)

            rows = cursor.fetchall()
            for row in rows:
                symbol = row[0]
                values = row[1:]

                if symbol not in stock_data:
                    stock_data[symbol] = {col: [] for col in columns}

                for i, col in enumerate(columns):
                    val = values[i]
                    if val is not None:
                        # Add to per-stock storage
                        stock_data[symbol][col].append(val)
                        # Add to global storage
                        global_sums[col] += val
                        global_counts[col] += 1

            conn.close()
            print(f"Successfully loaded data from {db_file}")
        except sqlite3.Error as e:
            print(f"Error reading {db_file}: {e}")

    # 2. Print Global Averages
    print("\n--- Global Averages (Absolute Values) ---")
    for col in columns:
        if global_counts[col] > 0:
            avg = global_sums[col] / global_counts[col]
            print(f"Average of {col}: {avg:.2f}")
        else:
            print(f"Average of {col}: N/A (no data found)")

    # 3. Create Per-Stock Average Database
    if os.path.exists(output_db_file):
        os.remove(output_db_file)

    try:
        output_conn = sqlite3.connect(output_db_file)
        output_cursor = output_conn.cursor()

        # Create table for per-stock averages
        avg_columns_sql = ", ".join([f"{col}_avg REAL" for col in columns])
        create_table_sql = f"CREATE TABLE average_stock_data (symbol TEXT PRIMARY KEY, {avg_columns_sql})"
        output_cursor.execute(create_table_sql)

        # Calculate and insert per-stock averages
        for symbol, cols in stock_data.items():
            row_values = [symbol]
            for col in columns:
                vals = cols[col]
                row_values.append(sum(vals) / len(vals) if vals else None)

            placeholders = ", ".join(["?" for _ in range(len(columns) + 1)])
            output_cursor.execute(f"INSERT INTO average_stock_data VALUES ({placeholders})", row_values)

        output_conn.commit()
        output_conn.close()
        print(f"\n--- Per-Stock Database Created ---")
        print(f"File: {output_db_file}")
        print(f"Table: average_stock_data")
        print(f"Total Symbols Processed: {len(stock_data)}")
    except sqlite3.Error as e:
        print(f"Error creating output database: {e}")

if __name__ == "__main__":
    # Configuration
    # You can change these file names if your databases are named differently
    SOURCE_DBS = ['stock_summary06_03.db', 'stock_summary05_03.db']
    OUTPUT_DB = 'stock_averages.db'
    TABLE = 'latest_stock_data'

    # The four columns you requested
    TARGET_COLUMNS = [
        'day_cum_ce_oi_chg',
        'day_cum_pe_oi_chg',
        'day_total_ce_volume',
        'day_total_pe_volume'
    ]

    process_stock_data(SOURCE_DBS, OUTPUT_DB, TABLE, TARGET_COLUMNS)
