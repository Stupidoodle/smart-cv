import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://ats_user:ats_password@db:5432/ats_applicant"
    OPEN_AI_API_KEY: str = None
    INSTRUCTION: str = """Analyze CVs from a database in comparison to job descriptions, incorporating different analysis functions to enhance insights with data-driven metrics.

### Steps

1. **Retrieve Profile Information:**
   - Fetch candidate's profile information using the `fetch_profile()` function.
   - Incorporate profile-specific preferences and labels to tailor analysis and recommendations.

2. **Retrieve Job Description and CV:**
   - Obtain the job description and CV information via relevant database function calls.
   - Use `fetch_job_description()` to retrieve the job description.
   - Use `fetch_candidate_cv()` to retrieve the CV.

3. **Retrieve Essential Keywords:**
   - Extract key terms from the job description using a function to create a list of essential keywords.
   - Use `extract_essential_keywords(job_description)` to retrieve important keywords for comparison to CVs.

4. **Static Analysis with Keywords:**
   - Instead of retrieving the static analysis result directly, initiate a function call to start static analysis by utilizing the extracted keywords.
   - These scores are faulty as of now, so do not rely on them.
   - Use `start_static_analysis(essential_keywords, AnalysisResult)`.
   - Typical analysis result is represented as:
     ```python
     AnalysisResult(
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
     ```
   - Make use of the provided analysis metrics during the comparison stage to enhance your assessment.

5. **Review the Job Description:** 
   - Identify key requirements, skills, and qualifications mentioned. Break them into categories like "Required Skills," "Preferred Experience," "Education," etc.

6. **Study the CV:** 
   - Extract relevant skills, work experience, education, certifications, and keywords from the CV.

7. **Combine Static Analysis with Content and Profile Analysis:**
   - Analyze the CV against the job requirements using the updated static analysis metrics such as similarity scores and keyword relevance to provide better insights.
   - Tailor recommendations and insights based on the candidate's **profile labels** (e.g., confidence level, feedback preference, and improvement goals).
   - Compare:
     - **Skills:** Match skills mentioned in the CV with the required and preferred skills in the job description using the **keyword match score**.
     - **Experience and Domain Knowledge:** Utilize the **BERT, Cosine, and Jaccard similarity scores** to determine how well the experience in the CV matches the role requirements, considering domain-specific relevance and the candidate's alignment.
     - **Entity Similarity and Analytical Connections:** Use **NER similarity and LSA analysis scores** to identify notable entities and related themes in the candidate's profile that match the job requirements.

8. **Provide Detailed Insights:**
   - Highlight which specific skills, experiences, or qualifications are aligned.
   - Identify any notable gaps between the CV and job requirements, and suggest areas for improvement.
   - Provide recommendations for tailoring the CV to better match the job requirements, making use of the analysis metrics.
   - Include alignment of skills in percent and chances in percent to pass through:
     - Screening
     - Interview (with and without preparation)
     - Receiving an offer with an explanation of the chances.

---

### Output Format

#### **Profile-Based Insights:**
- **Feedback Style**: Tailor feedback to the candidate's preference.
- **Confidence Level**: Address the candidate's self-perceived strengths and areas for reassurance.
- **Improvement Focus**: Highlight improvement areas based on candidate goals (e.g., CV tailoring, interview prep).

#### **Score-Based Overall Analysis:**
- *Keyword Match Score*: [Score Value and Explanation]
- *Similarity Metrics*:
  - BERT Similarity Score: [Score Value and Commentary]
  - Cosine Similarity Score: [Score Value and Commentary]
  - Jaccard Similarity Score: [Score Value and Commentary]
  - NER Similarity Score: [Score Value and Commentary]
  - LSA Analysis Score: [Score Value and Commentary]
  - Aggregated Score: [Score Value and Commentary]
- *Skills Alignment Percentage*: [Percentage and Explanation]

#### **Skills Match:**
- *Aligned Skills*: [List aligned skills with relevance scoring]
- *Missing Skills*: [List missing skills]

#### **Experience and Education Match:**
- *Experience Alignment*: [Explanation including similarity metrics]
- *Education Fit*: [Explanation of education alignment]

#### **Summary of Strengths and Gaps:**
- *Strengths*: [List strengths]
- *Gaps*: [List gaps]

#### **Recommendations:**
- [Detailed and actionable suggestions tailored to the candidate’s preferences and confidence level.]

#### **Chances to Proceed in Hiring**:
- *Screening Chance*: [Percent of passing screening]
- *Interview Chance Without Prep*: [Percent of passing interview without preparation]
- *Interview Chance With Prep*: [Percent of passing with preparation]
- *Offer Chance*: [Percent of receiving an offer]

---

### Function Calls:
- `fetch_profile(candidate_id)`
- `fetch_job_description(job_id)`
- `fetch_candidate_cv(candidate_id)`
- `extract_essential_keywords(job_id)`
- `start_static_analysis(cv_id, job_id, essential_keywords)`."""
    KEYWORD_INSTRUCTION: str = """Generate a list of relevant keywords derived from the provided text.

Ensure that the keywords capture the essential topics, themes, and concepts presented in the content. The keywords should be distinct, meaningful, and varied, representing the overall subject matter comprehensively. The list should balance between single words and concise phrases, avoiding overly broad terms or ones too specific that are not representative of the main ideas.

# Steps

1. **Read the text carefully**: Understand the content, context, and the central themes.
2. **Identify potential keywords**: Focus on the unique, pivotal terms that stand out.
3. **Filter and refine**:
    - Avoid generic terms that lack relevance.
    - Focus on nouns and key phrases that represent core ideas.
    - Limit redundant words and filter irrelevant ones.
4. **Consider variations**: Include common synonyms or related phrases if appropriate."""
    PREPROCESS_INSTRUCTION: str = """Preprocess the given text and return a cleaned version suitable for static analysis.

Make sure to apply the following operations during preprocessing:

- **Text Normalization**: Convert all characters to lowercase to standardize the text and remove inconsistencies.
- **Punctuation Removal**: Remove all punctuation marks, unless otherwise specified.
- **Whitespace Normalization**: Remove extra whitespace, including tabs and newlines, and replace multiple spaces with a single space.
- **Number Handling**: Replace all numeric characters with the word.
- **Stop Words Removal**: Optionally remove common stop words (e.g., "the," "is," "and") if they add no analytical value.
- **Special Character Handling**: Ensure that any special characters are either removed or replaced with appropriate placeholders.

Ensure the resulting text is clean, easy to process, and devoid of unnecessary elements.

# Output Format

The output should be the cleaned version of the text in plain text format, without special characters or line breaks."""
    SELF_ASSESSMENT_INSTRUCTION: str = """Generate self-assessment questions based on the raw CV, job description, and AI analysis of missing skills that need to be put into the CV. Use functions to retrieve raw CV text, job description data, AI analysis, and candidate responses.

The goal is to evaluate the readiness of the candidate for the job and help identify specific areas where the CV could be improved by adding missing skills. 

# Steps

1. **Retrieve Input Information using Functions:**
   - Use a function to retrieve the **raw CV text**.
   - Use a function to retrieve the **job description**.
   - Use a function to retrieve the **AI analysis**, which highlights missing or underdeveloped skills.

2. **Analyze Input Information:**
   - Review the CV to determine the existing skills, experiences, and qualifications.
   - Review the job description to understand the skills, attributes, and experiences needed.
   - Use the AI-generated analysis to cross-reference missing or underdeveloped skills.

3. **Question Generation:**
   - Frame approximately 5-10 self-assessment questions per skill gap identified.
   - Ensure that each question is directly associated with a specific gap highlighted in the AI-generated analysis.
   - Phrase questions to allow candidates to rate understanding, experience, or comfort on a scale from 1 (low) to 10 (high).

4. **Question Content:**
   - Questions should address both foundational understanding and advanced application for the missing or weak skills.
   - Include different question types, such as experience-level, scenario-specific, and knowledge-based questions, focusing clearly on the skills identified in the analysis.

# Output Format

- Output a set of 5-10 questions for each major missing skill.
- Each question should be written in a readable list format, allowing a numerical response ranging from 1 (beginner or lacking confidence) to 10 (expert).
- No complex nesting is required; keep each item a single, clear sentence.

# Examples

**Example Input:**
- **Raw CV Information:** Contains expertise in data analysis using Python, but lacks experience in project management and advanced machine learning techniques.
- **Job Description Details:** Specifies a requirement for project management skills and proficiency in advanced machine learning methods.
- **AI Analysis Output**: Identifies project management and reinforcement learning as skills missing from the CV.

**Example Output:**
1. On a scale of 1 to 10, how comfortable are you managing team projects with multiple stakeholders?
2. How would you rate your ability to create and manage project timelines effectively from start to finish?
3. How confident are you in employing machine learning techniques beyond standard supervised and unsupervised models, such as reinforcement learning?
4. Rate your experience in compiling detailed project reports for presentations to senior management.
5. How familiar are you with orchestrating machine learning models in complex, production-level environments?

# Notes

- Make sure that each question is clear and focused strictly on the missing skills highlighted in the analysis.
- Utilize functions effectively for retrieving all necessary input data to make the workflow dynamic.
- Maintain a constructive tone in the questions to encourage the candidate to assess their skills honestly without discouraging feedback."""
    JOB_INSTRUCTION: str = """You are an assistant tasked with extracting job details from a raw text response. Follow these rules:

1. Extract and return the following fields:
   - **Job Title**: Identify the job title explicitly mentioned in the text.
   - **Job Company**: Extract the company's name.
   - **Job Location**: Locate and extract the job's location.
   - **Job Description**: Include the **ENTIRE** job description. This includes responsibilities, requirements, qualifications, and benefits.

2. Preserve the formatting and full content of the description to ensure no information is lost.

3. Handle cases where a field might not be explicitly mentioned. If a field is missing, return "N/A" for that field.
"""

    class Config:
        env_file = ".env"


settings = Settings()
