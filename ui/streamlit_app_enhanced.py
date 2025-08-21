import streamlit as st
import requests
import json
from typing import Dict, Any, List

# Page configuration
st.set_page_config(
    page_title="JD-Copilot - Placement Analytics Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        flex: 1;
        margin: 0 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🎯 JD-Copilot - Placement Analytics Platform</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["🏠 Home", "🔍 Smart Q&A", "📊 Analytics Dashboard", "💼 Resume Matcher", "⚙️ System Status"]
)

# API configuration (allow override from UI)
api_url = st.text_input("API base URL", value="http://localhost:8000")

def make_api_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make API request with error handling"""
    try:
        if method == "GET":
            response = requests.get(f"{api_url}{endpoint}")
        else:
            response = requests.post(f"{api_url}{endpoint}", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API server. Is it running?"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

@st.cache_data(ttl=300)
def get_companies_list() -> List[str]:
    """Get companies list from API with fallback (cached)"""
    try:
        companies_data = make_api_request("/companies")
        if "error" not in companies_data and "companies" in companies_data:
            return companies_data["companies"]
        else:
            # Fallback to empty list if API fails
            return []
    except Exception:
        return []

# Home page
if page == "🏠 Home":
    st.markdown("## 🚀 Welcome to JD-Copilot!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✨ What's New in v2.0
        
        **🎯 Intelligent Query Routing**
        - Automatically detects query type
        - Routes to optimal data source (SQL/RAG/Hybrid)
        - Multi-hop analysis for complex questions
        
        **📊 Structured Data Analytics**
        - Company statistics and trends
        - Salary analysis and comparisons
        - Skills demand insights
        
        **🔍 Enhanced RAG System**
        - Company-specific filtering
        - Comprehensive chunk retrieval
        - Context-aware answers
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 Key Features
        
        **Smart Q&A System**
        - Ask questions in natural language
        - Get company-specific or global insights
        - Automatic query classification
        
        **Analytics Dashboard**
        - Placement statistics
        - Company comparisons
        - Skills analysis
        
        **Resume Matching**
        - Match your skills to job requirements
        - Get personalized improvement plans
        - Company-specific recommendations
        """)
    
    # Quick stats preview
    st.markdown("### 📊 Quick Stats Preview")
    stats = make_api_request("/stats/placement")
    
    if "error" not in stats and "data" in stats:
        data = stats.get("data", {})
        
        # Safe extraction with defaults
        company_count = data.get('company_count', 0) or 0
        role_count = data.get('role_count', 0) or 0
        avg_salary = data.get('avg_max_salary', 0) or 0
        top_skills = data.get('top_skills', []) or []
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <h3>{company_count}</h3>
                <p>Companies</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <h3>{role_count}</h3>
                <p>Roles</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Safe formatting to prevent TypeError with None values
            if avg_salary is not None and avg_salary > 0:
                salary_display = f"₹{avg_salary:.1f}L"
            else:
                salary_display = "₹0.0L"
            
            st.markdown(f"""
            <div class="stat-box">
                <h3>{salary_display}</h3>
                <p>Avg Max Salary</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            skill_count = len(top_skills) if top_skills else 0
            st.markdown(f"""
            <div class="stat-box">
                <h3>{skill_count}</h3>
                <p>Skill Categories</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        error_msg = stats.get('error', 'Unknown error') if isinstance(stats, dict) else 'Failed to load stats'
        st.error(f"Could not load stats: {error_msg}")

# Smart Q&A page
elif page == "🔍 Smart Q&A":
    st.markdown("## 🔍 Smart Q&A System")
    
    # Query analysis section
    st.markdown("### 📝 Query Analysis")
    question_input = st.text_input(
        "Enter your question:",
        placeholder="e.g., How many companies came last year? What skills do I need for marketing roles?"
    )
    
    if question_input:
        # Analyze the query
        analysis = make_api_request(f"/query/analyze?question={question_input}")
        
        if "error" not in analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                query_type = analysis.get('query_type', 'Unknown')
                st.markdown(f"""
                <div class="feature-card">
                    <h4>Query Type</h4>
                    <p><strong>{query_type.title()}</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                routing_strategy = analysis.get('routing_strategy', {})
                description = routing_strategy.get('description', 'No strategy available')
                st.markdown(f"""
                <div class="feature-card">
                    <h4>Routing Strategy</h4>
                    <p>{description}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Show extracted parameters
            if analysis['parameters']:
                st.markdown("**Extracted Parameters:**")
                st.json(analysis['parameters'])
    
    # Main Q&A interface
    st.markdown("### 💬 Ask Your Question")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Auto-fill the main question textarea with the analysis input so users can run the query
        question = st.text_area(
            "Your Question:",
            value=question_input if question_input else "",
            height=100,
            placeholder="Ask anything about placements, companies, roles, or skills..."
        )
    
    with col2:
        # Get companies dynamically from API
        companies_list = get_companies_list()
        company_options = [""] + companies_list if companies_list else [""]
        
        company = st.selectbox(
            "Filter by Company (Optional):",
            options=company_options,
            help="Leave empty for global analysis across all companies"
        )
        
        year = st.number_input(
            "Filter by Year (Optional):",
            min_value=2020,
            max_value=2025,
            value=None,
            help="Leave empty for all years"
        )
        
        top_k = st.slider(
            "Number of Results:",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of relevant snippets to retrieve"
        )
    
    if st.button("🚀 Get Answer", type="primary"):
        if question:
            with st.spinner("Analyzing your question..."):
                # Prepare filters
                filters = {
                    "company": company if company else None,
                    "year": year if year else None,
                    "role_contains": None
                }
                
                # Make API request
                response = make_api_request("/query", method="POST", data={
                    "question": question,
                    "filters": filters,
                    "top_k": top_k
                })
                
                if "error" not in response:
                    # Display answer
                    if response.get("answer"):
                        st.markdown("### 🎯 Answer")
                        st.markdown(response["answer"])
                    
                    # Display snippets
                    if response.get("snippets"):
                        st.markdown("### 📄 Relevant Snippets")
                        for i, snippet in enumerate(response["snippets"][:5]):  # Show first 5
                            metadata = snippet.get('metadata', {}) or {}
                            company = metadata.get('company', 'Unknown Company') or 'Unknown Company'
                            source = metadata.get('source', 'Unknown') or 'Unknown'
                            text = snippet.get('text', '') or ''
                            
                            with st.expander(f"Snippet {i+1} - {company}"):
                                st.markdown(f"**Source:** {source}")
                                st.markdown(f"**Text:** {text[:300]}...")
                else:
                    st.error(f"Error: {response['error']}")
        else:
            st.warning("Please enter a question first!")

# Analytics Dashboard page
elif page == "📊 Analytics Dashboard":
    st.markdown("## 📊 Analytics Dashboard")
    
    # Placement Statistics
    st.markdown("### 📈 Placement Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        year_filter = st.selectbox(
            "Select Year:",
            options=["All Years", "2024", "2023", "2022"],
            help="Filter statistics by specific year"
        )
    
    with col2:
        if st.button("🔄 Refresh Statistics"):
            st.rerun()
    
    # Get statistics
    year_param = int(year_filter) if year_filter != "All Years" else None
    stats = make_api_request(f"/stats/placement?year={year_param}" if year_param else "/stats/placement")
    
    if "error" not in stats:
        data = stats.get("data", {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Companies", data.get('company_count', 0))
        
        with col2:
            st.metric("Total Roles", data.get('role_count', 0))
        
        with col3:
            avg_min = data.get('avg_min_salary', 0) or 0
            if avg_min is not None and avg_min > 0:
                min_display = f"₹{avg_min:.1f}L"
            else:
                min_display = "₹0.0L"
            st.metric("Avg Min Salary", min_display)
        
        with col4:
            avg_max = data.get('avg_max_salary', 0) or 0
            if avg_max is not None and avg_max > 0:
                max_display = f"₹{avg_max:.1f}L"
            else:
                max_display = "₹0.0L"
            st.metric("Avg Max Salary", max_display)
        
        # Top skills chart
        if data.get('top_skills'):
            st.markdown("### 🎯 Top Skills in Demand")
            skills_data = data['top_skills'][:10]  # Top 10
            
            # Create a simple bar chart
            skill_names = [skill['skill'] for skill in skills_data]
            skill_counts = [skill['count'] for skill in skills_data]
            
            chart_data = {"Skill": skill_names, "Count": skill_counts}
            st.bar_chart(chart_data)
    
    # Company Analysis
    st.markdown("### 🏢 Company Analysis")
    companies = make_api_request("/stats/companies")
    
    if "error" not in companies:
        companies_data = companies.get("data", [])
        
        if companies_data:
            # Create a DataFrame-like display
            st.markdown("**Company Overview:**")
            for company in companies_data:
                with st.expander(f"🏢 {company['company_name']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Type:** {company.get('company_type', 'N/A')}")
                    with col2:
                        st.write(f"**Industry:** {company.get('industry', 'N/A')}")
                    with col3:
                        st.write(f"**Roles:** {company.get('role_count', 0)}")
                    st.write(f"**Location:** {company.get('location', 'N/A')}")

# Resume Matcher page
elif page == "💼 Resume Matcher":
    st.markdown("## 💼 Resume Matcher")
    
    st.markdown("""
    ### How it works:
    1. **Upload your resume** or paste the text
    2. **Select target companies** (optional)
    3. **Get personalized insights** on skills gaps and improvement plans
    """)
    
    # Resume input
    resume_text = st.text_area(
        "Paste your resume text here:",
        height=200,
        placeholder="Paste your resume content, skills, experience..."
    )
    
    # Company filter
    companies_list = get_companies_list()
    target_companies = st.multiselect(
        "Target Companies (Optional):",
        options=companies_list if companies_list else [],
        help="Select companies you're interested in for targeted analysis"
    )
    
    if st.button("🎯 Analyze Resume", type="primary"):
        if resume_text:
            with st.spinner("Analyzing your resume..."):
                response = make_api_request("/query/resume_match", method="POST", data={
                    "resume_text": resume_text,
                    "target_companies": target_companies
                })
                
                if "error" not in response:
                    results = response.get("results", [])
                    
                    if results:
                        st.markdown("### 📊 Analysis Results")
                        
                        for result in results[:3]:  # Show top 3 matches
                            score = result.get('score', 0) or 0
                            if score is not None:
                                score_display = f"{score:.2%}"
                            else:
                                score_display = "0.00%"
                                
                            with st.expander(f"🎯 {result['jd_id']} - Score: {score_display}"):
                                st.markdown(f"**Match Score:** {score_display}")
                                
                                if result.get("missing_skills"):
                                    st.markdown("**Skills to Develop:**")
                                    for skill in result["missing_skills"]:
                                        st.write(f"- {skill}")
                                
                                if result.get("improvement_plan"):
                                    st.markdown("**Improvement Plan:**")
                                    for step in result["improvement_plan"]:
                                        st.write(f"• {step}")
                    else:
                        st.info("No matching job descriptions found. Try adjusting your search criteria.")
                else:
                    st.error(f"Error: {response['error']}")
        else:
            st.warning("Please paste your resume text first!")

# System Status page
elif page == "⚙️ System Status":
    st.markdown("## ⚙️ System Status")
    
    # Health check
    st.markdown("### 🏥 API Health")
    health = make_api_request("/health")
    
    if "error" not in health:
        st.success("✅ API Server is running")
        st.json(health)
    else:
        st.error("❌ API Server is not responding")
        st.error(health["error"])
    
    # System information
    st.markdown("### 📊 System Information")
    
    # Test database connection
    db_stats = make_api_request("/stats/placement")
    if "error" not in db_stats:
        st.success("✅ Database connection successful")
    else:
        st.warning("⚠️ Database connection issues")
    
    # Test query routing
    test_question = "How many companies came last year?"
    routing_test = make_api_request(f"/query/analyze?question={test_question}")
    
    if "error" not in routing_test:
        query_type = routing_test.get('query_type', 'Unknown') or 'Unknown'
        st.success("✅ Query routing system working")
        st.markdown(f"**Test Query:** {test_question}")
        st.markdown(f"**Detected Type:** {query_type}")
    else:
        st.warning("⚠️ Query routing system issues")

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ by JD-Copilot Team | "
    "[GitHub](https://github.com/your-repo) | "
    "[Documentation](https://docs.jd-copilot.com)"
)
