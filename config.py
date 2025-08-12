# config.py

import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_community.document_loaders import AzureBlobStorageContainerLoader
from langchain.embeddings import AzureOpenAIEmbeddings
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient

# Load environment variables
load_dotenv()

# === LangChain Azure Chat Model ===
llm = AzureChatOpenAI(
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_END_POINT"),
    openai_api_version=os.getenv("API_VERSION"),
    deployment_name=os.getenv("MODEL_NAME"),
    temperature=0
)

# === Azure Blob Loader (LangChain wrapper) ===
loader = AzureBlobStorageContainerLoader(
    conn_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
    container=os.getenv("AZURE_STORAGE_CONTAINER_NAME")
)

# === Azure Embedding Model ===
embedding_model = AzureOpenAIEmbeddings(
    azure_deployment="text-embedding-ada-002",
    openai_api_version=os.getenv("API_VERSION"),
    azure_endpoint="https://gen-cim-eas-dep-genai-train-openai.openai.azure.com/",
    chunk_size=500
)

# === Raw Azure OpenAI Client (for chatbot & direct completions) ===
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# === Azure Blob Service Client (direct access) ===
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

if not AZURE_STORAGE_CONNECTION_STRING or not AZURE_STORAGE_CONTAINER_NAME:
    raise ValueError("Azure Blob Storage environment variables are missing in .env")

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)
