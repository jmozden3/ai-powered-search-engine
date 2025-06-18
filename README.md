# AI-Powered Search Engine

A sophisticated legal document search engine powered by Azure AI Search, Azure OpenAI, and advanced RAG (Retrieval-Augmented Generation) capabilities. This system enables intelligent search across legal enforcement documents with AI-generated answers and comprehensive tracing.

## Features

- **Advanced Search**: Hybrid semantic and vector search across multiple document fields (KeyFacts, DocumentText, Commentary)
- **AI-Generated Answers**: Uses Azure OpenAI (o3-mini) to generate comprehensive answers based on search results
- **FastAPI Web Interface**: RESTful API for integration with web applications
- **Command Line Interface**: Direct Python execution for testing and development
- **OpenTelemetry Tracing**: Full observability with Azure Monitor integration for monitoring AI operations
- **Robust Data Import**: Optimized scripts for importing CSV/Excel data to Azure SQL

## Architecture

- **Frontend**: FastAPI web framework with automatic API documentation
- **Search Engine**: Azure AI Search with vector embeddings using text-embedding-3-large
- **AI Model**: Azure OpenAI o3-mini for answer generation
- **Database**: Azure SQL Server for data storage
- **Monitoring**: OpenTelemetry with Azure Monitor for tracing and observability

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
- Need a text-embedding-3-large model deployed

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
     APPLICATIONINSIGHTS_CONNECTION_STRING=<your-app-insights-connection-string>
     ```

## Usage

### Running the API Server
Start the FastAPI server for web-based access:
```sh
python app.py
```
The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`

### Direct Command Line Usage
Run the search engine directly for testing:
```sh
python document_rag.py
```

### API Endpoints
- **POST /chat**: Submit questions and receive AI-generated answers with source documents
- **GET /health**: Health check endpoint
- **GET /**: Root endpoint with service status

### Tracing and Monitoring
The application includes comprehensive OpenTelemetry tracing that captures:
- OpenAI API calls (inputs and outputs)
- Search operations
- Error tracking

Tracing is automatically initialized and configured for both API and command-line usage.

To see Tracing in Azure AI Foundry:
1. In your Azure portal, create an Azure Application Insights Resource and copy the connection string (can be found on the resource overview page)
2. Go to Tracing in your Azure AI Foundry Project and click Manage Data Source. Paste in the connection string.
3. Now, when you run your application, you will see tracing metrics in the Tracing tab. 
> **Warning:** There is a 32KB limit on traces. Anything above this limit will likely not show up in Foundry Tracing Portal.  
> [Learn more about trace size limits and possible workarounds.](https://learn.microsoft.com/en-us/answers/questions/543396/how-to-increase-the-size-of-messages-logged-in-app)

## Data Import Scripts

### CSV to Azure SQL Import
The project includes scripts for importing data:

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