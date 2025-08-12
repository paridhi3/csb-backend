# agents/categorize_agent.py

from config import client  # Import centralized AzureOpenAI client
import os

def categorize_case_study(text: str) -> dict:
    """
    Categorizes a case study into:
    - Summary
    - Category
    - Domain
    - Technology
    """
    prompt = f"""
    You are a case study classification assistant.
    From the given text, provide:
    1. A concise summary (3-5 sentences).
    2. The Category (business area).
    3. The Domain (industry).
    4. The Technology (tools, platforms, or techniques used).

    Case Study:
    {text}

    Respond in JSON:
    {{
        "summary": "...",
        "domain": "...",
        "category": "...",
        "technology": "..."
    }}
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        return eval(response.choices[0].message.content.strip())
    except Exception:
        return {
            "summary": "Unknown",
            "domain": "Unknown",
            "category": "Unknown",
            "technology": "Unknown"
        }
