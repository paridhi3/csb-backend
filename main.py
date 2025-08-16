from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import json

from agents.reader_agent import process_case_study
from agents.categorize_agent import categorize_case_study
from agents.validation_agent import validate_case_study
from config import client

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

METADATA_FILE = "metadata.json"

@app.post("/process")
async def process_files(files: List[UploadFile]):
    all_metadata = []
    all_validation = []

    for file in files:
        file_bytes = await file.read()
        case_text, _ = process_case_study(file.filename, file_bytes)

        categorization = categorize_case_study(case_text)
        validation = validate_case_study(
            categorization.get("category", ""),
            categorization.get("domain", ""),
            categorization.get("technology", "")
        )

        metadata = {
            "file_name": file.filename,
            "summary": categorization.get("summary", ""),
            "category": categorization.get("category", ""),
            "domain": categorization.get("domain", ""),
            "technology": categorization.get("technology", "")
        }
        all_metadata.append(metadata)
        all_validation.append({"file_name": file.filename, **validation})

    # Save metadata to file (optional, to keep in sync)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=4, ensure_ascii=False)

    return {"metadata": all_metadata, "validation": all_validation}

def answer_from_metadata(query: str, metadata: list):
    q = query.lower()
    if "how many" in q and "technology" in q:
        tech_counts = {}
        for m in metadata:
            tech = m.get("technology", "").lower()
            if tech:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
        return f"Technology counts: {tech_counts}"
    elif "how many" in q and "category" in q:
        cat_counts = {}
        for m in metadata:
            cat = m.get("category", "").lower()
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        return f"Category counts: {cat_counts}"
    return None

from pydantic import BaseModel
class QueryRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat_with_metadata(request: QueryRequest):
    query = request.query

    # Read metadata.json content
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata_parsed = json.load(f)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing metadata JSON file")

    # Step 1: Try metadata-based rule
    meta_answer = answer_from_metadata(query, metadata_parsed)
    if meta_answer:
        return {"response": meta_answer}

    # Step 2: Use Azure OpenAI LLM
    try:
        context_text = json.dumps(metadata_parsed, indent=2)
        prompt = (
            f"Answer the following question using this case study metadata. Format the response in Markdown:\n"
            f"{context_text}\n\nQuestion: {query}"
        )


        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        bot_reply = response.choices[0].message.content.strip()
        return {"response": bot_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(category: str = None, domain: str = None):
    if not os.path.exists(METADATA_FILE):
        raise HTTPException(status_code=400, detail="Metadata file not found. Please process case studies first.")

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    filtered = metadata

    # Normalize inputs for case-insensitive comparison and handle "All"
    cat_filter = category.lower() if category and category.lower() != "all" else None
    dom_filter = domain.lower() if domain and domain.lower() != "all" else None

    if cat_filter and dom_filter:
        # Filter both category AND domain
        filtered = [
            m for m in filtered
            if m.get("category", "").lower() == cat_filter and m.get("domain", "").lower() == dom_filter
        ]
    elif cat_filter:
        # Only filter category
        filtered = [
            m for m in filtered
            if m.get("category", "").lower() == cat_filter
        ]
    elif dom_filter:
        # Only filter domain
        filtered = [
            m for m in filtered
            if m.get("domain", "").lower() == dom_filter
        ]
    # else no filters applied, return all metadata

    return {"results": filtered}