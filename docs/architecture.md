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
        LLM[LLM Service]
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
    Meta --> LLM
    LLM --> OpenAI
    Meta --> Analyzer
    Analyzer --> LLM
    Summary --> LLM
    DB --> Mongo
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
- **LLM Service**: Provides LLM functionality for analysis
- **Compliance Analyzer**: Analyzes manuscript for reproducibility compliance
- **Database Service**: Handles all database operations
- **Summarize Service**: Generates summaries of compliance analysis

### Storage
- **MongoDB**: Stores manuscripts, analysis results, and user feedback

## Error Handling

ReproAI implements a robust error handling system:

1. **Compliance Analysis**
   - Automatic retry mechanism for failed checklist items
   - 5-second delay between retries to handle rate limits
   - Detailed error collection and reporting
   - Progress tracking for partial completions

2. **User Feedback**
   - Clear error messages in the UI
   - Warning indicators for partial analyses
   - Real-time progress updates
   - Detailed error traces for debugging

3. **Data Integrity**
   - Transaction-based database operations
   - Validation of all user inputs
   - Schema validation for API responses
   - Automatic data cleanup

## Components

### Frontend (Streamlit)

- **Upload Component**
  - PDF file validation
  - Progress tracking
  - Error reporting

- **Results View**
  - Compliance score calculation
  - Analysis completeness indicators
  - Error and warning displays

- **Review View**
  - Detailed analysis results
  - User feedback collection
  - Error correction interface

### Services

- **PDF Extractor**
  - Text extraction
  - Error handling for corrupted files
  - Progress tracking

- **Metadata Extractor**
  - Title, authors, DOI extraction
  - Discipline classification
  - Schema validation
  - Retry mechanism

- **LLM Service**
  - Provides LLM functionality for analysis
  - Context management
  - Structured analysis
  - Error handling

- **Compliance Analyzer**
  - 22-item checklist analysis
  - Automatic retries for failed items
  - Error collection and reporting
  - Progress tracking
  - Rate limit handling

- **Database Service**
  - MongoDB operations
  - Transaction support
  - Error handling
  - Data validation

- **Summarize Service**
  - Result aggregation
  - Category-based analysis
  - Error handling for partial results

### LLM Implementation

#### Context Management
- Uses GPT-4 Turbo with 128K token context window
- Smart text truncation strategy:
  - 100K tokens reserved for input
  - 4K tokens reserved for output
  - Preserves most recent content when truncating
- Comprehensive error handling and retry logic

#### Structured Analysis
1. **Metadata Extraction**
   - JSON-structured extraction of:
     - Title and authors
     - Study design and discipline
     - DOI and contact information
   - Schema validation for consistency

2. **Compliance Analysis**
   - Per-item JSON responses containing:
     - Compliance status (Yes/No/Partial/N/A)
     - Supporting evidence and quotes
     - Section identification
   - Automatic retry for failed items

3. **Results Summarization**
   - Two-level summary generation:
     - Overview with key recommendations
     - Category-based analysis with severity
   - Structured output for reliable parsing

#### Error Handling
- Comprehensive logging of LLM interactions
- Debug mode for input/output inspection
- Rate limit management
- Automatic retries with exponential backoff

## Data Models

- **Manuscript**
  - Basic metadata (title, authors, DOI)
  - Extended metadata (discipline, design)
  - Analysis status tracking
  - Validation rules

- **ComplianceResult**
  - Analysis results
  - Supporting evidence
  - Error tracking
  - Validation schema

- **Feedback**
  - User corrections
  - Quality metrics
  - Validation rules

## Error Flow

```mermaid
graph TD
    A[Analysis Request] --> B{Compliance Analyzer}
    B --> |Success| C[Store Results]
    B --> |Failure| D[Retry Logic]
    D --> |Success| C
    D --> |Failure| E[Error Collection]
    E --> F[User Notification]
    F --> G[Partial Results]
    G --> H[Summary Generation]
```

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
│   ├── models/          # Data models (manuscript, compliance_result, feedback)
│   ├── pages/          # UI pages
│   ├── prompts/        # LLM prompts for analysis
│   └── services/       # Business logic
│       ├── compliance_analyzer.py
│       ├── db_service.py
│       ├── llm_service.py
│       ├── metadata_extractor.py
│       ├── pdf_extractor.py
│       └── summarize_service.py
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── static/           # Static assets (CSS)
├── .streamlit/       # Streamlit config
├── home.py          # Main application
└── requirements.txt  # Dependencies
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
