# ReproAI Architecture

## System Overview

ReproAI is a tool for analyzing scientific manuscripts for reproducibility compliance. The system consists of a Streamlit web interface, a MongoDB database for storage, and various services for manuscript analysis.

## Architecture Diagram

```mermaid
graph TD
    subgraph Frontend
        UI[Streamlit UI]
        Upload[Upload Component]
        Results[Results View]
        Review[Review View]
        Checklist[Checklist View]
    end

    subgraph Services
        PDF[PDF Extractor]
        Meta[Metadata Extractor]
        Analyzer[Compliance Analyzer]
        DB[Database Service]
        Summary[Summarize Service]
    end

    subgraph Storage
        Mongo[(MongoDB)]
    end

    subgraph External
        OpenAI[OpenAI API]
    end

    UI --> Upload
    UI --> Results
    UI --> Review
    UI --> Checklist
    Upload --> PDF
    PDF --> Meta
    Meta --> Analyzer
    Analyzer --> DB
    DB --> Mongo
    Meta --> OpenAI
    Analyzer --> OpenAI
    Summary --> OpenAI
    Results --> DB
    Review --> DB
    Checklist --> DB
```

## Component Descriptions

### Frontend Components
- **Streamlit UI**: Main web interface for user interaction
- **Upload Component**: Handles manuscript PDF uploads
- **Results View**: Shows compliance score and high-level overview
- **Review View**: Detailed analysis with feedback options
- **Checklist View**: Manages compliance checklist items

### Services
- **PDF Extractor**: Extracts text content from PDF files
- **Metadata Extractor**: Uses OpenAI to extract metadata (title, authors, etc.)
- **Compliance Analyzer**: Analyzes manuscript for reproducibility compliance
- **Database Service**: Handles all database operations
- **Summarize Service**: Generates summaries of compliance analysis

### Storage
- **MongoDB**: Stores manuscripts, analysis results, and user feedback

## Database Schema

```mermaid
erDiagram
    Manuscript ||--o{ ComplianceResult : has
    Manuscript ||--o{ Feedback : receives
    ComplianceResult ||--o{ Feedback : has
    ChecklistItem ||--o{ ComplianceResult : defines

    Manuscript {
        string doi PK
        string title
        string[] authors
        string design
        string text
        datetime created_at
        datetime analysis_date
    }

    ComplianceResult {
        string doi FK
        string item_id FK
        string compliance
        string explanation
        string quote
        string section
        datetime created_at
    }

    Feedback {
        string doi FK
        string item_id FK
        string rating
        string comments
        datetime created_at
    }

    ChecklistItem {
        string item_id PK
        string category
        string text
        string guidance
        datetime created_at
    }
```

## Configuration

The app uses Streamlit's secrets management for configuration:

```toml
# .streamlit/secrets.toml
MONGODB_URI = "mongodb connection string"
OPENAI_API_KEY = "openai api key"
```

For Streamlit Cloud deployment, these secrets are configured in the Streamlit Cloud dashboard.

## Directory Structure

```
reproai/
├── app/
│   ├── models/          # Data models
│   ├── pages/          # UI pages
│   ├── prompts/        # LLM prompts
│   └── services/       # Business logic
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── .streamlit/        # Streamlit config
├── streamlit_app.py   # Main app
└── requirements.txt   # Dependencies
```

## Security Considerations

1. Secrets Management
   - Sensitive data stored in Streamlit secrets
   - No hardcoded credentials in code
   - .streamlit/secrets.toml ignored by git

2. Database Security
   - MongoDB Atlas with secure connection
   - Minimal database user permissions
   - Connection string in secrets

3. API Security
   - OpenAI API key in secrets
   - Rate limiting on API calls
   - Error handling for API failures
