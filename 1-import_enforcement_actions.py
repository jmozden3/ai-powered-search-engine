# This script imports enforcement actions data from a EnforcementActions.csv into an Azure SQL database table called EnforcementActions

import os
import pyodbc
import csv

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Azure SQL connection settings
server = os.getenv('AZURE_SQL_SERVER')
database = os.getenv('AZURE_SQL_DATABASE')
username = os.getenv('AZURE_SQL_USERNAME')
password = os.getenv('AZURE_SQL_PASSWORD')

# Connection string for SQL authentication
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

def create_table_if_not_exists(cursor):
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EnforcementActions' AND xtype='U')
        CREATE TABLE EnforcementActions (
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

def insert_row(cursor, row, headers):
    # Filter out empty column names and their corresponding values
    filtered = [(col, val) for col, val in zip(headers, row) if col.strip()]
    filtered_headers = [col for col, _ in filtered]
    filtered_row = [val for _, val in filtered]
    placeholders = ','.join(['?'] * len(filtered_headers))
    columns = ','.join(f'[{col}]' for col in filtered_headers)
    sql = f"INSERT INTO EnforcementActions ({columns}) VALUES ({placeholders})"
    cursor.execute(sql, filtered_row)

def main():
    print('Data uploading...')
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        conn.commit()
        # Assumes the CSV file is in the same directory as this script
        with open('EnforcementActions.csv', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Get header
            for row in reader:
                # Convert empty strings to None
                row = [None if v == '' else v for v in row]
                try:
                    insert_row(cursor, row, headers)
                except Exception as e:
                    print(f"Error inserting row: {e}")
            conn.commit()
        print('Data import complete.')

if __name__ == '__main__':
    main()
