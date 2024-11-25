from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor


class BERTSimilarityAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.preprocessor = TextPreprocessor()

    def _split_into_chunks(self, text: str, chunk_size: int = 512) -> List[str]:
        """Split text into smaller chunks to handle BERT's max token limit."""
        sentences = text.split(".")
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Approximate token count (rough estimation)
            sentence_length = len(sentence.split())

            if current_length + sentence_length > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _get_text_embedding(self, text: str) -> np.ndarray:
        """Get BERT embedding for text, handling long sequences."""
        chunks = self._split_into_chunks(text)
        chunk_embeddings = self.model.encode(chunks)
        # Average embeddings of all chunks
        return np.mean(chunk_embeddings, axis=0)

    def _compute_semantic_similarity(
        self, cv_sections: List[str], job_sections: List[str]
    ) -> Dict[str, float]:
        """Compute semantic similarity between CV and job description sections."""
        cv_embeddings = [self._get_text_embedding(section) for section in cv_sections]
        job_embeddings = [self._get_text_embedding(section) for section in job_sections]

        similarities = {}
        for i, job_emb in enumerate(job_embeddings):
            section_similarities = [
                np.dot(job_emb, cv_emb)
                / (np.linalg.norm(job_emb) * np.linalg.norm(cv_emb))
                for cv_emb in cv_embeddings
            ]
            similarities[f"section_{i}"] = max(section_similarities)

        return similarities

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze semantic similarity between CV and job description."""
        # Clean and preprocess texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Split texts into relevant sections (could be improved with better section detection)
        cv_sections = [
            ". ".join(cv_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(cv_processed.cleaned_text.split(".")), 10)
        ]
        job_sections = [
            ". ".join(job_processed.cleaned_text.split(".")[: i + 10])
            for i in range(0, len(job_processed.cleaned_text.split(".")), 10)
        ]

        # Compute similarities
        section_similarities = self._compute_semantic_similarity(
            cv_sections, job_sections
        )

        # Calculate overall score
        overall_score = np.mean(list(section_similarities.values()))

        # Generate meaningful feedback
        suggestions = []
        matched_sections = []
        low_match_sections = []

        for section, score in section_similarities.items():
            if score >= 0.8:
                matched_sections.append(section)
            elif score <= 0.4:
                low_match_sections.append(section)

        if low_match_sections:
            suggestions.append(
                "Consider expanding these sections to better match the job requirements: "
                f"{', '.join(low_match_sections)}"
            )

        return AnalysisResult(
            score=float(overall_score),
            details={
                "section_similarities": section_similarities,
                "high_match_sections": matched_sections,
                "low_match_sections": low_match_sections,
                "suggestions": suggestions,
            },
            matched_items=matched_sections,
        )
