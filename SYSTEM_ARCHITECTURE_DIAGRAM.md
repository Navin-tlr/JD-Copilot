# JD-Copilot: System Architecture Diagrams

## 🏗️ **High-Level System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              JD-COPILOT ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   React UI      │    │  Flutter UI     │    │  Streamlit UI   │            │
│  │   (Web)         │    │  (Mobile)       │    │  (Admin)        │            │
│  │                 │    │                 │    │                 │            │
│  │ • Chat Interface│    │ • Native App    │    │ • Analytics     │            │
│  │ • Real-time     │    │ • Offline Mode  │    │ • Management    │            │
│  │ • Responsive    │    │ • Push Notif    │    │ • Monitoring    │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              API GATEWAY LAYER                                 │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        FastAPI Backend                                  │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │   │
│  │  │ Chat API    │  │ Workflow    │  │ Main API    │  │ Admin API   │   │   │
│  │  │ Endpoints   │  │ Endpoints   │  │ Endpoints   │  │ Endpoints   │   │   │
│  │  │             │  │             │  │             │  │             │   │   │
│  │  │ • /chat/*   │  │ • /workflow │  │ • /health   │  │ • /admin/*  │   │   │
│  │  │ • WebSocket │  │ • /context  │  │ • /metrics  │  │ • /users    │   │   │
│  │  │ • Sessions  │  │ • /state    │  │ • /status   │  │ • /reports  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                   │                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                            AI PROCESSING LAYER                                 │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Query       │  │ RAG Engine  │  │ LLM         │  │ Context     │            │
│  │ Router      │  │ (Hybrid)    │  │ Integration │  │ Manager     │            │
│  │             │  │             │  │             │  │             │            │
│  │ • 4-Way     │  │ • Vector    │  │ • OpenRouter│  │ • Memory    │            │
│  │   Classify  │  │   Search    │  │ • Gemini    │  │ • Entities  │            │
│  │ • Schema    │  │ • Chunking  │  │ • Kimi      │  │ • History   │            │
│  │   Helper    │  │ • Embedding │  │ • Fallback  │  │ • Resolution│            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│           │               │               │               │                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                               DATA LAYER                                       │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ SQLite      │  │ Pinecone    │  │ File        │  │ Cache       │            │
│  │ Database    │  │ Vector DB   │  │ Storage     │  │ Layer       │            │
│  │             │  │             │  │             │  │             │            │
│  │ • Companies │  │ • Embeddings│  │ • PDFs      │  │ • Redis     │            │
│  │ • Roles     │  │ • Chunks    │  │ • DOCX      │  │ • Sessions  │            │
│  │ • Skills    │  │ • Metadata  │  │ • JSON      │  │ • Queries   │            │
│  │ • Offers    │  │ • Similarity│  │ • Logs      │  │ • Responses │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 **Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              QUERY PROCESSING FLOW                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  User Query                                                                     │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────┐                                                               │
│  │ Chat        │  ──► Context Resolution ──► "this company" → "Acuity"         │
│  │ Interface   │                                                               │
│  └─────────────┘                                                               │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────┐                                                               │
│  │ FastAPI     │  ──► CORS ──► Authentication ──► Rate Limiting               │
│  │ Gateway     │                                                               │
│  └─────────────┘                                                               │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────┐                                                               │
│  │ Query       │  ──► LLM Classification ──► STRUCTURED/UNSTRUCTURED/         │
│  │ Router      │                              HYBRID/MULTI_HOP                │
│  └─────────────┘                                                               │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│  │ Structured  │    │ Unstructured│    │ Hybrid      │                        │
│  │ Processing  │    │ Processing  │    │ Processing  │                        │
│  │             │    │             │    │             │                        │
│  │ • SQL Query │    │ • Vector    │    │ • Both SQL  │                        │
│  │ • Database  │    │   Search    │    │   & Vector  │                        │
│  │ • Results   │    │ • Embedding │    │ • Combined  │                        │
│  │ • Format    │    │ • Similarity│    │ • Synthesis │                        │
│  └─────────────┘    └─────────────┘    └─────────────┘                        │
│      │                     │                     │                             │
│      └─────────────────────┼─────────────────────┘                             │
│                            │                                                   │
│                            ▼                                                   │
│  ┌─────────────┐                                                               │
│  │ LLM         │  ──► Response Generation ──► MBA-Specific Insights           │
│  │ Synthesis   │                                                               │
│  └─────────────┘                                                               │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────┐                                                               │
│  │ Response    │  ──► Streaming ──► Real-time Delivery ──► User Interface     │
│  │ Delivery    │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🗄️ **Database Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐                                                           │
│  │   COMPANIES     │                                                           │
│  │                 │                                                           │
│  │ • id (PK)       │                                                           │
│  │ • company_name  │                                                           │
│  │ • industry      │                                                           │
│  │ • location      │                                                           │
│  │ • company_type  │                                                           │
│  │ • created_at    │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           │ 1:N                                                                 │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │     ROLES       │                                                           │
│  │                 │                                                           │
│  │ • id (PK)       │                                                           │
│  │ • company_id    │ ──► FK to Companies                                      │
│  │ • title         │                                                           │
│  │ • specialization│                                                           │
│  │ • location      │                                                           │
│  │ • experience    │                                                           │
│  │ • created_at    │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           │ 1:N                                                                 │
│           ▼                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │     SKILLS      │    │  REQUIREMENTS   │    │     OFFERS      │            │
│  │                 │    │                 │    │                 │            │
│  │ • id (PK)       │    │ • id (PK)       │    │ • id (PK)       │            │
│  │ • role_id       │    │ • role_id       │    │ • role_id       │            │
│  │ • skill_name    │    │ • requirement   │    │ • salary_min    │            │
│  │ • skill_type    │    │ • req_type      │    │ • salary_max    │            │
│  │ • importance    │    │ • created_at    │    │ • benefits      │            │
│  │ • created_at    │    │                 │    │ • offer_type    │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              VECTOR DATABASE                                   │
│                                                                                 │
│  ┌─────────────────┐                                                           │
│  │    PINECONE     │                                                           │
│  │                 │                                                           │
│  │ Index: jd-copilot                                                           │
│  │ Dimensions: 384                                                             │
│  │ Metric: Cosine                                                              │
│  │                                                                             │
│  │ • Document Chunks                                                           │
│  │ • Embeddings                                                                │
│  │ • Metadata                                                                  │
│  │ • Similarity Search                                                         │
│  └─────────────────┘                                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 **Component Interaction Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMPONENT INTERACTIONS                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    HTTP/WS    ┌─────────────┐                                 │
│  │   React     │◄─────────────►│   FastAPI   │                                 │
│  │   Frontend  │               │   Backend   │                                 │
│  └─────────────┘               └─────────────┘                                 │
│                                        │                                       │
│                                        ▼                                       │
│  ┌─────────────┐               ┌─────────────┐                                 │
│  │   Flutter   │               │   Chat      │                                 │
│  │   Mobile    │               │   Service   │                                 │
│  └─────────────┘               └─────────────┘                                 │
│                                        │                                       │
│                                        ▼                                       │
│                               ┌─────────────┐                                 │
│                               │   Query     │                                 │
│                               │   Router    │                                 │
│                               └─────────────┘                                 │
│                                        │                                       │
│                                        ▼                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   SQLite    │    │  Pinecone   │    │   LLM       │    │   Context   │    │
│  │  Database   │    │  Vector DB  │    │  Services   │    │  Manager    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 **Performance Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PERFORMANCE LAYERS                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐                                                           │
│  │   Load          │                                                           │
│  │   Balancer      │  ──► Multiple FastAPI Instances                          │
│  │   (Nginx)       │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Cache         │                                                           │
│  │   Layer         │  ──► Redis for frequent queries                          │
│  │   (Redis)       │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Application   │                                                           │
│  │   Layer         │  ──► FastAPI + Uvicorn                                   │
│  │   (FastAPI)     │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Data          │                                                           │
│  │   Layer         │  ──► SQLite + Pinecone                                  │
│  │   (Databases)   │                                                           │
│  └─────────────────┘                                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔒 **Security Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐                                                           │
│  │   Network       │                                                           │
│  │   Security      │  ──► Firewall, VPN, DDoS Protection                      │
│  │   (External)    │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Application   │                                                           │
│  │   Security      │  ──► CORS, Rate Limiting, Input Validation              │
│  │   (FastAPI)     │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Data          │                                                           │
│  │   Security      │  ──► Encryption, Access Control, Audit Logs             │
│  │   (Databases)   │                                                           │
│  └─────────────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │   Infrastructure│                                                           │
│  │   Security      │  ──► Environment Variables, Secrets Management           │
│  │   (Config)      │                                                           │
│  └─────────────────┘                                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📈 **Monitoring & Analytics Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING ECOSYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Health    │    │   Metrics   │    │   Logs      │    │   Alerts    │    │
│  │   Checks    │    │   Collection│    │   Aggregation│   │   System    │    │
│  │             │    │             │    │             │    │             │    │
│  │ • API       │    │ • Response  │    │ • Structured│    │ • Email     │    │
│  │   Status    │    │   Times     │    │   Logging   │    │ • Slack     │    │
│  │ • Database  │    │ • Error     │    │ • Log       │    │ • PagerDuty │    │
│  │   Health    │    │   Rates     │    │   Rotation  │    │ • Webhooks  │    │
│  │ • Services  │    │ • Resource  │    │ • Search    │    │ • Escalation│    │
│  │   Status    │    │   Usage     │    │ • Analysis  │    │ • Recovery  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    │
│           │               │               │               │                   │
│           └───────────────┼───────────────┼───────────────┘                   │
│                           │               │                                   │
│                           ▼               ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Dashboard & Visualization                        │   │
│  │                                                                         │   │
│  │  • Real-time Metrics                                                    │   │
│  │  • Historical Trends                                                    │   │
│  │  • Performance Analytics                                                │   │
│  │  • User Behavior Insights                                               │   │
│  │  • System Health Overview                                               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

**These diagrams provide a comprehensive visual representation of the JD-Copilot system architecture, showing the relationships between components, data flow, security layers, and monitoring systems.**
