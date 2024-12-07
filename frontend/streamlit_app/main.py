import re

import streamlit as st
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time

API_BASE_URL = "http://ats_backend:8000/api/v1"

st.set_page_config(page_title="Applicant ATS", layout="wide")

st.title("Applicant Tracking System for Applicants")

menu = [
    "Upload CV",
    "View Analysis",
    "Job Management",
    "Assistant Management",
    "Start Analysis",
    "Interview Prep",
]
choice = st.sidebar.selectbox("Menu", menu)


def get_cvs():
    try:
        response = requests.get(f"{API_BASE_URL}/cv/list")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch CVs: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching CVs: {e}")
        return []


def get_analysis(cv_id: int, job_id: int):
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/results/list/{cv_id}/{job_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch analysis: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching analysis: {e}")
        return []


def get_jobs():
    try:
        response = requests.get(f"{API_BASE_URL}/jobs/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch Jobs: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching Jobs: {e}")
        return []


def get_assistants():
    try:
        response = requests.get(f"{API_BASE_URL}/assistants/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch Assistants: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching Assistants: {e}")
        return []


def get_conversations():
    try:
        response = requests.get(f"{API_BASE_URL}/conversations/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch Conversations: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching Conversations: {e}")
        return []


def get_messages(conversation_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages"
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch Messages: {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching Messages: {e}")
        return []


def get_conversation(conversation_id):
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/conversation/{conversation_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch conversation: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while fetching conversation: {e}")
        return None


def initiate_run(conversation_id):
    try:
        response = requests.post(f"{API_BASE_URL}/runs/{conversation_id}/run")
        if response.status_code == 200:
            run = response.json()
            return run
        else:
            st.error(f"Failed to initiate run: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while initiating run: {e}")
        return None


def poll_run(conversation_id, run_id):
    run_status = "pending"

    status_placeholder = st.empty()
    while run_status not in ["completed", "failed", "cancelled"]:
        time.sleep(2)  # Polling interval
        response = requests.get(f"{API_BASE_URL}/runs/{conversation_id}/run/{run_id}")
        if response.status_code == 200:
            run = response.json()
            run_status = run["status"]
            status_placeholder.write(
                f"Run Status: {run_status} - Updated at: {run['updated_at']}"
            )
        else:
            st.error(f"Failed to poll run status: {response.text}")
            break
    return run_status


def add_initial_message(conversation_id, content="Follow your instructions."):
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            json={
                "conversation_id": conversation_id,
                "role": "user",
                "content": content,
            },
        )
        if response.status_code == 200:
            st.write("User message added.")
        else:
            st.error(f"Failed to add user message: {response.text}")
    except Exception as e:
        st.error(f"An error occurred while adding user message: {e}")


if choice == "Upload CV":
    st.header("Upload Your CV")
    uploaded_file = st.file_uploader("Choose a LaTeX file", type=["tex", "pdf"])
    if uploaded_file is not None:
        if st.button("Upload CV"):
            mime_type = (
                "application/pdf"
                if uploaded_file.name.endswith(".pdf")
                else "text/x-tex"
            )
            files = {"file": (uploaded_file.name, uploaded_file, mime_type)}
            try:
                response = requests.post(f"{API_BASE_URL}/cv/upload", files=files)
                if response.status_code == 200:
                    st.success("CV uploaded and processed successfully!")
                    cv_info = response.json()
                    st.write(
                        {
                            "CV ID": cv_info["id"],
                            "Filename": cv_info["filename"],
                            "Uploaded At": cv_info["uploaded_at"],
                        }
                    )
                else:
                    st.error(f"Failed to upload CV: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

elif choice == "View Analysis":
    st.header("View Analysis Results")
    cvs = get_cvs()
    jobs = get_jobs()

    if not cvs:
        st.warning("No CVs available. Please upload a CV first.")
    if not jobs:
        st.warning("No Job Postings available. Please add a job first.")

    if cvs and jobs:
        cv_options = {f"{cv['filename']} (ID: {cv['id']})": cv["id"] for cv in cvs}
        selected_cv = st.selectbox("Select CV", list(cv_options.keys()))
        cv_id = cv_options[selected_cv]

        job_options = {
            f"{job['title']} at {job['company']} (ID: {job['id']})": job["id"]
            for job in jobs
        }
        selected_job = st.selectbox("Select Job", list(job_options.keys()))
        job_id = job_options[selected_job]

        if cv_id and job_id:
            analysis = get_analysis(cv_id, job_id)

            if analysis:
                selected_analysis = st.selectbox("Select Analysis", analysis)
                analysis_id = selected_analysis

                if "analysis_data" not in st.session_state:
                    st.session_state.analysis_data = None

                if "conversation_data" not in st.session_state:
                    st.session_state.conversation_data = None

                if "run_status" not in st.session_state:
                    st.session_state.run_status = None

                get_analysis_button = st.button("Get Analysis")

                if get_analysis_button:
                    st.session_state.analysis_data = None
                    st.session_state.conversation_data = None
                    st.session_state.run_status = None
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/analysis/results/{cv_id}/{job_id}/{analysis_id}"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.analysis_data = data
                        else:
                            st.error(f"Failed to retrieve analysis: {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

                if st.session_state.analysis_data:
                    data = st.session_state.analysis_data
                    st.write("**Analysis Results:**")
                    st.write(f"**Keyword Match Score:** {data['keyword_match_score']}%")
                    st.write(
                        f"**BERT Similarity Score:** {data['bert_similarity_score']}%"
                    )
                    st.write(
                        f"**Cosine Similarity Score:** {data['cosine_similarity_score']}%"
                    )
                    st.write(
                        f"**Jaccard Similarity Score:** {data['jaccard_similarity_score']}%"
                    )
                    st.write(
                        f"**NER Similarity Score:** {data['ner_similarity_score']}%"
                    )
                    st.write(f"**LSA Analysis Score:** {data['lsa_analysis_score']}%")
                    st.write(f"**Aggregated Score:** {data['aggregated_score']}%")

                    # Visualization
                    scores = {
                        "Keyword Match": data["keyword_match_score"],
                        "BERT Similarity": data["bert_similarity_score"],
                        "Cosine Similarity": data["cosine_similarity_score"],
                        "Jaccard Similarity": data["jaccard_similarity_score"],
                        "NER Similarity": data["ner_similarity_score"],
                        "LSA Analysis": data["lsa_analysis_score"],
                    }

                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(
                        x=list(scores.keys()),
                        y=list(scores.values()),
                        palette="viridis",
                        ax=ax,
                    )
                    ax.set_ylim(0, 100)
                    ax.set_ylabel("Score (%)")
                    ax.set_title("Detailed Analysis Scores")
                    st.pyplot(fig)

                    st.sidebar.subheader("Conversation History")
                    # Optionally, display conversation history
                    conversation_id = data.get(
                        "conversation_id"
                    )  # Ensure AnalysisResult includes conversation_id
                    if conversation_id:
                        messages = get_messages(conversation_id)
                        ai_response = None
                        if messages:
                            for msg in messages:
                                if msg["role"] == "user":
                                    st.sidebar.markdown(f"**You:** {msg['content']}")
                                elif msg["role"] == "assistant":
                                    try:
                                        ai_response = json.loads(msg["content"])
                                        st.sidebar.markdown(
                                            f"**AI Assistant:** {ai_response}"
                                        )
                                    except json.JSONDecodeError:
                                        ai_response = msg["content"]
                                        st.sidebar.markdown(
                                            f"**AI Assistant:** {ai_response}"
                                        )

                            if not ai_response:
                                st.sidebar.warning(
                                    "No AI Assistant responses available."
                                )

                            assistants = get_assistants()

                            if not assistants:
                                st.sidebar.warning(
                                    "No Assistants available. Please add an Assistant first."
                                )

                            if assistants and ai_response:
                                assistant_options = {
                                    f"{assistant['name']} (ID: {assistant['id']})": assistant[
                                        "id"
                                    ]
                                    for assistant in assistants
                                }
                                selected_assistant = st.sidebar.selectbox(
                                    "Select Assistant",
                                    list(assistant_options.keys()),
                                    index=3,
                                )
                                assistant_id = assistant_options[selected_assistant]

                                self_assessment_button = st.sidebar.button(
                                    "Start Self Assessment",
                                )

                                if self_assessment_button:
                                    analysis_data = {
                                        "cv_id": cv_id,
                                        "job_id": job_id,
                                        "assistant_id": assistant_id,
                                        "analysis_id": analysis_id,
                                    }
                                    try:
                                        response = requests.post(
                                            f"{API_BASE_URL}/conversations",
                                            json=analysis_data,
                                        )

                                        if response.status_code == 200:
                                            conversation = response.json()
                                            st.session_state.conversation_data = (
                                                conversation
                                            )
                                        else:
                                            st.sidebar.error(
                                                f"Failed to initiate conversation: {response.text}"
                                            )
                                    except Exception as e:
                                        st.sidebar.error(f"An error occurred: {e}")

                if (
                    st.session_state.conversation_data
                    and st.session_state.run_status is None
                ):
                    conversation = st.session_state.conversation_data
                    st.sidebar.success("Conversation initiated successfully!")
                    st.sidebar.write(
                        {
                            "Conversation ID": conversation["id"],
                            "CV ID": conversation["cv_id"],
                            "Job ID": conversation["job_id"],
                            "Assistant ID": conversation["assistant_id"],
                            "Started At": conversation["started_at"],
                        }
                    )

                    # Add initial user message
                    user_message = "Follow your instructions."
                    add_msg_response = requests.post(
                        f"{API_BASE_URL}/conversations/{conversation['id']}/messages",
                        json={
                            "conversation_id": conversation["id"],
                            "role": "user",
                            "content": user_message,
                        },
                    )
                    if add_msg_response.status_code == 200:
                        st.sidebar.write("User message added.")
                    else:
                        st.sidebar.error(
                            f"Failed to add user message: {add_msg_response.text}"
                        )

                    run_response = initiate_run(conversation["id"])
                    if run_response:
                        run_id = run_response["id"]
                        st.sidebar.write(
                            {
                                "Run ID": run_response["id"],
                                "Status": run_response["status"],
                                "Created At": run_response["created_at"],
                                "Updated At": run_response["updated_at"],
                            }
                        )

                        # Poll for run completion
                        run_status = poll_run(conversation["id"], run_id)

                        if run_status == "completed":
                            st.session_state.run_status = run_status
                        else:
                            st.sidebar.error("Analysis failed or is still in progress.")

                if st.session_state.run_status == "completed":
                    conversation = st.session_state.conversation_data
                    st.sidebar.success("Analysis completed successfully!")
                    # Fetch conversation messages
                    messages = get_messages(conversation["id"])
                    for msg in messages:
                        if msg["role"] == "assistant":
                            try:
                                questions = json.loads(msg["content"])

                                for question in questions["questions"]:
                                    st.sidebar.slider(
                                        question,
                                        1,
                                        10,
                                        5,
                                    )

                            except json.JSONDecodeError:
                                st.sidebar.markdown(
                                    f"**AI Assistant:** {msg['content']}"
                                )

elif choice == "Job Management":
    st.header("Manage Job Postings")
    sub_menu = st.sidebar.selectbox(
        "Job Menu", ["View Jobs", "Add Job", "Update Job", "Delete Job"]
    )

    if sub_menu == "View Jobs":
        st.subheader("All Job Postings")
        try:
            response = requests.get(f"{API_BASE_URL}/jobs/")
            if response.status_code == 200:
                jobs = response.json()
                if not jobs:
                    st.info("No job postings available.")
                else:
                    for job in jobs:
                        st.markdown(f"### {job['title']}")
                        st.markdown(f"**Company:** {job['company']}")
                        st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                        st.markdown(f"**Description:** {job['description']}")
                        st.markdown(f"**Posted At:** {job['posted_at']}")
                        st.markdown(f"**Status:** {job['status']}")
                        st.markdown(f"**URL:** {job.get('url', 'N/A')}")
                        st.markdown("---")
            else:
                st.error(f"Failed to retrieve jobs: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    elif sub_menu == "Add Job":
        st.subheader("Add a New Job Posting")
        with st.form("add_job_form"):
            title = st.text_input("Job Title")
            status = st.selectbox(
                "Status",
                [
                    "To be submitted",
                    "Submitted",
                    "Interview",
                    "Offer",
                    "Rejected",
                    "Hired",
                ],
            )
            company = st.text_input("Company")
            location = st.text_input("Location")
            description = st.text_area("Job Description")
            url = st.text_input("Job URL")
            submitted = st.form_submit_button("Add Job")
            if submitted:
                if url:
                    if not re.match(
                        r"^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$",
                        url,
                    ):
                        st.error("Please enter a valid URL.")
                if not url and (not title or not company or not description):
                    st.error("Please fill in all required fields.")
                elif not url or not re.match(
                    r"^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+$",
                    url,
                ):
                    st.error("Please enter a valid URL.")
                else:
                    job_data = {
                        "title": title,
                        "status": status,
                        "company": company,
                        "location": location,
                        "description": description,
                        "url": url,
                    }
                    try:
                        response = requests.post(f"{API_BASE_URL}/jobs/", json=job_data)
                        if response.status_code == 201:
                            st.success("Job posting added successfully!")
                            st.write(response.json())
                        else:
                            st.error(f"Failed to add job: {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    elif sub_menu == "Update Job":
        st.subheader("Update an Existing Job Posting")
        jobs = get_jobs()
        if jobs:
            job_options = {
                f"{job['title']} at {job['company']} (ID: {job['id']})": job["id"]
                for job in jobs
            }
            selected_job = st.selectbox(
                "Select Job to Update", list(job_options.keys())
            )
            job_id = job_options[selected_job]

            # Fetch job details
            try:
                response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
                if response.status_code == 200:
                    job = response.json()
                    with st.form("update_job_form"):
                        title = st.text_input("Job Title", value=job["title"])
                        status = st.selectbox(
                            "Status",
                            [
                                "To be submitted",
                                "Submitted",
                                "Interview",
                                "Offer",
                                "Rejected",
                                "Hired",
                            ],
                            index=[
                                "To be submitted",
                                "Submitted",
                                "Interview",
                                "Offer",
                                "Rejected",
                                "Hired",
                            ].index(job["status"]),
                        )
                        company = st.text_input("Company", value=job["company"])
                        location = st.text_input(
                            "Location", value=job.get("location", "")
                        )
                        description = st.text_area(
                            "Job Description", value=job["description"]
                        )
                        submitted = st.form_submit_button("Update Job")
                        if submitted:
                            update_data = {
                                "title": title,
                                "status": status,
                                "company": company,
                                "location": location,
                                "description": description,
                            }
                            update_response = requests.put(
                                f"{API_BASE_URL}/jobs/{job_id}", json=update_data
                            )
                            if update_response.status_code == 200:
                                st.success("Job posting updated successfully!")
                                st.write(update_response.json())
                            else:
                                st.error(
                                    f"Failed to update job: {update_response.text}"
                                )
                else:
                    st.error(f"Job not found: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.info("No job postings available to update.")

    elif sub_menu == "Delete Job":
        st.subheader("Delete a Job Posting")
        jobs = get_jobs()
        if jobs:
            job_options = {
                f"{job['title']} at {job['company']} (ID: {job['id']})": job["id"]
                for job in jobs
            }
            selected_job = st.selectbox(
                "Select Job to Delete", list(job_options.keys())
            )
            job_id = job_options[selected_job]
            if st.button("Delete Job"):
                try:
                    response = requests.delete(f"{API_BASE_URL}/jobs/{job_id}")
                    if response.status_code == 204:
                        st.success("Job posting deleted successfully!")
                    else:
                        st.error(f"Failed to delete job: {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.info("No job postings available to delete.")

elif choice == "Assistant Management":
    st.header("Manage Assistants")
    sub_menu = st.sidebar.selectbox(
        "Assistant Menu", ["View Assistants", "Add Assistant"]
    )

    if sub_menu == "View Assistants":
        st.subheader("All Assistants")
        try:
            assistants = get_assistants()
            if not assistants:
                response = requests.post(f"{API_BASE_URL}/assistants/initiate")
                if response.status_code == 200:
                    st.info("Assistant initiated successfully.")
                else:
                    st.error(f"Failed to initiate assistant: {response.text}")
                    st.info(
                        "Please check your API key and try again. If the problem persists, please contact support."
                    )
            else:
                for assistant in assistants:
                    st.markdown(f"### {assistant['name']} (ID: {assistant['id']})")
                    st.markdown(f"**Model:** {assistant['model']}")
                    st.markdown(f"**Instructions:** {assistant['instructions']}")
                    st.markdown("**Tools:**")
                    for tool in assistant["tools"]:
                        tool_info = f"- **Type:** {tool['type']}"
                        if tool["type"] == "function":
                            tool_info += f", **Function Name:** {tool['id']}"
                        st.markdown(tool_info)
                    st.markdown("---")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    elif sub_menu == "Add Assistant":
        st.subheader("Add a New Assistant")
        with st.form("add_assistant_form"):
            name = st.text_input("Assistant Name")
            instructions = st.text_area("Assistant Instructions")
            model = st.selectbox(
                "Model", ["gpt-4o", "gpt-4o-mini"]
            )  # Update models as needed

            # Define tools
            st.markdown("**Define Tools**")
            tool_type = st.selectbox(
                "Tool Type", ["function", "code_interpreter"], key="tool_type"
            )
            tool_name = st.text_input("Tool Name", key="tool_name")
            tool_description = st.text_area("Tool Description", key="tool_description")
            tool_parameters = st.text_area(
                "Tool Parameters (JSON)", key="tool_parameters"
            )

            submitted = st.form_submit_button("Add Assistant")
            if submitted:
                if not name or not instructions or not model:
                    st.error("Please fill in all required fields.")
                else:
                    # Parse tools
                    tools = []
                    if tool_type and tool_name and tool_description:
                        try:
                            if tool_type == "function":
                                parameters = (
                                    json.loads(tool_parameters)
                                    if tool_parameters
                                    else {}
                                )
                                tool = {
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "description": tool_description,
                                        "parameters": parameters,
                                        "strict": True,
                                    },
                                }
                            elif tool_type == "code_interpreter":
                                tool = {"type": "code_interpreter", "function": None}
                            tools.append(tool)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON for tool parameters.")

                    assistant_data = {
                        "name": name,
                        "instructions": instructions,
                        "model": model,
                        "tools": tools,
                    }

                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/assistants/", json=assistant_data
                        )
                        if response.status_code == 200:
                            st.success("Assistant created successfully!")
                            st.write(response.json())
                        else:
                            st.error(f"Failed to create assistant: {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

elif choice == "Start Analysis":
    st.header("Start CV and Job Analysis")
    with st.form("start_analysis_form"):
        assistants = get_assistants()
        cvs = get_cvs()
        jobs = get_jobs()

        if not assistants:
            st.warning("No Assistants available. Please add an Assistant first.")
        if not cvs:
            st.warning("No CVs available. Please upload a CV first.")
        if not jobs:
            st.warning("No Job Postings available. Please add a job first.")

        if assistants and cvs and jobs:
            assistant_options = {
                f"{assistant['name']} (ID: {assistant['id']})": assistant["id"]
                for assistant in assistants
            }
            selected_assistant = st.selectbox(
                "Select Assistant", list(assistant_options.keys())
            )
            assistant_id = assistant_options[selected_assistant]

            cv_options = {f"{cv['filename']} (ID: {cv['id']})": cv["id"] for cv in cvs}
            selected_cv = st.selectbox("Select CV", list(cv_options.keys()))
            cv_id = cv_options[selected_cv]

            job_options = {
                f"{job['title']} at {job['company']} (ID: {job['id']})": job["id"]
                for job in jobs
            }
            selected_job = st.selectbox("Select Job", list(job_options.keys()))
            job_id = job_options[selected_job]

            submitted = st.form_submit_button("Start Analysis")
            if submitted:
                analysis_data = {
                    "cv_id": cv_id,
                    "job_id": job_id,
                    "assistant_id": assistant_id,
                }
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/conversations/", json=analysis_data
                    )
                    if response.status_code == 200:
                        conversation = response.json()
                        st.success("Conversation initiated successfully!")
                        st.write(
                            {
                                "Conversation ID": conversation["id"],
                                "CV ID": conversation["cv_id"],
                                "Job ID": conversation["job_id"],
                                "Assistant ID": conversation["assistant_id"],
                                "Started At": conversation["started_at"],
                            }
                        )

                        # Add initial user message
                        user_message = "Follow your instructions."
                        add_msg_response = requests.post(
                            f"{API_BASE_URL}/conversations/{conversation['id']}/messages",
                            json={
                                "conversation_id": conversation["id"],
                                "role": "user",
                                "content": user_message,
                            },
                        )
                        if add_msg_response.status_code == 200:
                            st.write("User message added.")
                        else:
                            st.error(
                                f"Failed to add user message: {add_msg_response.text}"
                            )

                        # Run Assistant
                        run_response = initiate_run(conversation["id"])
                        if run_response:
                            run_id = run_response["id"]
                            st.write(
                                {
                                    "Run ID": run_response["id"],
                                    "Status": run_response["status"],
                                    "Created At": run_response["created_at"],
                                    "Updated At": run_response["updated_at"],
                                }
                            )

                            # Poll for run completion
                            run_status = poll_run(conversation["id"], run_id)

                            if run_status == "completed":
                                st.success("Analysis completed successfully!")
                                # Fetch conversation messages
                                messages = get_messages(conversation["id"])
                                for msg in messages:
                                    if msg["role"] == "user":
                                        st.markdown(f"**You:** {msg['content']}")
                                    elif msg["role"] == "assistant":
                                        try:
                                            ai_response = json.loads(msg["content"])
                                            st.markdown(
                                                f"**AI Assistant:** {ai_response}"
                                            )
                                        except json.JSONDecodeError:
                                            st.markdown(
                                                f"**AI Assistant:** {msg['content']}"
                                            )
                            else:
                                st.error("Analysis failed or is still in progress.")
                    else:
                        st.error(f"Failed to initiate conversation: {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

elif choice == "Interview Prep":
    st.header("Prepare for Interviews")
    st.write("Coming soon!")
