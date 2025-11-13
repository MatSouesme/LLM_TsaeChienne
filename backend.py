"""
Job Matcher AI Backend - FastAPI Application
Matches resumes with job openings using Claude AI
"""

import os
import time
import json
from typing import Optional
from datetime import datetime
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic
from pypdf import PdfReader
from dotenv import load_dotenv
from storage.offers_db import init_db, add_offer, list_offers, get_offer
from agents.conversational_agent import ConversationalJobAgent
from agents.profile_management_agent import ProfileManagementAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Job Matcher AI",
    description="AI-powered Resume to Job Matching",
    version="1.0.0"
)

# CORS middleware for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize local offers DB
init_db()

# Observability metrics
metrics = {
    "total_requests": 0,
    "successful_matches": 0,
    "total_latency": 0.0,
    "total_cost": 0.0,
    "errors": 0
}


class MatchRequest(BaseModel):
    """Request model for job matching"""
    resume_text: str
    industry: str
    location: Optional[str] = None
    salary: Optional[int] = None


class ObservabilityMetrics(BaseModel):
    """Observability metrics model"""
    total_requests: int
    successful_matches: int
    avg_latency: float
    avg_cost: float
    errors: int
    status: str


class ChatRequest(BaseModel):
    """Request model for conversational chat"""
    session_id: str
    message: str
    resume_text: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for conversational chat"""
    session_id: str
    agent_response: str
    state: str
    timestamp: str


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")


def calculate_token_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on Claude 3.5 Sonnet pricing"""
    # Claude 3.5 Sonnet pricing (as of 2024)
    INPUT_COST_PER_1M = 3.00  # $3 per 1M input tokens
    OUTPUT_COST_PER_1M = 15.00  # $15 per 1M output tokens

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M

    return round(input_cost + output_cost, 4)


# Mock job database (in production, this would be a real database or API)
JOB_DATABASE = [
    # Diverse job offers for testing
    {
        "title": "Chauffeur Poids Lourd - Longue Distance",
        "company": "TransEurope Logistics",
        "location": "Paris / France",
        "salary": 42000,
        "industry": "health",  # Using different industry for variety
        "description": "Recherche chauffeur poids lourd expérimenté pour routes internationales Europe. Permis C + FIMO requis. Trajets longue distance, livraisons régulières Allemagne, Belgique, Italie. Respect des temps de conduite, maintenance véhicule. Hébergement payé en déplacement.",
        "requirements": ["Permis C", "FIMO", "Carte conducteur", "Expérience route", "Ponctualité", "Autonomie"]
    },
    {
        "title": "Agent d'Entretien - Bureaux et Espaces Commerciaux",
        "company": "CleanPro Services",
        "location": "Paris",
        "salary": 28000,
        "industry": "health",
        "description": "Recherche agent d'entretien pour nettoyage bureaux et espaces commerciaux. Travail en horaires décalés (tôt matin ou soirée). Nettoyage sols, sanitaires, vitres, poubelles. Utilisation produits professionnels. Possibilité temps partiel ou temps plein. Débutants acceptés avec formation.",
        "requirements": ["Rigueur", "Ponctualité", "Autonomie", "Sens du détail", "Bonne condition physique"]
    },
    {
        "title": "Gouvernante d'Hôtel de Luxe",
        "company": "Hôtel Le Grand Paris",
        "location": "Paris",
        "salary": 35000,
        "industry": "health",
        "description": "Hôtel 5 étoiles recherche gouvernante expérimentée. Supervision équipe ménage (10 personnes), contrôle qualité chambres, gestion stocks linge et produits. Standards luxe très élevés. Expérience hôtellerie haut de gamme requise. Horaires variables, disponibilité week-ends.",
        "requirements": ["Expérience hôtellerie luxe", "Management équipe", "Rigueur", "Standards qualité", "Gestion stocks", "Langues (anglais)"]
    },
    {
        "title": "Quantitative Researcher - ML & Statistics",
        "company": "Quant Capital Partners",
        "location": "Paris / Remote",
        "salary": 150000,
        "industry": "fintech",
        "description": "Seeking a quantitative researcher with strong mathematical background (Master's/PhD in Mathematics, Statistics, or Physics). Design and implement trading strategies using statistical models, machine learning, and optimization techniques. Work with time series, stochastic processes, deep learning. Python/R expert required.",
        "requirements": ["Python", "R", "Mathematics", "Statistics", "Machine Learning", "Stochastic Calculus", "Financial Modeling", "PyTorch/TensorFlow"]
    },
    {
        "title": "Senior Python Developer",
        "company": "Tech Corp Inc.",
        "location": "Remote / France",
        "salary": 130000,
        "industry": "technology",
        "description": "We're seeking a Senior Python Developer with strong experience in trading systems, FinTech, and high-frequency data processing. Must have expertise in Python, SQL, Docker, and distributed systems.",
        "requirements": ["Python", "SQL", "Docker", "Trading Systems", "FinTech"]
    },
    {
        "title": "Data Engineer L3",
        "company": "DataFlow Systems",
        "location": "Paris / Remote",
        "salary": 125000,
        "industry": "technology",
        "description": "Looking for a Data Engineer with cloud experience (AWS/GCP), strong SQL skills, ETL pipelines, and experience with big data technologies.",
        "requirements": ["SQL", "ETL", "Cloud (AWS/GCP)", "Python", "Big Data"]
    },
    {
        "title": "ML Ops Specialist",
        "company": "AI Innovations Ltd",
        "location": "Remote",
        "salary": 120000,
        "industry": "technology",
        "description": "Seeking an MLOps specialist to build and maintain ML infrastructure. Strong DevOps background with Python, Kubernetes, ML frameworks.",
        "requirements": ["Python", "Kubernetes", "MLOps", "CI/CD", "ML Frameworks"]
    },
    {
        "title": "Backend Developer",
        "company": "Startup XYZ",
        "location": "Paris",
        "salary": 115000,
        "industry": "technology",
        "description": "Backend developer for fintech startup. Python/Django, PostgreSQL, REST APIs. Equity options available.",
        "requirements": ["Python", "Django", "PostgreSQL", "REST APIs"]
    },
    {
        "title": "Software Engineer - Gambling Platform",
        "company": "Remote First Co",
        "location": "Fully Remote",
        "salary": 110000,
        "industry": "gambling",
        "description": "Full-stack engineer for online gambling platform. Python, React, real-time systems.",
        "requirements": ["Python", "React", "Real-time Systems", "PostgreSQL"]
    },
    {
        "title": "Lead Backend Engineer",
        "company": "Gaming Corp",
        "location": "Remote / Europe",
        "salary": 140000,
        "industry": "gambling",
        "description": "Lead backend engineer for sports betting platform. Microservices, Python, Kafka, Redis.",
        "requirements": ["Python", "Microservices", "Kafka", "Redis", "Sports Betting"]
    },
    {
        "title": "Senior Data Scientist",
        "company": "Casino Analytics",
        "location": "France",
        "salary": 135000,
        "industry": "gambling",
        "description": "Senior data scientist for casino analytics. Python, ML, statistics, responsible gaming algorithms.",
        "requirements": ["Python", "Machine Learning", "Statistics", "SQL", "Gaming"]
    },
    {
        "title": "Platform Engineer",
        "company": "Poker Tech",
        "location": "Remote",
        "salary": 128000,
        "industry": "gambling",
        "description": "Platform engineer for online poker. Python, Go, infrastructure as code, high availability systems.",
        "requirements": ["Python", "Go", "Infrastructure", "High Availability"]
    },
    {
        "title": "Full Stack Developer - iGaming",
        "company": "iGaming Solutions",
        "location": "Paris / Remote",
        "salary": 122000,
        "industry": "gambling",
        "description": "Full stack developer for iGaming platform. Python, TypeScript, Vue.js, real-time betting systems.",
        "requirements": ["Python", "TypeScript", "Vue.js", "Real-time Systems"]
    },
    {
        "title": "DevOps Engineer - Betting Platform",
        "company": "BetTech Ltd",
        "location": "Remote",
        "salary": 118000,
        "industry": "gambling",
        "description": "DevOps engineer for betting platform. Kubernetes, Python, Terraform, monitoring, CI/CD.",
        "requirements": ["Kubernetes", "Python", "Terraform", "CI/CD", "Monitoring"]
    }
]

# Load jobs from SQLite database
def load_jobs_from_db():
    """Load all jobs from SQLite offers database."""
    try:
        all_offers = list_offers()
        jobs = []
        for offer in all_offers:
            # Get full offer details
            full_offer = get_offer(offer['id'])
            if full_offer:
                jobs.append({
                    'title': full_offer['title'],
                    'company': full_offer['company'],
                    'location': full_offer['location'],
                    'salary': full_offer['salary'] or 0,
                    'industry': full_offer['industry'],
                    'description': full_offer['description'],
                    'requirements': full_offer['requirements']
                })
        return jobs if jobs else JOB_DATABASE  # Fallback to hardcoded if DB empty
    except Exception as e:
        print(f"Error loading jobs from DB: {e}, using hardcoded jobs")
        return JOB_DATABASE

# Load jobs dynamically from SQLite
ACTIVE_JOB_DATABASE = load_jobs_from_db()
print(f"Loaded {len(ACTIVE_JOB_DATABASE)} jobs from database")

# Initialize Conversational Agent
conversational_agent = ConversationalJobAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    job_database=ACTIVE_JOB_DATABASE,
    verbose=False  # Set to True for debugging
)

# Initialize Profile Management Agent
profile_agent = ProfileManagementAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    job_database=ACTIVE_JOB_DATABASE,
    verbose=True  # Set to True for debugging
)


def get_matching_jobs(industry: str, location: Optional[str], salary: Optional[int]) -> list:
    """Filter jobs from database based on criteria"""
    filtered_jobs = []

    for job in ACTIVE_JOB_DATABASE:
        # Industry match
        if industry and job["industry"].lower() != industry.lower():
            continue

        # Salary match (job salary should be >= requested salary)
        if salary and job["salary"] < salary:
            continue

        # Location match (basic string matching)
        if location:
            location_lower = location.lower()
            job_location_lower = job["location"].lower()
            # Match if remote or location is in job location
            if "remote" not in location_lower and "remote" not in job_location_lower:
                if location_lower not in job_location_lower:
                    continue

        filtered_jobs.append(job)

    return filtered_jobs[:10]  # Return top 10 matches


async def generate_job_matches_stream(resume_text: str, industry: str, location: Optional[str], salary: Optional[int]):
    """Generate job matches with streaming response"""
    start_time = time.time()

    try:
        # Get matching jobs from database
        matching_jobs = get_matching_jobs(industry, location, salary)

        if not matching_jobs:
            yield json.dumps({
                "error": "No matching jobs found for your criteria. Please try different parameters."
            }) + "\n"
            return

        # Prepare context for Claude
        jobs_context = "\n\n".join([
            f"Job {i+1}: {job['title']} at {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Salary: ${job['salary']:,}\n"
            f"Description: {job['description']}\n"
            f"Requirements: {', '.join(job['requirements'])}"
            for i, job in enumerate(matching_jobs)
        ])

        salary_text = f"${salary:,}" if salary else "Not specified"

        prompt = f"""You are an expert recruiter analyzing resume-job matches.

USER'S RESUME:
{resume_text}

USER'S CRITERIA:
- Industry: {industry}
- Preferred Location: {location or 'Any'}
- Minimum Salary: {salary_text}

AVAILABLE JOBS:
{jobs_context}

TASK:
Analyze the resume against each job and provide the TOP 5 best matches.

For each match, provide:
1. Job Title and Company
2. Match Score (0-100%)
3. Match Summary (2-3 sentences explaining why it's a good fit, highlighting relevant skills/experience)

Format your response as a JSON array with this exact structure:
[
  {{{{
    "job_title": "Job Title",
    "company": "Company Name",
    "match_score": 95,
    "match_summary": "Detailed explanation of the match...",
    "salary": 130000,
    "location": "Remote / France"
  }}}},
  ...
]

Only return the JSON array, no additional text."""

        # Call Claude API with streaming
        input_tokens = 0
        output_tokens = 0

        with anthropic_client.messages.stream(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            # Yield status update
            yield json.dumps({"status": "analyzing"}) + "\n"

            full_response = ""

            for text in stream.text_stream:
                full_response += text
                # Stream partial response
                yield json.dumps({"chunk": text}) + "\n"

            # Get usage information
            message = stream.get_final_message()
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

        # Parse the response
        try:
            # Extract JSON from response
            json_start = full_response.find('[')
            json_end = full_response.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                matches_json = full_response[json_start:json_end]
                matches = json.loads(matches_json)

                # Ensure we have top 5
                matches = matches[:5]

                # Calculate metrics
                latency = time.time() - start_time
                cost = calculate_token_cost(input_tokens, output_tokens)

                # Update global metrics
                metrics["total_requests"] += 1
                metrics["successful_matches"] += 1
                metrics["total_latency"] += latency
                metrics["total_cost"] += cost

                # Send final result
                yield json.dumps({
                    "status": "complete",
                    "matches": matches,
                    "metrics": {
                        "latency": round(latency, 2),
                        "cost": cost,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens
                    }
                }) + "\n"
            else:
                raise ValueError("Could not parse JSON from response")

        except Exception as e:
            metrics["errors"] += 1
            yield json.dumps({
                "error": f"Error parsing AI response: {str(e)}",
                "raw_response": full_response[:500]
            }) + "\n"

    except Exception as e:
        metrics["errors"] += 1
        yield json.dumps({"error": f"Error generating matches: {str(e)}"}) + "\n"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Matcher AI API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/api/metrics")
async def get_metrics():
    """Get observability metrics"""
    avg_latency = metrics["total_latency"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0
    avg_cost = metrics["total_cost"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0

    return ObservabilityMetrics(
        total_requests=metrics["total_requests"],
        successful_matches=metrics["successful_matches"],
        avg_latency=round(avg_latency, 2),
        avg_cost=round(avg_cost, 4),
        errors=metrics["errors"],
        status="online"
    )


@app.get("/api/offers")
def api_list_offers():
    """List all job offers (id, title, company, metadata)."""
    return list_offers()


@app.get("/api/offers/{offer_id}")
def api_get_offer(offer_id: int):
    """Get a single offer's full details."""
    offer = get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@app.post("/api/offers")
async def api_create_offer(
    title: str = Form(...),
    company: str = Form(...),
    location: str = Form(""),
    salary: Optional[int] = Form(None),
    industry: str = Form(""),
    description: str = Form(""),
    requirements: str = Form(""),
    pdf_file: UploadFile = File(None)
):
    """Create a new job offer. Accepts an optional PDF file."""
    pdf_bytes = None
    pdf_filename = None
    if pdf_file:
        pdf_bytes = await pdf_file.read()
        pdf_filename = pdf_file.filename

    req_list = [r.strip() for r in requirements.split(',') if r.strip()]
    offer_id = add_offer(title, company, location, salary, industry, description, req_list, pdf_bytes, pdf_filename)
    return {"id": offer_id}


@app.post("/api/match")
async def match_jobs(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    industry: str = Form(...),
    location: Optional[str] = Form(None),
    salary: Optional[str] = Form(None)
):
    """Match jobs endpoint with streaming support"""

    # Validate inputs
    if not resume_file and not resume_text:
        raise HTTPException(status_code=400, detail="Either resume_file or resume_text must be provided")

    if not industry:
        raise HTTPException(status_code=400, detail="Industry is required")

    # Extract resume text
    if resume_file:
        # Check file size (5MB limit)
        contents = await resume_file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        # Check file type
        if resume_file.filename.endswith('.pdf'):
            resume_content = extract_text_from_pdf(contents)
        elif resume_file.filename.endswith('.txt'):
            resume_content = contents.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
    else:
        resume_content = resume_text

        # Check text length (5000 characters limit)
        if len(resume_content) > 5000:
            raise HTTPException(status_code=400, detail="Resume text exceeds 5000 characters limit")

    # Parse salary
    salary_int = None
    if salary:
        try:
            salary_int = int(salary)
        except ValueError:
            raise HTTPException(status_code=400, detail="Salary must be a valid number")

    # Return streaming response
    return StreamingResponse(
        generate_job_matches_stream(resume_content, industry, location, salary_int),
        media_type="application/x-ndjson"
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }


@app.post("/api/detailed-score")
async def detailed_score(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    job_title: str = Form(...),
    company: str = Form(...),
    description: Optional[str] = Form(None),
    requirements: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    location: Optional[str] = Form("Remote"),
    salary: Optional[int] = Form(None)
):
    """
    Generate detailed explainable score for a specific resume-job match.

    This endpoint uses the hybrid scoring agent to provide:
    - Deterministic scores (skills, experience, education, salary, location)
    - Semantic scores (soft skills, culture fit, growth potential, projects)
    - Bonus scores (industry experience, rare skills, career trajectory)
    - Detailed explanations and recommendations
    """
    from scoring.scoring_agent import ScoringAgent

    # Validate inputs
    if not resume_file and not resume_text:
        raise HTTPException(status_code=400, detail="Either resume_file or resume_text must be provided")

    # Extract resume text
    if resume_file:
        contents = await resume_file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        if resume_file.filename.endswith('.pdf'):
            resume_content = extract_text_from_pdf(contents)
        elif resume_file.filename.endswith('.txt'):
            resume_content = contents.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
    else:
        resume_content = resume_text
        if len(resume_content) > 5000:
            raise HTTPException(status_code=400, detail="Resume text exceeds 5000 characters limit")

    # Use provided description and requirements, or try to find job in database
    job_description = description
    job_requirements = []
    job_location = location
    job_salary = salary or 0

    if not description or not requirements:
        # Try to find in database as fallback
        matching_job = None
        for job in JOB_DATABASE:
            if job['title'] == job_title and job['company'] == company:
                matching_job = job
                break

        if matching_job:
            job_description = job_description or matching_job['description']
            if not requirements:
                job_requirements = matching_job['requirements']
            job_location = matching_job['location']
            job_salary = matching_job['salary']
            industry = industry or matching_job.get('industry')
        elif not description:
            raise HTTPException(
                status_code=400,
                detail="Job description is required"
            )

    # Parse requirements if provided as string
    if requirements:
        job_requirements = [req.strip() for req in requirements.split(',')]

    try:
        # Initialize scoring agent
        agent = ScoringAgent()

        # Score the candidate and collect usage info
        start_time = time.time()
        detailed_match, usage = agent.score_candidate(
            resume_text=resume_content,
            job_title=job_title,
            company=company,
            job_description=job_description,
            job_requirements=job_requirements,
            job_location=job_location,
            job_salary=job_salary,
            candidate_location=location,
            candidate_salary_expectation=salary,
            industry=industry,
            company_culture=None
        )

        # Update observability metrics
        latency = time.time() - start_time
        input_tokens = usage.get('input_tokens', 0) if usage else 0
        output_tokens = usage.get('output_tokens', 0) if usage else 0
        cost = calculate_token_cost(input_tokens, output_tokens) if (input_tokens or output_tokens) else 0.0

        metrics["total_requests"] += 1
        metrics["successful_matches"] += 1
        metrics["total_latency"] += latency
        metrics["total_cost"] += cost

        # Convert to dict and return
        return detailed_match.to_dict()

    except Exception as e:
        metrics["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Error generating detailed score: {str(e)}")


@app.post("/api/chat")
async def chat_with_agent(
    session_id: Optional[str] = Form(None),
    message: str = Form(...),
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None)
):
    """
    Conversational agent endpoint for interactive job matching.

    This endpoint enables a chat-based interface where the agent:
    - Asks clarifying questions when information is missing
    - Searches for jobs intelligently
    - Presents matches with reasoning
    - Remembers conversation context

    Args:
        session_id: Session identifier (generated if not provided)
        message: User's message
        resume_file: Optional resume file upload (PDF/TXT)
        resume_text: Optional resume as plain text

    Returns:
        JSON response with agent's reply and session info
    """
    import uuid

    # Generate session_id if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Extract resume text from file if provided
    resume_content = resume_text
    if resume_file:
        contents = await resume_file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        if resume_file.filename.endswith('.pdf'):
            resume_content = extract_text_from_pdf(contents)
        elif resume_file.filename.endswith('.txt'):
            resume_content = contents.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    try:
        # Process message with agent
        start_time = time.time()
        response = conversational_agent.chat(
            session_id=session_id,
            user_message=message,
            resume_text=resume_content
        )

        # Update metrics
        latency = time.time() - start_time
        metrics["total_requests"] += 1
        metrics["successful_matches"] += 1
        metrics["total_latency"] += latency

        # Add latency to response
        response["latency"] = round(latency, 2)

        return response

    except Exception as e:
        metrics["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Error in conversational agent: {str(e)}")


@app.get("/api/chat/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a conversation session.

    Args:
        session_id: Session identifier

    Returns:
        Session summary including state and collected information
    """
    try:
        summary = conversational_agent.get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")


@app.delete("/api/chat/session/{session_id}")
async def reset_session(session_id: str):
    """
    Reset/clear a conversation session.

    Args:
        session_id: Session identifier

    Returns:
        Confirmation message
    """
    try:
        conversational_agent.reset_session(session_id)
        return {"message": f"Session {session_id} has been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")


# ========================================
# PROFILE MANAGEMENT AGENT ENDPOINTS
# ========================================

@app.post("/api/profile/chat")
async def profile_agent_chat(
    session_id: str = Form(...),
    message: str = Form(...),
    resume_file: Optional[UploadFile] = File(None)
):
    """
    Chat with the Profile Management Agent.

    The agent will analyze CVs, identify gaps, suggest optimizations,
    and help build a complete profile.

    Args:
        session_id: Session identifier
        message: User's message
        resume_file: Optional CV file (PDF or TXT)

    Returns:
        Agent response with profile state and tools used
    """
    resume_content = None

    # Process resume file if provided
    if resume_file:
        file_bytes = await resume_file.read()

        if resume_file.filename.endswith('.pdf'):
            resume_content = extract_text_from_pdf(file_bytes)
        elif resume_file.filename.endswith('.txt'):
            resume_content = file_bytes.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    try:
        # Process message with profile agent
        start_time = time.time()
        response = profile_agent.process_message(
            session_id=session_id,
            user_message=message,
            resume_text=resume_content
        )

        # Update metrics
        latency = time.time() - start_time
        metrics["total_requests"] += 1
        metrics["successful_matches"] += 1
        metrics["total_latency"] += latency

        # Add latency to response
        response["latency"] = round(latency, 2)

        return response

    except Exception as e:
        metrics["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Error in profile agent: {str(e)}")


@app.get("/api/profile/{session_id}")
async def get_profile(session_id: str):
    """
    Get current profile state for a session.

    Args:
        session_id: Session identifier

    Returns:
        Complete profile data with completeness score
    """
    try:
        summary = profile_agent.get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")


@app.delete("/api/profile/{session_id}")
async def reset_profile_session(session_id: str):
    """
    Reset/clear a profile session.

    Args:
        session_id: Session identifier

    Returns:
        Confirmation message
    """
    try:
        profile_agent.reset_session(session_id)
        return {"message": f"Profile session {session_id} has been reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting profile session: {str(e)}")


@app.post("/api/profile/{session_id}/analyze")
async def force_profile_analysis(session_id: str):
    """
    Force a complete profile analysis without conversation.

    Useful for getting current state of gaps, matches, and completeness.

    Args:
        session_id: Session identifier

    Returns:
        Analysis results with gaps, matches, and completeness score
    """
    try:
        analysis = profile_agent.force_analyze_profile(session_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing profile: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
