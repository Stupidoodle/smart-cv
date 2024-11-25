from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from .analyzers.keyword_matcher import KeywordMatcher
from .analyzers.bert_similarity import BERTSimilarityAnalyzer
from .analyzers.cosine_similarity import CosineSimilarityAnalyzer
from .analyzers.jaccard_similarity import JaccardSimilarityAnalyzer
from .analyzers.ner_similarity import NERSimilarityAnalyzer
from .analyzers.lsa_similarity import LSAAnalyzer

from .base import BaseAnalyzer


class CVAnalysisPipeline:
    def __init__(self):
        # Initialize analyzers with weights
        self.analyzers = {
            "keyword": (KeywordMatcher(), 0.2),
            "bert": (BERTSimilarityAnalyzer(), 0.2),
            "cosine": (CosineSimilarityAnalyzer(), 0.15),
            "jaccard": (JaccardSimilarityAnalyzer(), 0.15),
            "ner": (NERSimilarityAnalyzer(), 0.2),
            "lsa": (LSAAnalyzer(), 0.1),
        }

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
        detailed_matches = {}

        for name, result, _ in successful_results:
            # Collect matched items
            all_matched_items.update(result.matched_items)

            # Collect suggestions
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

            # Store detailed matches per analyzer
            detailed_matches[name] = {
                "matched_items": result.matched_items,
                "missing_items": missing_items,
                "specific_details": result.details,
            }

        # Generate categorized improvement suggestions
        categorized_suggestions = self._categorize_suggestions(all_suggestions)

        return {
            "total_score": float(total_score),
            "match_percentage": float(total_score * 100),
            "overall_analysis": {
                "matched_items": list(all_matched_items),
                "missing_items": list(all_missing_items),
                "suggestions": categorized_suggestions,
            },
            "detailed_analysis": {
                name: {"score": result.score, "analysis": detailed_matches[name]}
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

        return {
            k: list(set(v)) for k, v in categorized.items() if v
        }  # Remove duplicates

    def analyze(self, cv_text: str, job_text: str) -> Dict[str, Any]:
        """Run all analyzers in parallel and aggregate results."""
        # Run analyzers in parallel
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._run_analyzer, name, analyzer, cv_text, job_text)
                for name, (analyzer, _) in self.analyzers.items()
            ]
            results = [future.result() for future in futures]

        # Aggregate results
        aggregated_results = self._aggregate_scores(results)

        # Add metadata
        aggregated_results["metadata"] = {
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
