"""
orchestrator.py

Query routing orchestrator that analyzes user questions and routes them to the appropriate search method:
1. Basic Keyword Search with Filters (simple_search.py)
2. Advanced Document Search (document_rag.py)  
3. NL2SQL (placeholder)
"""

import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import AzureOpenAI
from enum import Enum

# Import your existing modules
from simple_search import basic_search
from document_rag import advanced_search

# Load environment variables
load_dotenv()

# Azure OpenAI configuration
API_VERSION = "2024-08-01-preview"
aoai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
aoai_key = os.environ.get("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

# Initialize Azure OpenAI client
aoai_client = AzureOpenAI(
    azure_endpoint=aoai_endpoint,
    api_key=aoai_key,
    api_version=API_VERSION
)

class QueryType(str, Enum):
    """Enumeration of supported query types"""
    BASIC_SEARCH = "basic_search"
    ADVANCED_SEARCH = "advanced_search"
    NL2SQL = "nl2sql"
    CLARIFICATION_NEEDED = "clarification_needed"

class QueryClassification(BaseModel):
    """
    Pydantic model for query classification results.
    """
    query_type: QueryType
    confidence: float  # 0.0 to 1.0
    reasoning: str
    clarification_question: Optional[str] = None

# Orchestrator prompt for query classification
ORCHESTRATOR_PROMPT = """You are a query classification expert for a legal enforcement document search system. Your job is to analyze user questions and classify them into one of these categories:

## QUERY TYPES:

### 1. BASIC_SEARCH (basic_search)
Use for queries that can be converted into structured search filters. These typically involve:
- Specific date ranges ("from 2020 to 2023", "in 2022")
- Specific programs/sanctions ("Iran sanctions", "OFAC violations", "Cuba program")
- Specific document types ("voluntary disclosures", "enforcement actions")
- Specific industries ("financial services", "shipping")
- Specific penalty amounts or ranges ("over $1 million", "penalties above $500k")
- Specific respondent characteristics ("US companies", "foreign entities")

Examples:
- "Find OFAC violations related to Iran sanctions from 2020 to 2023"
- "Show me voluntary disclosures in the financial services industry"
- "Search for cases involving penalties over $1 million in 2022"
- "Find enforcement actions against shipping companies for Cuba sanctions"

### 2. ADVANCED_SEARCH (advanced_search)
Use for complex questions that require semantic understanding and analysis of document content:
- Questions about legal interpretations or implications
- Questions asking "what", "how", "why" that need content analysis
- Questions requiring synthesis across multiple documents
- Questions about specific legal concepts or procedures
- Questions that need expert commentary analysis

Examples:
- "Can Iranian origin banknotes be imported into the U.S.?"
- "What are the compliance requirements for financial institutions dealing with sanctioned entities?"
- "How does OFAC determine penalty amounts?"
- "What constitutes a voluntary disclosure under OFAC regulations?"

### 3. NL2SQL (nl2sql)
Use for statistical or aggregate questions that would be better answered by database queries:
- Questions asking for counts, totals, averages, or statistics
- Questions comparing numbers across different categories
- Questions about trends over time (statistical trends, not interpretive)
- Questions asking for rankings or top/bottom lists

Examples:
- "How many violations were there in 2023?"
- "What's the average penalty amount for financial institutions?"
- "Which industry had the most violations last year?"
- "Show me the top 10 largest penalties by amount"

### 4. CLARIFICATION_NEEDED (clarification_needed)
Use when the query is too vague, ambiguous, or lacks sufficient context:
- Very short or unclear questions
- Questions that could apply to multiple categories
- Questions missing key context (time periods, specific topics, etc.)

Examples:
- "Tell me about sanctions"
- "What happened?"
- "Search for violations"

## INSTRUCTIONS:
1. Classify the query into one of the 4 types above
2. Provide a confidence score (0.0 to 1.0) for your classification
3. Explain your reasoning in 1-2 sentences
4. If classification is CLARIFICATION_NEEDED, provide a specific clarification question

## CONFIDENCE GUIDELINES:
- 0.9-1.0: Very clear classification, obvious category
- 0.7-0.8: Clear classification with minor ambiguity  
- 0.5-0.6: Moderate confidence, could potentially fit multiple categories
- 0.0-0.4: Low confidence, ambiguous or unclear

Be decisive but honest about confidence levels. When in doubt between BASIC_SEARCH and ADVANCED_SEARCH, prefer ADVANCED_SEARCH for better user experience."""

def classify_query(user_question: str) -> QueryClassification:
    """
    Classify user query into appropriate search type using LLM.
    
    Args:
        user_question: The user's input question
        
    Returns:
        QueryClassification: Classification result with type, confidence, and reasoning
    """
    try:
        print(f"🤔 Analyzing query type for: '{user_question}'")
        
        messages = [
            {"role": "system", "content": ORCHESTRATOR_PROMPT},
            {"role": "user", "content": f"Classify this query: {user_question}"}
        ]
        
        completion = aoai_client.beta.chat.completions.parse(
            model=aoai_deployment,
            messages=messages,
            response_format=QueryClassification,
        )
        
        classification = completion.choices[0].message.parsed
        print(f"📊 Classification: {classification.query_type.value} (confidence: {classification.confidence:.2f})")
        print(f"💭 Reasoning: {classification.reasoning}")
        
        return classification
        
    except Exception as e:
        print(f"❌ Error classifying query: {e}")
        # Default to advanced search on error
        return QueryClassification(
            query_type=QueryType.ADVANCED_SEARCH,
            confidence=0.5,
            reasoning="Error occurred during classification, defaulting to advanced search"
        )

def nl2sql_placeholder(user_question: str) -> Dict[str, Any]:
    """
    Placeholder function for NL2SQL functionality.
    This would eventually convert natural language questions to SQL queries
    and execute them against a structured database.
    
    Args:
        user_question: The user's question
        
    Returns:
        Dict with placeholder response
    """
    print("🔧 NL2SQL functionality is not yet implemented")
    
    return {
        "question": user_question,
        "query_type": "nl2sql",
        "status": "not_implemented",
        "message": "Statistical and aggregate queries are not yet supported. This feature is coming soon!",
        "suggested_alternative": "Try rephrasing your question to search for specific documents or cases instead.",
        "documents": [],
        "answer": "I apologize, but I cannot process statistical queries yet. This feature is under development. Please try asking about specific documents, cases, or legal concepts instead."
    }

def process_query_with_routing(user_question: str) -> Dict[str, Any]:
    """
    Main orchestrator function that analyzes the query and routes to appropriate search method.
    
    Args:
        user_question: The user's input question
        
    Returns:
        Dict: Response from the selected search method, enhanced with routing metadata
    """
    print("🚀 Starting query orchestration...")
    print("="*60)
    
    # Step 1: Classify the query
    classification = classify_query(user_question)
    
    # Step 2: Route to appropriate handler based on classification
    try:
        if classification.query_type == QueryType.CLARIFICATION_NEEDED:
            return {
                "question": user_question,
                "query_type": "clarification_needed",
                "classification": classification.dict(),
                "clarification_question": classification.clarification_question,
                "message": "I need more information to help you effectively.",
                "documents": [],
                "answer": f"I need clarification to provide the best results. {classification.clarification_question}"
            }
            
        elif classification.query_type == QueryType.BASIC_SEARCH:
            print("📋 Routing to Basic Keyword Search with Filters...")
            result = basic_search(user_question)
            
            # Transform basic search result to match expected format
            return {
                "question": user_question,
                "query_type": "basic_search",
                "classification": classification.dict(),
                "search_parameters": result,
                "documents": [],  # Basic search returns parameters, not documents
                "answer": f"I've processed your query into structured search parameters. The system would search for documents matching these criteria: {json.dumps(result, indent=2)}"
            }
            
        elif classification.query_type == QueryType.ADVANCED_SEARCH:
            print("🔍 Routing to Advanced Document Search...")
            result = advanced_search(user_question)
            
            # Enhance result with classification metadata
            result["query_type"] = "advanced_search"
            result["classification"] = classification.dict()
            return result
            
        elif classification.query_type == QueryType.NL2SQL:
            print("📊 Routing to NL2SQL...")
            result = nl2sql_placeholder(user_question)
            result["classification"] = classification.dict()
            return result
            
        else:
            # Fallback to advanced search
            print("⚠️ Unknown classification, defaulting to Advanced Document Search...")
            result = advanced_search(user_question)
            result["query_type"] = "advanced_search_fallback"
            result["classification"] = classification.dict()
            return result
            
    except Exception as e:
        print(f"❌ Error during query processing: {e}")
        return {
            "question": user_question,
            "query_type": "error",
            "error": str(e),
            "message": "An error occurred while processing your query.",
            "documents": [],
            "answer": "I apologize, but I encountered an error while processing your question. Please try rephrasing your query."
        }

def example_usage():
    """Example usage showing different query types"""
    
    example_queries = [
        # Basic search examples
        "Find OFAC violations related to Iran sanctions from 2020 to 2023",
        "Show me voluntary disclosures in the financial services industry",
        
        # Advanced search examples  
        "Can Iranian origin banknotes be imported into the U.S.?",
        "What are the compliance requirements for financial institutions?",
        
        # NL2SQL examples
        "How many violations were there in 2023?",
        "What's the average penalty amount for financial institutions?",
        
        # Clarification needed examples
        "Tell me about sanctions",
        "What happened?"
    ]
    
    for query in example_queries:
        print("\n" + "="*80)
        print(f"Example Query: {query}")
        print("="*80)
        
        result = process_query_with_routing(query)
        
        print("\n📋 Result Summary:")
        print(f"Query Type: {result.get('query_type', 'unknown')}")
        if 'classification' in result:
            print(f"Confidence: {result['classification']['confidence']:.2f}")
            print(f"Reasoning: {result['classification']['reasoning']}")

if __name__ == "__main__":
    print("🎛️ Query Orchestrator - Intelligent Routing System")
    print("="*60)
    
    # Run examples
    # example_usage()
    
    print("\n" + "="*60) 
    print("💬 Interactive Mode")
    print("="*60)
    
    while True:
        user_input = input("\n🔍 Enter your question (or 'quit' to exit): ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        result = process_query_with_routing(user_input)
        
        print(f"\n📊 Query Type: {result.get('query_type', 'unknown')}")
        if 'classification' in result:
            print(f"🎯 Confidence: {result['classification']['confidence']:.2f}")
        
        print(f"\n💬 Answer:")
        print(result.get('answer', 'No answer available'))
        
        if result.get('query_type') == 'clarification_needed':
            print(f"\n❓ Clarification needed: {result.get('clarification_question', '')}")

    print("👋 Goodbye!")