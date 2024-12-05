# Smart CV - An ATS for Applicants

Smart CV is an open-source Applicant Tracking System (ATS) designed specifically for job seekers. Unlike traditional ATS systems used by employers, this tool helps applicants optimize their applications, track their job search progress, and improve their chances of success.

## Features

### CV Management
- Upload and manage CVs in LaTeX format
- Automatic PDF generation
- Version control for tracking changes
- Future support planned for multiple formats

### Job Application Tracking
- Add and manage job postings
- Track application status and progress
- Store job descriptions and requirements
- Analyze job-CV match quality

### AI-Powered Analysis
- Static analysis using multiple algorithms:
  - Keyword matching
  - BERT similarity scoring
  - Cosine similarity analysis
  - Jaccard similarity comparison
  - Named Entity Recognition (NER)
  - Latent Semantic Analysis (LSA)
- Aggregated scoring system
- AI-driven improvement suggestions
- Skill gap identification

### Self-Assessment System
- Skill proficiency evaluation
- Gap analysis against job requirements
- Personalized improvement recommendations (Coming soon)
- Progress tracking over time (Coming soon)

### Interview Preparation (Coming Soon)
- AI-generated practice questions
- Role-specific preparation guides
- Company research integration
- Mock interview simulations

### Analytics Dashboard (Coming Soon)
- Application success metrics
- Skill development tracking
- Interview performance analytics
- Career progress visualization

## Technology Stack

### Backend
- FastAPI (Python web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- OpenAI API (AI capabilities)
- Sentence Transformers (NLP)
- spaCy (NLP)
- Docker (Containerization)

### Frontend
- Streamlit (UI framework)
- Recharts (Data visualization)
- Tailwind CSS (Styling)

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.12+
- PostgreSQL 13+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Stupidoodle/smart-cv.git
cd smart-cv
```

2. Set up environment variables:
```bash
# Create .env file in backend directory
touch backend/.env
# Edit .env with your configuration
```
The .env file should look something like this:
````plaintext
API_V1_STR=/api/v1
DATABASE_URL=postgresql://ats_user:ats_password@db:5432/ats_applicant
OPEN_AI_API_KEY=sk...
````

3. Start the services using Docker Compose:
```bash
cd docker
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
smart-cv/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── migrations/
│   └── tests/
├── frontend/
│   └── streamlit_app/
└── docker/
    └── docker-compose.yml
```

## API Documentation

The API documentation is automatically generated and available at `/docs` when running the backend server. It includes all available endpoints, request/response schemas, and example usage.

Key endpoints include:
- `/api/v1/cv/`: CV management
- `/api/v1/jobs/`: Job posting management
- `/api/v1/analysis/`: CV analysis
- `/api/v1/assistants/`: AI assistant interactions

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

### Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install development dependencies:
```bash
pip install -r backend/requirements.txt
pip install -r backend/base-requirements.txt
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests
```bash
pytest backend/tests/
```

## Roadmap

- [ ] Get jobs from link
  - [ ] Better Job ID tracking
- [ ] Native PDF support
- [ ] Self assessment integration
- [ ] Skill system and integration
- [ ] Enhanced interview preparation system
- [ ] Job board integration
- [ ] Career development tracking
- [ ] Documentation
- [ ] Community features
- [ ] Advanced analytics dashboard
- [ ] CV Editor

## License

This project is licensed under the CC BY-NC-ND 4.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for their powerful AI models
- The FastAPI community
- All contributors and users of the project

## Support

For support, please:
1. ~~Check the [documentation](docs/)~~
2. Search existing [issues](https://github.com/Stupidoodle/smart-cv/issues)
3. Create a new issue if needed

## Security

As I am planning to make this for **personal use only** and never deploy this due to 
the sensitive nature of CVs etc. security concerns will be ignored for now. If you 
want to SQLInject yourself go ahead. I will not be held responsible for any damages. 
Maybe in the future I will add some security features, just because I can.

Known security issues:
- SQL Injection
- No HTTPS
- No CSRF protection
- No rate limiting
- No authentication
- No authorization
- No input validation
- No output encoding
- No secure headers
- No secure cookies
- No secure CORS policy
- No secure content policy
- No secure referrer policy
- No secure X-Frame-Options
- No secure X-Content-Type-Options
- No secure X-XSS-Protection
- No secure HSTS policy
- No secure cookie attributes
- No secure password storage
- No secure file uploads
- No secure API design
- No secure database configuration
- No secure ORM configuration
- No secure logging configuration
- No secure error handling
- No secure dependency management
- No secure third-party libraries
- No secure development practices
- No secure deployment practices
- No secure CI/CD pipeline
- No secure secrets management
- No encryption at rest, in transit, in use, or in saving