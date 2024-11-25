from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np


@dataclass
class AnalysisResult:
    score: float
    details: Dict[str, Any]
    matched_items: List[str]


class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        pass


class AnalysisPipeline:
    def __init__(self):
        self.analyzers: Dict[str, tuple[BaseAnalyzer, float]] = {}
        self.weights = {
            "keyword": 0.2,
            "cosine": 0.2,
            "jaccard": 0.15,
            "ner": 0.15,
            "bert": 0.2,
            "lsa": 0.1,
        }

    def add_analyzer(self, name: str, analyzer: BaseAnalyzer, weight: float):
        """Add an analyzer to the pipeline with its weight."""
        self.analyzers[name] = (analyzer, weight)

    def analyze(self, cv_text: str, job_text: str) -> Dict[str, Any]:
        """Run all analyzers and aggregate results."""
        results = {}
        total_score = 0.0

        for name, (analyzer, weight) in self.analyzers.items():
            try:
                result = analyzer.analyze(cv_text, job_text)
                results[name] = result
                total_score += result.score * weight
            except Exception as e:
                print(f"Error in {name} analyzer: {str(e)}")
                results[name] = AnalysisResult(0.0, {"error": str(e)}, [])

        return {
            "total_score": total_score,
            "detailed_results": results,
            "summary": self._generate_summary(results),
        }

    def _generate_summary(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Generate a summary of the analysis results."""
        all_matched_items = []
        missing_skills = set()

        for result in results.values():
            all_matched_items.extend(result.matched_items)
            if "missing_skills" in result.details:
                missing_skills.update(result.details["missing_skills"])

        return {
            "matched_items": list(set(all_matched_items)),
            "missing_skills": list(missing_skills),
            "improvement_suggestions": self._generate_suggestions(results),
        }

    def _generate_suggestions(self, results: Dict[str, AnalysisResult]) -> List[str]:
        """Generate improvement suggestions based on analysis results."""
        suggestions = []
        # Implementation of suggestion generation logic
        return suggestions
