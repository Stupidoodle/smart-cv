import json

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import true, String, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models.assistant import Assistant as AssistantModel
from app.models.tool import Tool as ToolModel
from app.schemas.assistant import AssistantCreate, AssistantResponse
from app.services.openai_assistant_service import OpenAIAssistantService
from app.core.config import settings

router = APIRouter()
ai_service = OpenAIAssistantService()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/initiate")
def initiate_assistant(db: Session = Depends(get_db)):
    try:
        assistant_entry = db.query(AssistantModel).filter(
            AssistantModel.name == "Smart CV Assistant"
        )
        if not assistant_entry.first():
            try:
                assistant_data = ai_service.create_assistant(
                    name="Smart CV Assistant",
                    instructions=settings.INSTRUCTION,
                    model="gpt-4o",
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "fetch_job_description",
                                "description": "Retrieve the job description",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "fetch_candidate_cv",
                                "description": "Retrieve the candidate's CV",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "extract_essential_keywords",
                                "description": "Retrieves important keywords from a job description",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "required": ["job_description"],
                                    "properties": {
                                        "job_description": {
                                            "type": "string",
                                            "description": "The job description text from which to extract keywords",
                                        }
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "start_static_analysis",
                                "description": "Initiate a function call to start static analysis by utilizing the extracted keywords.",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "required": [
                                        "essential_keywords",
                                        "AnalysisResult",
                                    ],
                                    "properties": {
                                        "essential_keywords": {
                                            "type": "array",
                                            "description": "List of keywords essential for the static analysis.",
                                            "items": {
                                                "type": "string",
                                                "description": "An individual keyword for analysis.",
                                            },
                                        },
                                        "AnalysisResult": {
                                            "type": "object",
                                            "description": "Result object containing various scores from the static analysis.",
                                            "properties": {
                                                "aggregated_score": {
                                                    "type": "number",
                                                    "description": "Overall aggregated score from the static analysis.",
                                                },
                                                "bert_similarity_score": {
                                                    "type": "number",
                                                    "description": "Similarity score calculated using BERT.",
                                                },
                                                "cosine_similarity_score": {
                                                    "type": "number",
                                                    "description": "Cosine similarity score.",
                                                },
                                                "cv_id": {
                                                    "type": "string",
                                                    "description": "ID associated with the CV.",
                                                },
                                                "job_id": {
                                                    "type": "string",
                                                    "description": "ID associated with the job.",
                                                },
                                                "jaccard_similarity_score": {
                                                    "type": "number",
                                                    "description": "Jaccard similarity score.",
                                                },
                                                "keyword_match_score": {
                                                    "type": "number",
                                                    "description": "Score representing how well the keywords matched.",
                                                },
                                                "lsa_analysis_score": {
                                                    "type": "number",
                                                    "description": "Score from Latent Semantic Analysis.",
                                                },
                                                "ner_similarity_score": {
                                                    "type": "number",
                                                    "description": "Similarity score calculated using Named Entity Recognition.",
                                                },
                                            },
                                            "required": [
                                                "aggregated_score",
                                                "bert_similarity_score",
                                                "cosine_similarity_score",
                                                "cv_id",
                                                "job_id",
                                                "jaccard_similarity_score",
                                                "keyword_match_score",
                                                "lsa_analysis_score",
                                                "ner_similarity_score",
                                            ],
                                            "additionalProperties": False,
                                        },
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                    ],
                )
                db_assistant = AssistantModel(
                    id=assistant_data.id,
                    name=assistant_data.name,
                    instructions=assistant_data.instructions,
                    model=assistant_data.model,
                )
                db.add(db_assistant)
                db.commit()
                db.refresh(db_assistant)

                for tool in assistant_data.tools:
                    tool_entry = (
                        db.query(ToolModel)
                        .filter(
                            ToolModel.assistant_id == db_assistant.id,
                            ToolModel.type == tool.type,
                        )
                        .filter(
                            cast(ToolModel.function_definition, JSONB)
                            == json.dumps(tool.function.model_dump())
                            if tool.type == "function"
                            else true()
                        )
                        .first()
                    )

                    if not tool_entry:
                        db_tool = ToolModel(
                            id=(
                                tool.function.name
                                if tool.type == "function"
                                else tool.type
                            ),
                            assistant_id=db_assistant.id,
                            type=tool.type,
                            function_definition=(
                                tool.function.model_dump()
                                if tool.type == "function"
                                else None
                            ),
                        )
                        db.add(db_tool)
                        db.commit()
                        db.refresh(db_tool)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        keyword_assistant_entry = db.query(AssistantModel).filter(
            AssistantModel.name == "Keyword Assistant"
        )
        if not keyword_assistant_entry.first():
            try:
                keyword_assistant_data = ai_service.create_assistant(
                    name="Keyword Assistant",
                    instructions=settings.KEYWORD_INSTRUCTION,
                    model="gpt-4o-mini",
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "list_of_strings",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "strings": {
                                        "type": "array",
                                        "description": "A list of strings.",
                                        "items": {"type": "string"},
                                    }
                                },
                                "required": ["strings"],
                                "additionalProperties": False,
                            },
                        },
                    },
                )
                db_keyword_assistant = AssistantModel(
                    id=keyword_assistant_data.id,
                    name=keyword_assistant_data.name,
                    instructions=keyword_assistant_data.instructions,
                    model=keyword_assistant_data.model,
                )
                db.add(db_keyword_assistant)
                db.commit()
                db.refresh(db_keyword_assistant)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        pre_process_assistant_entry = db.query(AssistantModel).filter(
            AssistantModel.name == "Preprocess Assistant"
        )
        if not pre_process_assistant_entry.first():
            try:
                pre_process_assistant_data = ai_service.create_assistant(
                    name="Preprocess Assistant",
                    instructions=settings.PREPROCESS_INSTRUCTION,
                    model="gpt-4o-mini",
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "string_schema",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "description": "A string value.",
                                    }
                                },
                                "required": ["value"],
                                "additionalProperties": False,
                            },
                        },
                    },
                )
                db_pre_process_assistant = AssistantModel(
                    id=pre_process_assistant_data.id,
                    name=pre_process_assistant_data.name,
                    instructions=pre_process_assistant_data.instructions,
                    model=pre_process_assistant_data.model,
                )
                db.add(db_pre_process_assistant)
                db.commit()
                db.refresh(db_pre_process_assistant)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        self_assessment_assistant_entry = db.query(AssistantModel).filter(
            AssistantModel.name == "Self Assessment Assistant"
        )
        if not self_assessment_assistant_entry.first():
            try:
                self_assessment_assistant_data = ai_service.create_assistant(
                    name="Self Assessment Assistant",
                    instructions=settings.SELF_ASSESSMENT_INSTRUCTION,
                    model="gpt-4o-mini",
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "fetch_job_description_1",
                                "description": "Retrieve the job description",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "fetch_candidate_cv_1",
                                "description": "Retrieve the candidate's CV",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "fetch_ai_analysis",
                                "description": "Fetches AI-generated analysis without any parameters",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        },
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "questions_scale",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "questions": {
                                        "type": "array",
                                        "description": "A list of questions that will be answered on a scale of 1-10.",
                                        "items": {
                                            "type": "string",
                                            "description": "A question to be rated on a scale of 1-10.",
                                        },
                                    }
                                },
                                "required": ["questions"],
                                "additionalProperties": False,
                            },
                        },
                    },
                )
                db_self_assessment_assistant = AssistantModel(
                    id=self_assessment_assistant_data.id,
                    name=self_assessment_assistant_data.name,
                    instructions=self_assessment_assistant_data.instructions,
                    model=self_assessment_assistant_data.model,
                )
                db.add(db_self_assessment_assistant)
                db.commit()
                db.refresh(db_self_assessment_assistant)

                for tool in self_assessment_assistant_data.tools:
                    tool_entry = (
                        db.query(ToolModel)
                        .filter(
                            ToolModel.assistant_id == db_self_assessment_assistant.id,
                            ToolModel.type == tool.type,
                        )
                        .filter(
                            cast(ToolModel.function_definition, JSONB)
                            == json.dumps(tool.function.model_dump())
                            if tool.type == "function"
                            else true()
                        )
                        .first()
                    )

                    if not tool_entry:
                        db_tool = ToolModel(
                            id=(
                                tool.function.name
                                if tool.type == "function"
                                else tool.type
                            ),
                            assistant_id=db_self_assessment_assistant.id,
                            type=tool.type,
                            function_definition=(
                                tool.function.model_dump()
                                if tool.type == "function"
                                else None
                            ),
                        )
                        db.add(db_tool)
                        db.commit()
                        db.refresh(db_tool)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        job_assistant_entry = db.query(AssistantModel).filter(
            AssistantModel.name == "Job Assistant"
        )
        if not job_assistant_entry.first():
            try:
                job_assistant_data = ai_service.create_assistant(
                    name="Job Assistant",
                    instructions=settings.JOB_INSTRUCTION,
                    model="gpt-4o-2024-11-20",
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "get_job_text",
                                "description": "Retrieves job text without any parameters",
                                "strict": True,
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                    "required": [],
                                },
                            },
                        }
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "job",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "job_title": {
                                        "type": "string",
                                        "description": "The title of the job position.",
                                    },
                                    "job_description": {
                                        "type": "string",
                                        "description": "A detailed description of the job responsibilities and requirements.",
                                    },
                                    "job_company": {
                                        "type": "string",
                                        "description": "The name of the company offering the job.",
                                    },
                                    "job_location": {
                                        "type": "string",
                                        "description": "The geographical location of the job.",
                                    },
                                },
                                "required": [
                                    "job_title",
                                    "job_description",
                                    "job_company",
                                    "job_location",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                )
                db_job_assistant = AssistantModel(
                    id=job_assistant_data.id,
                    name=job_assistant_data.name,
                    instructions=job_assistant_data.instructions,
                    model=job_assistant_data.model,
                )
                db.add(db_job_assistant)
                db.commit()
                db.refresh(db_job_assistant)

                for tool in job_assistant_data.tools:
                    tool_entry = (
                        db.query(ToolModel)
                        .filter(
                            ToolModel.assistant_id == db_job_assistant.id,
                            ToolModel.type == tool.type,
                        )
                        .filter(
                            cast(ToolModel.function_definition, JSONB)
                            == json.dumps(tool.function.model_dump())
                            if tool.type == "function"
                            else true()
                        )
                        .first()
                    )

                    if not tool_entry:
                        db_tool = ToolModel(
                            id=(
                                tool.function.name
                                if tool.type == "function"
                                else tool.type
                            ),
                            assistant_id=db_job_assistant.id,
                            type=tool.type,
                            function_definition=(
                                tool.function.model_dump()
                                if tool.type == "function"
                                else None
                            ),
                        )
                        db.add(db_tool)
                        db.commit()
                        db.refresh(db_tool)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Assistant(s) created successfully"}


@router.post("/", response_model=AssistantResponse)
def create_assistant(assistant: AssistantCreate, db: Session = Depends(get_db)):
    try:
        # Create Assistant via OpenAI
        assistant_data = ai_service.create_assistant(
            name=assistant.name,
            instructions=assistant.instructions,
            model=assistant.model,
            tools=[tool.model_dump() for tool in assistant.tools],
            response_format=assistant.response_format,
        )

        # Save Assistant in DB
        db_assistant = AssistantModel(
            id=assistant_data.id,
            name=assistant_data.name,
            instructions=assistant_data.instructions,
            model=assistant_data.model,
        )
        db.add(db_assistant)
        db.commit()
        db.refresh(db_assistant)

        return db_assistant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AssistantResponse])
def list_assistants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assistants = ai_service.list_assistants()
    if assistants:
        for assistant in assistants:
            assistant_entry = (
                db.query(AssistantModel)
                .filter(AssistantModel.id == assistant.id)
                .first()
            )

            if not assistant_entry:
                db_assistant = AssistantModel(
                    id=assistant.id,
                    name=assistant.name,
                    instructions=assistant.instructions,
                    model=assistant.model,
                )
                db.add(db_assistant)
                db.commit()
                db.refresh(db_assistant)

                # Process tools for the new assistant
            for tool in assistant.tools:
                tool_entry = (
                    db.query(ToolModel)
                    .filter(
                        ToolModel.assistant_id == assistant_entry.id,
                        ToolModel.type == tool.type,
                    )
                    .filter(
                        cast(ToolModel.function_definition, String)
                        == json.dumps(tool.function.model_dump())
                        if tool.type == "function"
                        else None
                    )
                    .first()
                )

                if not tool_entry:
                    db_tool = ToolModel(
                        id=(
                            tool.function.name if tool.type == "function" else tool.type
                        ),
                        assistant_id=assistant_entry.id,
                        type=tool.type,
                        function_definition=(
                            tool.function.model_dump()
                            if tool.type == "function"
                            else None
                        ),
                    )
                    db.add(db_tool)
                    db.commit()
                    db.refresh(db_tool)

    # Fetch and return paginated list of assistants
    assistants = db.query(AssistantModel).offset(skip).limit(limit).all()
    return assistants


@router.get("/{assistant_id}", response_model=AssistantResponse)
def get_assistant(assistant_id: str, db: Session = Depends(get_db)):
    assistant = (
        db.query(AssistantModel).filter(AssistantModel.id == assistant_id).first()
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant
