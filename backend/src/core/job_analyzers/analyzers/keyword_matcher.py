from typing import List, Dict, Set
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor, ProcessedText


class KeywordMatcher(BaseAnalyzer):
    def __init__(self):
        self.preprocessor = TextPreprocessor()

    def _calculate_weighted_match(
        self, cv_keywords: Set[str], job_keywords: Set[str], job_skills: Set[str]
    ) -> Dict:
        """Calculate weighted keyword match score."""
        # Give higher weight to skill matches
        skill_matches = cv_keywords.intersection(job_skills)
        keyword_matches = cv_keywords.intersection(job_keywords)

        # Calculate scores
        skill_score = len(skill_matches) / len(job_skills) if job_skills else 0
        keyword_score = len(keyword_matches) / len(job_keywords) if job_keywords else 0

        # Weighted average (skills are weighted higher)
        final_score = skill_score * 0.7 + keyword_score * 0.3

        return {
            "skill_matches": list(skill_matches),
            "keyword_matches": list(keyword_matches),
            "skill_score": skill_score,
            "keyword_score": keyword_score,
            "missing_skills": list(job_skills - cv_keywords),
        }

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze keyword matches between CV and job description."""
        # Process both texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Extract skills specifically from job description
        job_skills = self.preprocessor.get_skills_and_requirements(job_text)

        # Calculate matches
        match_details = self._calculate_weighted_match(
            cv_processed.keywords, job_processed.keywords, job_skills
        )

        # Generate improvement suggestions
        suggestions = []
        if match_details["missing_skills"]:
            suggestions.append(
                f"Consider adding these missing skills: {', '.join(match_details['missing_skills'])}"
            )

        return AnalysisResult(
            score=match_details["skill_score"] * 0.7
            + match_details["keyword_score"] * 0.3,
            details={
                "matched_skills": match_details["skill_matches"],
                "matched_keywords": match_details["keyword_matches"],
                "missing_skills": match_details["missing_skills"],
                "skill_score": match_details["skill_score"],
                "keyword_score": match_details["keyword_score"],
                "suggestions": suggestions,
            },
            matched_items=match_details["skill_matches"]
            + match_details["keyword_matches"],
        )
