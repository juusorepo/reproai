# ReproAI Architecture

## System Overview

ReproAI is a tool for analyzing scientific manuscripts for reproducibility compliance. The system consists of a Streamlit web interface, a MongoDB database for storage, and various services for manuscript analysis.

## Architecture Diagram

```mermaid
graph TD
    subgraph Frontend
        UI[Streamlit UI]
        Upload[Upload Component]
        Results[Results Component]
        Feedback[Feedback Component]
    end

    subgraph Services
        PDF[PDF Extractor]
        Meta[Metadata Extractor]
        Analyzer[Compliance Analyzer]
        DB[Database Service]
    end

    subgraph Storage
        Mongo[(MongoDB)]
    end

    subgraph External
        OpenAI[OpenAI API]
    end

    UI --> Upload
    UI --> Results
    UI --> Feedback
    Upload --> PDF
    PDF --> Meta
    Meta --> Analyzer
    Analyzer --> DB
    DB --> Mongo
    Meta --> OpenAI
    Analyzer --> OpenAI
    Results --> DB
    Feedback --> DB
```

## Component Descriptions

### Frontend Components
- **Streamlit UI**: Main web interface for user interaction
- **Upload Component**: Handles manuscript PDF uploads
- **Results Component**: Displays compliance analysis results
- **Feedback Component**: Allows users to provide feedback on analysis results

### Services
- **PDF Extractor**: Extracts text content from PDF files
- **Metadata Extractor**: Uses OpenAI to extract metadata (title, authors, etc.)
- **Compliance Analyzer**: Analyzes manuscript for reproducibility compliance
- **Database Service**: Handles all database operations

### Storage
- **MongoDB**: Stores manuscripts, analysis results, and user feedback

## Database Schema

```mermaid
erDiagram
    Manuscript ||--o{ ComplianceResult : has
    Manuscript ||--o{ Feedback : receives
    ComplianceResult ||--o{ Feedback : has

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
        string item_id
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
```

## Workflow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant PDF as PDF Extractor
    participant Meta as Metadata Extractor
    participant Analyzer as Compliance Analyzer
    participant DB as Database
    participant AI as OpenAI

    User->>UI: Upload Manuscript
    UI->>PDF: Extract Text
    PDF-->>UI: Text Content
    UI->>Meta: Extract Metadata
    Meta->>AI: Request Analysis
    AI-->>Meta: Metadata
    Meta-->>UI: Manuscript Info
    UI->>DB: Save Manuscript
    UI->>Analyzer: Analyze Compliance
    Analyzer->>AI: Request Analysis
    AI-->>Analyzer: Compliance Results
    Analyzer->>DB: Save Results
    DB-->>UI: Return Results
    UI-->>User: Display Results
    User->>UI: Provide Feedback
    UI->>DB: Save Feedback
```

## Environment Setup

The application requires the following environment variables:
- `MONGODB_URI`: MongoDB connection string
- `OPENAI_API_KEY`: OpenAI API key for manuscript analysis

## API Documentation

### Database Service

The database service provides the following operations:
- `save_manuscript(manuscript: Manuscript)`: Save a new manuscript
- `get_manuscript(doi: str)`: Retrieve a manuscript by DOI
- `save_compliance_results(results: List[ComplianceResult])`: Save compliance analysis results
- `get_compliance_results(doi: str)`: Get compliance results for a manuscript
- `save_feedback(feedback: Feedback)`: Save user feedback
- `get_feedback(doi: str, item_id: str)`: Get feedback for a specific compliance item
