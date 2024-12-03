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
from app.models.message import Message
from app.models.run import Run as RunModel
from app.schemas.analysis import AnalysisResponse as AnalysisResponseSchema
from sqlalchemy.orm import Session
from typing import Tuple, List, Optional

from app.services.cv_service import compile_latex
from app.services.openai_assistant_service import OpenAIAssistantService
from app.utils.file_management import PDF_DIR


def pre_process(
    text: str, ai_service: OpenAIAssistantService, db: Session, cv_id: int, job_id: int
) -> str:
    pre_process_assistant = (
        db.query(AssistantModel)
        .filter(AssistantModel.name == "Preprocess Assistant")
        .first()
    )
    pre_process_assistant_thread = ai_service.create_thread()
    db_conversation = ConversationModel(
        id=pre_process_assistant_thread.id,
        cv_id=cv_id,
        job_id=job_id,
        assistant_id=pre_process_assistant.id,
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    message = ai_service.add_message_to_thread(
        thread_id=pre_process_assistant_thread.id,
        role="user",
        content=text,
    )
    db_message = Message(
        id=message.id,
        conversation_id=db_conversation.id,
        role=message.role,
        content=message.content[0].text.value,
        timestamp=datetime.fromtimestamp(message.created_at),
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    pre_process_assistant_run = ai_service.run_assistant_on_thread(
        thread_id=pre_process_assistant_thread.id,
        assistant_id=pre_process_assistant.id,
    )
    db_run = RunModel(
        id=pre_process_assistant_run.id,
        conversation_id=db_conversation.id,
        status=pre_process_assistant_run.status,
        updated_at=datetime.now(),
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    if pre_process_assistant_run.status == "completed":
        message_result = ai_service.list_messages_in_thread(
            thread_id=pre_process_assistant_thread.id
        )[0]

        text = json.loads(
            ai_service.list_messages_in_thread(
                thread_id=pre_process_assistant_thread.id,
            )[0]
            .content[0]
            .text.value
        ).get("value")

        db_message_result = Message(
            id=message_result.id,
            conversation_id=db_conversation.id,
            role=message_result.role,
            content=text,
            timestamp=datetime.fromtimestamp(message_result.created_at),
        )
        db.add(db_message_result)
        db.commit()
        db.refresh(db_message_result)

    return text


def handle_run(
    run: Run,
    ai_service: OpenAIAssistantService,
    db: Session,
    conversation_id: str,
):
    current_run = run

    while current_run.status == "requires_action":
        with SessionLocal() as session:
            try:
                conversation = (
                    session.query(ConversationModel)
                    .filter(ConversationModel.id == conversation_id)
                    .first()
                )

                tool_outputs = []
                cv_entry = session.query(CV).filter(CV.id == conversation.cv_id).first()
                job_entry = (
                    session.query(Job).filter(Job.id == conversation.job_id).first()
                )

                pdf_file_path = cv_entry.filepath.replace(".tex", ".pdf")
                if not os.path.exists(pdf_file_path):
                    compile_latex(cv_entry.filepath)

                cv_id = cv_entry.id
                job_id = job_entry.id

                for (
                    tool_call
                ) in current_run.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name

                    if (
                        function_name == "fetch_candidate_cv"
                        or function_name == "fetch_candidate_cv_1"
                    ):
                        cv_text = extract_text_from_pdf(
                            PDF_DIR + "/" + os.path.basename(pdf_file_path)
                        )
                        cv_text = pre_process(
                            cv_text, ai_service, session, cv_id, job_id
                        )
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"cv_text": cv_text}),
                            }
                        )

                    elif (
                        function_name == "fetch_job_description"
                        or function_name == "fetch_job_description_1"
                    ):
                        job_description = job_entry.description
                        job_description = pre_process(
                            job_description, ai_service, session, cv_id, job_id
                        )
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(
                                    {"job_description": str(job_description)}
                                ),
                            }
                        )

                    elif function_name == "fetch_ai_analysis":
                        analysis_result = (
                            session.query(AnalysisResult)
                            .filter(AnalysisResult.id == conversation.analysis_id)
                            .first()
                        )
                        analysis_message = (
                            session.query(Message)
                            .filter(
                                Message.conversation_id
                                == analysis_result.conversation_id,
                                Message.role == "assistant",
                            )
                            .first()
                        )
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(
                                    {
                                        "analysis_message": analysis_message.content,
                                    }
                                ),
                            }
                        )

                    elif function_name == "extract_essential_keywords":
                        keyword_assistant = (
                            session.query(AssistantModel)
                            .filter(AssistantModel.name == "Keyword Assistant")
                            .first()
                        )
                        keyword_thread = ai_service.create_thread()
                        db_conversation = ConversationModel(
                            id=keyword_thread.id,
                            cv_id=conversation.cv_id,
                            job_id=conversation.job_id,
                            assistant_id=keyword_assistant.id,
                        )
                        session.add(db_conversation)
                        session.commit()
                        session.refresh(db_conversation)
                        message = ai_service.add_message_to_thread(
                            thread_id=keyword_thread.id,
                            role="user",
                            content=tool_call.function.arguments,
                        )
                        db_message = Message(
                            id=message.id,
                            conversation_id=db_conversation.id,
                            role=message.role,
                            content=message.content[0].text.value,
                            timestamp=datetime.fromtimestamp(message.created_at),
                        )
                        session.add(db_message)
                        session.commit()
                        session.refresh(db_message)
                        keyword_run = ai_service.run_assistant_on_thread(
                            thread_id=keyword_thread.id,
                            assistant_id=keyword_assistant.id,
                        )
                        db_run = RunModel(
                            id=keyword_run.id,
                            conversation_id=db_conversation.id,
                            status=keyword_run.status,
                            created_at=datetime.fromtimestamp(run.created_at),
                            updated_at=datetime.now(),
                        )
                        session.add(db_run)
                        session.commit()
                        session.refresh(db_run)

                        if keyword_run.status == "completed":
                            message_result = ai_service.list_messages_in_thread(
                                thread_id=keyword_thread.id
                            )[0]
                            keyword_output = json.loads(
                                ai_service.list_messages_in_thread(
                                    thread_id=keyword_thread.id
                                )[0]
                                .content[0]
                                .text.value
                            ).get("strings")
                            db_message_result = Message(
                                id=message_result.id,
                                conversation_id=db_conversation.id,
                                role=message_result.role,
                                content=keyword_output,
                                timestamp=datetime.fromtimestamp(
                                    message_result.created_at
                                ),
                            )
                            session.add(db_message_result)
                            session.commit()
                            session.refresh(db_message_result)

                            tool_outputs.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({"keywords": keyword_output}),
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
                                cv_id=conversation.cv_id,
                                job_id=conversation.job_id,
                                conversation=conversation,
                                keywords=keywords,
                                session=session,
                            )

                            # Convert to dict immediately after creation while session is still active
                            analysis_dict = {
                                "id": analysis.id,
                                "cv_id": analysis.cv_id,
                                "job_id": analysis.job_id,
                                "keyword_match_score": float(
                                    analysis.keyword_match_score
                                ),
                                "bert_similarity_score": float(
                                    analysis.bert_similarity_score
                                ),
                                "cosine_similarity_score": float(
                                    analysis.cosine_similarity_score
                                ),
                                "jaccard_similarity_score": float(
                                    analysis.jaccard_similarity_score
                                ),
                                "ner_similarity_score": float(
                                    analysis.ner_similarity_score
                                ),
                                "lsa_analysis_score": float(
                                    analysis.lsa_analysis_score
                                ),
                                "aggregated_score": float(analysis.aggregated_score),
                            }

                            tool_outputs.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps(analysis_dict),
                                }
                            )

                        except Exception as e:
                            raise Exception(f"Error during analysis: {e}")

                run_entry = (
                    session.query(RunModel)
                    .filter(
                        RunModel.id == current_run.id,
                        RunModel.conversation_id == conversation.id,
                    )
                    .first()
                )

                # Submit tool outputs and get new run state
                new_run = ai_service.run_assistant_on_thread(
                    thread_id=current_run.thread_id,
                    run_id=current_run.id,
                    tool_outputs=tool_outputs,
                )

                # Update run entry if it exists
                if run_entry:
                    run_entry.status = new_run.status
                    run_entry.updated_at = datetime.now()
                    session.commit()

                # Update current run for next iteration
                current_run = new_run

            except Exception as e:
                session.rollback()
                raise e

    return current_run


def analyze_cv(
    cv_id: int,
    job_id: int,
    conversation: ConversationModel,
    keywords: Optional[List[str]] = None,
    session: Optional[Session] = None,
) -> Optional[AnalysisResult]:
    if session is None:
        session = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        cv_entry = session.query(CV).filter(CV.id == cv_id).first()
        job_entry = session.query(Job).filter(Job.id == job_id).first()
        conversation_entry = session.query(ConversationModel).filter(
            ConversationModel.id == conversation.id
        )
        existing_analysis = (
            session.query(AnalysisResult)
            .filter(
                AnalysisResult.cv_id == cv_id,
                AnalysisResult.job_id == job_id,
                AnalysisResult.conversation_id == conversation.id,
            )
            .first()
        )

        if existing_analysis:
            return existing_analysis

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

        # Aggregate scores
        aggregated = (
            keyword_score * 0.2
            + bert_score * 0.2
            + cosine_score * 0.2
            + jaccard_score * 0.1
            + ner_score * 0.2
            + lsa_score * 0.1
        )

        # Create and persist analysis results
        analysis = AnalysisResult(
            cv_id=cv_id,
            job_id=job_id,
            conversation_id=conversation.id,
            keyword_match_score=keyword_score,
            bert_similarity_score=float(bert_score),
            cosine_similarity_score=float(cosine_score),
            jaccard_similarity_score=float(jaccard_score),
            ner_similarity_score=float(ner_score),
            lsa_analysis_score=float(lsa_score),
            aggregated_score=float(aggregated),
        )
        session.add(analysis)
        session.commit()

        # Refresh to ensure all attributes are loaded
        session.refresh(analysis)
        return analysis

    except Exception as e:
        session.rollback()
        raise e
    finally:
        if should_close:
            session.close()


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
    bert_model = SentenceTransformer("bert-base-nli-mean-tokens")
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
    nlp = spacy.load("en_core_web_sm")
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
