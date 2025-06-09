# ai-powered-search-engine

## Pre-reqs
- Create all Azure resources in South Central US region
- Services needed:
   - Azure SQL server and a database
   - Azure OpenAI
   - Azure AI search (standard tier)
- Install **ODBC Driver 18 for SQL Server** on your local machine
  - Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

## Setup

### 1. Azure OpenAI
- Need a text-embedding-ada-002 model deployed

### 2. Azure AI Search
- May need system-assigned identity turned on in your search service
- Grant the Azure identity (eg your user id) "Search Index Data Contributor" role on your Search Service. If using Azure AD authentication, you may also need to add the "Search Service Contributor" role.

### 3. Azure SQL Server
- **Settings > Microsoft Entra ID**: 
  - Set yourself as the Microsoft Entra admin
  - **Enable Microsoft Entra authentication** - The scripts use Azure AD authentication exclusively
- **Important**: Ensure your user account has appropriate database permissions for creating/modifying tables

### 4. Local Development Setup
1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Authenticate with Azure:**
   ```sh
   az login
   ```

3. **Environment Configuration:**
   - Copy `sample.env` to `.env` and fill in your Azure credentials and configuration values
   - Key environment variables needed:
     ```
     AZURE_SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=tcp:<your-server>.database.windows.net,1433;Database=<your-database>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30
     AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
     AZURE_SEARCH_ADMIN_KEY=<your-search-admin-key>
     AZURE_SEARCH_INDEX_NAME=<your-index-name>
     AZURE_OPENAI_ENDPOINT=https://<your-openai-service>.openai.azure.com/
     AZURE_OPENAI_API_KEY=<your-openai-key>
     AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<your-embedding-model-deployment-name>
     ```

## Data Import Scripts

### CSV to Azure SQL Import
The project includes optimized scripts for importing enforcement actions data:

1. **Prepare your data:**
   - Place your CSV file in the project directory
   - Update the `CSV_FILE` and `table_name` variables in the import script as needed

2. **Run the import:**
   ```sh
   python import_sql_data.py
   ```

**Features:**
- ✅ **Azure AD Authentication** - Uses your `az login` credentials (no passwords stored)
- ✅ **Batch Processing** - Processes 1000 rows at a time for optimal performance
- ✅ **Truncate & Reload** - Each run clears existing data and loads fresh data
- ✅ **Validation** - Checks CSV file and SQL connection before importing
- ✅ **Progress Tracking** - Shows import progress in real-time

### Generate Embeddings and Upload to AI Search
After importing data to SQL, generate embeddings and upload to Azure AI Search:

```sh
python <embedding_script_name>.py
```

This script:
- Reads data from the Azure SQL database
- Generates embeddings for text fields using Azure OpenAI
- Uploads the data with embeddings to Azure AI Search
- Recreates the search index on each run