from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor, ProcessedText


class CosineSimilarityAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer(
            min_df=1, stop_words="english", sublinear_tf=True, use_idf=True
        )

    def _get_important_terms(
        self, feature_names: List[str], tfidf_matrix: np.ndarray, top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """Get most important terms based on TF-IDF scores."""
        importance_scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
        term_scores = list(zip(feature_names, importance_scores))
        return sorted(term_scores, key=lambda x: x[1], reverse=True)[:top_n]

    def _analyze_section_similarity(
        self, cv_sections: List[str], job_sections: List[str]
    ) -> Dict[str, float]:
        """Analyze similarity between sections using TF-IDF and cosine similarity."""
        # Combine all texts for vectorization
        all_sections = cv_sections + job_sections

        # Fit and transform the vectorizer
        tfidf_matrix = self.vectorizer.fit_transform(all_sections)

        # Calculate similarities between job sections and CV sections
        similarities = {}
        feature_names = self.vectorizer.get_feature_names_out()

        for i, job_section in enumerate(job_sections):
            job_vector = tfidf_matrix[len(cv_sections) + i]
            cv_vectors = tfidf_matrix[: len(cv_sections)]

            # Calculate cosine similarity with each CV section
            section_similarities = cosine_similarity(job_vector, cv_vectors)
            max_similarity = float(np.max(section_similarities))

            # Get important terms for this section
            section_terms = self._get_important_terms(
                feature_names, tfidf_matrix[len(cv_sections) + i]
            )

            similarities[f"section_{i}"] = {
                "score": max_similarity,
                "important_terms": section_terms,
            }

        return similarities

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze similarity between CV and job description using cosine similarity."""
        # Preprocess texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Split into sections (could be improved with better section detection)
        cv_sections = [
            ". ".join(cv_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(cv_processed.cleaned_text.split(".")), 10)
        ]
        job_sections = [
            ". ".join(job_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(job_processed.cleaned_text.split(".")), 10)
        ]

        # Analyze similarities
        section_similarities = self._analyze_section_similarity(
            cv_sections, job_sections
        )

        # Calculate overall score
        overall_score = np.mean([s["score"] for s in section_similarities.values()])

        # Collect important terms and generate suggestions
        all_important_terms = []
        missing_terms = []
        suggestions = []

        for section, data in section_similarities.items():
            terms = [term for term, score in data["important_terms"]]
            all_important_terms.extend(terms)

            if data["score"] < 0.4:
                missing_terms.extend(terms)
                suggestions.append(
                    f"Section {section} needs improvement. "
                    f"Consider adding content related to: {', '.join(terms[:5])}"
                )

        return AnalysisResult(
            score=float(overall_score),
            details={
                "section_similarities": {
                    k: v["score"] for k, v in section_similarities.items()
                },
                "important_terms": list(set(all_important_terms)),
                "missing_terms": list(set(missing_terms)),
                "suggestions": suggestions,
            },
            matched_items=list(set(all_important_terms) - set(missing_terms)),
        )
