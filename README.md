# ReproAI - Manuscript Compliance Analysis Tool

A Streamlit-based tool for analyzing scientific manuscripts against reporting guidelines.

## Features

- Upload and analyze PDF manuscripts
- Extract metadata automatically
- Check compliance against Nature Human Behavior checklist
- Generate detailed compliance reports
- Interactive visualization of compliance results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reproai.git
cd reproai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in your environment variables in `.env`:
- `MONGODB_URI`: Your MongoDB connection string
- `OPENAI_API_KEY`: Your OpenAI API key

## Running the App Locally

```bash
streamlit run streamlit_app.py
```

## Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Add your environment variables in Streamlit Cloud:
   - Go to your app's settings
   - Add the following in the "Secrets" section:
   ```toml
   [secrets]
   MONGODB_URI = "your_actual_mongodb_uri"
   OPENAI_API_KEY = "your_actual_openai_key"
   ```

## Usage

1. Upload a scientific manuscript (PDF)
2. The tool will automatically:
   - Extract metadata
   - Analyze compliance with reporting guidelines
   - Generate a detailed report
   - Show compliance statistics

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
