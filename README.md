# ReproAI - Manuscript Compliance Analysis Tool

A Streamlit-based tool for analyzing scientific manuscripts against reporting guidelines. ReproAI uses OpenAI's GPT-4 to analyze manuscripts and provide detailed feedback on their compliance with reproducibility guidelines.

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
  - Summary dashboard with compliance score
  - Detailed view of each checklist item
  - User feedback system for results

- **Data Management**
  - MongoDB integration for data persistence
  - Track analysis history
  - Store and retrieve user feedback

## Architecture

See [Architecture Documentation](docs/architecture.md) for detailed system design information.

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

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in your environment variables in `.env`:
```env
MONGODB_URI=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_api_key
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

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Add your environment variables in Streamlit Cloud:
   ```toml
   [secrets]
   MONGODB_URI = "your_mongodb_connection_string"
   OPENAI_API_KEY = "your_openai_api_key"
   ```

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
