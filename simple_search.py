"""
simple_search.py

Basic LLM inference with structured outputs for search query processing.
Uses Azure OpenAI with structured output to parse user queries into search parameters.
"""

import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AzureOpenAI
from prompts import simple_search_prompt

# Load environment variables
load_dotenv()

# Azure OpenAI configuration
API_VERSION = "2024-08-01-preview"
aoai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
aoai_key = os.environ.get("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")


# Initialize Azure OpenAI client
try:
    aoai_client = AzureOpenAI(
        azure_endpoint=aoai_endpoint,
        api_key=aoai_key,
        api_version=API_VERSION
    )
except Exception as e:
    print(f"Failed to initialize Azure OpenAI client: {e}")
    raise


class SearchParameters(BaseModel):
    """
    Pydantic model for structured search parameters.
    """
    DateIssuedBegin: Optional[int] = None
    DateIssuedEnd: Optional[int] = None
    LegalIssue: List[str] = []
    Program: List[str] = []
    DocumentType: List[str] = []
    RegulatoryProvision: List[str] = []
    Published: Optional[bool] = None
    EnforcementCharacterization: List[str] = []
    NumberOfViolationsLow: Optional[int] = None
    NumberOfViolationsHigh: Optional[int] = None
    OFACPenalty: List[str] = []
    AggregatePenalty: List[str] = []
    Industry: List[str] = []
    RespondentNationality: List[str] = []
    VoluntaryDisclosure: List[str] = []
    EgregiousCase: List[str] = []
    KeyWords: str = ""
    ExcludeCommentaries: bool = False


def user_query_to_structured_outputs(user_input: str) -> Optional[SearchParameters]:
    """
    Function 2: Convert user query to structured outputs using LLM.
    
    Parameters:
    - user_input (str): The raw user query
    
    Returns:
    - Optional[SearchParameters]: Structured output or None if error
    """
    try:
        print(f"Step 2: 🔄 Converting user query to structured outputs...")
        
        messages = [
            {"role": "system", "content": simple_search_prompt},
            {"role": "user", "content": user_input}
        ]
        
        completion = aoai_client.beta.chat.completions.parse(
            model=aoai_deployment,
            messages=messages,
            response_format=SearchParameters,
        )
        
        print("Step 2: ✅ Structured outputs received from LLM")
        structured_output = completion.choices[0].message.parsed
        print(f"Structured Output: {structured_output}")
        return structured_output
        
    except Exception as e:
        print(f"Step 2: ❌ Error getting structured outputs: {e}")
        return None


def structured_outputs_mapping(search_params: SearchParameters) -> dict:
    """
    Function 3: Map human-readable display values to ID codes.
    
    Parameters:
    - search_params (SearchParameters): Structured outputs from function 2
    
    Returns:
    - dict: Parameters with display values mapped to IDs
    """
    try:
        print("Step 3: 🔄 Mapping display values to ID codes...")
        
        # Convert to dict for manipulation
        params_dict = search_params.model_dump()
        mapped_params = params_dict.copy()
        
        # Fields that need ID mapping
        list_fields_to_map = [
            'LegalIssue', 'Program', 'DocumentType', 'RegulatoryProvision',
            'EnforcementCharacterization', 'OFACPenalty', 'AggregatePenalty',
            'Industry', 'RespondentNationality', 'VoluntaryDisclosure', 'EgregiousCase'
        ]
        
        # Map each field's human-readable values to IDs
        for field_name in list_fields_to_map:
            if field_name in mapped_params and mapped_params[field_name]:
                original_values = mapped_params[field_name]
                mapped_values = []
                
                for human_readable_value in original_values:
                    # Placeholder: map every value to ID=1
                    # Later: connect to actual data source for true ID mapping
                    mapped_id = 1
                    mapped_values.append(mapped_id)
                    print(f"   Mapped '{human_readable_value}' → ID: {mapped_id}")
                
                mapped_params[field_name] = mapped_values
        
        print("Step 3: ✅ Display values mapped to IDs successfully")
        return mapped_params
        
    except Exception as e:
        print(f"Step 3: ❌ Error in mapping process: {e}")
        return search_params.model_dump()


def create_final_json_payload(mapped_params: dict) -> dict:
    """
    Function 4: Create the final JSON payload ready for search API.
    
    Parameters:
    - mapped_params (dict): Parameters with mapped IDs from function 3
    
    Returns:
    - dict: Final JSON payload (the actual search parameters)
    """
    try:
        print("Step 4: 🔄 Creating final JSON payload...")
        
        # Return the actual JSON payload - just the search parameters
        print("Step 4: ✅ Final JSON payload created successfully")
        return mapped_params
        
    except Exception as e:
        print(f"Step 4: ❌ Error creating final payload: {e}")
        return None


def basic_search(user_input: str) -> dict:
    """
    Main function for basic search with filters - converts user query to structured search parameters.
    
    Parameters:
    - user_input (str): The raw user query
    
    Returns:
    - dict: Final JSON payload with search parameters or None if error
    """
    print(f"Step 1: 🚀 Starting basic search process for query: '{user_input}'")
    print("="*60)
    
    # Function 2: Get structured outputs from LLM
    structured_outputs = user_query_to_structured_outputs(user_input)
    if not structured_outputs:
        print("Step 1: ❌ Failed at function 2 (structured outputs)")
        return None
    
    # Function 3: Map display values to IDs
    mapped_params = structured_outputs_mapping(structured_outputs)
    if not mapped_params:
        print("Step 1: ❌ Failed at function 3 (mapping)")
        return None
    
    # Function 4: Create final payload
    final_payload = create_final_json_payload(mapped_params)
    if not final_payload:
        print("Step 1: ❌ Failed at function 4 (final payload)")
        return None
    
    print("="*60)
    print("Step 1: 🎉 Basic search process completed successfully!")
    return final_payload


def example_usage():
    """Example usage of the complete 4-function process."""
    
    # Example queries
    example_queries = [
        "Find OFAC violations related to Iran sanctions from 2020 to 2023",
        "Show me voluntary disclosures in the financial services industry",
        "Search for cases involving global distribution systems with penalties over $1 million"
    ]
    
    for query in example_queries:
        print("\n" + "="*80)
        print(f"Example Query: {query}")
        print("="*80)
        
        # Run complete process
        final_json = basic_search(query)
        
        if final_json:
            print("\n📋 Final JSON Payload:")
            print(json.dumps(final_json, indent=2))
        else:
            print("❌ Process failed - Could not create final JSON payload")


if __name__ == "__main__":
    print("🔍 Simple Search Query Parser - 4-Function Pipeline")
    print("="*60)
    
    # Run example usage
    #example_usage()
    
    print("\n" + "="*60)
    print("💬 Interactive Mode")
    print("="*60)
    
    # Interactive mode
    while True:
        user_input = input("\n🔍 Enter your search query (or 'quit' to exit): ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        # Run complete 4-function process
        final_json = basic_search(user_input)
        
        if final_json:
            print("\n📋 Final JSON Payload:")
            print(json.dumps(final_json, indent=2))
        else:
            print("❌ Process failed - Could not create final JSON payload")
            print("Please try again with a different query.")
    
    print("👋 Goodbye!")