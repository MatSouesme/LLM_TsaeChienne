"""
Deterministic scoring tool for resume-job matching.

This tool calculates objective, rule-based scores based on:
- Skills matching (15 points)
- Experience years (10 points)
- Education level (5 points)
- Salary fit (5 points)
- Location match (5 points)

Total: 40 points
"""

import os
import re
from typing import Dict, List, Any, Tuple, Optional
from .models import DeterministicScore, ScoreDetail


class DeterministicScoringTool:
    """Tool for calculating deterministic scores based on objective criteria."""

    # Common technical skills to look for
    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "react", "vue", "angular", "node.js", "django", "flask", "fastapi",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
        "git", "ci/cd", "jenkins", "github actions", "gitlab",
        "machine learning", "deep learning", "nlp", "computer vision",
        "data science", "data engineering", "etl", "spark", "hadoop",
        "agile", "scrum", "rest api", "graphql", "microservices"
    }

    def __init__(self, api_key: str = None, use_semantic_experience: bool = True):
        """
        Initialize the deterministic scoring tool.

        Args:
            api_key: Optional Anthropic API key for semantic experience evaluation
            use_semantic_experience: If True, use AI to evaluate experience relevance
        """
        self.use_semantic_experience = use_semantic_experience
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.use_semantic_experience and self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                self.model = "claude-3-haiku-20240307"
            except Exception as e:
                print(f"Warning: Could not initialize Claude client: {e}")
                self.use_semantic_experience = False

    def score_resume_job_match(
        self,
        resume_text: str,
        job_requirements: List[str],
        job_description: str,
        job_location: str,
        job_salary: int,
        candidate_location: str = None,
        candidate_salary_expectation: int = None,
        job_title: str = ""
    ) -> DeterministicScore:
        """
        Calculate deterministic scores for a resume-job match.

        Args:
            resume_text: Full text of the resume
            job_requirements: List of required skills/qualifications
            job_description: Full job description
            job_location: Job location
            job_salary: Job salary
            candidate_location: Candidate's preferred location
            candidate_salary_expectation: Candidate's salary expectation
            job_title: Job title (used for semantic experience relevance)

        Returns:
            DeterministicScore with all components calculated
        """
        # Calculate each component
        skills_score = self._score_skills_matching(resume_text, job_requirements, job_description)
        experience_score = self._score_experience_years(resume_text, job_description, job_title)
        education_score = self._score_education_match(resume_text, job_requirements, job_description)
        salary_score = self._score_salary_fit(job_salary, candidate_salary_expectation)
        location_score = self._score_location_match(job_location, candidate_location)

        return DeterministicScore(
            skills_matching=skills_score,
            experience_years=experience_score,
            education_match=education_score,
            salary_fit=salary_score,
            location_match=location_score
        )

    def _smart_skill_match(self, skill_requirement: str, resume_text: str) -> bool:
        """
        Intelligent skill matching that handles variations and partial matches.

        Examples:
        - "Permis C" matches "Permis B, C, CE" ✓
        - "FIMO" matches "FIMO / FCO" ✓
        - "Docker" matches "Dockerization" ✓
        """
        skill_lower = skill_requirement.lower()
        resume_lower = resume_text.lower()

        # Direct match
        if skill_lower in resume_lower:
            return True

        # Extract key words from skill (ignore common words)
        stop_words = {'a', 'an', 'the', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'de', 'des', 'et', 'ou', 'à'}
        skill_words = [w for w in re.findall(r'\b\w+\b', skill_lower) if w not in stop_words]

        # Check if all key words are present
        if all(word in resume_lower for word in skill_words):
            return True

        # Special handling for certifications/licenses (e.g., "Permis C")
        # Look for patterns like "Permis B, C, CE" where C is standalone
        if 'permis' in skill_lower or 'license' in skill_lower:
            # Extract the letter/type (e.g., "C" from "Permis C")
            cert_type = re.search(r'\b([A-Z]+\d*)\b', skill_requirement)
            if cert_type:
                cert = cert_type.group(1)
                # Look for this cert in resume (as word boundary or in list)
                patterns = [
                    rf'\b{cert}\b',  # Standalone
                    rf',\s*{cert}\b',  # In comma-separated list
                    rf'\b{cert}\s*,',  # In comma-separated list
                    rf'/\s*{cert}\b',  # In slash-separated list
                ]
                for pattern in patterns:
                    if re.search(pattern, resume_text, re.IGNORECASE):
                        return True

        # Handle acronyms (e.g., "CI/CD" vs "CI / CD" vs "CI-CD")
        skill_clean = re.sub(r'[/\-\s]+', '', skill_lower)
        resume_clean = re.sub(r'[/\-\s]+', '', resume_lower)
        if len(skill_clean) <= 10 and skill_clean in resume_clean:
            return True

        return False

    # Soft skill keywords for semantic evaluation
    SOFT_SKILL_KEYWORDS = {
        'ponctualite', 'punctuality', 'autonomie', 'autonomous', 'autonomy',
        'leadership', 'lead', 'communication', 'communicat',
        'esprit', 'equipe', 'team', 'teamwork', 'collaboration',
        'rigueur', 'rigor', 'rigorous', 'organisation', 'organiz',
        'adaptabilite', 'adaptability', 'flexible', 'flexibility',
        'proactivite', 'proactive', 'motivation', 'motivated',
        'relationnel', 'interpersonal', 'creativity', 'creative',
        'problem solving', 'critical thinking', 'initiative'
    }

    def _evaluate_soft_skills_semantic(
        self,
        resume_text: str,
        soft_skills: List[str],
        job_description: str
    ) -> List[str]:
        """
        Evaluate soft skills using semantic analysis with Claude.

        Args:
            resume_text: Candidate's resume
            soft_skills: List of soft skills to evaluate
            job_description: Job description for context

        Returns:
            List of soft skills that the candidate demonstrates
        """
        if not self.client or not soft_skills:
            return []

        skills_str = ", ".join(soft_skills)

        prompt = f"""Analyze whether the candidate demonstrates the following soft skills/qualities based on their resume.

SOFT SKILLS TO EVALUATE:
{skills_str}

JOB CONTEXT:
{job_description}

CANDIDATE RESUME:
{resume_text}

INSTRUCTIONS:
For each soft skill, determine if the candidate's resume DEMONSTRATES this quality, either:
1. Explicitly mentioned (e.g., "Punctual", "Autonomous")
2. Implicitly demonstrated (e.g., "Managed team of 5" shows Leadership)
3. Evidenced by achievements (e.g., "Delivered projects on time" shows Punctuality)

Be reasonable but not overly generous. Look for concrete evidence.

Examples:
- "Ponctualite" / "Punctuality": Look for "on-time delivery", "respect des delais", "punctual"
- "Autonomie" / "Autonomy": Look for "independent work", "self-managed", "autonome"
- "Leadership": Look for "managed", "led", "coordinated", "team lead"

Provide your evaluation in this EXACT format:
MATCHED: [skill1, skill2, skill3]

If no soft skills are demonstrated, respond:
MATCHED: []

Example response:
MATCHED: [Autonomie, Leadership]
"""

        try:
            response = self._call_claude(prompt, max_tokens=256)

            # Parse response
            matched = []
            for line in response.strip().split('\n'):
                if line.startswith('MATCHED:'):
                    matched_str = line.replace('MATCHED:', '').strip()
                    # Handle [] or [skill1, skill2]
                    matched_str = matched_str.strip('[]')
                    if matched_str:
                        matched = [s.strip() for s in matched_str.split(',')]
                    break

            return [s for s in matched if s]  # Filter empty strings

        except Exception as e:
            print(f"Error in semantic soft skills evaluation: {e}")
            return []

    def _score_skills_matching(
        self,
        resume_text: str,
        job_requirements: List[str],
        job_description: str
    ) -> ScoreDetail:
        """
        Score skills matching (15 points max).

        Separates hard skills (deterministic matching) from soft skills (semantic evaluation).
        Uses AI to evaluate soft skills for better accuracy.
        """
        resume_lower = resume_text.lower()
        job_desc_lower = job_description.lower()

        # STEP 1: Separate hard skills from soft skills
        hard_skills = []
        soft_skills = []

        for req in job_requirements:
            req_lower = req.lower()
            # Check if this is a soft skill
            is_soft_skill = any(keyword in req_lower for keyword in self.SOFT_SKILL_KEYWORDS)

            if is_soft_skill:
                soft_skills.append(req)
            else:
                hard_skills.append(req)

        # Also extract technical skills from job description
        tech_skills_in_desc = set()
        for skill in self.TECH_SKILLS:
            if skill in job_desc_lower:
                tech_skills_in_desc.add(skill)

        # Combine with explicit hard skills from requirements
        all_hard_skills = set(s.lower().strip() for s in hard_skills)
        all_hard_skills.update(tech_skills_in_desc)

        # If no hard skills found, add requirements as hard skills
        if not all_hard_skills:
            all_hard_skills = set(req.lower().strip() for req in job_requirements if req not in soft_skills)

        # If still empty, use defaults
        if not all_hard_skills and not soft_skills:
            all_hard_skills = {"programming", "development", "engineering"}

        # STEP 2: Match hard skills (deterministic)
        matched_hard = []
        missing_hard = []

        for skill in all_hard_skills:
            if self._smart_skill_match(skill, resume_text):
                matched_hard.append(skill)
            else:
                missing_hard.append(skill)

        # STEP 3: Match soft skills (semantic with Claude if available)
        matched_soft = []
        missing_soft = []

        if soft_skills:
            if self.client and self.use_semantic_experience:
                try:
                    matched_soft = self._evaluate_soft_skills_semantic(
                        resume_text, soft_skills, job_description
                    )
                    missing_soft = [s for s in soft_skills if s not in matched_soft]
                except Exception as e:
                    print(f"Soft skills semantic evaluation failed, using deterministic fallback: {e}")
                    # Fallback to deterministic matching
                    for skill in soft_skills:
                        if self._smart_skill_match(skill, resume_text):
                            matched_soft.append(skill)
                        else:
                            missing_soft.append(skill)
            else:
                # No Claude available, use deterministic
                for skill in soft_skills:
                    if self._smart_skill_match(skill, resume_text):
                        matched_soft.append(skill)
                    else:
                        missing_soft.append(skill)

        # STEP 4: Calculate combined score
        total_required = len(all_hard_skills) + len(soft_skills)
        total_matched = len(matched_hard) + len(matched_soft)

        if total_required > 0:
            match_ratio = total_matched / total_required
            score = match_ratio * 15

            # Bonus for additional technical skills
            bonus_skills = []
            for skill in self.TECH_SKILLS:
                if skill in resume_lower and skill not in all_hard_skills:
                    bonus_skills.append(skill)

            # Add up to 2 bonus points for additional skills
            bonus = min(2, len(bonus_skills) * 0.2)
            score = min(15, score + bonus)
        else:
            score = 10.0  # Default
            match_ratio = 0.67

        # Build explanation
        all_matched = matched_hard + matched_soft
        all_missing = missing_hard + missing_soft

        explanation = f"{total_matched}/{total_required} competences requises maitrisees"
        if all_matched:
            explanation += f". Matchees: {', '.join(all_matched[:5])}"
        if all_missing:
            explanation += f". Manquantes: {', '.join(all_missing[:3])}"

        return ScoreDetail(
            score=score,
            max_score=15.0,
            explanation=explanation,
            metadata={
                "matched_skills": all_matched[:10],
                "missing_skills": all_missing[:10],
                "match_ratio": round(match_ratio, 2),
                "hard_skills_matched": len(matched_hard),
                "soft_skills_matched": len(matched_soft),
                "semantic_soft_skills": bool(self.client and soft_skills)
            }
        )

    def _extract_experience_from_dates(self, resume_text: str) -> int:
        """
        Extract years of experience by parsing date ranges in the resume.

        Handles patterns like:
        - "2015-2024" or "2015 - 2024"
        - "2015 à 2024" or "2015 to 2024"
        - "Depuis 2015" or "Since 2015"
        - "2015 à aujourd'hui" or "2015 to present"

        Returns total years of experience (sum of all periods).
        """
        from datetime import datetime
        current_year = datetime.now().year

        # Pattern 1: Date ranges "2015-2024", "2015 à 2024", "2015 to 2024"
        date_range_patterns = [
            r'(\d{4})\s*[-–—]\s*(\d{4})',  # 2015-2024
            r'(\d{4})\s+(?:à|a|to)\s+(\d{4})',  # 2015 à 2024
        ]

        # Pattern 2: "Depuis/Since 2015", "2015 à aujourd'hui", "2015 to present"
        ongoing_patterns = [
            r'(?:[Dd]epuis|[Ss]ince)\s+(\d{4})',  # Depuis 2015
            r'(\d{4})\s+(?:à|a|to)\s+(?:aujourd\'?hui|present|now|maintenant)',  # 2015 à aujourd'hui
        ]

        total_years = 0
        found_dates = set()  # Avoid counting overlapping periods

        # Extract date ranges
        for pattern in date_range_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                start_year = int(match[0])
                end_year = int(match[1])

                # Sanity checks
                if 1950 <= start_year <= current_year and start_year <= end_year <= current_year + 1:
                    years = end_year - start_year
                    if (start_year, end_year) not in found_dates:
                        total_years += years
                        found_dates.add((start_year, end_year))

        # Extract ongoing periods
        for pattern in ongoing_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            for match in matches:
                start_year = int(match) if isinstance(match, str) else int(match[0])

                # Sanity check
                if 1950 <= start_year <= current_year:
                    years = current_year - start_year
                    # Check if not already counted
                    if not any(start_year == s for s, e in found_dates):
                        total_years += years
                        found_dates.add((start_year, current_year))

        return total_years

    def _call_claude(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Call Claude API with a prompt.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in the response

        Returns:
            Claude's response text
        """
        if not self.client:
            raise ValueError("Claude client not initialized. Cannot call semantic methods.")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            raise

    def _extract_relevant_experience_years(
        self,
        resume_text: str,
        job_title: str,
        job_description: str
    ) -> Tuple[int, str]:
        """
        Extract years of RELEVANT experience for the target job using AI.

        This method uses Claude to analyze the candidate's work history and determine
        how many years of directly applicable experience they have for the specific job.

        Args:
            resume_text: Full text of the candidate's resume
            job_title: Title of the job position
            job_description: Full job description

        Returns:
            Tuple of (relevant_years, explanation)
        """
        if not self.client or not self.use_semantic_experience:
            # Fallback to total years if semantic evaluation unavailable
            return self._extract_experience_from_dates(resume_text), "Total experience (semantic evaluation unavailable)"

        prompt = f"""Analyze the candidate's work experience and determine how many years of RELEVANT, DIRECTLY APPLICABLE experience they have for this specific job.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

CRITICAL INSTRUCTIONS:
1. Only count experience that is DIRECTLY relevant and applicable to the target job
2. Consider domain/industry alignment, technical skills relevance, and functional area match
3. Examples:
   - 12 years as truck driver for "Truck Driver" job = 12 relevant years
   - 12 years as truck driver for "Software Developer" job = 0 relevant years (completely different field)
   - 3 years as Data Scientist for "Truck Driver" job = 0 relevant years (no driving experience)
   - 5 years in team management + 3 years as developer for "Engineering Manager" = 5-6 relevant years (partial)
   - 2 years Python dev + 3 years Java dev for "Python Developer" = 5 relevant years (all programming)

4. Transferable skills count partially:
   - Leadership roles can transfer across industries (50-75% credit)
   - Technical skills in similar domains (75-100% credit)
   - Completely different domains = 0% credit

Evaluate carefully:
- Job titles and responsibilities
- Domain/industry alignment
- Technical skills overlap
- Functional area match (engineering vs sales vs operations, etc.)

Provide:
1. Number of relevant years (0 to 50, can be decimal like 2.5)
2. Brief explanation (2-3 sentences max) justifying the count

Format your response EXACTLY as:
RELEVANT_YEARS: [number]
EXPLANATION: [your explanation]

Example responses:
RELEVANT_YEARS: 0
EXPLANATION: The candidate has 12 years of experience as a truck driver, but the target job is Software Developer. These are completely different fields with no transferable skills.

RELEVANT_YEARS: 8
EXPLANATION: The candidate has 10 years as a Data Scientist, directly applicable to the Data Scientist role. All experience is highly relevant.
"""

        try:
            response = self._call_claude(prompt, max_tokens=512)

            # Parse response
            relevant_years = 0
            explanation = "Could not parse Claude response"

            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith('RELEVANT_YEARS:'):
                    years_text = line.replace('RELEVANT_YEARS:', '').strip()
                    try:
                        relevant_years = int(float(years_text))  # Convert to int after parsing float
                        relevant_years = max(0, min(relevant_years, 50))  # Clamp to 0-50
                    except ValueError:
                        print(f"Warning: Could not parse years from: {years_text}")
                elif line.startswith('EXPLANATION:'):
                    explanation = line.replace('EXPLANATION:', '').strip()

            # If we couldn't parse anything useful, fallback
            if relevant_years == 0 and "Could not parse" in explanation:
                print(f"Warning: Failed to parse Claude response. Falling back to total years.")
                print(f"Response was: {response[:200]}")
                total_years = self._extract_experience_from_dates(resume_text)
                return total_years, f"Fallback: {total_years} years total experience"

            return relevant_years, explanation

        except Exception as e:
            print(f"Error in semantic experience evaluation: {e}")
            # Fallback to total years
            total_years = self._extract_experience_from_dates(resume_text)
            return total_years, f"Fallback due to error: {total_years} years total experience"

    def _score_experience_years(self, resume_text: str, job_description: str, job_title: str = "") -> ScoreDetail:
        """
        Score years of experience (10 points max).

        Uses AI to extract RELEVANT years of experience for the specific job,
        ensuring that experience in different fields doesn't inflate the score.

        Args:
            resume_text: Candidate's resume
            job_description: Job description
            job_title: Job title (required for semantic relevance evaluation)
        """
        resume_lower = resume_text.lower()
        job_desc_lower = job_description.lower()

        # SEMANTIC EVALUATION: Extract relevant years using AI (if available and job_title provided)
        if self.use_semantic_experience and self.client and job_title:
            try:
                resume_years, semantic_explanation = self._extract_relevant_experience_years(
                    resume_text, job_title, job_description
                )
                using_semantic = True
            except Exception as e:
                print(f"Semantic experience extraction failed, using fallback: {e}")
                resume_years = self._extract_experience_from_dates(resume_text)
                semantic_explanation = None
                using_semantic = False
        else:
            # FALLBACK: Extract total years from dates
            resume_years = self._extract_experience_from_dates(resume_text)
            semantic_explanation = None
            using_semantic = False

            # If still no dates found, try text patterns
            if resume_years == 0:
                years_patterns = [
                    r'(\d+)\+?\s*(?:years?|ans?)\s+(?:of\s+)?(?:experience|expérience)',
                    r'(?:experience|expérience)\s*:?\s*(\d+)\+?\s*(?:years?|ans?)',
                    r'(\d+)\+?\s*(?:years?|ans?)\s+(?:in|dans|en)',
                ]

                for pattern in years_patterns:
                    match = re.search(pattern, resume_lower)
                    if match:
                        resume_years = max(resume_years, int(match.group(1)))

        # Try to extract required years from job description
        required_years_patterns = [
            r'(\d+)\+?\s*(?:years?|ans?)\s+(?:of\s+)?(?:experience|expérience)',
            r'minimum\s+(?:of\s+)?(\d+)\s*(?:years?|ans?)',
            r'at least\s+(\d+)\s*(?:years?|ans?)',
        ]

        required_years = 0
        for pattern in required_years_patterns:
            match = re.search(pattern, job_desc_lower)
            if match:
                required_years = max(required_years, int(match.group(1)))

        # Heuristic: if no years found, infer from job title
        if required_years == 0:
            if "senior" in job_desc_lower or "lead" in job_desc_lower:
                required_years = 5
            elif "junior" in job_desc_lower or "graduate" in job_desc_lower:
                required_years = 1
            else:
                required_years = 3

        # Calculate score based on experience match
        if resume_years >= required_years:
            # More experience is generally better - be lenient with "overqualification"
            if resume_years <= required_years + 5:
                score = 10.0  # Perfect match
                base_explanation = f"{resume_years} ans d'experience pertinente, excellent profil"
            elif resume_years <= required_years + 10:
                score = 9.0  # Very experienced - still excellent
                base_explanation = f"{resume_years} ans d'experience pertinente, tres experimente"
            elif resume_years <= required_years + 15:
                score = 8.0  # Possibly overqualified but still good
                base_explanation = f"{resume_years} ans d'experience pertinente, tres senior"
            else:
                score = 7.0  # Significantly overqualified
                base_explanation = f"{resume_years} ans d'experience pertinente, profil tres senior"
        else:
            # Under qualified
            gap = required_years - resume_years
            score = max(0, 10 - (gap * 2))
            base_explanation = f"{resume_years} ans d'experience pertinente, {required_years} requis"

        # Use semantic explanation if available, otherwise use base explanation
        if semantic_explanation and using_semantic:
            explanation = semantic_explanation
        else:
            explanation = base_explanation

        return ScoreDetail(
            score=score,
            max_score=10.0,
            explanation=explanation,
            metadata={
                "resume_years": resume_years,
                "required_years": required_years,
                "semantic_evaluation": using_semantic
            }
        )

    def _score_education_match(
        self,
        resume_text: str,
        job_requirements: List[str],
        job_description: str
    ) -> ScoreDetail:
        """
        Score education level match (5 points max).

        Checks if candidate's education matches job requirements.
        """
        resume_lower = resume_text.lower()
        job_text = (job_description + " " + " ".join(job_requirements)).lower()

        # Education levels and their scores
        education_levels = {
            "phd": 5,
            "doctorate": 5,
            "doctorat": 5,
            "master": 4,
            "msc": 4,
            "mba": 4,
            "bachelor": 3,
            "licence": 3,
            "degree": 3,
            "diploma": 2,
            "diplôme": 2,
        }

        # Find candidate's education level
        candidate_level = 0
        candidate_degree = "Non spécifié"
        for degree, score in education_levels.items():
            if degree in resume_lower:
                if score > candidate_level:
                    candidate_level = score
                    candidate_degree = degree.capitalize()

        # Find required education level
        required_level = 0
        required_degree = "Non spécifié"
        for degree, score in education_levels.items():
            if degree in job_text and ("required" in job_text or "requis" in job_text or "minimum" in job_text):
                if score > required_level:
                    required_level = score
                    required_degree = degree.capitalize()

        # Default to Bachelor if not specified
        if required_level == 0:
            required_level = 3
            required_degree = "Bachelor (par défaut)"

        # Calculate score
        if candidate_level >= required_level:
            score = 5.0
            explanation = f"{candidate_degree} correspond aux attentes ({required_degree})"
        elif candidate_level >= required_level - 1:
            score = 3.0
            explanation = f"{candidate_degree} légèrement en dessous de {required_degree}"
        else:
            score = 1.0
            explanation = f"{candidate_degree} en dessous de {required_degree}"

        return ScoreDetail(
            score=score,
            max_score=5.0,
            explanation=explanation,
            metadata={
                "candidate_level": candidate_level,
                "required_level": required_level
            }
        )

    def _score_salary_fit(
        self,
        job_salary: int,
        candidate_salary_expectation: int = None
    ) -> ScoreDetail:
        """
        Score salary fit (5 points max).

        Compares job salary with candidate expectations.
        """
        if candidate_salary_expectation is None or candidate_salary_expectation == 0:
            # No expectation specified, assume it's acceptable
            return ScoreDetail(
                score=5.0,
                max_score=5.0,
                explanation="Salaire non spécifié, assumé acceptable",
                metadata={"job_salary": job_salary}
            )

        # Calculate percentage difference
        diff_percent = ((job_salary - candidate_salary_expectation) / candidate_salary_expectation) * 100

        if diff_percent >= 10:
            score = 5.0
            explanation = f"Salaire offert supérieur aux attentes (+{diff_percent:.0f}%)"
        elif diff_percent >= 0:
            score = 5.0
            explanation = f"Salaire offert correspond aux attentes (±{abs(diff_percent):.0f}%)"
        elif diff_percent >= -10:
            score = 4.0
            explanation = f"Salaire légèrement en dessous des attentes ({diff_percent:.0f}%)"
        elif diff_percent >= -20:
            score = 2.0
            explanation = f"Salaire en dessous des attentes ({diff_percent:.0f}%)"
        else:
            score = 0.0
            explanation = f"Salaire très en dessous des attentes ({diff_percent:.0f}%)"

        return ScoreDetail(
            score=score,
            max_score=5.0,
            explanation=explanation,
            metadata={
                "job_salary": job_salary,
                "candidate_expectation": candidate_salary_expectation,
                "diff_percent": round(diff_percent, 2)
            }
        )

    def _score_location_match(
        self,
        job_location: str,
        candidate_location: str = None
    ) -> ScoreDetail:
        """
        Score location match (5 points max).

        Compares job location with candidate preferences.
        """
        if not candidate_location:
            # No preference specified
            return ScoreDetail(
                score=3.0,
                max_score=5.0,
                explanation="Localisation non spécifiée",
                metadata={"job_location": job_location}
            )

        job_loc_lower = job_location.lower()
        candidate_loc_lower = candidate_location.lower()

        # Check for remote
        if "remote" in job_loc_lower or "télétravail" in job_loc_lower:
            score = 5.0
            explanation = "Poste en remote, flexible"
        elif "remote" in candidate_loc_lower and "remote" not in job_loc_lower:
            score = 1.0
            explanation = "Candidat recherche remote, poste sur site"
        elif candidate_loc_lower in job_loc_lower or job_loc_lower in candidate_loc_lower:
            score = 5.0
            explanation = "Localisation parfaitement alignée"
        else:
            # Check for country match
            countries = ["france", "paris", "lyon", "marseille", "toulouse", "bordeaux"]
            candidate_country = None
            job_country = None

            for country in countries:
                if country in candidate_loc_lower:
                    candidate_country = country
                if country in job_loc_lower:
                    job_country = country

            if candidate_country and job_country and candidate_country == job_country:
                score = 3.0
                explanation = "Même région mais pas même ville"
            else:
                score = 1.0
                explanation = "Localisations différentes"

        return ScoreDetail(
            score=score,
            max_score=5.0,
            explanation=explanation,
            metadata={
                "job_location": job_location,
                "candidate_location": candidate_location or "Non spécifié"
            }
        )
