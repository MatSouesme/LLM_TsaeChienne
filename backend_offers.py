"""
Job Matcher AI Backend - Experimental offers-matching copy
Non-destructive copy of backend.py with an added /api/match_offers endpoint
that scores an uploaded resume against stored offers and returns the top-K matches
as a single JSON response (Option A requested).
"""

import os
import time
import json
from typing import Optional
from datetime import datetime
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from anthropic import Anthropic
from pypdf import PdfReader
from dotenv import load_dotenv
from storage.offers_db import init_db, add_offer, list_offers, get_offer

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Job Matcher AI (Offers)",
    description="Experimental: score a CV against stored job offers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize DB
init_db()

# Observability metrics (separate from main backend to avoid collisions)
metrics = {
    "total_requests": 0,
    "successful_matches": 0,
    "total_latency": 0.0,
    "total_cost": 0.0,
    "errors": 0
}


class ObservabilityMetrics(BaseModel):
    total_requests: int
    successful_matches: int
    avg_latency: float
    avg_cost: float
    errors: int
    status: str


def extract_text_from_pdf(pdf_file: bytes) -> str:
    try:
        pdf_reader = PdfReader(BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")


def calculate_token_cost(input_tokens: int, output_tokens: int) -> float:
    INPUT_COST_PER_1M = 3.00
    OUTPUT_COST_PER_1M = 15.00
    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
    return round(input_cost + output_cost, 4)


@app.get("/")
async def root():
    return {"message": "Job Matcher AI API (offers copy)", "status": "online"}


@app.get("/api/metrics")
async def get_metrics():
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
    return list_offers()


@app.get("/api/offers/{offer_id}")
def api_get_offer(offer_id: int):
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
    pdf_bytes = None
    pdf_filename = None
    if pdf_file:
        pdf_bytes = await pdf_file.read()
        pdf_filename = pdf_file.filename

    req_list = [r.strip() for r in requirements.split(',') if r.strip()]
    offer_id = add_offer(title, company, location, salary, industry, description, req_list, pdf_bytes, pdf_filename)
    return {"id": offer_id}


@app.post("/api/match_offers")
async def match_offers(
    resume_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    salary: Optional[str] = Form(None),
    max_offers: Optional[int] = Form(50),
    top_k: Optional[int] = Form(3)
):
    """
    Score the provided resume against stored offers and return the top-K matches as JSON.

    - resume_file or resume_text required
    - optional filters: industry, location, salary
    - max_offers: limit how many offers to score (default 50)
    - top_k: how many top results to return (default 3)
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

    # parse salary
    salary_int = None
    if salary:
        try:
            salary_int = int(salary)
        except ValueError:
            raise HTTPException(status_code=400, detail="Salary must be a valid number")

    # Fetch offers and apply light filtering
    offers = list_offers()
    if not offers:
        raise HTTPException(status_code=400, detail="No offers available in the database")

    # optional filtering by industry
    if industry:
        offers = [o for o in offers if (o.get('industry') or '').lower() == industry.lower()]

    # limit number of offers to score
    offers_to_score = offers[: max(1, min(len(offers), max_offers))]

    agent = ScoringAgent()
    scored_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    start_time = time.time()

    try:
        for o in offers_to_score:
            full = get_offer(o['id'])
            if not full:
                continue

            # Score against this offer
            detailed, usage = agent.score_candidate(
                resume_text=resume_content,
                job_title=full.get('title', ''),
                company=full.get('company', ''),
                job_description=full.get('description', ''),
                job_requirements=full.get('requirements', []),
                job_location=full.get('location', ''),
                job_salary=full.get('salary') or 0,
                candidate_location=location,
                candidate_salary_expectation=salary_int,
                industry=full.get('industry') or industry,
                company_culture=None
            )

            scored_results.append({
                "id": full.get('id'),
                "job_title": detailed.job_title,
                "company": detailed.company,
                "match_score": detailed.match_score,
                "salary": detailed.salary,
                "location": detailed.location,
                "detail": detailed.to_dict()
            })

            if usage:
                total_input_tokens += usage.get('input_tokens', 0)
                total_output_tokens += usage.get('output_tokens', 0)

        # Sort and pick top_k
        scored_results.sort(key=lambda x: x['match_score'], reverse=True)
        top_results = scored_results[: max(1, min(len(scored_results), top_k))]

        # metrics
        latency = time.time() - start_time
        cost = calculate_token_cost(total_input_tokens, total_output_tokens) if (total_input_tokens or total_output_tokens) else 0.0

        metrics["total_requests"] += 1
        metrics["successful_matches"] += len(top_results)
        metrics["total_latency"] += latency
        metrics["total_cost"] += cost

        return JSONResponse({
            "matches": top_results,
            "metrics": {
                "latency": round(latency, 2),
                "cost": cost,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens
            }
        })

    except Exception as e:
        metrics["errors"] += 1
        raise HTTPException(status_code=500, detail=f"Error scoring offers: {str(e)}")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
