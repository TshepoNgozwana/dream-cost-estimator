# connectors/__init__.py
from .openai_conn import OpenAIConnector

REGISTRY = {
    "OpenAI": OpenAIConnector(),
    # Add more later
}
