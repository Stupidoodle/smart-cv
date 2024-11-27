import streamlit as st
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

API_BASE_URL = "http://ats_backend:8000/api/v1"

st.set_page_config(page_title="Applicant ATS", layout="wide")

st.title("Applicant Tracking System for Applicants")

menu = ["Upload CV", "View Analysis", "Job Management", "Start Analysis", "Interview Prep"]
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

if choice == "Upload CV":
    st.header("Upload Your CV")
    uploaded_file = st.file_uploader("Choose a LaTeX file", type="tex")
    if uploaded_file is not None:
        if st.button("Upload CV"):
            files = {"file": (uploaded_file.name, uploaded_file, "text/x-tex")}
            try:
                response = requests.post(f"{API_BASE_URL}/cv/upload", files=files)
                if response.status_code == 200:
                    st.success("CV uploaded and processed successfully!")
                    cv_info = response.json()
                    st.write({
                        "CV ID": cv_info["id"],
                        "Filename": cv_info["filename"],
                        "Uploaded At": cv_info["uploaded_at"]
                    })
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
        # Create a mapping of CV descriptions
        cv_options = {f"{cv['filename']} (ID: {cv['id']})": cv['id'] for cv in cvs}
        selected_cv = st.selectbox("Select CV", list(cv_options.keys()))
        cv_id = cv_options[selected_cv]

        # Create a mapping of Job descriptions
        job_options = {
            f"{job['title']} at {job['company']} (ID: {job['id']})": job['id'] for job
            in jobs}
        selected_job = st.selectbox("Select Job", list(job_options.keys()))
        job_id = job_options[selected_job]

    if st.button("Get Analysis"):
        try:
            response = requests.get(f"{API_BASE_URL}/analysis/results/{cv_id}/{job_id}")
            if response.status_code == 200:
                data = response.json()
                st.write("**Analysis Results:**")
                st.write(f"**Keyword Match Score:** {data['keyword_match_score']}%")
                st.write(f"**BERT Similarity Score:** {data['bert_similarity_score']}%")
                st.write(f"**Cosine Similarity Score:** {data['cosine_similarity_score']}%")
                st.write(f"**Jaccard Similarity Score:** {data['jaccard_similarity_score']}%")
                st.write(f"**NER Similarity Score:** {data['ner_similarity_score']}%")
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
                sns.barplot(x=list(scores.keys()), y=list(scores.values()), palette="viridis", ax=ax)
                ax.set_ylim(0, 100)
                ax.set_ylabel("Score (%)")
                ax.set_title("Detailed Analysis Scores")
                st.pyplot(fig)
            else:
                st.error(f"Failed to retrieve analysis: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif choice == "Job Management":
    st.header("Manage Job Postings")
    sub_menu = st.sidebar.selectbox("Job Menu", ["View Jobs", "Add Job", "Update Job", "Delete Job"])

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
                        st.markdown("---")
            else:
                st.error(f"Failed to retrieve jobs: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    elif sub_menu == "Add Job":
        st.subheader("Add a New Job Posting")
        with st.form("add_job_form"):
            title = st.text_input("Job Title")
            company = st.text_input("Company")
            location = st.text_input("Location")
            description = st.text_area("Job Description")
            submitted = st.form_submit_button("Add Job")
            if submitted:
                if not title or not company or not description:
                    st.error("Please fill in all required fields.")
                else:
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description
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
            job_options = {f"{job['title']} (ID: {job['id']})": job['id'] for job in jobs}
            selected_job = st.selectbox("Select Job to Update", list(job_options.keys()))
            job_id = job_options[selected_job]

            # Fetch job details
            try:
                response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
                if response.status_code == 200:
                    job = response.json()
                    with st.form("update_job_form"):
                        title = st.text_input("Job Title", value=job['title'])
                        company = st.text_input("Company", value=job['company'])
                        location = st.text_input("Location", value=job.get('location', ''))
                        description = st.text_area("Job Description", value=job['description'])
                        submitted = st.form_submit_button("Update Job")
                        if submitted:
                            update_data = {
                                "title": title,
                                "company": company,
                                "location": location,
                                "description": description
                            }
                            update_response = requests.put(f"{API_BASE_URL}/jobs/{job_id}", json=update_data)
                            if update_response.status_code == 200:
                                st.success("Job posting updated successfully!")
                                st.write(update_response.json())
                            else:
                                st.error(f"Failed to update job: {update_response.text}")
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
            job_options = {f"{job['title']} (ID: {job['id']})": job['id'] for job in jobs}
            selected_job = st.selectbox("Select Job to Delete", list(job_options.keys()))
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

elif choice == "Start Analysis":
    st.header("Start CV and Job Analysis")
    with st.form("start_analysis_form"):
        cvs = get_cvs()
        jobs = get_jobs()

        if not cvs:
            st.warning("No CVs available. Please upload a CV first.")
        if not jobs:
            st.warning("No Job Postings available. Please add a job first.")

        if cvs and jobs:
            # Create a mapping of CV descriptions
            cv_options = {f"{cv['filename']} (ID: {cv['id']})": cv['id'] for cv in cvs}
            selected_cv = st.selectbox("Select CV", list(cv_options.keys()))
            cv_id = cv_options[selected_cv]

            # Create a mapping of Job descriptions
            job_options = {f"{job['title']} at {job['company']} (ID: {job['id']})": job['id'] for job in jobs}
            selected_job = st.selectbox("Select Job", list(job_options.keys()))
            job_id = job_options[selected_job]

            submitted = st.form_submit_button("Start Analysis")
            if submitted:
                analysis_data = {
                    "cv_id": cv_id,
                    "job_id": job_id
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/analysis/start", json=analysis_data)
                    if response.status_code == 201:
                        st.success("Analysis started successfully!")
                        analysis = response.json()
                        st.write("**Analysis Results:**")
                        st.write(f"**Keyword Match Score:** {analysis['keyword_match_score']}%")
                        st.write(f"**BERT Similarity Score:** {analysis['bert_similarity_score']}%")
                        st.write(f"**Cosine Similarity Score:** {analysis['cosine_similarity_score']}%")
                        st.write(f"**Jaccard Similarity Score:** {analysis['jaccard_similarity_score']}%")
                        st.write(f"**NER Similarity Score:** {analysis['ner_similarity_score']}%")
                        st.write(f"**LSA Analysis Score:** {analysis['lsa_analysis_score']}%")
                        st.write(f"**Aggregated Score:** {analysis['aggregated_score']}%")

                        # Visualization
                        scores = {
                            "Keyword Match": analysis["keyword_match_score"],
                            "BERT Similarity": analysis["bert_similarity_score"],
                            "Cosine Similarity": analysis["cosine_similarity_score"],
                            "Jaccard Similarity": analysis["jaccard_similarity_score"],
                            "NER Similarity": analysis["ner_similarity_score"],
                            "LSA Analysis": analysis["lsa_analysis_score"],
                        }

                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(x=list(scores.keys()), y=list(scores.values()), palette="viridis", ax=ax)
                        ax.set_ylim(0, 100)
                        ax.set_ylabel("Score (%)")
                        ax.set_title("Detailed Analysis Scores")
                        st.pyplot(fig)
                    else:
                        st.error(f"Failed to start analysis: {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please ensure at least one CV and one Job Posting are available.")

elif choice == "Interview Prep":
    st.header("Prepare for Interviews")
    st.write("Coming soon!")
