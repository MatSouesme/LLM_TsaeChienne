"""
Profile Management Tools for the Profile Agent.

This module provides 8 intelligent tools that the ProfileManagementAgent
can use to analyze, update, and optimize candidate profiles.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from scoring.scoring_agent import ScoringAgent


class ProfileToolkit:
    """
    Toolkit providing 8 intelligent tools for profile management.

    Tools:
    1. extract_cv_structured_data - Parse CV into structured JSON
    2. update_profile_field - Update a specific profile field
    3. analyze_profile_gaps - Identify missing information
    4. suggest_skill_additions - Recommend complementary skills
    5. validate_experience_consistency - Check timeline coherence
    6. calculate_match_potential - Predict job matches
    7. optimize_profile_for_industry - Industry-specific suggestions
    8. generate_profile_summary - Create professional summary
    """

    def __init__(self, api_key: str = None, job_database: List[Dict] = None):
        """
        Initialize the toolkit.

        Args:
            api_key: Anthropic API key
            job_database: List of job offers for matching
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)
        self.job_database = job_database or []

        # Initialize advanced scoring agent (100-point system)
        self.scoring_agent = ScoringAgent(api_key=self.api_key)

    def extract_cv_structured_data(self, resume_text: str) -> str:
        """
        Extract structured data from CV using Claude AI.

        Args:
            resume_text: Raw CV text

        Returns:
            JSON string with structured profile data
        """
        prompt = f"""Analyze this CV and extract structured information. Return ONLY a JSON object with these fields:

{{
  "skills": ["skill1", "skill2", ...],
  "years_of_experience": <number>,
  "experience_entries": [
    {{"title": "...", "company": "...", "duration": "...", "achievements": ["..."]}},
    ...
  ],
  "education": [{{"degree": "...", "institution": "...", "year": "..."}}, ...],
  "location": "city/country or Remote",
  "salary_expectation": <number or null>,
  "industry": "target industry if mentioned",
  "certifications": ["cert1", "cert2", ...],
  "languages": ["lang1", "lang2", ...]
}}

CV:
{resume_text}

Return ONLY the JSON, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text.strip()

            # Validate JSON
            try:
                parsed = json.loads(result)
                # Store original resume text for advanced scoring
                parsed["resume_text"] = resume_text
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                return json.dumps({"error": "Could not parse CV", "raw": result[:200]})

        except Exception as e:
            return json.dumps({"error": str(e)})

    def update_profile_field(self, profile: Dict, field_value: str) -> str:
        """
        Update a specific profile field.

        Args:
            profile: Current profile dict
            field_value: String in format "field|value"

        Returns:
            Confirmation message with updated completeness score
        """
        if '|' not in field_value:
            return "Error: Input must be in format 'field|value'"

        field, value = field_value.split('|', 1)
        field = field.strip().lower()
        value = value.strip()

        # Field mapping
        field_map = {
            "skills": "skills",
            "skill": "skills",
            "experience": "years_of_experience",
            "years": "years_of_experience",
            "education": "education",
            "degree": "education",
            "location": "location",
            "salary": "salary_expectation",
            "industry": "industry",
            "certifications": "certifications",
            "languages": "languages"
        }

        if field not in field_map:
            return f"Unknown field: {field}. Valid fields: {', '.join(field_map.keys())}"

        actual_field = field_map[field]

        # Handle list fields
        if actual_field in ["skills", "certifications", "languages"]:
            if isinstance(value, str):
                value = [v.strip() for v in value.split(',')]
            if actual_field not in profile:
                profile[actual_field] = []
            profile[actual_field].extend(value)
            profile[actual_field] = list(set(profile[actual_field]))  # Remove duplicates
        else:
            profile[actual_field] = value

        # Calculate completeness
        completeness = self._calculate_completeness(profile)

        return json.dumps({
            "success": True,
            "field": actual_field,
            "value": value,
            "completeness": completeness,
            "message": f"Updated {actual_field} successfully. Profile is now {completeness}% complete."
        })

    def analyze_profile_gaps(self, profile: Dict) -> str:
        """
        Analyze profile to identify missing information and impact.

        Args:
            profile: Current profile dict

        Returns:
            JSON with gaps, priorities, and impact on matching
        """
        required_fields = {
            "skills": {"weight": 25, "description": "Technical and soft skills"},
            "years_of_experience": {"weight": 15, "description": "Years of professional experience"},
            "education": {"weight": 10, "description": "Educational background"},
            "location": {"weight": 15, "description": "Work location or remote preference"},
            "salary_expectation": {"weight": 10, "description": "Expected salary range"},
            "industry": {"weight": 20, "description": "Target industry"},
            "certifications": {"weight": 5, "description": "Professional certifications"}
        }

        gaps = []
        total_weight = 0
        missing_weight = 0

        for field, info in required_fields.items():
            total_weight += info["weight"]
            if field not in profile or not profile[field]:
                gaps.append({
                    "field": field,
                    "priority": info["weight"],
                    "description": info["description"],
                    "impact": f"Adding this could improve match score by ~{info['weight']}%"
                })
                missing_weight += info["weight"]

        # Sort by priority
        gaps.sort(key=lambda x: x["priority"], reverse=True)

        completeness = ((total_weight - missing_weight) / total_weight) * 100

        return json.dumps({
            "completeness_score": round(completeness, 1),
            "missing_fields": len(gaps),
            "gaps": gaps,
            "recommendation": gaps[0]["field"] if gaps else "Profile is complete!",
            "estimated_match_improvement": missing_weight
        }, indent=2)

    def suggest_skill_additions(self, profile: Dict, target_industry: str = None) -> str:
        """
        Suggest complementary skills based on current profile and target industry.

        Args:
            profile: Current profile dict
            target_industry: Target industry (optional)

        Returns:
            JSON with skill suggestions and justifications
        """
        current_skills = profile.get("skills", [])
        industry = target_industry or profile.get("industry", "tech")

        # Industry-specific skill recommendations
        skill_recommendations = {
            "fintech": ["Python", "SQL", "Risk Management", "Blockchain", "Financial Modeling", "Compliance"],
            "tech": ["Python", "JavaScript", "Docker", "Kubernetes", "CI/CD", "Agile", "Cloud (AWS/GCP)"],
            "health": ["HIPAA Compliance", "Healthcare IT", "Data Privacy", "Medical Terminology"],
            "gambling": ["Risk Analysis", "Statistics", "Python", "Real-time Systems", "Payment Processing"],
            "data": ["Python", "SQL", "Machine Learning", "Data Visualization", "Statistics", "Spark"]
        }

        industry_lower = industry.lower()
        recommended = skill_recommendations.get(industry_lower, skill_recommendations["tech"])

        # Find missing skills
        current_skills_lower = [s.lower() for s in current_skills]
        suggestions = []

        for skill in recommended:
            if skill.lower() not in current_skills_lower:
                suggestions.append({
                    "skill": skill,
                    "reason": f"Highly valued in {industry} industry",
                    "priority": "high" if skill in recommended[:3] else "medium"
                })

        return json.dumps({
            "current_skills_count": len(current_skills),
            "target_industry": industry,
            "suggestions": suggestions[:5],  # Top 5
            "message": f"Adding these skills could increase matches in {industry} by 15-30%"
        }, indent=2)

    def validate_experience_consistency(self, profile: Dict) -> str:
        """
        Validate experience timeline and progression coherence.

        Args:
            profile: Current profile dict

        Returns:
            JSON with validation results and suggestions
        """
        experience_entries = profile.get("experience_entries", [])
        years_claimed = profile.get("years_of_experience", 0)

        if not experience_entries:
            return json.dumps({
                "valid": False,
                "warnings": ["No experience entries found"],
                "suggestions": ["Add detailed work history with dates"]
            })

        warnings = []
        suggestions = []

        # Check if claimed years match entries
        total_duration = 0
        for entry in experience_entries:
            duration = entry.get("duration", "")
            # Try to extract years from duration
            years_match = re.search(r'(\d+)[\s]*(?:years?|ans?)', duration.lower())
            if years_match:
                total_duration += int(years_match.group(1))

        if total_duration > 0 and abs(total_duration - years_claimed) > 2:
            warnings.append(f"Claimed {years_claimed} years but entries show ~{total_duration} years")
            suggestions.append("Update years_of_experience to match work history")

        # Check for gaps
        if len(experience_entries) < years_claimed / 5:
            warnings.append("Few job entries for the claimed experience")
            suggestions.append("Add more detailed work history")

        # Check for career progression
        titles = [e.get("title", "").lower() for e in experience_entries]
        if titles:
            has_senior = any("senior" in t or "lead" in t or "principal" in t for t in titles)
            if years_claimed >= 8 and not has_senior:
                suggestions.append("Consider highlighting senior/lead roles if applicable")

        return json.dumps({
            "valid": len(warnings) == 0,
            "experience_entries_count": len(experience_entries),
            "claimed_years": years_claimed,
            "calculated_years": total_duration if total_duration > 0 else "unknown",
            "warnings": warnings,
            "suggestions": suggestions
        }, indent=2)

    def calculate_match_potential(self, profile: Dict) -> str:
        """
        Calculate how many jobs match the current profile using hybrid scoring.

        Uses a two-phase approach:
        1. Quick simple scoring (100 pts) on all jobs for filtering
        2. Advanced AI scoring (100 pts with semantic analysis) on top 3 matches

        Args:
            profile: Current profile dict

        Returns:
            JSON with match count and predictions
        """
        if not self.job_database:
            return json.dumps({
                "error": "No job database available",
                "matches": 0
            })

        skills = set(s.lower() for s in profile.get("skills", []))
        industry = profile.get("industry", "").lower()
        location = profile.get("location", "").lower()
        salary = profile.get("salary_expectation")
        resume_text = profile.get("resume_text", "")

        # Phase 1: Quick simple scoring on all jobs
        simple_matches = []
        for job in self.job_database:
            score = 0
            reasons = []

            # Industry match (30 points)
            if industry and job.get("industry", "").lower() == industry:
                score += 30
                reasons.append("Industry match")

            # Skills match (40 points)
            job_requirements = [r.lower() for r in job.get("requirements", [])]
            matched_skills = skills.intersection(set(job_requirements))
            if matched_skills:
                skill_score = min(40, (len(matched_skills) / len(job_requirements)) * 40 if job_requirements else 0)
                score += skill_score
                reasons.append(f"{len(matched_skills)} skills matched")

            # Location match (15 points)
            job_location = job.get("location", "").lower()
            if "remote" in location or "remote" in job_location:
                score += 15
                reasons.append("Remote compatible")
            elif location and location in job_location:
                score += 15
                reasons.append("Location match")

            # Salary match (15 points)
            if salary:
                job_salary = job.get("salary", 0)
                try:
                    salary_num = int(salary) if isinstance(salary, (int, float)) else int(re.sub(r'[^\d]', '', str(salary)))
                    if job_salary >= salary_num * 0.9:  # Within 10%
                        score += 15
                        reasons.append("Salary aligned")
                except:
                    pass

            if score >= 50:  # Threshold for "match"
                simple_matches.append({
                    "job": job,
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "score": round(score, 1),
                    "reasons": reasons,
                    "location": job.get("location", ""),
                    "salary": job.get("salary", 0)
                })

        # Sort by score
        simple_matches.sort(key=lambda x: x["score"], reverse=True)

        # Phase 2: Advanced AI scoring on top matches (if resume available)
        # If resume exists, use advanced scoring on ALL jobs (or top 5), not just simple matches
        advanced_matches = []
        jobs_to_score = []

        if resume_text:
            # If simple scoring found matches, use those. Otherwise, score ALL jobs.
            if len(simple_matches) > 0:
                jobs_to_score = [m["job"] for m in simple_matches[:5]]
                print(f"[ProfileToolkit] Running advanced AI scoring on top {len(jobs_to_score)} simple matches...")
            else:
                # No simple matches - use advanced scoring on ALL jobs!
                jobs_to_score = self.job_database[:5]  # Top 5 from database
                print(f"[ProfileToolkit] No simple matches found. Running advanced AI scoring on all {len(jobs_to_score)} jobs...")

            for i, job in enumerate(jobs_to_score):
                try:
                    print(f"  [{i+1}/{len(jobs_to_score)}] Scoring {job.get('title')} at {job.get('company')}...")

                    # Use advanced ScoringAgent
                    detailed_match, usage = self.scoring_agent.score_candidate(
                        resume_text=resume_text,
                        job_title=job.get("title", ""),
                        company=job.get("company", ""),
                        job_description=job.get("description", ""),
                        job_requirements=job.get("requirements", []),
                        job_location=job.get("location", ""),
                        job_salary=job.get("salary", 0),
                        candidate_location=profile.get("location"),
                        candidate_salary_expectation=salary,
                        industry=job.get("industry")
                    )

                    advanced_matches.append({
                        "job_title": job.get("title"),
                        "company": job.get("company"),
                        "score": round(detailed_match.match_score, 1),
                        "reasons": detailed_match.strengths[:3],  # Top 3 strengths
                        "location": job.get("location", ""),
                        "salary": job.get("salary", 0),
                        "recommendation": detailed_match.recommendation,
                        "breakdown": {
                            "deterministic": round(detailed_match.score_breakdown.deterministic.total, 1),
                            "semantic": round(detailed_match.score_breakdown.semantic.total, 1),
                            "bonus": round(detailed_match.score_breakdown.bonus.total, 1)
                        }
                    })
                    print(f"      Score: {detailed_match.match_score:.1f}/100")
                except Exception as e:
                    print(f"      Error: {str(e)}")
                    # Fallback to basic job info
                    advanced_matches.append({
                        "job_title": job.get("title", "Unknown"),
                        "company": job.get("company", "Unknown"),
                        "score": 0,
                        "reasons": ["Scoring failed"],
                        "location": job.get("location", ""),
                        "salary": job.get("salary", 0),
                        "error": f"Advanced scoring failed: {str(e)}"
                    })

        # Prepare final output
        final_matches = advanced_matches if advanced_matches else [
            {k: v for k, v in m.items() if k != "job"}
            for m in simple_matches[:5]
        ]

        # Filter out matches with score >= 50 for count
        valid_matches = [m for m in final_matches if m.get("score", 0) >= 50]
        matches_count = len(valid_matches) if valid_matches else len(final_matches)

        return json.dumps({
            "total_jobs_in_database": len(self.job_database),
            "matches_found": matches_count,
            "match_rate": round((matches_count / len(self.job_database)) * 100, 1) if self.job_database else 0,
            "top_matches": final_matches,
            "average_match_score": round(sum(m["score"] for m in final_matches) / len(final_matches), 1) if final_matches else 0,
            "message": f"Your profile matches {matches_count} out of {len(self.job_database)} jobs using {'advanced AI scoring' if advanced_matches else 'simple scoring'}",
            "scoring_type": "advanced" if advanced_matches else "simple"
        }, indent=2)

    def optimize_profile_for_industry(self, profile: Dict, target_industry: str) -> str:
        """
        Provide industry-specific optimization recommendations.

        Args:
            profile: Current profile dict
            target_industry: Target industry

        Returns:
            JSON with prioritized recommendations
        """
        recommendations = []

        # Check skills alignment
        skills_result = self.suggest_skill_additions(profile, target_industry)
        skills_data = json.loads(skills_result)

        if skills_data.get("suggestions"):
            recommendations.append({
                "priority": "HIGH",
                "category": "Skills",
                "action": f"Add {len(skills_data['suggestions'])} industry-relevant skills",
                "details": [s["skill"] for s in skills_data["suggestions"][:3]],
                "impact": "+20-30% match rate"
            })

        # Check completeness
        gaps_result = self.analyze_profile_gaps(profile)
        gaps_data = json.loads(gaps_result)

        if gaps_data["completeness_score"] < 80:
            top_gap = gaps_data["gaps"][0] if gaps_data["gaps"] else None
            if top_gap:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Completeness",
                    "action": f"Add {top_gap['field']}",
                    "details": [top_gap["description"]],
                    "impact": top_gap["impact"]
                })

        # Industry-specific advice
        industry_tips = {
            "fintech": "Highlight experience with financial systems, compliance, and security",
            "tech": "Emphasize cloud technologies, scalability, and modern development practices",
            "health": "Showcase data privacy awareness and healthcare domain knowledge",
            "gambling": "Focus on real-time systems, statistics, and responsible gaming awareness"
        }

        tip = industry_tips.get(target_industry.lower(), "Tailor your profile to highlight relevant experience")
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Industry Alignment",
            "action": "Update profile emphasis",
            "details": [tip],
            "impact": "+10-15% relevance"
        })

        return json.dumps({
            "target_industry": target_industry,
            "recommendations_count": len(recommendations),
            "recommendations": recommendations,
            "estimated_total_improvement": "+30-50% overall match quality"
        }, indent=2)

    def generate_profile_summary(self, profile: Dict) -> str:
        """
        Generate a professional summary based on profile data.

        Args:
            profile: Current profile dict

        Returns:
            Professional summary text
        """
        years = profile.get("years_of_experience", 0)
        skills = profile.get("skills", [])
        industry = profile.get("industry", "technology")
        education = profile.get("education", [])

        # Build summary using Claude
        prompt = f"""Generate a compelling professional summary (2-3 sentences) for a candidate with:
- {years} years of experience
- Skills: {', '.join(skills[:8])}
- Industry: {industry}
- Education: {education[0].get('degree', 'N/A') if education else 'N/A'}

Make it concise, impactful, and achievement-oriented. Return ONLY the summary text."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            return json.dumps({
                "summary": summary,
                "word_count": len(summary.split()),
                "character_count": len(summary)
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "summary": f"Experienced {industry} professional with {years} years of expertise in {', '.join(skills[:3])}."
            })

    def _calculate_completeness(self, profile: Dict) -> int:
        """Calculate profile completeness percentage."""
        fields = ["skills", "years_of_experience", "education", "location",
                  "salary_expectation", "industry", "certifications"]
        filled = sum(1 for f in fields if profile.get(f))
        return round((filled / len(fields)) * 100)
