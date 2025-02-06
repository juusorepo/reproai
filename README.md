# Scientific Manuscript Analysis App

A Streamlit-based web application for analyzing scientific manuscripts in PDF format.

## Features
- PDF text extraction
- Automatic metadata extraction (title, authors, abstract) using GPT-4
- MongoDB storage for analysis results
- User-friendly interface for manuscript upload and analysis

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your-api-key
MONGODB_URI=your-mongodb-uri
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

## Project Structure
- `/app/services`: Core services for PDF processing and metadata extraction
- `/app/models`: Data models
- `streamlit_app.py`: Main application file
