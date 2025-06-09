import os
import pyodbc
import csv
import sys
import struct
from azure.identity import DefaultAzureCredential

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Azure SQL connection settings
conn_str_base = os.getenv('AZURE_SQL_CONNECTION_STRING')

# CSV file path
CSV_FILE = 'sample_data_subset.csv'
table_name = 'EnforcementActionsSubset'

def get_azure_sql_token():
    """Get Azure AD access token for SQL Database"""
    try:
        credential = DefaultAzureCredential()
        # The scope for Azure SQL Database
        token = credential.get_token("https://database.windows.net/.default")
        return token.token
    except Exception as e:
        print(f"ERROR getting Azure AD token: {e}")
        return None

def create_connection_string_with_token():
    """Create connection string using Azure AD token"""
    if not conn_str_base:
        print("ERROR: AZURE_SQL_CONNECTION_STRING environment variable not set")
        return None
        
    token = get_azure_sql_token()
    if not token:
        return None
    
    # Convert token to the format pyodbc expects
    token_bytes = token.encode('utf-16-le')
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    
    return conn_str_base, token_struct

def validate_csv_file():
    """Check if CSV file exists and is readable"""
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: CSV file '{CSV_FILE}' not found in current directory")
        return False
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            if not headers:
                print("ERROR: CSV file appears to be empty")
                return False
        print(f"✓ CSV file validated: {len(headers)} columns found")
        return True
    except Exception as e:
        print(f"ERROR reading CSV file: {e}")
        return False

def validate_sql_connection():
    """Test SQL Server connection using Azure AD"""
    try:
        conn_info = create_connection_string_with_token()
        if not conn_info:
            return False
        
        conn_str, token_struct = conn_info
        
        # Connect using the token
        conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        print("✓ SQL Server connection successful (Azure AD)")
        return True
    except Exception as e:
        print(f"ERROR connecting to SQL Server with Azure AD: {e}")
        print("Make sure you're logged in with 'az login' or have proper Azure credentials configured")
        return False

def create_or_truncate_table(cursor):
    """Create table if not exists, otherwise truncate existing table"""
    # Check if table exists
    cursor.execute(f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = '{table_name}'
    """)
    table_exists = cursor.fetchone()[0] > 0
    
    if table_exists:
        print(f"Table '{table_name}' exists. Truncating...")
        cursor.execute(f"TRUNCATE TABLE {table_name}")
    else:
        print(f"Creating table '{table_name}'...")
        cursor.execute(f'''
            CREATE TABLE {table_name} (
                ID INT PRIMARY KEY,
                BrowserFile NVARCHAR(255),
                Title NVARCHAR(255),
                DateIssued DATETIME,
                Published BIT,
                DocumentTypes NVARCHAR(MAX),
                KeyFacts NVARCHAR(MAX),
                DocumentText NVARCHAR(MAX),
                Commentary NVARCHAR(MAX),
                NumberOfViolations INT NULL,
                SettlementAmount FLOAT NULL,
                OfacPenalty NVARCHAR(50) NULL,
                AggregatePenalty NVARCHAR(50) NULL,
                BasePenalty NVARCHAR(50) NULL,
                StatutoryMaximum NVARCHAR(50) NULL,
                VSD NVARCHAR(10) NULL,
                Egregious NVARCHAR(10) NULL,
                WillfulOrReckless NVARCHAR(10) NULL,
                Criminal NVARCHAR(10) NULL,
                RegulatoryProvisions NVARCHAR(MAX) NULL,
                LegalIssues NVARCHAR(MAX) NULL,
                SanctionPrograms NVARCHAR(MAX) NULL,
                EnforcementCharacterizations NVARCHAR(MAX) NULL,
                Industries NVARCHAR(MAX) NULL,
                AggravatingFactors NVARCHAR(MAX) NULL,
                MitigatingFactors NVARCHAR(MAX) NULL
            )
        ''')

def prepare_batch_data(headers, rows):
    """Prepare data for batch insert"""
    # Filter out empty column names
    filtered_headers = [col for col in headers if col.strip()]
    header_indices = [i for i, col in enumerate(headers) if col.strip()]
    
    # Prepare batch data
    batch_rows = []
    for row in rows:
        # Convert empty strings to None and filter by valid columns
        filtered_row = [None if row[i] == '' else row[i] for i in header_indices]
        batch_rows.append(filtered_row)
    
    return filtered_headers, batch_rows

def batch_insert(cursor, headers, batch_rows):
    """Insert multiple rows in a single batch"""
    if not batch_rows:
        return
    
    filtered_headers, processed_rows = prepare_batch_data(headers, batch_rows)
    
    placeholders = ','.join(['?'] * len(filtered_headers))
    columns = ','.join(f'[{col}]' for col in filtered_headers)
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    cursor.executemany(sql, processed_rows)

def main():
    print('Validating prerequisites...')
    
    # Validate CSV file
    if not validate_csv_file():
        sys.exit(1)
    
    # Validate SQL connection  
    if not validate_sql_connection():
        sys.exit(1)
    
    print('Validation passed. Starting truncate and reload...')
    
    # Get connection info with token
    conn_info = create_connection_string_with_token()
    if not conn_info:
        print("ERROR: Could not establish Azure AD connection")
        sys.exit(1)
    
    conn_str, token_struct = conn_info
    
    # Connect and import data
    conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
    try:
        cursor = conn.cursor()
        create_or_truncate_table(cursor)
        conn.commit()
        
        # Import data in batches
        batch_size = 1000  # Process 1000 rows at a time
        batch_rows = []
        total_rows = 0
        
        with open(CSV_FILE, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Get header
            
            for row in reader:
                batch_rows.append(row)
                total_rows += 1
                
                # Process batch when it reaches batch_size
                if len(batch_rows) >= batch_size:
                    try:
                        batch_insert(cursor, headers, batch_rows)
                        conn.commit()
                        print(f"Processed {total_rows} rows...")
                        batch_rows = []  # Reset batch
                    except Exception as e:
                        print(f"Error inserting batch at row {total_rows}: {e}")
                        batch_rows = []  # Reset batch to continue
            
            # Process remaining rows in final batch
            if batch_rows:
                try:
                    batch_insert(cursor, headers, batch_rows)
                    conn.commit()
                    print(f"Processed final {len(batch_rows)} rows...")
                except Exception as e:
                    print(f"Error inserting final batch: {e}")
        
        print(f'Truncate and reload complete. Total rows loaded: {total_rows}')
    finally:
        conn.close()

if __name__ == '__main__':
    main()