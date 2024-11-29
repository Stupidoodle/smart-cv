import json
from datetime import datetime

import spacy
from openai.types.beta.threads import Run
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
from app.models.assistant import Assistant as AssistantModel
from app.models.conversation import Conversation as ConversationModel
from app.models.run import Run as RunModel
from app.schemas.analysis import AnalysisResponse as AnalysisResponseSchema
from sqlalchemy.orm import Session
from typing import Tuple, List, Optional

from app.services.cv_service import compile_latex
from app.services.openai_assistant_service import OpenAIAssistantService
from app.utils.file_management import PDF_DIR

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load BERT model
bert_model = SentenceTransformer("bert-base-nli-mean-tokens")


def handle_run(
    run: Run,
    ai_service: OpenAIAssistantService,
    db: Session,
    conversation: ConversationModel,
):
    if run.status == "requires_action":
        tool_outputs = []
        cv_entry = db.query(CV).filter(CV.id == conversation.cv_id).first()
        job_entry = db.query(Job).filter(Job.id == conversation.job_id).first()
        pdf_file_path = cv_entry.filepath.replace(".tex", ".pdf")
        if not os.path.exists(pdf_file_path):
            compile_latex(cv_entry.filepath)

        cv_text = extract_text_from_pdf(pdf_file_path)
        job_description = job_entry.description
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == "fetch_candidate_cv":
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"cv_text": cv_text}),
                    }
                )
            elif function_name == "fetch_job_description":
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(
                            {
                                "job_description": job_description,
                            }
                        ),
                    }
                )
            elif function_name == "extract_essential_keywords":
                keyword_assistant = (
                    db.query(AssistantModel)
                    .filter(
                        AssistantModel.name == "Keyword Assistant",
                    )
                    .first()
                )
                keyword_assistant_thread = ai_service.create_thread()
                ai_service.add_message_to_thread(
                    thread_id=keyword_assistant_thread.id,
                    role="user",
                    content=tool_call.function.arguments,
                )
                keyword_assistant_run = ai_service.run_assistant_on_thread(
                    thread_id=keyword_assistant_thread.id,
                    assistant_id=keyword_assistant.id,
                )
                if keyword_assistant_run.status == "completed":
                    keyword_assistant_output = json.loads(
                        ai_service.list_messages_in_thread(
                            thread_id=keyword_assistant_thread.id
                        )[0]
                        .content[0]
                        .text.value
                    ).get("strings")

                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(
                                {"keywords": keyword_assistant_output}
                            ),
                        }
                    )
                else:
                    raise Exception("Keyword Assistant failed to run.")
            elif function_name == "start_static_analysis":
                keywords = json.loads(tool_call.function.arguments).get(
                    "essential_keywords"
                )
                try:
                    analysis = analyze_cv(
                        conversation.cv_id, conversation.job_id, keywords
                    )
                except Exception as e:
                    raise Exception(f"Error during analysis: {e}")
                if not analysis:
                    raise Exception("Analysis failed.")
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(AnalysisResponseSchema.from_orm(analysis)),
                    }
                )
            else:
                # Handle unknown functions
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": "Function not implemented.",
                    }
                )

            run_entry = (
                db.query(RunModel)
                .filter(
                    RunModel.id == run.id,
                    RunModel.conversation_id == conversation.id,
                )
                .first()
            )

            run = ai_service.run_assistant_on_thread(
                thread_id=run.thread_id, run_id=run.id, tool_outputs=tool_outputs
            )

            if run_entry:
                run_entry.status = run.status
                run_entry.updated_at = datetime.now()

            handle_run(run, ai_service, db, conversation)

            return run


def analyze_cv(
    cv_id: int, job_id: int, keywords: Optional[List[str]] = None
) -> Optional[AnalysisResult]:
    db: Session = SessionLocal()
    try:
        cv_entry = db.query(CV).filter(CV.id == cv_id).first()
        job_entry = db.query(Job).filter(Job.id == job_id).first()
        existing_analysis = db.query(AnalysisResult).filter(
            AnalysisResult.cv_id == cv_id, AnalysisResult.job_id == job_id
        )
        if existing_analysis.first():
            return existing_analysis.first()

        if not cv_entry:
            raise Exception("CV not found in database.")
        if not job_entry:
            raise Exception("Job not found in database.")

        # Extract text from CV
        pdf_file_path = cv_entry.filepath.replace(".tex", ".pdf")
        if not os.path.exists(pdf_file_path):
            compile_latex(str(cv_entry.filepath))
        extracted_text = extract_text_from_pdf(
            PDF_DIR + "/" + os.path.basename(pdf_file_path)
        )

        # Extract text from Job Description
        job_description = str(job_entry.description)

        # Perform analysis
        keyword_score = keyword_matching(extracted_text, job_description, keywords)
        bert_score = bert_similarity_score(extracted_text, job_description)
        cosine_score = cosine_similarity_score(extracted_text, job_description)
        jaccard_score = jaccard_similarity_score(extracted_text, job_description)
        ner_score = ner_similarity_score(extracted_text, job_description)
        lsa_score = lsa_analysis_score(extracted_text, job_description)

        # Aggregate scores (weighted average example)
        aggregated = (
            keyword_score * 0.2
            + bert_score * 0.2
            + cosine_score * 0.2
            + jaccard_score * 0.1
            + ner_score * 0.2
            + lsa_score * 0.1
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
            aggregated_score=float(aggregated),
        )
        db.add(analysis)
        db.commit()

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise e
    finally:
        db.close()

    return analysis


def extract_text_from_pdf(pdf_file_path: str) -> str:
    try:
        text = textract.process(pdf_file_path).decode("utf-8")
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")


def keyword_matching(
    cv_text: str, job_description: str, keywords: Optional[List[str]]
) -> float:
    # Define essential keywords (could be dynamic or stored in DB)
    if keywords:
        essential_keywords = keywords
    else:
        essential_keywords = [
            "python",
            "machine learning",
            "data analysis",
            "sql",
            "communication",
            "teamwork",
        ]

    cv_words = set(cv_text.lower().split())
    job_words = set(job_description.lower().split())
    matched_keywords = cv_words.intersection(job_words).intersection(
        set(essential_keywords)
    )
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


def lsa_analysis_score(
    cv_text: str, job_description: str, n_components: int = 100
) -> float:
    documents = [cv_text, job_description]
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), max_features=10000
    )
    X = vectorizer.fit_transform(documents)

    # Ensure n_components is less than the number of features
    n_components = min(n_components, X.shape[1] - 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_reduced = svd.fit_transform(X)

    similarity = cosine_similarity([X_reduced[0]], [X_reduced[1]])[0][0] * 100
    return round(similarity, 2)
