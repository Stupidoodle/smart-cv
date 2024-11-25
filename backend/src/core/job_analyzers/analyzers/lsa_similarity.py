from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple, Any
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor


class LSAAnalyzer(BaseAnalyzer):
    def __init__(self, n_components: int = 100):
        self.preprocessor = TextPreprocessor()
        self.n_components = n_components
        self.vectorizer = TfidfVectorizer(
            min_df=1, stop_words="english", sublinear_tf=True, use_idf=True
        )
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)

    def _get_topic_terms(
        self,
        transformed_matrix: np.ndarray,
        feature_names: List[str],
        n_top_terms: int = 5,
    ) -> List[List[str]]:
        """Extract top terms for each topic/component."""
        topics = []
        for topic_idx in range(self.n_components):
            top_terms_idx = transformed_matrix[topic_idx].argsort()[-n_top_terms:]
            topics.append([feature_names[i] for i in top_terms_idx])
        return topics

    def _analyze_semantic_topics(
        self, cv_sections: List[str], job_sections: List[str]
    ) -> Dict[str, Any]:
        """Analyze semantic topics in both CV and job description."""
        # Combine all texts for vectorization
        all_sections = cv_sections + job_sections

        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(all_sections)

        # Apply LSA
        lsa_matrix = self.svd.fit_transform(tfidf_matrix)

        # Get feature names
        feature_names = self.vectorizer.get_feature_names_out()

        # Extract topics
        topic_terms = self._get_topic_terms(self.svd.components_, feature_names)

        # Split matrices back into CV and job components
        cv_matrix = lsa_matrix[: len(cv_sections)]
        job_matrix = lsa_matrix[len(cv_sections) :]

        # Calculate similarities between sections
        similarities = cosine_similarity(cv_matrix, job_matrix)

        # Find best matching sections
        best_matches = {}
        for job_idx in range(len(job_sections)):
            best_cv_idx = similarities[:, job_idx].argmax()
            best_matches[f"job_section_{job_idx}"] = {
                "cv_section": f"cv_section_{best_cv_idx}",
                "similarity": float(similarities[best_cv_idx, job_idx]),
                "topics": topic_terms[job_idx],
            }

        return {
            "topic_terms": topic_terms,
            "section_matches": best_matches,
            "raw_similarities": similarities.tolist(),
        }

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze semantic similarity using LSA."""
        # Process texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Split into sections
        cv_sections = [
            ". ".join(cv_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(cv_processed.cleaned_text.split(".")), 10)
        ]
        job_sections = [
            ". ".join(job_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(job_processed.cleaned_text.split(".")), 10)
        ]

        # Perform LSA analysis
        analysis_results = self._analyze_semantic_topics(cv_sections, job_sections)

        # Calculate overall score
        section_scores = [
            match["similarity"]
            for match in analysis_results["section_matches"].values()
        ]
        overall_score = float(np.mean(section_scores))

        # Generate suggestions based on topic analysis
        suggestions = []
        matched_topics = set()
        missing_topics = set()

        for section, match in analysis_results["section_matches"].items():
            if match["similarity"] < 0.5:
                topics = match["topics"]
                missing_topics.update(topics)
                suggestions.append(
                    f"Section {section} could be improved by adding content "
                    f"related to: {', '.join(topics)}"
                )
            else:
                matched_topics.update(match["topics"])

        # Additional semantic suggestions
        if missing_topics:
            suggestions.append(
                "Consider incorporating these key concepts: "
                f"{', '.join(list(missing_topics)[:5])}"
            )

        return AnalysisResult(
            score=overall_score,
            details={
                "section_matches": analysis_results["section_matches"],
                "matched_topics": list(matched_topics),
                "missing_topics": list(missing_topics),
                "suggestions": suggestions,
            },
            matched_items=list(matched_topics),
        )
