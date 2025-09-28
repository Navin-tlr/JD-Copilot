# Deep Dive Mode and PDF Parsing Classifications

## Overview

This document explains the purpose and functionality of Deep Dive Mode in the JD-Copilot system, as well as the new classifications that are applied during PDF parsing and ingestion.

## Deep Dive Mode

### Purpose

Deep Dive Mode is an advanced search capability that activates when the structured database search returns insufficient or no results for a user's query. It provides access to comprehensive analysis by searching through thousands of unstructured job descriptions and company profiles stored in the vector database.

### How It Works

1. **Trigger Conditions**: Deep Dive Mode is offered when:
   - The structured database returns no direct matches
   - Limited results are found in the structured data
   - A structured answer is generated but requires additional context verification

2. **User Consent**: Users must explicitly consent to activate Deep Dive Mode by replying with "yes" or "deep-dive" to the consent prompt.

3. **Search Process**:
   - Retrieves relevant snippets from the vector database
   - Synthesizes a comprehensive answer from the unstructured data
   - Provides detailed analysis based on job descriptions and company profiles

4. **Benefits**:
   - Access to detailed, unstructured job description content
   - Comprehensive company profile analysis
   - Enhanced context and insights not available in structured data
   - Better coverage for complex or specific queries

### Technical Implementation

- Uses vector similarity search (RAG - Retrieval Augmented Generation)
- Leverages Pinecone/Chroma for vector storage
- Processes unstructured text from PDF documents
- Synthesizes answers using LLM capabilities

## PDF Parsing Classifications

### Overview

During PDF ingestion, the system performs structured extraction using LLM-powered analysis to classify and categorize job description content. This creates searchable structured data alongside the unstructured vector embeddings.

### Structured Data Extraction

The system extracts the following structured information from PDF job descriptions:

#### Company Information
- **company_name**: Actual company name (not program names)
- **year**: Placement year
- **company_type**: Type of company/organization
- **industry**: Industry sector
- **location**: Company headquarters or primary location

#### Role Information
- **title**: Exact job title as mentioned
- **specialization**: MBA specialization category (required field)
  - HR
  - MARKETING
  - FINANCE
  - LEAN OPERATION AND SYSTEMS
  - BUSINESS ANALYTICS
- **location**: Job location (if specified)
- **salary_min_lpa**: Minimum salary in LPA (null if not mentioned)
- **salary_max_lpa**: Maximum salary in LPA (null if not mentioned)
- **skills**: Array of required skills
- **requirements**: Array of job requirements
- **responsibilities**: Array of job responsibilities

### Role Type Classifications

After basic extraction, the system applies rule-based classification to determine higher-level role categories based on specialization and content analysis.

#### Marketing Specialization Classifications
- **B2B**: Business-to-business roles (enterprise clients, partnerships, account management)
- **PERFORMANCE MARKETING**: Digital advertising and campaign optimization (Google Ads, Meta Ads, PPC, ROAS)
- **MEDIA OPERATIONS**: Ad operations and campaign trafficking
- **BRAND MARKETING**: Brand strategy and positioning
- **CONTENT MARKETING**: Content creation and SEO
- **FMCG**: Fast-moving consumer goods

#### Finance Specialization Classifications
- **FUND MANAGEMENT**: Portfolio and asset management, investment analysis
- **CORPORATE FINANCE**: Treasury, financial modeling, M&A
- **RISK & COMPLIANCE**: Risk management, regulatory compliance, audit

#### HR Specialization Classifications
- **TALENT ACQUISITION**: Recruitment and sourcing
- **LEARNING & DEVELOPMENT**: Training programs and curriculum design
- **HR OPERATIONS**: People operations, onboarding, employee lifecycle

#### Operations (Lean Operation and Systems) Classifications
- **PROCESS EXCELLENCE**: Process improvement, Lean, Six Sigma
- **SUPPLY CHAIN OPERATIONS**: Logistics, procurement, inventory management

#### Business Analytics Classifications
- **DATA ANALYTICS**: SQL, Python, data visualization, dashboards
- **MACHINE LEARNING**: Predictive modeling, classification/regression models

#### Cross-Specialization Classifications
- **B2C**: Business-to-consumer roles (consumer acquisition)

these are examples but it should classify based on specialization and JD Data.
### Classification Methodology

- **Rule-Based**: Uses deterministic pattern matching (no LLM for final classification)
- **Multi-Label**: Roles can have multiple classifications
- **Specialization-Aware**: Same keywords may map to different categories based on MBA specialization
- **Confidence Scoring**: Each classification includes a confidence score based on pattern matching
- **Minimum Threshold**: Only classifications with confidence ≥ 0.30 are retained


### Technical Implementation

- **Primary Classification**: LLM-based batch processing for initial role type assignment
- **Fallback Classification**: Rule-based system using pattern matching
- **Data Storage**: Classifications stored in structured database with debug information
- **Search Integration**: Classifications enable filtered search and analytics

## Integration with Deep Dive Mode

The structured classifications from PDF parsing enhance Deep Dive Mode by:
- Providing metadata for filtering vector search results
- Enabling hybrid search combining structured and unstructured data
- Supporting analytics and reporting on classification distributions
- Improving answer quality through structured context augmentation
