
# JD-Copilot RAG System Benchmark Report
Generated: 2025-09-05 10:59:20

## Executive Summary
- **Total Queries Evaluated:** 20
- **Overall Accuracy:** 0.134 ± 0.081
- **Exact Match Rate:** 0.000
- **Average Response Time:** 10.67s ± 7.46s
- **Semantic Similarity:** 0.299

## Performance by Category

### Tool Listing (1 queries)
- Average Accuracy: 0.194
- Average Response Time: 12.00s

### Location Based (1 queries)
- Average Accuracy: 0.010
- Average Response Time: 4.38s

### Learning Opportunity (1 queries)
- Average Accuracy: 0.265
- Average Response Time: 16.05s

### Role Listing (1 queries)
- Average Accuracy: 0.047
- Average Response Time: 5.87s

### Salary Comparison (1 queries)
- Average Accuracy: 0.021
- Average Response Time: 4.34s

### Role Description (1 queries)
- Average Accuracy: 0.190
- Average Response Time: 21.49s

### Task Listing (1 queries)
- Average Accuracy: 0.148
- Average Response Time: 25.03s

### Opportunity Listing (1 queries)
- Average Accuracy: 0.282
- Average Response Time: 22.56s

### Company Identification (2 queries)
- Average Accuracy: 0.073
- Average Response Time: 5.30s

### Comparative Analysis (1 queries)
- Average Accuracy: 0.150
- Average Response Time: 24.77s

### Company Count (1 queries)
- Average Accuracy: 0.129
- Average Response Time: 6.65s

### Yes No Question (1 queries)
- Average Accuracy: 0.257
- Average Response Time: 5.76s

### Industry Identification (3 queries)
- Average Accuracy: 0.127
- Average Response Time: 5.14s

### Skill Analysis (1 queries)
- Average Accuracy: 0.205
- Average Response Time: 14.42s

### Feature Identification (1 queries)
- Average Accuracy: 0.165
- Average Response Time: 15.51s

### Job Type (1 queries)
- Average Accuracy: 0.069
- Average Response Time: 3.84s

### Compensation Type (1 queries)
- Average Accuracy: 0.017
- Average Response Time: 4.61s

## Performance by Difficulty

### Easy Queries (7 queries)
- Average Accuracy: 0.112
- Average Response Time: 6.71s

### Medium Queries (8 queries)
- Average Accuracy: 0.109
- Average Response Time: 8.85s

### Hard Queries (5 queries)
- Average Accuracy: 0.204
- Average Response Time: 19.10s

## Detailed Results

### Query 1: How many companies are offering finance roles?
- **Category:** company_count
- **Difficulty:** easy
- **Overall Accuracy:** 0.129
- **Response Time:** 6.65s

**Expected Answer:**
1 (Mill Story – Finance & Accounting Internship)

**Generated Answer:**
Result: SQL Query: SELECT COUNT(DISTINCT c.id) AS company_count
FROM companies c
JOIN roles r ON c.id = r.company_id
JOIN offers o ON r.id = o.role_id
WHERE r.specialization = 'finance';
Result: ('[(0,)]', {'result': [(0,)], 'col_keys': ['company_count']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.145
- Keyword Overlap: 0.000
- Entity Accuracy: 1.000

---

### Query 2: Who are the companies with HR opportunities?
- **Category:** company_identification
- **Difficulty:** easy
- **Overall Accuracy:** 0.047
- **Response Time:** 3.73s

**Expected Answer:**
Accorian (Associate – People Operations)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT c.company_name
FROM companies c
JOIN roles r ON c.id = r.company_id
WHERE r.specialization = 'HR';
Result: ("[('Accorian',)]", {'result': [('Accorian',)], 'col_keys': ['company_name']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.233
- Keyword Overlap: 0.000
- Entity Accuracy: 0.000

---

### Query 3: Which companies are hiring for PR or communications roles?
- **Category:** company_identification
- **Difficulty:** easy
- **Overall Accuracy:** 0.100
- **Response Time:** 6.88s

**Expected Answer:**
Madison PR (Account Executive)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT c.company_name
FROM companies c
JOIN roles r ON c.id = r.company_id
WHERE LOWER(r.title) LIKE '%pr%' 
   OR LOWER(r.title) LIKE '%public relations%'
   OR LOWER(r.title) LIKE '%communications%'
   OR LOWER(r.specialization) LIKE '%pr%'
   OR LOWER(r.specialization) LIKE '%public relations%'
   OR LOWER(r.specialization) LIKE '%communications%';
Result: ("[('Target',)]", {'result': [('Target',)], 'col_keys': ['company_name']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.125
- Keyword Overlap: 0.250
- Entity Accuracy: 0.500

---

### Query 4: Are there any admission-related jobs?
- **Category:** yes_no_question
- **Difficulty:** easy
- **Overall Accuracy:** 0.257
- **Response Time:** 5.76s

**Expected Answer:**
Yes, Masters' Union (Admission Counselor)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT r.id, r.title, c.company_name
FROM roles r
JOIN companies c ON r.company_id = c.id
WHERE LOWER(r.title) LIKE '%admission%' OR LOWER(r.role_description) LIKE '%admission%' OR LOWER(r.specialization) LIKE '%admission%';
Result: ('[(8, \'Admission Counselor\', "Masters\' Union")]', {'result': [(8, 'Admission Counselor', "Masters' Union")], 'col_keys': ['id', 'title', 'company_name']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.384
- Keyword Overlap: 0.800
- Entity Accuracy: 1.000

---

### Query 5: Which roles are open for freshers?
- **Category:** role_listing
- **Difficulty:** medium
- **Overall Accuracy:** 0.047
- **Response Time:** 5.87s

**Expected Answer:**
Accorian (Associate HR Ops – Fresher), TAP Academy (BDA – freshers encouraged)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT r.title
FROM roles r
JOIN requirements req ON r.id = req.role_id
WHERE req.requirement_text LIKE '%fresher%' OR req.requirement_text LIKE '%0 years%' OR req.requirement_text LIKE '%no experience%';
Result: ('[]', {'result': [], 'col_keys': ['title']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.185
- Keyword Overlap: 0.100
- Entity Accuracy: 0.000

---

### Query 6: Which jobs mention placements explicitly?
- **Category:** feature_identification
- **Difficulty:** easy
- **Overall Accuracy:** 0.165
- **Response Time:** 15.51s

**Expected Answer:**
TAP Academy (student placements)

**Generated Answer:**
Based on the available documents, I found **one role** that explicitly mentions placements:

---

**Job Title:** *Not explicitly stated, but contextually inferred as a Placement/Outreach Role*  
**Company:** TAP Academy  
**Location:** Not specified  
**Key Responsibilities (Placement-Related):**  
- **Market Research & Networking:** Stay updated on industry hiring trends, skill requirements, and **placement opportunities**.  
- **Reporting & Pipeline Management:** Track and report on **outreach activities, lead generation efforts, and placement successes**.  

**Relevance for MBA Students:**  
This role is directly aligned with **MBA career services, corporate relations, or placement coordination functions**. It involves:  
- **Strategic networking** with recruiters to secure roles for students.  
- **Data-driven reporting** on placement metrics (e.g., offer-to-interview ratios, salary trends).  
- **Cross-functional collaboration** with marketing (branding), HR (candidate profiling), and analytics (dashboards).  

**Strategic Insight:**  
While no other companies explicitly mention "placements" in the provided data, TAP Academy’s focus on **placement tracking and industry trend analysis** highlights a niche opportunity for MBA students specializing in **HR (talent acquisition), Business Analytics (dashboarding), or Marketing (employer branding)**.  

**Recommendation:**  
If you’re targeting **corporate relations, campus recruitment, or ed-tech placement roles**, emphasize:  
- **CRM proficiency** (e.g., Salesforce, Zoho).  
- **Data visualization** (PowerBI/Tableau for placement dashboards).  
- **Stakeholder management** (bridging students and recruiters).  

No other companies in the dataset explicitly reference placements.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.452
- Keyword Overlap: 0.750
- Entity Accuracy: 0.000

---

### Query 7: Are there any ed-tech companies hiring?
- **Category:** industry_identification
- **Difficulty:** medium
- **Overall Accuracy:** 0.114
- **Response Time:** 5.65s

**Expected Answer:**
TAP Academy (BDA role)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT c.company_name
FROM companies c
JOIN roles r ON c.id = r.company_id
JOIN offers o ON r.id = o.role_id
WHERE c.industry = 'ed-tech' AND o.expected_hires > 0;
Result: ('[]', {'result': [], 'col_keys': ['company_name']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.071
- Keyword Overlap: 0.000
- Entity Accuracy: 1.000

---

### Query 8: Which companies are in consulting or cybersecurity?
- **Category:** industry_identification
- **Difficulty:** medium
- **Overall Accuracy:** 0.148
- **Response Time:** 4.67s

**Expected Answer:**
Accorian (cybersecurity advisory firm)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT company_name
FROM companies
WHERE industry IN ('consulting', 'cybersecurity');
Result: ('[]', {'result': [], 'col_keys': ['company_name']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.240
- Keyword Overlap: 0.000
- Entity Accuracy: 1.000

---

### Query 9: Which jobs are specifically internships?
- **Category:** job_type
- **Difficulty:** easy
- **Overall Accuracy:** 0.069
- **Response Time:** 3.84s

**Expected Answer:**
Mill Story (Finance Internship)

**Generated Answer:**
Result: SQL Query: SELECT * FROM roles WHERE LOWER(title) LIKE '%intern%' OR LOWER(title) LIKE '%internship%';
Result: ("[(9, 9, 'Finance & Accounting Intern', 'FINANCE', 'Sarjapur Road, Bengaluru', '', '2025-08-19 15:55:38')]", {'result': [(9, 9, 'Finance & Accounting Intern', 'FINANCE', 'Sarjapur Road, Bengaluru', '', '2025-08-19 15:55:38')], 'col_keys': ['id', 'company_id', 'title', 'specialization', 'location', 'role_description', 'created_at']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.222
- Keyword Overlap: 0.250
- Entity Accuracy: 0.000

---

### Query 10: Which job is in the food & consumer space?
- **Category:** industry_identification
- **Difficulty:** medium
- **Overall Accuracy:** 0.119
- **Response Time:** 5.11s

**Expected Answer:**
Mill Story (D2C food brand – chemical-free flour)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT r.title
FROM roles r
JOIN companies c ON r.company_id = c.id
WHERE c.industry = 'food & consumer';
Result: ('[]', {'result': [], 'col_keys': ['title']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.095
- Keyword Overlap: 0.000
- Entity Accuracy: 1.000

---

### Query 11: What finance-related tasks are mentioned?
- **Category:** task_listing
- **Difficulty:** hard
- **Overall Accuracy:** 0.148
- **Response Time:** 25.03s

**Expected Answer:**
Accounting, P&L, balance sheet, cash flow, budgeting, expense tracking, invoice checks, audits, compliance, fundraising support, pitch deck prep

**Generated Answer:**
Finance-Related Tasks Identified in the Available Data
----------------------------------------------------

Company: Mill Story  
Role: Finance & Accounting Intern  

Key Finance Tasks Mentioned  
1. Book-keeping & Accuracy  
   • Maintain clean and accurate books of accounts.  

2. Financial Statement Preparation  
   • Build Pro-forma accounting statements:  
     – Profit & Loss (P&L)  
     – Balance Sheet  
     – Cash-Flow Statement  

3. Budgeting & Expense Control  
   • Assist in budgeting processes.  
   • Track expenses and verify invoices.  

4. Fund-Raising Support  
   • Contribute to fundraising preparation activities—hands-on exposure to how early-stage start-ups ready themselves for investor rounds.

Relevance for MBA Students  
• Specialization Fit: Directly aligns with Finance specialization; also useful for Entrepreneurship electives.  
• Skill Development: Offers practical experience in start-up finance, investor-readiness, and financial modeling—competencies highly valued by VC/PE firms and corporate finance roles.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.503
- Keyword Overlap: 0.474
- Entity Accuracy: 0.000

---

### Query 12: What do HR operations jobs involve?
- **Category:** role_description
- **Difficulty:** hard
- **Overall Accuracy:** 0.190
- **Response Time:** 21.49s

**Expected Answer:**
Employee lifecycle management, engagement, compliance audits, labor law adherence, HR processes, people initiatives

**Generated Answer:**
## Strategic Analysis: HR Operations Roles Across the Market

### Core Responsibilities in HR Operations

Based on the available data from **Accorian** and **TAP Academy**, HR Operations roles encompass a comprehensive employee lifecycle management approach:

**Primary Functions:**
- **End-to-End Employee Lifecycle Management**: From hire-to-retire processes including onboarding, transfers, performance management, and exit formalities
- **Employee Experience Design**: Strategizing and deploying initiatives that enhance employee touchpoints throughout their journey
- **Stakeholder Partnership**: Acting as the Single Point of Contact (SPOC) for employee queries while collaborating with leadership on organization design and development
- **Process Optimization**: Streamlining HR processes to enhance operational efficiency and reduce turnaround times
- **Compliance Management**: Ensuring adherence to labor laws and regulatory requirements across all people practices

### Strategic Implications for MBA-HR Students

**Relevance for MBA-HR Specialization:**
- **High Strategic Value**: These roles sit at the intersection of operational excellence and strategic HR, making them ideal for MBA graduates who understand both business strategy and people management
- **Cross-Functional Exposure**: You'll interact with finance (compensation), operations (productivity metrics), and business leaders (organization design), providing T-shaped skill development
- **Data-Driven Decision Making**: The emphasis on reporting and pipeline management aligns with modern HR analytics requirements

### Market Trends & Skills Gap Analysis

**Most Critical Skills Identified:**
1. **HR Technology Proficiency** (HRMS systems)
2. **Process Re-engineering** capabilities
3. **Labor Law & Compliance** expertise
4. **MS Office Suite** (particularly Excel for analytics)
5. **Stakeholder Management** and communication

**Strategic Advice for Career Preparation:**

**Immediate Actions:**
- **Certification Path**: Pursue SHRM-CP or PHR certifications to demonstrate compliance expertise
- **Technical Upskilling**: Gain hands-on experience with popular HRMS platforms (Workday, SAP SuccessFactors, or BambooHR)
- **Process Excellence**: Consider Six Sigma Green Belt certification to strengthen process optimization credentials

**Long-term Career Trajectory:**
- **Entry Point**: Associate-People Operations roles serve as excellent gateways to strategic HR business partner positions
- **Specialization Opportunities**: Focus on either **Employee Experience Design** (high-growth area) or **HR Analytics & Technology** (future-proof skill set)
- **Compensation Growth**: These foundational roles typically lead to HR Manager positions within 3-4 years, with significant salary progression

### Competitive Positioning for Placements

**Differentiation Strategy:**
- **Combine MBA Business Acumen**: Leverage your strategic thinking to propose data-driven HR solutions
- **Technology-First Approach**: Position yourself as an HR professional who can bridge traditional HR with digital transformation
- **Quantify Impact**: Prepare case studies showing how HR process improvements can directly impact business metrics (retention rates, productivity indices)

**Recommended Portfolio Projects:**
- Design an employee onboarding journey map with measurable KPIs
- Create a compliance dashboard tracking key labor law metrics
- Develop a process optimization proposal for a specific HR function with ROI projections

This analysis positions HR Operations not just as administrative roles, but as strategic business enablers where MBA-HR graduates can create measurable business impact from day one.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.525
- Keyword Overlap: 0.846
- Entity Accuracy: 0.000

---

### Query 13: What opportunities does TAP Academy offer?
- **Category:** opportunity_listing
- **Difficulty:** hard
- **Overall Accuracy:** 0.282
- **Response Time:** 22.56s

**Expected Answer:**
Lead generation, partnership development, LinkedIn outreach, placement strategy, market research, reporting, career advancement

**Generated Answer:**
Strategic Placement Brief – TAP Academy Opportunities for MBA Students
──────────────────────────────────────────────────────────────

1. Core Opportunity  
   Job Title: Business Development Associate  
   Company: TAP Academy (Ed-Tech, BTM Layout, Bangalore)  
   Experience Band: 0–3 years (prior Ed-Tech exposure is a plus)  

2. Role Mandate & MBA Relevance  
   • Lead Generation for Placements  
     – Identify and engage companies with active hiring demand via cold-calling, cold-emailing, and LinkedIn outreach.  
     – MBA Lens: Directly leverages Marketing & Sales funnel concepts; ideal for students specialising in Marketing or Business Analytics who want hands-on experience in B2B demand generation.  

   • Partnership Development  
     – Build and nurture relationships with HR heads, recruiters, and decision-makers to secure placement slots for TAP Academy learners.  
     – MBA Lens: Mirrors Strategic HR & Corporate Relations roles; HR majors can showcase stakeholder-management and talent-sourcing capabilities.  

   • LinkedIn & Social-Media Outreach  
     – Craft targeted campaigns, optimise messaging, and track engagement metrics.  
     – MBA Lens: Demonstrates digital marketing proficiency—critical for Marketing and Business Analytics students aiming to prove ROI on social channels.  

   • Competitor Intelligence & Opportunity Mapping  
     – Monitor rival Ed-Tech placement records to uncover whitespace and refine value propositions.  
     – MBA Lens: Combines Competitive Strategy (core to General Management) with data-driven decision making.  

   • Reporting & Pipeline Management  
     – Maintain dashboards on outreach volume, lead conversion, and placement success rates.  
     – MBA Lens: Showcases Operations & Analytics acumen—perfect for students targeting roles in Sales Operations or Business Intelligence.  

3. Compensation & Logistics  
   • Location: BTM Layout, Bangalore (start-up hub; strong peer-learning ecosystem).  
   • Compensation: Not disclosed in retrieved data; recommend clarifying CTC, variable pay, and ESOPs during interviews.  

4. Strategic Advice for MBA Applicants  
   • Position Yourself as a “Revenue-Linked HR-Marketing Hybrid”  
     – Emphasise coursework in B2B Sales, Digital Marketing, and Strategic HRM.  
     – Quantify prior achievements: e.g., “Increased LinkedIn response rate by 35 % through A/B-tested messaging.”  

   • Skill Stack to Highlight  
     – CRM tools (HubSpot, Salesforce).  
     – LinkedIn Sales Navigator & social-listening platforms.  
     – Excel / Google Sheets for pipeline dashboards; basic SQL a bonus.  
     – Storytelling with data (PowerBI or Tableau quick-wins).  

   • Certifications That Add Immediate Credibility  
     – HubSpot Inbound Sales or LinkedIn Marketing Labs (Marketing).  
     – SHRM-CP learning modules (HR).  
     – Google Analytics & Ads certificates (cross-functional).  

   • Interview Differentiator  
     – Present a 30-60-90-day plan: target company list, outreach cadence, KPI milestones (e.g., 50 qualified leads/month, 15 % placement conversion).  

5. Long-Term Career Trajectory  
   • 12–18 months in this role can pivot you into:  
     – Corporate Relations / Campus Recruitment Manager in larger Ed-Techs or universities.  
     – Account Executive or Customer Success Manager in SaaS firms (leveraging Ed-Tech network).  
     – Strategic HR Business Partner roles with a strong talent-branding narrative.  

6. Immediate Next Steps  
   1. Customise your résumé headline: “MBA (Marketing/HR) | B2B Lead Generation | Ed-Tech Placement Specialist.”  
   2. Build a 1-page outreach portfolio: sample cold-email sequence + mock dashboard screenshot.  
   3. Reach out to TAP Academy’s HR via LinkedIn with a concise value proposition referencing their placement KPIs.  

──────────────────────────────────────────────────────────────
Bottom line: TAP Academy offers a rare, cross-functional entry point where MBA students can simultaneously sharpen sales, marketing, HR, and analytics capabilities while directly impacting revenue and learner outcomes.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.524
- Keyword Overlap: 0.769
- Entity Accuracy: 1.000

---

### Query 14: What are the most sought-after skills across these JDs?
- **Category:** skill_analysis
- **Difficulty:** hard
- **Overall Accuracy:** 0.205
- **Response Time:** 14.42s

**Expected Answer:**
Communication, problem-solving, Excel/Google Sheets, HRMS, CRM, cold calling, negotiation, PR/media skills

**Generated Answer:**
Strategic Market Insight – Skill Heat-Map Across Retrieved JDs  
(Scope: Masters’ Union & Accorian postings only)

1. Presentation & Negotiation Mastery  
   Cited By: Masters’ Union (100 % of its JDs)  
   Relevant Specializations: Marketing, Sales, Business Development, General Management  
   Why It Matters: In B2C inside-sales / admission-counsellor roles, the candidate who can pitch value propositions crisply and close prospects on the same call outperforms peers by 2-3× conversion rates.  
   Strategic Advice: Treat this as a cross-functional “must-have”; even Finance & HR majors who interface with internal clients need persuasive storytelling.  
   Recommended Certifications:  
   – “High-Impact Presentation” – Dale Carnegie (2-day)  
   – “Negotiation Mastery” – Harvard Online (6 wks, ₹65 k)

2. CRM & Sales Pipeline Discipline  
   Cited By: Masters’ Union (explicitly in both JDs)  
   Relevant Specializations: Marketing, Business Analytics, Sales & Channel Management  
   Why It Matters: Companies are moving from gut-feel to data-driven funnel management; ability to tag, score and forecast leads in CRM is now baseline employability for customer-facing MBA roles.  
   Strategic Advice: Pair CRM literacy with basic SQL / Power BI to become the “tech-savvy marketer” every ed-tech & fintech firm is hunting.  
   Recommended Certifications:  
   – Salesforce Sales-Operations Bootcamp (free Trailhead + Super-badge)  
   – HubSpot CRM + HubSpot Reporting

3. Time-Management & Multi-Tasking Under Six-Day Week Pressure  
   Cited By: Masters’ Union (all JDs)  
   Relevant Specializations: Operations, General Management, HR (for high-volume recruiting)  
   Why It Matters: Six-day work cultures (start-ups, ed-tech, consulting) filter for stamina; students who have practised 14-hour term-project sprints + live client simulations adapt fastest.  
   Strategic Advice: Build visible proof – use “sprint retrospectives” from your term projects / live practicum to demonstrate throughput in interviews.  
   Recommended Tools: Notion, Trello, Pomodoro Tracker; certify on “Getting Things Done” (GTD) Practitioner.

4. Analytical & Problem-Solving Acumen  
   Cited By: Accorian (HR role)  
   Relevant Specializations: Business Analytics, HR (People Analytics), Finance  
   Why It Matters: Even HR is becoming a data function; Accorian wants evidence-based redesign of “hire-to-retire” processes.  
   Strategic Advice: Position yourself as the MBA who can quantify cost-per-hire, predict attrition, and justify policy changes with ROI.  
   Recommended Certifications:  
   – People Analytics – Wharton Online  
   – Tableau Desktop Specialist + basic Python (pandas) for HR data sets

5. HR Tech & Compliance (Labour-Law) Fluency  
   Cited By: Accorian  
   Relevant Specializations: HR, Operations (plant IR), Legal & Corporate Governance  
   Why It Matters: Post-pandemic, every firm is digitizing HRMS and needs in-house talent who can translate statutory changes into system workflows.  
   Strategic Advice: This is a niche but high-margin skill; fewer MBA-HR students certify on labour codes → premium pay.  
   Recommended Certifications:  
   – SHRM-SCP (global) + India Labour Codes Certificate – NLSIU  
   – SAP SuccessFactors or Workday HCM Functional (any one)

Cross-Company Trend Summary  
• Sales & Customer-facing DNA dominates Masters’ Union JDs → demand for “Revenue Engineers” who blend CRM analytics with persuasive communication.  
• Accorian signals the rise of “HR-Analytics” hybrids; pure admin HR roles are disappearing.  
• Both companies implicitly reward candidates who can thrive in 6-day, high-velocity cultures → resilience & productivity frameworks are now employability differentiators.

Actionable Portfolio Recommendation for MBA Students  
A. Build a T-shaped profile:  
   – Vertical depth: pick ONE of (a) CRM+Sales Analytics, (b) People Analytics, (c) Financial Modelling.  
   – Horizontal breadth: certify in Presentation, Negotiation, and Productivity tools (every recruiter asks for these).  

B. Demonstrate stamina & results simultaneously: show metrics (leads converted, process cycle-time reduced) achieved during 60-hour weeks—this maps directly to the six-day requirement.

C. Differentiate early:  
   – Marketing/BA majors → stack Salesforce + Tableau.  
   – HR majors → stack HRMS + Labour Codes + Power BI.  
   – Finance/Ops → add Six-Sigma-Green-Belt to analytical core.

If you need comparative insights beyond these two firms, let me know and I’ll pull the wider 2024-25 placement database.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.465
- Keyword Overlap: 0.500
- Entity Accuracy: 0.625

---

### Query 15: Which jobs are based in Bangalore?
- **Category:** location_based
- **Difficulty:** medium
- **Overall Accuracy:** 0.010
- **Response Time:** 4.38s

**Expected Answer:**
Mill Story, TAP Academy, Madison PR (also Gurgaon/Mumbai)

**Generated Answer:**
Result: SQL Query: SELECT * FROM roles WHERE location = 'Bangalore';
Result: ('[]', {'result': [], 'col_keys': ['id', 'company_id', 'title', 'specialization', 'location', 'role_description', 'created_at']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.050
- Keyword Overlap: 0.000
- Entity Accuracy: 0.000

---

### Query 16: Which role has the highest salary package?
- **Category:** salary_comparison
- **Difficulty:** medium
- **Overall Accuracy:** 0.021
- **Response Time:** 4.34s

**Expected Answer:**
Madison PR (up to 5.5 LPA)

**Generated Answer:**
Result: SQL Query: SELECT r.title
FROM roles r
JOIN offers o ON r.id = o.role_id
ORDER BY o.salary_max_lpa DESC
LIMIT 1;
Result: ("[('Account Executive',)]", {'result': [('Account Executive',)], 'col_keys': ['title']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.104
- Keyword Overlap: 0.000
- Entity Accuracy: 0.000

---

### Query 17: Which jobs are paid internships?
- **Category:** compensation_type
- **Difficulty:** easy
- **Overall Accuracy:** 0.017
- **Response Time:** 4.61s

**Expected Answer:**
Mill Story (Finance Internship)

**Generated Answer:**
Result: SQL Query: SELECT DISTINCT r.title
FROM roles r
JOIN offers o ON r.id = o.role_id
WHERE LOWER(r.title) LIKE '%intern%'
  AND o.salary_min_lpa > 0;
Result: ('[]', {'result': [], 'col_keys': ['title']})

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.087
- Keyword Overlap: 0.000
- Entity Accuracy: 0.000

---

### Query 18: List all the tools/software mentioned in the JDs
- **Category:** tool_listing
- **Difficulty:** hard
- **Overall Accuracy:** 0.194
- **Response Time:** 12.00s

**Expected Answer:**
Excel, Google Sheets, Tally, Zoho Books, HRMS, CRM, LinkedIn, PR tools, MS Office

**Generated Answer:**
Based on the available job descriptions, here are the tools/software explicitly mentioned:

**Tools/Software Identified:**
- **MS Office Suite** (mentioned by Accorian)
- **HRMS** (Human Resource Management System) (mentioned by Accorian)

**Strategic Analysis for MBA Students:**

**Skill Name:** MS Office Suite & HRMS Proficiency
**Cited By Companies:** Accorian
**Relevant Specializations:** HR, Operations, Business Analytics
**Why It Matters:** These are foundational tools for any HR professional. MS Office (especially Excel for data analysis, PowerPoint for presentations, and Word for documentation) is essential for day-to-day operations. HRMS proficiency is critical as companies increasingly digitize their HR processes.

**Strategic Advice:** While these are table-stakes skills, the emphasis on HRMS indicates a broader trend toward HR digitization. MBA students should view this as an opportunity to differentiate themselves by gaining expertise in advanced HR technologies beyond basic HRMS.

**Recommended Certifications/Training:**
- **MS Office:** Advanced Excel certification (for data analysis), PowerBI certification (for HR dashboards)
- **HRMS:** Workday HCM certification, SAP SuccessFactors certification, or Oracle HCM Cloud certification
- **Cross-functional:** Tableau or PowerBI for HR analytics, Python/R for advanced HR data analysis

**Note:** The limited tool mentions suggest these JDs focus more on process expertise than specific technical tools. MBA students should proactively seek exposure to modern HR tech stacks (like People Analytics platforms, Employee Experience tools, and AI-driven HR systems) to stay competitive.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.613
- Keyword Overlap: 0.385
- Entity Accuracy: 0.333

---

### Query 19: Which jobs are better for freshers?
- **Category:** comparative_analysis
- **Difficulty:** medium
- **Overall Accuracy:** 0.150
- **Response Time:** 24.77s

**Expected Answer:**
Accorian (fresher role), TAP Academy (freshers encouraged)

**Generated Answer:**
## Strategic Market Analysis: Fresher-Friendly Opportunities

Based on comprehensive analysis of available placement data, here are the **most accessible entry points** for MBA freshers:

### **Tier 1: Immediate Entry Opportunities**

**1. TAP Academy - Business Development/Sales Trainee**
- **Why It's Ideal**: Explicitly welcomes freshers with "excellent communication skills"
- **Core Requirements**: 
  - Cold calling & emailing proficiency
  - LinkedIn networking skills
  - Strong verbal/written communication
- **MBA Relevance**: Perfect for Marketing specialization students to build foundational sales skills
- **Strategic Advantage**: Provides direct client interaction experience, crucial for marketing careers

**2. Masters' Union - Admission Counselor**
- **Entry Barrier**: While requiring "proven experience," the role focuses on B2C sales which freshers can demonstrate through internships
- **Key Skills**: CRM usage, target achievement, understanding professional learning needs
- **MBA Mapping**: Excellent for Marketing/HR students interested in education sector careers

### **Tier 2: Specialized Entry with Internship Experience**

**3. MADISON PUBLIC RELATIONS - PR Executive**
- **Entry Requirement**: Previous internship experience (manageable during MBA)
- **Ideal Specialization**: Marketing (Public Relations/Communications track)
- **Unique Value**: Combines storytelling skills with media relations - highly valued in corporate communications roles

### **Cross-Company Strategic Insights**

**Most Fresher-Friendly Skills to Develop:**
1. **Communication Excellence** (mentioned by 100% of companies)
2. **LinkedIn & Social Media Proficiency** (TAP Academy emphasis)
3. **CRM Familiarity** (Masters' Union requirement - easily learned via online certifications)
4. **Cold Outreach Skills** (TAP Academy - can be practiced independently)

**Specialization-Specific Recommendations:**

- **Marketing Students**: Focus on TAP Academy and MADISON PR roles. Build portfolio with social media campaigns and PR writing samples.
- **HR Students**: Masters' Union role aligns well with talent acquisition aspects. Emphasize counseling and professional development understanding.
- **Business Analytics**: While not directly listed, data-driven sales approaches using CRM analytics could be your differentiator.

**Immediate Action Plan for Freshers:**
1. **Week 1-2**: Complete HubSpot CRM certification (free)
2. **Week 3-4**: Build LinkedIn presence with 500+ connections and regular industry content sharing
3. **Week 5-6**: Create mock cold outreach campaigns as portfolio pieces
4. **Apply Strategy**: Target TAP Academy immediately, use gained experience for Masters' Union applications

**Pro Tip**: The market shows clear preference for **communication-heavy roles** for freshers. Your MBA differentiator should be combining these communication skills with business strategy understanding that non-MBA candidates lack.

*Note: Structured data could not be retrieved.*

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.462
- Keyword Overlap: 0.571
- Entity Accuracy: 0.000

---

### Query 20: Is there any role where I can learn fundraising?
- **Category:** learning_opportunity
- **Difficulty:** medium
- **Overall Accuracy:** 0.265
- **Response Time:** 16.05s

**Expected Answer:**
Yes, Mill Story (finance intern supports fundraising & pitch decks)

**Generated Answer:**
Fundraising exposure is explicitly offered by only one company in the current data set.

Role: Finance & Accounting Intern  
Company: Mill Story  
Location: Not specified  
Compensation: Not specified  

What you will do (fundraising-related)  
- “Support in fundraising preparations — real exposure to how start-ups raise capital.”  
- Work on pro-forma accounting and core statements (P&L, balance-sheet, cash-flow) that are typically folded into investor decks & data rooms.  
- Assist in keeping books “clean and accurate” – a prerequisite for any due-diligence exercise.  

Relevance for MBA students  
• Specialization fit: Corporate Finance / Strategy / Entrepreneurship.  
• Skill bridge: Links classroom valuation, financial-modeling and term-sheet concepts to live deal work.  
• Network upside: Early-stage start-ups give interns direct access to founders and often to angel/VC conversations—valuable for placement pitches in PE/VC, I-banking or start-up roles later.  

Strategic advice  
1. Highlight start-up finance coursework and DCF/LBO models on your résumé.  
2. Build a simple sample financial model + three-statement projection you can walk through in interviews.  
3. If offered the internship, volunteer to build the KPI dashboard that feeds into the investor deck—this becomes a strong CV bullet.  

Recommended certifications / training  
• “Startup Valuation & Financial Modelling” (Coursera – HEC/Wharton)  
• “Raising Capital & Valuing Early-Stage Businesses” (Wall Street Prep)  
• Advanced Excel & Power BI for investor dashboards.  

Bottom line: Among the companies documented, Mill Story is the only opportunity that advertises hands-on fundraising exposure; target this role if learning the funding process is your primary objective.

**Accuracy Breakdown:**
- Exact Match: 0.000
- Partial Match: 0.000
- Semantic Similarity: 0.492
- Keyword Overlap: 0.667
- Entity Accuracy: 1.000

---
