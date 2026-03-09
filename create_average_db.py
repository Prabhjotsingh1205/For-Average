import sqlite3
import os

def create_average_db(source_db_files, output_db_file, table_name, columns):
    """
    Groups data from source_db_files by 'symbol' and calculates the
    average for each column in 'columns', then saves it to output_db_file.
    """
    # Create the output database and table
    if os.path.exists(output_db_file):
        os.remove(output_db_file)

    # Temporary storage for all stock data
    # { 'SYMBOL': { 'col1': [v1, v2], 'col2': [v1, v2] } }
    stock_data = {}

    # Extract data from source databases
    for db_file in source_db_files:
        if not os.path.exists(db_file):
            print(f"Warning: Source database '{db_file}' not found. Skipping.")
            continue

        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Select all symbols and the columns we care about
            cols_str = ", ".join(columns)
            query = f"SELECT symbol, {cols_str} FROM {table_name}"
            cursor.execute(query)

            for row in cursor.fetchall():
                symbol = row[0]
                values = row[1:]

                if symbol not in stock_data:
                    stock_data[symbol] = {col: [] for col in columns}

                for i, col in enumerate(columns):
                    val = values[i]
                    if val is not None:
                        stock_data[symbol][col].append(val)

            conn.close()
            print(f"Loaded data from {db_file}")
        except sqlite3.Error as e:
            print(f"Error reading {db_file}: {e}")

    # Calculate averages per symbol and insert into the output database
    output_conn = sqlite3.connect(output_db_file)
    output_cursor = output_conn.cursor()

    avg_columns_sql = ", ".join([f"{col}_avg REAL" for col in columns])
    create_table_sql = f"CREATE TABLE average_stock_data (symbol TEXT PRIMARY KEY, {avg_columns_sql})"
    output_cursor.execute(create_table_sql)

    for symbol, cols in stock_data.items():
        row_values = [symbol]
        for col in columns:
            vals = cols[col]
            if vals:
                row_values.append(sum(vals) / len(vals))
            else:
                row_values.append(None)

        placeholders = ", ".join(["?" for _ in range(len(columns) + 1)])
        output_cursor.execute(f"INSERT INTO average_stock_data VALUES ({placeholders})", row_values)

    output_conn.commit()

    print(f"\n--- Results ---")
    print(f"Processed {len(stock_data)} unique stock symbols.")
    print(f"New database created: {output_db_file}")

    output_conn.close()

if __name__ == "__main__":
    # Configuration
    source_databases = ['stock_summary06_03.db', 'stock_summary07_03.db']
    output_database = 'stock_averages.db'
    source_table = 'latest_stock_data'
    target_columns = [
        'day_cum_ce_oi_chg',
        'day_cum_pe_oi_chg',
        'day_total_ce_volume',
        'day_total_pe_volume'
    ]

    create_average_db(source_databases, output_database, source_table, target_columns)
