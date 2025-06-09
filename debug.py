import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def check_available_drivers():
    """Check what ODBC drivers are available on your system"""
    print("Available ODBC drivers:")
    drivers = pyodbc.drivers()
    for driver in drivers:
        print(f"  - {driver}")
    return drivers

def test_connection_string():
    """Test your current connection string format"""
    conn_str = os.getenv('AZURE_SQL_CONNECTION_STRING')
    print(f"\nYour connection string: {conn_str}")
    
    if not conn_str:
        print("ERROR: AZURE_SQL_CONNECTION_STRING not found in environment")
        return
    
    # Try to parse driver from connection string
    if "Driver=" in conn_str:
        driver_part = conn_str.split("Driver=")[1].split(";")[0]
        print(f"Driver specified in connection string: {driver_part}")
        
        # Check if this driver exists
        available_drivers = pyodbc.drivers()
        driver_clean = driver_part.replace("{", "").replace("}", "")
        
        if driver_clean in available_drivers:
            print("✓ Driver found in system")
        else:
            print("❌ Driver NOT found in system")
            print("Available SQL Server drivers:")
            sql_drivers = [d for d in available_drivers if "SQL Server" in d]
            for driver in sql_drivers:
                print(f"  - {driver}")

def main():
    print("=== ODBC DRIVER DIAGNOSTICS ===")
    
    # Check available drivers
    drivers = check_available_drivers()
    
    # Test connection string
    test_connection_string()
    
    print("\n=== RECOMMENDATIONS ===")
    sql_drivers = [d for d in drivers if "SQL Server" in d]
    if sql_drivers:
        print("Try updating your connection string to use one of these drivers:")
        for driver in sql_drivers:
            print(f"  Driver={{{driver}}};...")
    else:
        print("No SQL Server ODBC drivers found. You may need to install one:")
        print("Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")

if __name__ == '__main__':
    main()