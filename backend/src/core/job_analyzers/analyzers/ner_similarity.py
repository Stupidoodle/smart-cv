from collections import defaultdict
from typing import Dict, List, Set
import spacy
from ..base import BaseAnalyzer, AnalysisResult
from ....utils.text_preprocessor import TextPreprocessor


class NERSimilarityAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.entity_weights = {
            "SKILL": 1.0,  # Custom skill entities
            "PRODUCT": 0.9,  # Software, tools, technologies
            "ORG": 0.8,  # Organizations
            "GPE": 0.7,  # Geographical locations
            "CARDINAL": 0.6,  # Numbers (years of experience)
            "DATE": 0.5,  # Time expressions
        }

    def _categorize_entities(
        self, entities: List[Dict[str, str]]
    ) -> Dict[str, Set[str]]:
        """Categorize entities by their type."""
        categorized = defaultdict(set)
        for entity in entities:
            categorized[entity["label"]].add(entity["text"].lower())
        return dict(categorized)

    def _calculate_category_similarity(
        self, cv_entities: Set[str], job_entities: Set[str]
    ) -> Dict[str, float]:
        """Calculate similarity scores for a specific entity category."""
        if not job_entities:
            return {"score": 1.0, "matched": set(), "missing": set()}

        matched = cv_entities.intersection(job_entities)
        missing = job_entities - cv_entities

        score = len(matched) / len(job_entities) if job_entities else 0.0

        return {"score": score, "matched": matched, "missing": missing}

    def _extract_skills(self, text: str) -> Set[str]:
        """Extract potential skills using pattern matching and NER."""
        skills = set()

        # Use the preprocessor's skill extraction
        skills.update(self.preprocessor.get_skills_and_requirements(text))

        return skills

    def analyze(self, cv_text: str, job_text: str) -> AnalysisResult:
        """Analyze similarity based on named entities and skills."""
        # Process texts
        cv_processed = self.preprocessor.process(cv_text)
        job_processed = self.preprocessor.process(job_text)

        # Extract skills (treated as a special entity type)
        cv_skills = self._extract_skills(cv_text)
        job_skills = self._extract_skills(job_text)

        # Categorize entities
        cv_entities = self._categorize_entities(cv_processed.entities)
        job_entities = self._categorize_entities(job_processed.entities)

        # Add skills to entity categories
        cv_entities["SKILL"] = cv_skills
        job_entities["SKILL"] = job_skills

        # Calculate similarities for each entity type
        similarities = {}
        matched_entities = []
        missing_entities = []
        weighted_scores = []

        for entity_type in self.entity_weights.keys():
            cv_type_entities = cv_entities.get(entity_type, set())
            job_type_entities = job_entities.get(entity_type, set())

            category_sim = self._calculate_category_similarity(
                cv_type_entities, job_type_entities
            )

            similarities[entity_type] = category_sim["score"]
            matched_entities.extend(category_sim["matched"])
            missing_entities.extend(category_sim["missing"])

            # Add weighted score
            weighted_scores.append(
                category_sim["score"] * self.entity_weights[entity_type]
            )

        # Calculate overall score
        overall_score = (
            sum(weighted_scores) / sum(self.entity_weights.values())
            if weighted_scores
            else 0.0
        )

        # Generate suggestions
        suggestions = []
        if missing_entities:
            entity_suggestions = defaultdict(list)
            for entity in missing_entities:
                for entity_type, entities in job_entities.items():
                    if entity in entities:
                        entity_suggestions[entity_type].append(entity)
                        break

            for entity_type, entities in entity_suggestions.items():
                if entities:
                    suggestions.append(
                        f"Consider adding these {entity_type.lower()} mentions: "
                        f"{', '.join(entities[:5])}"
                    )

        return AnalysisResult(
            score=overall_score,
            details={
                "entity_similarities": similarities,
                "matched_entities": list(set(matched_entities)),
                "missing_entities": list(set(missing_entities)),
                "suggestions": suggestions,
            },
            matched_items=list(set(matched_entities)),
        )
