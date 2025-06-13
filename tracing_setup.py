# tracing_setup.py
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
import os

def setup_tracing():
    # Step 1: Instrument OpenAI SDK
    OpenAIInstrumentor().instrument()

    # Step 2: Connect to your Foundry project
    foundry_project_endpoint = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")

    project_client = AIProjectClient(
        endpoint=foundry_project_endpoint,
        credential=DefaultAzureCredential(),
    )

    # Step 3: Get connection string to Application Insights
    connection_string = project_client.telemetry.get_connection_string()

    # Step 4: Configure Azure Monitor to export traces
    configure_azure_monitor(connection_string=connection_string)
