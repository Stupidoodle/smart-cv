from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from datetime import datetime

from .analyzers.keyword_matcher import KeywordMatcher
from .analyzers.bert_similarity import BERTSimilarityAnalyzer
from .analyzers.cosine_similarity import CosineSimilarityAnalyzer
from .analyzers.jaccard_similarity import JaccardSimilarityAnalyzer
from .analyzers.ner_similarity import NERSimilarityAnalyzer
from .analyzers.lsa_similarity import LSAAnalyzer

from .base import BaseAnalyzer
from ...db.service import DatabaseService
from ...db.models import CV, JobPosting, Analysis, Skill


class IntegratedAnalysisPipeline:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        # Initialize analyzers with weights
        self.analyzers = {
            "keyword": (KeywordMatcher(), 0.2),
            "bert": (BERTSimilarityAnalyzer(), 0.2),
            "cosine": (CosineSimilarityAnalyzer(), 0.15),
            "jaccard": (JaccardSimilarityAnalyzer(), 0.15),
            "ner": (NERSimilarityAnalyzer(), 0.2),
            "lsa": (LSAAnalyzer(), 0.1),
        }

    async def _store_identified_skills(
        self, cv_id: str, job_id: str, skills: List[str]
    ) -> List[Skill]:
        """Store identified skills in the database."""
        stored_skills = []
        for skill_name in skills:
            # Attempt to categorize skill (you might want to enhance this)
            category = (
                "technical"
                if any(
                    tech in skill_name.lower()
                    for tech in ["python", "java", "sql", "aws"]
                )
                else "soft"
            )

            skill = await self.db.get_or_create_skill(skill_name, category)
            stored_skills.append(skill)
        return stored_skills

    async def _store_analysis_result(
        self, cv_id: str, job_id: str, results: Dict[str, Any]
    ) -> Analysis:
        """Store analysis results in the database."""
        return await self.db.create_analysis(cv_id, job_id, results)

    async def _extract_skills_from_results(self, results: Dict[str, Any]) -> List[str]:
        """Extract all identified skills from analysis results."""
        skills = set()

        # Extract from matched items
        skills.update(results["overall_analysis"]["matched_items"])

        # Extract from missing items
        skills.update(results["overall_analysis"]["missing_items"])

        # Extract from detailed analysis
        for analyzer_results in results["detailed_analysis"].values():
            if "matched_skills" in analyzer_results.get("analysis", {}):
                skills.update(analyzer_results["analysis"]["matched_skills"])
            if "missing_skills" in analyzer_results.get("analysis", {}):
                skills.update(analyzer_results["analysis"]["missing_skills"])

        return list(skills)

    def _run_analyzer(
        self, name: str, analyzer: BaseAnalyzer, cv_text: str, job_text: str
    ) -> Dict[str, Any]:
        """Run a single analyzer and handle any errors."""
        try:
            result = analyzer.analyze(cv_text, job_text)
            return {"name": name, "success": True, "result": result}
        except Exception as e:
            return {"name": name, "success": False, "error": str(e)}

    def _aggregate_scores(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate scores from different analyzers."""
        successful_results = [
            (name, result["result"], weight)
            for name, result, weight in [
                (r["name"], r["result"], self.analyzers[r["name"]][1])
                for r in results
                if r["success"]
            ]
        ]

        if not successful_results:
            return {"total_score": 0.0, "error": "No analyzers completed successfully"}

        # Calculate weighted average score
        total_weight = sum(weight for _, _, weight in successful_results)
        total_score = sum(
            result.score * weight / total_weight
            for _, result, weight in successful_results
        )

        # Aggregate matched items and suggestions
        all_matched_items = set()
        all_suggestions = []
        all_missing_items = set()

        for _, result, _ in successful_results:
            all_matched_items.update(result.matched_items)
            all_suggestions.extend(result.details.get("suggestions", []))

            # Collect missing items from different analyzers
            missing_items = []
            for key in [
                "missing_skills",
                "missing_terms",
                "missing_entities",
                "missing_topics",
            ]:
                if key in result.details:
                    missing_items.extend(result.details[key])
            all_missing_items.update(missing_items)

        return {
            "total_score": float(total_score),
            "match_percentage": float(total_score * 100),
            "overall_analysis": {
                "matched_items": list(all_matched_items),
                "missing_items": list(all_missing_items),
                "suggestions": self._categorize_suggestions(all_suggestions),
            },
            "detailed_analysis": {
                name: {"score": result.score, "analysis": result.details}
                for name, result, _ in successful_results
            },
        }

    def _categorize_suggestions(self, suggestions: List[str]) -> Dict[str, List[str]]:
        """Categorize improvement suggestions by type."""
        categorized = {
            "skills": [],
            "content": [],
            "format": [],
            "keywords": [],
            "other": [],
        }

        for suggestion in suggestions:
            if any(
                keyword in suggestion.lower()
                for keyword in ["skill", "technology", "tool"]
            ):
                categorized["skills"].append(suggestion)
            elif any(
                keyword in suggestion.lower()
                for keyword in ["add", "expand", "include"]
            ):
                categorized["content"].append(suggestion)
            elif any(
                keyword in suggestion.lower()
                for keyword in ["format", "structure", "organize"]
            ):
                categorized["format"].append(suggestion)
            elif any(
                keyword in suggestion.lower()
                for keyword in ["keyword", "term", "phrase"]
            ):
                categorized["keywords"].append(suggestion)
            else:
                categorized["other"].append(suggestion)

        return {k: list(set(v)) for k, v in categorized.items() if v}

    async def analyze(self, cv_id: str, job_id: str) -> Dict[str, Any]:
        """Run analysis pipeline and store results in database."""
        # Get CV and Job content from database
        async with self.db.get_db() as session:
            cv = await session.get(CV, cv_id)
            job = await session.get(JobPosting, job_id)

            if not cv or not job:
                raise ValueError("CV or Job posting not found")

            cv_text = cv.content
            job_text = job.content

        # Run analyzers in parallel
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._run_analyzer, name, analyzer, cv_text, job_text)
                for name, (analyzer, _) in self.analyzers.items()
            ]
            results = [future.result() for future in futures]

        # Aggregate results
        aggregated_results = self._aggregate_scores(results)

        # Extract and store identified skills
        skills = await self._extract_skills_from_results(aggregated_results)
        await self._store_identified_skills(cv_id, job_id, skills)

        # Store analysis results
        analysis = await self._store_analysis_result(cv_id, job_id, aggregated_results)

        # Add metadata
        aggregated_results["metadata"] = {
            "analysis_id": analysis.id,
            "timestamp": datetime.utcnow().isoformat(),
            "analyzers_used": [name for name, _ in self.analyzers.items()],
            "analyzer_weights": {
                name: weight for name, (_, weight) in self.analyzers.items()
            },
            "successful_analyzers": [r["name"] for r in results if r["success"]],
            "failed_analyzers": [
                {"name": r["name"], "error": r["error"]}
                for r in results
                if not r["success"]
            ],
        }

        return aggregated_results
