# This script reads all rows from the EnforcementActions table in Azure SQL, generates embeddings for the main text fields (without chunking), and uploads them to Azure AI Search, recreating the index each run

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex
)
from datetime import datetime, timezone
import json
import hashlib
from typing import Any

from azure.core.credentials import AzureKeyCredential  
from azure.search.documents import SearchClient  
from datetime import datetime
import os  
from dotenv import load_dotenv  
from azure.core.credentials import AzureKeyCredential  
from azure.identity import DefaultAzureCredential

import openai
from openai import AzureOpenAI

import pyodbc

load_dotenv()

# Azure AI Search settings
ai_search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
ai_search_key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
ai_search_index = os.environ["AZURE_SEARCH_INDEX_NAME"]

# Azure OpenAI settings
aoai_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# SQL connection settings
sql_server = os.environ["AZURE_SQL_SERVER"]
sql_database = os.environ["AZURE_SQL_DATABASE"]
sql_username = os.environ["AZURE_SQL_USERNAME"]
sql_password = os.environ["AZURE_SQL_PASSWORD"]

# ODBC connection string
conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={sql_server};"
    f"DATABASE={sql_database};"
    f"UID={sql_username};"
    f"PWD={sql_password}"
)

# Initialize DefaultAzureCredential
credential = DefaultAzureCredential()

search_index_client = SearchIndexClient(
    ai_search_endpoint, 
    AzureKeyCredential(ai_search_key)
)

search_client = SearchClient(
    ai_search_endpoint, 
    ai_search_index, 
    AzureKeyCredential(ai_search_key)
)

# Initialize Azure OpenAI client
openai_client = AzureOpenAI(
    api_key=aoai_key,
    azure_endpoint=aoai_endpoint,
    api_version="2024-02-15-preview"
)

def generate_embeddings(text, model=None):
    if not text.strip():
        # Return a zero vector if text is empty
        return [0.0] * 1536
    try:
        deployment = model or aoai_deployment
        response = openai_client.embeddings.create(input=[text], model=deployment)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 1536

# NOTE: This index creation process (delete and recreate) is suitable for initial setup, development, and MVP scenarios.
# For production, consider blue/green deployment, index aliasing, or schema migration strategies to avoid downtime and data loss.
def create_index():
    # Always delete the index if it exists, to fully overwrite schema and data
    try:
        search_index_client.delete_index(ai_search_index)
        print(f"Deleted existing index: {ai_search_index}")
    except Exception as e:
        print(f"Index {ai_search_index} did not exist or could not be deleted: {e}")

    fields = [
        SimpleField(name="ID", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="BrowserFile", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="Title", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="DateIssued", type=SearchFieldDataType.DateTimeOffset, filterable=True, facetable=True),
        SimpleField(name="Published", type=SearchFieldDataType.Boolean, filterable=True),
        SimpleField(name="DocumentTypes", type=SearchFieldDataType.String, filterable=True),
        # Embedding fields (vector search)
        SearchField(
            name="KeyFactsVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile"
        ),
        SearchField(
            name="DocumentTextVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile"
        ),
        SearchField(
            name="CommentaryVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile"
        ),
        # Text fields for embedding
        SearchableField(name="KeyFacts", type=SearchFieldDataType.String),
        SearchableField(name="DocumentText", type=SearchFieldDataType.String),
        SearchableField(name="Commentary", type=SearchFieldDataType.String),
        SimpleField(name="NumberOfViolations", type=SearchFieldDataType.Int32, filterable=True, facetable=True),
        SimpleField(name="SettlementAmount", type=SearchFieldDataType.Double, filterable=True, facetable=True),
        SearchableField(name="OfacPenalty", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="AggregatePenalty", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="BasePenalty", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="StatutoryMaximum", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="VSD", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="Egregious", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="WillfulOrReckless", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="Criminal", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="RegulatoryProvisions", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="LegalIssues", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="SanctionPrograms", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="EnforcementCharacterizations", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="Industries", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="AggravatingFactors", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="MitigatingFactors", type=SearchFieldDataType.String, filterable=True),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            )
        ]
    )

    index = SearchIndex(
        name=ai_search_index,
        fields=fields,
        vector_search=vector_search
    )
    result = search_index_client.create_or_update_index(index)
    print("Index has been created")


def fetch_enforcement_actions():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM EnforcementActions")
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


def populate_index(batch_size=100):
    print("Populating index from SQL...")
    rows = fetch_enforcement_actions()
    print(f"Fetched {len(rows)} rows from SQL.")
    batch = []
    for i, row in enumerate(rows):
        # Convert ID to string for AI Search
        row["ID"] = str(row["ID"])
        # Generate embeddings for KeyFacts, DocumentText, Commentary
        for field, vec_field in [("KeyFacts", "KeyFactsVector"), ("DocumentText", "DocumentTextVector"), ("Commentary", "CommentaryVector")]:
            text = row.get(field) or ""
            row[vec_field] = generate_embeddings(text)
        batch.append(row)
        if len(batch) >= batch_size or i == len(rows)-1:
            try:
                search_client.upload_documents(documents=batch)
                print(f"Uploaded batch {i+1-len(batch)+1} to {i+1}")
            except Exception as e:
                print(f"Error uploading batch ending at row {row['ID']}: {e}")
            batch = []

if __name__ == "__main__":
    create_index()
    populate_index()