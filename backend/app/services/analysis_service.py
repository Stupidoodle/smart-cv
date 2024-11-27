import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import jaccard
import numpy as np
import textract
import os
from app.models.analysis import AnalysisResult
from app.database import SessionLocal
from app.models.cv import CV
from app.models.job import Job
from sqlalchemy.orm import Session
from typing import Tuple

from app.services.cv_service import compile_latex
from app.utils.file_management import PDF_DIR

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load BERT model
bert_model = SentenceTransformer('bert-base-nli-mean-tokens')

def analyze_cv(cv_id: int, job_id: int):
    db: Session = SessionLocal()
    try:
        cv_entry = db.query(CV).filter(CV.id == cv_id).first()
        job_entry = db.query(Job).filter(Job.id == job_id).first()
        if not cv_entry:
            raise Exception("CV not found in database.")
        if not job_entry:
            raise Exception("Job not found in database.")

        # Extract text from CV
        pdf_file_path = cv_entry.filepath.replace(".tex", ".pdf")
        if not os.path.exists(pdf_file_path):
            compile_latex(cv_entry.filepath)
        extracted_text = extract_text_from_pdf(PDF_DIR + "/" + os.path.basename(pdf_file_path))

        # Extract text from Job Description
        job_description = job_entry.description

        # Perform analysis
        keyword_score = keyword_matching(extracted_text, job_description)
        bert_score = bert_similarity_score(extracted_text, job_description)
        cosine_score = cosine_similarity_score(extracted_text, job_description)
        jaccard_score = jaccard_similarity_score(extracted_text, job_description)
        ner_score = ner_similarity_score(extracted_text, job_description)
        lsa_score = lsa_analysis_score(extracted_text, job_description)

        # Aggregate scores (weighted average example)
        aggregated = (
            keyword_score * 0.2 +
            bert_score * 0.2 +
            cosine_score * 0.2 +
            jaccard_score * 0.1 +
            ner_score * 0.2 +
            lsa_score * 0.1
        )

        # Store analysis results
        analysis = AnalysisResult(
            cv_id=cv_id,
            job_id=job_id,
            keyword_match_score=keyword_score,
            bert_similarity_score=float(bert_score),
            cosine_similarity_score=float(cosine_score),
            jaccard_similarity_score=float(jaccard_score),
            ner_similarity_score=float(ner_score),
            lsa_analysis_score=float(lsa_score),
            aggregated_score=float(aggregated)
        )
        db.add(analysis)
        db.commit()

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise e
    finally:
        db.close()

def extract_text_from_pdf(pdf_file_path: str) -> str:
    try:
        text = textract.process(pdf_file_path).decode('utf-8')
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")

def keyword_matching(cv_text: str, job_description: str) -> float:
    # Define essential keywords (could be dynamic or stored in DB)
    essential_keywords = ["python", "machine learning", "data analysis", "sql", "communication", "teamwork"]

    cv_words = set(cv_text.lower().split())
    job_words = set(job_description.lower().split())
    matched_keywords = cv_words.intersection(job_words).intersection(set(essential_keywords))
    if not essential_keywords:
        return 0.0
    score = (len(matched_keywords) / len(essential_keywords)) * 100
    return round(score, 2)

def bert_similarity_score(cv_text: str, job_description: str) -> float:
    embeddings = bert_model.encode([cv_text, job_description])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0] * 100
    return round(similarity, 2)

def cosine_similarity_score(cv_text: str, job_description: str) -> float:
    vectorizer = TfidfVectorizer().fit([cv_text, job_description])
    vectors = vectorizer.transform([cv_text, job_description])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0] * 100
    return round(similarity, 2)

def jaccard_similarity_score(cv_text: str, job_description: str) -> float:
    cv_set = set(cv_text.lower().split())
    job_set = set(job_description.lower().split())
    if not cv_set or not job_set:
        return 0.0
    intersection = cv_set.intersection(job_set)
    union = cv_set.union(job_set)
    similarity = (len(intersection) / len(union)) * 100
    return round(similarity, 2)

def ner_similarity_score(cv_text: str, job_description: str) -> float:
    cv_doc = nlp(cv_text)
    job_doc = nlp(job_description)

    cv_entities = set([ent.text.lower() for ent in cv_doc.ents])
    job_entities = set([ent.text.lower() for ent in job_doc.ents])

    if not job_entities:
        return 0.0

    matched_entities = cv_entities.intersection(job_entities)
    similarity = (len(matched_entities) / len(job_entities)) * 100
    return round(similarity, 2)


def lsa_analysis_score(cv_text: str, job_description: str,
                       n_components: int = 100) -> float:
    documents = [cv_text, job_description]
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2),
                                 max_features=10000)
    X = vectorizer.fit_transform(documents)

    # Ensure n_components is less than the number of features
    n_components = min(n_components, X.shape[1] - 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_reduced = svd.fit_transform(X)

    similarity = cosine_similarity([X_reduced[0]], [X_reduced[1]])[0][0] * 100
    return round(similarity, 2)

