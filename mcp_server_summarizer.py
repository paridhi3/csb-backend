# mcp_server_summarizer.py

"""
MCP Tool Server for summarization and categorization using the OpenAI LLM API.
Provides tools to summarize text and categorize it into category, domain and technologies.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents.mcp import MCPToolServer, tool

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SummarizerMCPServer(MCPToolServer):
    @tool
    async def summarize(self, text: str):
        """
        Summarizes the provided text using OpenAI chat completion.
        """
        prompt = f"Summarize this technical/business case study in detail:\n\n{text[:3500]}"
        response = await openai_client.chat.completions.acreate(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    @tool
    async def categorize(self, text: str):
        """
        Categorizes the text by listing category, domain and technologies.
        """
        prompt = (
            f"Given the following case study, list:\n"
            f"1. Category (e.g., case study, research, tutorial)\n"
            f"2. Domain (business, finance, healthcare, etc.)\n"
            f"3. Technologies used (comma-separated list):\n\n{text[:3000]}"
        )
        response = await openai_client.chat.completions.acreate(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    SummarizerMCPServer().serve()