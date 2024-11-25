import spacy
from typing import List, Set, Dict
import re
from dataclasses import dataclass


@dataclass
class ProcessedText:
    raw_text: str
    cleaned_text: str
    tokens: List[str]
    lemmas: List[str]
    entities: List[Dict[str, str]]
    noun_phrases: List[str]
    keywords: Set[str]


class TextPreprocessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.stop_words = self.nlp.Defaults.stop_words

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep important ones
        text = re.sub(r"[^a-zA-Z0-9\s+#\.\/\-]", "", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text

    def extract_keywords(self, doc) -> Set[str]:
        """Extract important keywords from text."""
        keywords = set()

        # Add named entities
        for ent in doc.ents:
            keywords.add(ent.text.lower())

        # Add noun phrases
        for chunk in doc.noun_chunks:
            keywords.add(chunk.text.lower())

        # Add important single tokens
        for token in doc:
            if (
                not token.is_stop
                and not token.is_punct
                and token.is_alpha
                and (token.pos_ in ["NOUN", "PROPN", "ADJ", "VERB"])
            ):
                keywords.add(token.lemma_.lower())

        return keywords

    def process(self, text: str) -> ProcessedText:
        """Process text and return various useful formats."""
        cleaned_text = self.clean_text(text)
        doc = self.nlp(cleaned_text)
        # Get tokens and lemmas
        tokens = [
            token.text for token in doc if not token.is_stop and not token.is_punct
        ]
        lemmas = [
            token.lemma_ for token in doc if not token.is_stop and not token.is_punct
        ]

        # Get named entities
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

        # Get noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]

        # Extract keywords
        keywords = self.extract_keywords(doc)

        return ProcessedText(
            raw_text=text,
            cleaned_text=cleaned_text,
            tokens=tokens,
            lemmas=lemmas,
            entities=entities,
            noun_phrases=noun_phrases,
            keywords=keywords,
        )

    def get_skills_and_requirements(self, text: str) -> Set[str]:
        """Extract specific skills and requirements from text."""
        doc = self.nlp(text)
        skills = set()

        # Pattern matching for common skill patterns
        skill_patterns = [
            r"experience (?:in|with) ([^.,;]+)",
            r"knowledge of ([^.,;]+)",
            r"familiarity with ([^.,;]+)",
            r"proficiency in ([^.,;]+)",
            r"skilled in ([^.,;]+)",
            r"expertise in ([^.,;]+)",
        ]

        # Extract skills using patterns
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                skills.add(match.group(1).strip())

        # Add technical terms and tool names from entities and noun phrases
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                skills.add(ent.text.lower())

        # Add noun phrases that might represent skills
        for chunk in doc.noun_chunks:
            if any(
                tech_word in chunk.text.lower()
                for tech_word in [
                    "python",
                    "java",
                    "sql",
                    "aws",
                    "cloud",
                    "docker",
                    "kubernetes",
                ]
            ):
                skills.add(chunk.text.lower())

        return skills
