# ReproAI - Manuscript Compliance Analysis Tool

A Streamlit-based tool for analyzing scientific manuscripts against reporting guidelines. ReproAI uses OpenAI's GPT-4 to analyze manuscripts and provide detailed feedback on their compliance with reproducibility guidelines.

## Requirements

- Python 3.13 or higher
- MongoDB database (local or Atlas)
- OpenAI API key

## Features

- **PDF Processing**
  - Upload and process PDF manuscripts
  - Automatic text extraction and sectioning
  - Metadata extraction (title, authors, DOI)

- **Compliance Analysis**
  - Check against Nature Human Behavior checklist
  - AI-powered analysis of each checklist item
  - Detailed explanations with supporting quotes
  - Section identification for evidence

- **Interactive Interface**
  - Clear visualization of compliance results
  - View Results with compliance score and summary
  - Review page with detailed analysis
  - Interactive checklist management
  - User feedback system for results

- **Data Management**
  - MongoDB integration for data persistence
  - Track analysis history
  - Store and retrieve user feedback

## Architecture

See [Architecture Documentation](docs/architecture.md) for detailed system design information.

## LLM Analysis Process

ReproAI uses GPT-4 Turbo to perform sophisticated analysis of scientific manuscripts through a multi-stage process:

### 1. Metadata Extraction
- Extracts key manuscript information including:
  - Title and authors
  - Study design classification
  - DOI and corresponding author's email
  - Abstract
  - Academic discipline classification
- Uses structured JSON output format for consistent parsing

### 2. Compliance Analysis
- Analyzes manuscript against reporting guidelines
- For each checklist item:
  - Evaluates compliance status (Yes/No/Partial/N/A)
  - Provides explanation for the assessment
  - Extracts supporting quotes from the text
  - Identifies relevant manuscript sections

### 3. Results Summarization
- Generates two types of summaries:
  1. Overview Summary
     - Overall compliance assessment
     - Key strengths and gaps
     - Critical recommendations (1-3 items)
  2. Category-Based Analysis
     - Per-category compliance level
     - Severity assessment (high/medium/low)
     - Specific improvement recommendations

### Technical Implementation
- Uses GPT-4 Turbo with 128K token context window
- Implements smart text truncation (preserving recent content)
- Structured JSON outputs for reliable parsing
- Comprehensive error handling and logging
- Debug mode for LLM input/output inspection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reproai.git
cd reproai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Local Development

1. Create `.streamlit/secrets.toml`:
```toml
MONGODB_URI = "your_mongodb_connection_string"
OPENAI_API_KEY = "your_openai_api_key"
```

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud (share.streamlit.io)
3. Add your secrets in the Streamlit Cloud dashboard:
   - Go to App Settings > Secrets
   - Add the following variables:
     ```toml
     MONGODB_URI = "your_mongodb_connection_string"
     OPENAI_API_KEY = "your_openai_api_key"
     ```

## Database Setup

1. Create a MongoDB database (local or Atlas)
2. Import initial checklist items:
```bash
python scripts/init_db.py
```

## Running the App

### Local Development
```bash
streamlit run streamlit_app.py
```

### Docker Deployment
```bash
docker build -t reproai .
docker run -p 8501:8501 reproai
```

## Usage

1. Start the app and navigate to the web interface
2. Upload a manuscript PDF or select a previously analyzed one
3. View the analysis results in three main sections:
   - **Results**: High-level overview with compliance score
   - **Review**: Detailed analysis with feedback options
   - **Checklist**: View and manage checklist items

## Project Structure

```
reproai/
├── app/
│   ├── models/          # Data models
│   ├── pages/          # Streamlit pages
│   ├── prompts/        # OpenAI prompts
│   └── services/       # Business logic
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── tests/            # Test files
├── .env.example      # Example environment file
├── requirements.txt  # Python dependencies
└── streamlit_app.py  # Main application file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web framework
- [OpenAI](https://openai.com/) for the GPT-4 API
- Nature Human Behavior for the reproducibility checklist
