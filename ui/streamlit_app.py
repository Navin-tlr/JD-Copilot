from __future__ import annotations

import requests
import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Y² - Placement Co-Pilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the Y^2 design aesthetic
st.markdown("""
<style>
    /* Dark theme matching Figma design */
    .main {
        background-color: #363232;
        color: white;
    }
    
    /* Custom styling for the app */
    .stApp {
        background-color: #363232;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom card styling */
    .y2-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(10px);
    }
    
    .y2-title {
        font-family: 'PP Neue Bit', sans-serif;
        font-weight: bold;
        font-size: 32px;
        color: white;
        text-align: center;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    .y2-subtitle {
        font-family: 'PP Neue Bit', sans-serif;
        font-size: 18px;
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        margin-bottom: 32px;
        line-height: 1.4;
    }
    
    .y2-tagline {
        font-family: 'PP Neue Bit', sans-serif;
        font-size: 16px;
        color: rgba(255, 255, 255, 0.6);
        text-align: center;
        font-style: italic;
        margin-bottom: 40px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        padding: 12px 16px;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }
    
    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        padding: 16px;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: bold;
        padding: 12px 32px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
    }
    
    /* Tab styling */
    .stTabs > div > div > div > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs > div > div > div > div > div > button {
        background-color: transparent;
        color: rgba(255, 255, 255, 0.7);
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        margin: 0 4px;
    }
    
    .stTabs > div > div > div > div > div > button[aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div > div > div {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .stSlider > div > div > div > div > div > div > div > div > div {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
    }
    
    /* Success/Info/Warning styling */
    .stSuccess {
        background-color: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 12px;
        padding: 16px;
    }
    
    .stInfo {
        background-color: rgba(33, 150, 243, 0.1);
        border: 1px solid rgba(33, 150, 243, 0.3);
        border-radius: 12px;
        padding: 16px;
    }
    
    .stWarning {
        background-color: rgba(255, 152, 0, 0.1);
        border: 1px solid rgba(255, 152, 0, 0.3);
        border-radius: 12px;
        padding: 16px;
    }
    
    .stError {
        background-color: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 12px;
        padding: 16px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: white;
        padding: 12px 16px;
    }
    
    .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 16px;
        margin-top: 8px;
    }
    
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .y2-title {
            font-size: 28px;
        }
        
        .y2-subtitle {
            font-size: 16px;
        }
        
        .y2-tagline {
            font-size: 14px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Main header with Y^2 branding
st.markdown("""
<div style="text-align: center; padding: 40px 20px;">
    <div class="y2-title">Y²</div>
    <div class="y2-subtitle">I'm your placement co-pilot. I don't hold hands. I hand you weapons</div>
    <div class="y2-tagline">I'm not here for chit-chat. Aim, fire, and I deliver..</div>
</div>
""", unsafe_allow_html=True)

# API Configuration
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        api_url = st.text_input(
            "🔗 API Base URL",
            value="http://localhost:8000",
            help="Configure the backend API endpoint"
        )

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

# Main tabs
tab1, tab2 = st.tabs(["🎯 JD Q&A", "📋 Resume Match"])

with tab1:
    st.markdown("""
    <div class="y2-card">
        <h3 style="color: white; margin-bottom: 20px;">🎯 Ask Questions About Job Descriptions</h3>
    """, unsafe_allow_html=True)
    
    # Question input
    q = st.text_area(
        "Your Question",
        value="What is the job title and location for this role?",
        height=120,
        help="Ask any question about the job descriptions",
        placeholder="e.g., What skills are required for marketing roles? What companies are hiring in Bangalore?"
    )
    
    # Filters in columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Company dropdown with search
        companies = load_companies()
        if companies:
            company = st.selectbox(
                "🏢 Filter by Company",
                options=[""] + companies,
                help="Select a specific company to filter results"
            )
        else:
            company = st.text_input("🏢 Filter: Company", "", help="Type company name")
            if companies == []:
                st.warning("⚠️ Could not load companies. Make sure the API is running.")
    
    with col2:
        year = st.text_input("📅 Filter: Year", "", help="e.g., 2024")
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)
        show_metadata = st.checkbox("Show metadata", value=False)
    
    # Ask button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Ask", type="primary", use_container_width=True):
            if not q.strip():
                st.error("❌ Please enter a question.")
            else:
                with st.spinner("🔍 Searching and analyzing..."):
                    try:
                        payload = {
                            "question": q,
                            "filters": {"company": company if company else None, "year": int(year) if year else None},
                            "top_k": top_k,
                        }
                        r = requests.post(f"{api_url}/query", json=payload, timeout=120)
                        
                        if r.status_code == 200:
                            data = r.json()
                            
                            # Show LLM answer first if available
                            if data.get("answer"):
                                st.success("🤖 AI Answer:")
                                st.markdown(data["answer"])
                                st.divider()
                            
                            # Show snippets
                            snippets = data.get("snippets", [])
                            if snippets:
                                st.info(f"📄 Found {len(snippets)} relevant snippets:")
                                
                                for i, snippet in enumerate(snippets, 1):
                                    with st.expander(f"Result {i} (Score: {snippet['score']:.3f})"):
                                        st.markdown(snippet["text"])
                                        
                                        if show_metadata:
                                            st.json(snippet["metadata"])
                            else:
                                st.warning("⚠️ No relevant results found. Try adjusting your filters or question.")
                                
                        else:
                            st.error(f"❌ API Error: {r.status_code} - {r.text}")
                            
                    except requests.exceptions.Timeout:
                        st.error("⏰ Request timed out. The question might be too complex or the server is busy.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("""
    <div class="y2-card">
        <h3 style="color: white; margin-bottom: 20px;">📋 Resume Matching</h3>
    """, unsafe_allow_html=True)
    
    resume = st.text_area(
        "📄 Paste your resume text",
        height=200,
        placeholder="Paste your resume content here to find matching job opportunities...",
        help="Upload or paste your resume text to find relevant job matches"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        top_k = st.slider("Top K matches", min_value=1, max_value=10, value=5)
    
    with col2:
        if st.button("🎯 Match Resume", type="primary", use_container_width=True):
            if not resume.strip():
                st.error("❌ Please paste your resume text.")
            else:
                with st.spinner("🔍 Analyzing resume and finding matches..."):
                    try:
                        payload = {"resume_text": resume, "top_k": top_k}
                        r = requests.post(f"{api_url}/query/resume_match", json=payload, timeout=60)
                        
                        if r.status_code == 200:
                            st.success("✅ Resume analysis complete!")
                            st.json(r.json())
                        else:
                            st.error(f"❌ API Error: {r.status_code} - {r.text}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 40px 20px; color: rgba(255, 255, 255, 0.5); font-size: 14px;">
    Powered by Y² - Your Placement Co-Pilot
</div>
""", unsafe_allow_html=True)


