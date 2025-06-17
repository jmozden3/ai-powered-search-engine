import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable message content capture BEFORE imports
os.environ['OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT'] = 'true'

# Import OpenTelemetry components
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor

# Global flag to ensure tracing is only set up once
_tracing_initialized = False

def setup_tracing():
    """Configure OpenTelemetry tracing for OpenAI SDK calls."""
    global _tracing_initialized
    
    if _tracing_initialized:
        print("✓ Tracing already initialized")
        return
    
    print("Setting up tracing...")
    
    # Instrument OpenAI SDK
    OpenAIInstrumentor().instrument()
    
    # Configure Azure Monitor
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        configure_azure_monitor(connection_string=connection_string)
        print("✓ Tracing configured successfully")
    else:
        print("⚠ No Application Insights connection string found")
    
    _tracing_initialized = True