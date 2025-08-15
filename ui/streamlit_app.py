from __future__ import annotations

import requests
import streamlit as st


st.set_page_config(page_title="jd-copilot", layout="wide")
st.title("🎯 jd-copilot: Job Description AI Assistant")

api_url = st.text_input("API base URL", value="http://localhost:8000")

# Load companies for dropdown
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_companies():
    try:
        response = requests.get(f"{api_url}/companies", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("companies", [])
    except:
        pass
    return []

tab1, tab2 = st.tabs(["💬 JD Q&A", "📝 Resume Match"])

with tab1:
    st.header("Ask Questions About Job Descriptions")
    
    # Question input
    q = st.text_area("Your Question", 
                     value="What is the job title and location for this role?", 
                     height=100,
                     help="Ask any question about the job descriptions")
    
    # Filters in columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Company dropdown with search
        companies = load_companies()
        if companies:
            company = st.selectbox(
                "Filter by Company", 
                options=[""] + companies,
                help="Select a specific company to filter results"
            )
        else:
            company = st.text_input("Filter: Company", "", help="Type company name")
            if companies == []:
                st.warning("Could not load companies. Make sure the API is running.")
    
    with col2:
        year = st.text_input("Filter: Year", "", help="e.g., 2024")
    
    # Advanced options
    with st.expander("Advanced Options"):
        top_k = st.slider("Number of results", min_value=1, max_value=10, value=3)
        show_metadata = st.checkbox("Show metadata", value=False)
    
    if st.button("🔍 Ask", type="primary"):
        if not q.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Searching and analyzing..."):
                try:
                    payload = {
                        "question": q,
                        "filters": {"company": company or None, "year": int(year) if year else None},
                        "top_k": top_k,
                    }
                    r = requests.post(f"{api_url}/query", json=payload, timeout=120)
                    
                    if r.status_code == 200:
                        data = r.json()
                        
                        # Show LLM answer first if available
                        if data.get("answer"):
                            st.success("🤖 AI Answer:")
                            st.write(data["answer"])
                            st.divider()
                        
                        # Show snippets
                        snippets = data.get("snippets", [])
                        if snippets:
                            st.info(f"📄 Found {len(snippets)} relevant snippets:")
                            
                            for i, snippet in enumerate(snippets, 1):
                                with st.expander(f"Result {i} (Score: {snippet['score']:.3f})"):
                                    st.write(snippet["text"])
                                    
                                    if show_metadata:
                                        st.json(snippet["metadata"])
                        else:
                            st.warning("No relevant results found. Try adjusting your filters or question.")
                            
                    else:
                        st.error(f"API Error: {r.status_code} - {r.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The question might be too complex or the server is busy.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    resume = st.text_area("Paste resume text")
    top_k = st.slider("Top K", min_value=1, max_value=10, value=3)
    if st.button("Match"):
        payload = {"resume_text": resume, "top_k": top_k}
        r = requests.post(f"{api_url}/query/resume_match", json=payload, timeout=60)
        st.json(r.json())


