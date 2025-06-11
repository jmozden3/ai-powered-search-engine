# This script reads all rows from a CSV file, generates embeddings for the main text fields, and uploads them to Azure AI Search, recreating the index each run

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
import struct
import sys
import os
import pandas as pd
from typing import Any

from azure.core.credentials import AzureKeyCredential  
from azure.search.documents import SearchClient  
from datetime import datetime
from dotenv import load_dotenv  
from azure.core.credentials import AzureKeyCredential  

import openai
from openai import AzureOpenAI

load_dotenv()

# Azure AI Search settings
ai_search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
ai_search_key = os.environ["AZURE_SEARCH_KEY"]
ai_search_index = os.environ["AZURE_SEARCH_INDEX"]

# Azure OpenAI settings
aoai_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# CSV file configuration - update this filename as needed (assumes file is in current directory)
csv_filename = 'sample_data_subset.csv'

# Initialize Azure clients
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

def validate_csv_file():
    """Check if the CSV file exists and has data"""
    try:
        if not os.path.exists(csv_filename):
            print(f"ERROR: CSV file '{csv_filename}' does not exist")
            return False
        
        # Try to read the CSV file and check if it has data
        df = pd.read_csv(csv_filename)
        record_count = len(df)
        
        if record_count == 0:
            print(f"ERROR: CSV file '{csv_filename}' is empty")
            return False
        
        print(f"✓ CSV file '{csv_filename}' found with {record_count} records")
        print(f"✓ Columns found: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR reading CSV file: {e}")
        return False

def generate_embeddings(text, model=None):
    """Generate embeddings for given text"""
    if not text or not text.strip():
        # Return a zero vector if text is empty (3072 dimensions for text-embedding-3-large)
        return [0.0] * 3072
    try:
        deployment = model or aoai_deployment
        response = openai_client.embeddings.create(input=[text], model=deployment)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return [0.0] * 3072

def create_index():
    """Create or recreate the Azure AI Search index"""
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
        # Embedding fields (vector search) - 3072 dimensions for text-embedding-3-large
        SearchField(
            name="KeyFactsVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="myHnswProfile"
        ),
        SearchField(
            name="DocumentTextVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="myHnswProfile"
        ),
        SearchField(
            name="CommentaryVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
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
    print("✓ Index has been created")

def read_csv_data():
    """Fetch all data from CSV file"""
    try:
        # Read CSV with all values as strings initially
        df = pd.read_csv(csv_filename, dtype=str)
        
        # Convert DataFrame to list of dictionaries
        rows = df.to_dict('records')
        
        # Handle NaN values and only convert specific fields that need non-string types
        for row in rows:
            for key, value in row.items():
                # Handle NaN values - convert to appropriate defaults
                if pd.isna(value) or value == 'nan':
                    if key == 'DateIssued':
                        row[key] = None
                    elif key == 'Published':
                        row[key] = False
                    elif key in ['NumberOfViolations', 'SettlementAmount']:
                        row[key] = None
                    else:
                        row[key] = ""  # All other fields become empty strings
                else:
                    # Convert only the specific fields that need non-string types
                    if key == 'DateIssued' and value:
                        try:
                            parsed_date = pd.to_datetime(value)
                            if parsed_date.tz is None:
                                parsed_date = parsed_date.tz_localize('UTC')
                            row[key] = parsed_date.to_pydatetime()
                        except Exception as e:
                            print(f"Warning: Could not parse date '{value}' for row {row.get('ID', 'unknown')}: {e}")
                            row[key] = None
                    elif key == 'Published':
                        # Convert to boolean
                        row[key] = str(value).lower() in ['true', '1', 'yes', 'on']
                    elif key == 'NumberOfViolations' and value:
                        try:
                            row[key] = int(float(value))  # Convert via float first to handle decimals
                        except:
                            row[key] = None
                    elif key == 'SettlementAmount' and value:
                        try:
                            row[key] = float(value)
                        except:
                            row[key] = None
                    # All other fields stay as strings (which is what they already are)
        
        return rows
        
    except Exception as e:
        print(f"ERROR reading CSV file: {e}")
        raise

def populate_index(batch_size=25):
    """Populate the search index with data from CSV file"""
    print("Populating index from CSV...")
    rows = read_csv_data()
    print(f"Fetched {len(rows)} rows from CSV.")
    
    batch = []
    for i, row in enumerate(rows):
        # Convert ID to string for AI Search
        row["ID"] = str(row["ID"])
        
        # Generate embeddings for KeyFacts, DocumentText, Commentary
        print(f"Generating embeddings for row {i+1}/{len(rows)}...")
        for field, vec_field in [("KeyFacts", "KeyFactsVector"), ("DocumentText", "DocumentTextVector"), ("Commentary", "CommentaryVector")]:
            text = row.get(field) or ""
            row[vec_field] = generate_embeddings(text)
        
        batch.append(row)
        
        # Upload batch when it reaches batch_size or is the last row
        if len(batch) >= batch_size or i == len(rows)-1:
            try:
                search_client.upload_documents(documents=batch)
                print(f"✓ Uploaded batch {i+1-len(batch)+1} to {i+1}")
            except Exception as e:
                print(f"ERROR uploading batch ending at row {row['ID']}: {e}")
            batch = []
    
    print(f"✓ Index population complete. Processed {len(rows)} records.")

def main():
    """Main function that orchestrates the indexing process"""
    print("AZURE AI SEARCH INDEXING TOOL (CSV VERSION)")
    print("=" * 50)
    
    print("Validating prerequisites...")
    
    # Validate CSV file exists and has data
    if not validate_csv_file():
        print("❌ CSV validation failed. Please check your file path and ensure the file exists with data.")
        sys.exit(1)
    
    print("✓ All validations passed. Starting indexing process...")
    
    try:
        # Create the search index
        create_index()
        
        # Populate the index with data
        populate_index()
        
        print("\n🎉 Indexing process completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Indexing process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()