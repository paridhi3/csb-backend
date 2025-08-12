# agents/validation_agent.py

from config import client  # Import the shared AzureOpenAI client
import os

def validate_case_study(category: str, domain: str, technology: str) -> dict:
    """
    Validates extracted case study details and gives confidence scores (0-1).
    """
    prompt = f"""
    Validate the extracted case study details below and return a JSON object
    with confidence scores for each field between 0 and 1.

    Category: {category}
    Domain: {domain}
    Technology: {technology}

    Respond in JSON:
    {{
        "category_confidence": 0.xx,
        "domain_confidence": 0.xx,
        "technology_confidence": 0.xx
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
            "category_confidence": 0.0,
            "domain_confidence": 0.0,
            "technology_confidence": 0.0
        }
