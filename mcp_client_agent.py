# mcp_client_agent.py

from langchain.vectorstores import Chroma
from langchain.embeddings import AzureOpenAIEmbeddings
import os

class MCPAgentClient:
    def __init__(self):
        self.index = None
        self.documents = []
        self.embedding_model = AzureOpenAIEmbeddings(deployment_name="text-embedding-ada-002")
        self.persist_dir = "./chroma_db"  # directory for Chroma persistence

    async def build_index(self):
        # Initialize or load Chroma index
        self.index = Chroma(
            collection_name="case_studies",
            embedding_function=self.embedding_model,
            persist_directory=self.persist_dir
        )
        # Add documents' summaries to Chroma
        texts = [doc["summary"] for doc in self.documents]
        self.index.add_texts(texts)
        self.index.persist()

    async def ask_multi_file(self, query):
        # Query the Chroma vector store for relevant documents
        if not self.index:
            print("Index not built yet.")
            return None
        docs = self.index.similarity_search(query)
        answers = "\n\n".join([doc.page_content for doc in docs])
        return answers