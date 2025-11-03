# CV-Job Matching System with Explainable AI Scoring

An intelligent resume-to-job matching system powered by Claude AI, featuring a hybrid scoring architecture that combines deterministic rules with semantic analysis to provide transparent, explainable candidate evaluations.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Scoring System](#scoring-system)
- [Testing](#testing)
- [Technical Details](#technical-details)
- [Performance](#performance)

## Overview

This application provides two complementary approaches to candidate-job matching:

### Simple Matching Mode

Quick matching against multiple job positions with streaming results. Ideal for rapid candidate screening across multiple opportunities.

- Resume upload support (PDF/TXT, up to 5MB) or direct text input
- Real-time streaming responses for immediate feedback
- Filters by industry, location, and salary requirements
- Returns top 5 matches with scores and summaries
- Average latency: 4-5 seconds
- Cost per request: $0.01-0.02

### Detailed Scoring Mode

Comprehensive 100-point evaluation with complete transparency and justification. Designed for in-depth candidate assessment for specific positions.

- Hybrid scoring combining rule-based and AI-powered analysis
- Three-tier evaluation: Deterministic (40 pts), Semantic (40 pts), Bonus (20 pts)
- Complete breakdown of all scoring components
- Detailed strengths and weaknesses analysis
- Hiring recommendation with justification
- Average latency: 50-60 seconds
- Cost per evaluation: $0.03-0.05

## Architecture

### System Design

The application uses a modular architecture with clear separation of concerns:

```
Frontend (HTML/JS) <---> FastAPI Backend <---> Scoring Module <---> Claude AI API
```

### Scoring Architecture

The detailed scoring system implements a hybrid approach:

1. **Deterministic Scoring Tool** (40 points)
   - Skills matching with intelligent normalization
   - Experience years with AI-powered relevance evaluation
   - Education level comparison
   - Salary fit calculation
   - Location compatibility assessment

2. **Semantic Scoring Tool** (40 points)
   - Soft skills analysis (leadership, communication, teamwork)
   - Culture fit evaluation
   - Growth potential assessment
   - Project relevance matching

3. **Bonus Scoring Tool** (20 points)
   - Industry-specific experience evaluation
   - Rare skills detection (contextualized to job requirements)
   - Career trajectory analysis

4. **Score Explainer**
   - Aggregates all scores
   - Generates overall explanation
   - Extracts strengths (components >80% of max)
   - Identifies weaknesses (components <60% of max)
   - Provides hiring recommendation

## Project Structure

```
langchain/
├── backend.py                    # FastAPI server with endpoints
├── index.html                    # Production frontend interface
├── wire.html                     # Static wireframe prototype
├── pyproject.toml                # Python dependencies
├── uv.lock                       # Locked dependency versions
├── .env.example                  # Example environment configuration
├── README.md                     # This file
│
├── scoring/                      # Detailed scoring module
│   ├── __init__.py
│   ├── scoring_agent.py          # Main orchestrator
│   ├── deterministic_scoring_tool.py  # Rule-based scoring
│   ├── semantic_scoring_tool.py       # AI semantic analysis
│   ├── bonus_scoring_tool.py          # Bonus factors
│   ├── score_explainer.py             # Report generation
│   └── models.py                      # Pydantic data models
│
├── tests/                        # Comprehensive test suite
│   ├── test_all_cvs.py           # Full system validation
│   ├── test_scoring_agent.py     # Integration tests
│   ├── test_deterministic_scoring.py
│   ├── test_semantic_scoring.py
│   ├── test_bonus_scoring.py
│   ├── test_experience_relevance.py
│   ├── test_bonus_contextualization.py
│   ├── test_skills_fix.py
│   ├── test_extraction_fix.py
│   ├── test_api_detailed_score.py
│   └── test_chauffeur_*.py       # Specific validation tests
│
└── test_cv_*.txt                 # Test resume samples
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Anthropic API key
- Modern web browser

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd langchain
```

2. Install dependencies using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Your `.env` file should contain:
```
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### Starting the Application

1. Start the backend server:
```bash
python backend.py
```

The server will start on `http://localhost:8000`

2. Open the frontend:
```bash
# On Windows
start index.html

# On macOS
open index.html

# On Linux
xdg-open index.html
```

### Simple Matching Workflow

1. Upload a resume (PDF/TXT) or paste resume text
2. Select target industry (required)
3. Optionally specify location and minimum salary
4. Click "Find Best Matches"
5. View streaming results with top 5 matches
6. Copy results or download as JSON

### Detailed Scoring via API

```python
import requests

# Prepare the job data
job_data = {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "description": "...",
    "requirements": ["Python", "Docker", "SQL"],
    "location": "Remote",
    "salary": 130000,
    "industry": "fintech"
}

# Send request
response = requests.post(
    "http://localhost:8000/api/detailed-score",
    files={"resume_file": open("resume.pdf", "rb")},
    data={"job_data": json.dumps(job_data)}
)

result = response.json()
print(f"Score: {result['match_score']}/100")
print(f"Recommendation: {result['recommendation']}")
```

## API Reference

### POST /api/match

Quick matching with streaming response.

**Request** (multipart/form-data):
- `resume_file` (optional): PDF or TXT file
- `resume_text` (optional): Plain text resume
- `industry` (required): Target industry
- `location` (optional): Preferred location
- `salary` (optional): Minimum salary

**Response**: NDJSON stream
```json
{"status": "analyzing"}
{"chunk": "partial response..."}
{"status": "complete", "matches": [...], "metrics": {...}}
```

### POST /api/detailed-score

Comprehensive scoring with detailed breakdown.

**Request** (multipart/form-data):
- `resume_file` (optional): PDF or TXT file
- `resume_text` (optional): Plain text resume
- `job_data` (required): JSON string with job details

**Response**: JSON
```json
{
  "match_score": 85.0,
  "recommendation": "Strongly recommended",
  "score_breakdown": {
    "deterministic": {
      "total": 35.0,
      "skills_matching": {"score": 13.5, "max": 15, "explanation": "..."},
      "experience_years": {"score": 8.0, "max": 10, "explanation": "..."},
      "education_match": {"score": 5.0, "max": 5, "explanation": "..."},
      "salary_fit": {"score": 4.5, "max": 5, "explanation": "..."},
      "location_match": {"score": 4.0, "max": 5, "explanation": "..."}
    },
    "semantic": {
      "total": 33.0,
      "soft_skills": {"score": 13.0, "max": 15, "explanation": "..."},
      "culture_fit": {"score": 8.0, "max": 10, "explanation": "..."},
      "growth_potential": {"score": 8.0, "max": 10, "explanation": "..."},
      "project_relevance": {"score": 4.0, "max": 5, "explanation": "..."}
    },
    "bonus": {
      "total": 17.0,
      "industry_experience": {"score": 9.0, "max": 10, "explanation": "..."},
      "rare_skills": {"score": 4.0, "max": 5, "explanation": "..."},
      "career_trajectory": {"score": 4.0, "max": 5, "explanation": "..."}
    }
  },
  "strengths": [
    "Strong technical skills with 10+ matched competencies",
    "Outstanding soft skills and communication abilities"
  ],
  "weaknesses": [
    "Salary expectation slightly above budget"
  ],
  "overall_explanation": "..."
}
```

### GET /api/metrics

System observability metrics.

**Response**: JSON
```json
{
  "total_requests": 42,
  "successful_matches": 40,
  "avg_latency": 4.2,
  "avg_cost": 0.08,
  "errors": 2,
  "status": "online"
}
```

### GET /api/health

Health check endpoint.

**Response**: JSON
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Scoring System

### Deterministic Scoring (40 points)

**Skills Matching (15 points)**
- Extracts skills from resume and job requirements
- Separates hard skills (technical) from soft skills
- Uses intelligent matching (e.g., "Docker" matches "Dockerization")
- Awards points for matched skills + bonus for additional relevant skills
- Soft skills are evaluated separately using AI

**Experience Years (10 points)**
- Extracts years of experience from resume
- Uses AI to evaluate relevance to the target position
- Key innovation: Distinguishes transferable vs. non-transferable experience
- Example: 12 years as truck driver = 0 relevant years for software developer
- Scales score based on job requirements

**Education Match (5 points)**
- Detects education level (PhD, Master, Bachelor, Diploma, etc.)
- Compares against job requirements
- Awards proportional points

**Salary Fit (5 points)**
- Calculates gap between candidate expectation and job offer
- Applies graduated penalty for larger gaps
- Full points if expectations align

**Location Match (5 points)**
- Remote positions get maximum points
- Matches city, region, and country
- Partial points for regional matches

### Semantic Scoring (40 points)

All semantic scoring uses Claude AI for nuanced evaluation:

**Soft Skills (15 points)**
- Analyzes leadership, communication, teamwork, problem-solving, initiative
- Evaluates both explicit mentions and implicit demonstrations
- Returns score with 2-3 sentence justification

**Culture Fit (10 points)**
- Assesses values alignment, work style, environment preferences
- Considers company culture if provided
- Identifies potential cultural mismatches

**Growth Potential (10 points)**
- Evaluates learning capacity, career progression, adaptability
- Considers certifications, courses, career advancement
- Assesses long-term potential

**Project Relevance (5 points)**
- Analyzes similarity between past projects and job requirements
- Identifies transferable experience
- Highlights relevant achievements

### Bonus Scoring (20 points)

**Industry Experience (10 points)**
- Evaluates years in specific industry
- Assesses domain knowledge depth
- Considers industry-specific projects

**Rare Skills (5 points)**
- Identifies uncommon, valuable skills
- Contextualizes to job requirements (innovation: not just "rare" but "rare AND relevant")
- Example: ML skills are valuable for data scientist but not for truck driver

**Career Trajectory (5 points)**
- Analyzes career progression coherence
- Evaluates upward mobility
- Identifies concerning gaps or patterns

### Recommendation Thresholds

- **85-100**: Strongly recommended
- **75-84**: Recommended
- **65-74**: Consider for interview
- **50-64**: Moderate fit
- **0-49**: Not recommended

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest tests/
```

Run specific test:
```bash
python tests/test_all_cvs.py
```

### Test Suite

The project includes comprehensive tests covering:

1. **Unit Tests**
   - `test_deterministic_scoring.py`: Rule-based calculations
   - `test_semantic_scoring.py`: AI semantic analysis
   - `test_bonus_scoring.py`: Bonus scoring factors

2. **Integration Tests**
   - `test_scoring_agent.py`: Full pipeline integration
   - `test_api_detailed_score.py`: API endpoint testing

3. **System Validation**
   - `test_all_cvs.py`: End-to-end validation with 5 scenarios
     - Perfect match: Truck driver → Truck driver (85/100)
     - Good match: Housekeeper → Cleaning agent (83/100)
     - Stretch match: Housekeeper → Luxury hotel manager (63/100)
     - Mismatch: Data scientist → Truck driver (40/100)
     - Mismatch: Truck driver → Senior developer (20/100)

4. **Feature-Specific Tests**
   - `test_experience_relevance.py`: Experience contextualization
   - `test_bonus_contextualization.py`: Rare skills contextualization
   - `test_skills_fix.py`: Skills matching accuracy
   - `test_extraction_fix.py`: Experience extraction

### Test Data

Three test resumes covering different profiles:

- `test_cv_maths_tech.txt`: Data Scientist / ML Engineer
- `test_cv_chauffeur.txt`: Professional truck driver
- `test_cv_menage.txt`: Cleaning/housekeeping professional

## Technical Details

### Technology Stack

**Backend**
- FastAPI: Modern Python web framework
- Anthropic SDK: Claude AI integration (claude-3-haiku-20240307)
- PyPDF: PDF text extraction
- Pydantic: Data validation and serialization
- Uvicorn: ASGI server

**Frontend**
- Vanilla JavaScript (no framework dependencies)
- Fetch API with streaming support
- CSS3 with glassmorphism design
- HTML5 semantic markup

**AI/ML**
- Claude 3 Haiku for all AI operations
- Structured prompts with guided scoring
- Response parsing with validation

### Key Innovations

**1. Experience Relevance Evaluation**

Traditional systems count total years of experience. This system uses AI to evaluate if experience is actually applicable to the target role:

```python
# Before: 12 years truck driver → 9.0/10 points for developer role (incorrect)
# After: AI evaluates → 0.0/10 points (correct, experience not transferable)
```

**2. Contextualized Rare Skills**

Rare skills are only valuable if relevant to the position:

```python
# ML/AI skills for Data Scientist role → 5/5 points
# ML/AI skills for Truck Driver role → 0/5 points (not relevant)
```

**3. Hard vs. Soft Skills Separation**

- Hard skills: Deterministic matching with normalization
- Soft skills: AI semantic evaluation of demonstrations

**4. Explainability First**

Every score component includes:
- Numerical score
- Maximum possible score
- Detailed explanation
- Evidence from resume

### Database

The current implementation uses a mock database in `backend.py` with 15 sample job postings. For production deployment, replace with:

- Real job board API integration (LinkedIn, Indeed, etc.)
- Database (PostgreSQL, MongoDB)
- Elasticsearch for advanced search

### Privacy and Compliance

- GDPR compliant: No data persistence
- Session-based: Data cleared after response
- No tracking or analytics
- API keys stored securely in environment variables
- No third-party data sharing

## Performance

### Metrics

| Metric | Simple Match | Detailed Score |
|--------|--------------|----------------|
| Latency | 4-5 seconds | 50-60 seconds |
| API Calls | 1 | 9 |
| Cost per Request | $0.01-0.02 | $0.03-0.05 |
| Accuracy | Good | Excellent |
| Detail Level | Basic | Comprehensive |

### Optimization Opportunities

1. **Caching**: Cache job descriptions and common skill extractions
2. **Parallel Processing**: Run independent AI calls in parallel
3. **Batch Mode**: Process multiple candidates simultaneously
4. **Model Selection**: Use smaller models for simpler tasks
5. **Prompt Optimization**: Reduce token usage in prompts

### Scalability Considerations

- Current: Single candidate, sequential processing
- Production needs:
  - Async processing for multiple candidates
  - Queue system for long-running evaluations
  - Result caching
  - Rate limiting
  - Load balancing

## Troubleshooting

### Backend Issues

**Server won't start**
- Verify Python version: `python --version` (requires 3.11+)
- Install dependencies: `uv sync` or `pip install -e .`
- Check port availability: `netstat -ano | findstr :8000` (Windows)

**API key errors**
- Verify `.env` file exists and contains valid API key
- Check Anthropic API status: https://status.anthropic.com
- Ensure API key has sufficient credits

### Frontend Issues

**Shows "Offline" status**
- Verify backend is running on http://localhost:8000
- Check browser console for errors (F12)
- Verify CORS is enabled in backend

**File upload fails**
- Ensure file size < 5MB
- Verify file format (PDF or TXT only)
- Try text paste as alternative

### Scoring Issues

**Unexpectedly low scores**
- Review score breakdown for specific weak components
- Check resume format (ensure text is extractable)
- Verify job requirements are appropriate

**High latency**
- Detailed scoring requires ~50-60 seconds (by design)
- Use simple matching mode for faster results
- Check network connection to Anthropic API

## Development

### Adding New Features

**Add new scoring component:**

1. Define score model in `scoring/models.py`
2. Implement scoring logic in appropriate tool
3. Update `ScoringAgent` to include new component
4. Add tests in `tests/`
5. Update documentation

**Add new job source:**

1. Implement API client for job board
2. Update `get_matching_jobs()` in `backend.py`
3. Add data transformation logic
4. Test with real job data

### Code Quality

- Type hints throughout codebase
- Pydantic models for data validation
- Comprehensive docstrings
- Modular architecture
- Test coverage for critical paths

## License

This project is for educational purposes.

## Acknowledgments

- Anthropic for Claude AI API
- FastAPI for excellent web framework
- The Python community for robust tooling
