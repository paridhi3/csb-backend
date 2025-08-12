# app.py

import os
import json
import pandas as pd
import streamlit as st

# Import config objects
from config import llm, loader, embedding_model, client

# Import agents
from agents.reader_agent import process_case_study
from agents.categorize_agent import categorize_case_study
from agents.validation_agent import validate_case_study

# Constants
METADATA_FILE = "metadata.json"
VALIDATION_FILE = "validation_results.json"

# Streamlit UI setup
st.set_page_config(page_title="Case Study Categorizer", layout="wide", page_icon="📁")
st.title("📁 Case Study Categorizer")

# Sidebar navigation
page = st.sidebar.radio("Navigation", [
    "Categorizer & Validator",
    "Chatbot",
    "Search by Category & Domain"
])

# ========================================
# PAGE 1 - CATEGORIZER & VALIDATOR
# ========================================
if page == "Categorizer & Validator":
    uploaded_files = st.file_uploader(
        "Upload PDF or PPTX case study files",
        type=["pdf", "pptx"],
        accept_multiple_files=True
    )

    if st.button("Process Uploaded Files"):
        if not uploaded_files:
            st.warning("Please upload at least one file to process.")
            st.stop()

        all_metadata = []
        all_validation = []
        results = []

        for uploaded_file in uploaded_files:
            try:
                # Read file content in memory
                file_bytes = uploaded_file.read()
                case_text, _ = process_case_study(uploaded_file.name, file_bytes)

                categorization = categorize_case_study(case_text)
                summary = categorization.get("summary", "")
                category = categorization.get("category", "")
                domain = categorization.get("domain", "")
                technology = categorization.get("technology", "")

                all_metadata.append({
                    "file_name": uploaded_file.name,
                    "summary": summary,
                    "category": category,
                    "domain": domain,
                    "technology": technology
                })

                validation = validate_case_study(category, domain, technology)
                all_validation.append({
                    "file_name": uploaded_file.name,
                    **validation
                })

                results.append({
                    "File Name": uploaded_file.name,
                    "Category": category,
                    "Domain": domain,
                    "Technology": technology,
                    "Category Confidence": validation.get("category_confidence", 0.0),
                    "Domain Confidence": validation.get("domain_confidence", 0.0),
                    "Technology Confidence": validation.get("technology_confidence", 0.0),
                })

            except Exception as e:
                results.append({
                    "File Name": uploaded_file.name,
                    "Category": f"Error: {e}",
                    "Domain": "Error",
                    "Technology": "Error",
                    "Category Confidence": "Error",
                    "Domain Confidence": "Error",
                    "Technology Confidence": "Error"
                })

        # Save results in session
        st.session_state.results_df = pd.DataFrame(results)
        st.session_state.all_metadata = all_metadata
        st.session_state.all_validation = all_validation

        # Save to files
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_metadata, f, indent=4, ensure_ascii=False)
        with open(VALIDATION_FILE, "w", encoding="utf-8") as f:
            json.dump(all_validation, f, indent=4, ensure_ascii=False)

    # Show results
    if "results_df" in st.session_state:
        st.dataframe(st.session_state.results_df, use_container_width=True)

# ========================================
# PAGE 2 - CHATBOT
# ========================================
elif page == "Chatbot":
    st.markdown("<br>", unsafe_allow_html=True)
    st.header("Case Study Query Bot 💬")

    # Load metadata from session state or file
    if "all_metadata" in st.session_state:
        metadata = st.session_state.all_metadata
    elif os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = []

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_query = st.chat_input("Ask me about the case studies...")

    def answer_from_metadata(query: str):
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

    if user_query:
        meta_answer = answer_from_metadata(user_query)

        if meta_answer:
            st.session_state.chat_history.append(("user", user_query))
            st.session_state.chat_history.append(("bot", meta_answer))
        else:
            context_text = json.dumps(metadata, indent=2)
            prompt = (
                f"Answer the following question using this case study metadata:\n"
                f"{context_text}\n\nQuestion: {user_query}"
            )
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            bot_reply = response.choices[0].message.content.strip()
            st.session_state.chat_history.append(("user", user_query))
            st.session_state.chat_history.append(("bot", bot_reply))

    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(text)

# ========================================
# PAGE 3 - SEARCH BY CATEGORY & DOMAIN
# ========================================
elif page == "Search by Category & Domain":
    st.header("🔍 Search Case Studies by Category & Domain")

    # Load metadata from session state or file
    if "all_metadata" in st.session_state:
        metadata = st.session_state.all_metadata
    elif os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        st.warning("No metadata found. Please run 'Categorizer & Validator' first.")
        st.stop()

    df_meta = pd.DataFrame(metadata)

    categories = ["All"] + sorted(df_meta["category"].dropna().unique())
    domains = ["All"] + sorted(df_meta["domain"].dropna().unique())

    selected_category = st.selectbox("Select Category", categories)
    selected_domain = st.selectbox("Select Domain", domains)

    filtered_df = df_meta.copy()
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]
    if selected_domain != "All":
        filtered_df = filtered_df[filtered_df["domain"] == selected_domain]

    if filtered_df.empty:
        st.info("No case studies match the selected filters.")
    else:
        st.dataframe(filtered_df, use_container_width=True)
