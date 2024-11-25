from typing import Set, List, Dict
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor, ProcessedText


class JaccardSimilarityAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.preprocessor = TextPreprocessor()

    def _calculate_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def _analyze_similarities(
        self, cv_processed: ProcessedText, job_processed: ProcessedText
    ) -> Dict[str, float]:
        """Analyze various aspects using Jaccard similarity."""
        similarities = {
            "keyword_similarity": self._calculate_jaccard_similarity(
                cv_processed.keywords, job_processed.keywords
            ),
            "token_similarity": self._calculate_jaccard_similarity(
                set(cv_processed.tokens), set(job_processed.tokens)
            ),
            "entity_similarity": self._calculate_jaccard_similarity(
                {ent["text"].lower() for ent in cv_processed.entities},
                {ent["text"].lower() for ent in job_processed.entities},
            ),
            "noun_phrase_similarity": self._calculate_jaccard_similarity(
                set(cv_processed.noun_phrases), set(job_processed.noun_phrases)
            ),
        }

        return similarities

    def _get_missing_elements(
        self, cv_elements: Set[str], job_elements: Set[str]
    ) -> List[str]:
        """Get elements present in job description but missing from CV."""
        return list(job_elements - cv_elements)

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze similarity between CV and job description using Jaccard similarity."""
        # Process texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Calculate similarities for different aspects
        similarities = self._analyze_similarities(cv_processed, job_processed)

        # Calculate weighted average score
        weights = {
            "keyword_similarity": 0.4,
            "token_similarity": 0.2,
            "entity_similarity": 0.2,
            "noun_phrase_similarity": 0.2,
        }

        overall_score = sum(
            score * weights[aspect] for aspect, score in similarities.items()
        )

        # Find missing elements
        missing_keywords = self._get_missing_elements(
            cv_processed.keywords, job_processed.keywords
        )
        missing_entities = self._get_missing_elements(
            {ent["text"].lower() for ent in cv_processed.entities},
            {ent["text"].lower() for ent in job_processed.entities},
        )

        # Generate suggestions
        suggestions = []
        if missing_keywords:
            suggestions.append(
                f"Consider adding these keywords: {', '.join(missing_keywords[:5])}"
            )
        if missing_entities:
            suggestions.append(
                f"Consider mentioning these topics: {', '.join(missing_entities[:5])}"
            )

        # Collect matched items
        matched_items = cv_processed.keywords.intersection(job_processed.keywords) | {
            ent["text"].lower() for ent in cv_processed.entities
        }.intersection({ent["text"].lower() for ent in job_processed.entities})

        return AnalysisResult(
            score=overall_score,
            details={
                "similarities": similarities,
                "missing_keywords": missing_keywords,
                "missing_entities": missing_entities,
                "suggestions": suggestions,
            },
            matched_items=list(matched_items),
        )
