import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql://ats_user:ats_password@db:5432/ats_applicant"
    OPEN_AI_API_KEY: str = None
    INSTRUCTION: str = """Analyze CVs from a database in comparison to job descriptions, incorporating different analysis functions to enhance insights with data-driven metrics.

# Steps

1. **Retrieve Job Description and CV:**
   - Obtain the job description and CV information via relevant database function calls.
   - Use `fetch_job_description()` to retrieve the job description.
   - Use `fetch_candidate_cv()` to retrieve the CV.

2. **Retrieve Essential Keywords:**
   - Extract key terms from the job description using a function to create a list of essential keywords.
   - Use `extract_essential_keywords(job_description)` to retrieve important keywords for comparison to CVs.

3. **Static Analysis with Keywords:**
   - Instead of retrieving the static analysis result directly, initiate a function call to start static analysis by utilizing the extracted keywords.
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

4. **Review the Job Description:** 
   - Identify key requirements, skills, and qualifications mentioned. Break them into categories like "Required Skills," "Preferred Experience," "Education," etc.

5. **Study the CV:** 
   - Extract relevant skills, work experience, education, certifications, and keywords from the CV.

6. **Combine Static Analysis with Content Analysis:**
   - Analyze the CV against the job requirements using the updated static analysis metrics such as similarity scores and keyword relevance to provide better insights.
   - Compare:
     - **Skills:** Match skills mentioned in the CV with the required and preferred skills in the job description using the **keyword match score**.
     - **Experience and Domain Knowledge:** Utilize the **BERT, Cosine, and Jaccard similarity scores** to determine how well the experience in the CV matches the role requirements, considering domain-specific relevance and the candidate's alignment.
     - **Entity Similarity and Analytical Connections:** Use **NER similarity and LSA analysis scores** to identify notable entities and related themes in the candidate's profile that match the job requirements.

7. **Provide Detailed Insights:**
   - Highlight which specific skills, experiences, or qualifications are aligned.
   - Identify any notable gaps between the CV and job requirements, and suggest areas for improvement.
   - Provide recommendations for tailoring the CV to better match the job requirements, making use of the analysis metrics.

# Insights to Provide

- **Score-Based Overall Analysis:**
  - *Keyword Match Score*: [Explain how keywords from the CV match the JD and point out key areas]
  - *Similarity Metrics*: [BERT, Cosine, Jaccard, etc. scores for deeper content match insights]

- **Skills Alignment:**
  - *Aligned Skills*: [List skills present in both the JD and CV along with relevant similarity scores]
  - *Missing Skills*: [List skills from the JD missing in the CV]

- **Experience and Education Match:**
  - *Experience Alignment*: [Explain current experience and whether it matches, including similarity metrics; Include notable relevant experience from the CV that aligns directly with the JD.]
  - *Education Fit*: [Explain how the candidate's education matches or doesn't match the job requirements]

- **Summary of Strengths and Gaps:**
  - *Strengths*: [List strengths, skills, or experiences that strongly align with JD]
  - *Gaps*: [List any requirements not matched in the CV]

- **Recommendations:**
  - [Provide specific suggestions for improvements, keeping in mind similarity metrics and using them to guide actionable advice.]

# Output Format

Provide the output in structured text:

- **Score-Based Overall Analysis:**
  - *Keyword Match Score*: [Score Value and Explanation]
  - *Similarity Metrics*:
    - BERT Similarity Score: [Score Value and Commentary]
    - Cosine Similarity Score: [Score Value and Commentary]
    - Jaccard Similarity Score: [Score Value and Commentary]
    - NER Similarity Score: [Score Value and Commentary]
    - LSA Analysis Score: [Score Value and Commentary]
    - Aggregated Score: [Score Value and Commentary]

- **Skills Match:**
  - *Aligned Skills*: [List aligned skills with relevance scoring]
  - *Missing Skills*: [List missing skills]

- **Experience and Education Match:**
  - *Experience Alignment*: [Explanation including similarity metrics]
  - *Education Fit*: [Explanation of education alignment]

- **Summary of Strengths and Gaps:**
  - *Strengths*: [List strengths]
  - *Gaps*: [List gaps]

- **Recommendations:**
  - [Detailed and actionable suggestions]

# Example

**Function Calls:**
- `fetch_job_description(job_id='123')` returns the job description.
- `fetch_candidate_cv(candidate_id='456')` returns the candidate CV.
- `extract_essential_keywords(job_id='123')` extracts essential keywords from the job description.
- `start_static_analysis(cv_id='456', job_id='123', essential_keywords=['Python', 'SQL'])` performs the static analysis.

**Job Description Overview:**
- Required Skills: [Python, SQL, Machine Learning, Data Analysis]
- Preferred Experience: [3+ years working in data science, experience visualizing data, cloud computing exposure]
- Required Education: [Bachelor’s in Computer Science or related field]

**Candidate CV:**
- Skills: [Python, Machine Learning, Data Visualization/Plots, Git]
- Experience: [2 years in data analysis at company X, 1 year in software development]
- Education: [Bachelor’s in Mathematics]

**Static Analysis Result:**
- Keyword Match Score: 0.78
- BERT Similarity Score: 0.88
- Cosine Similarity Score: 0.81
- Jaccard Similarity Score: 0.75
- NER Similarity Score: 0.70
- LSA Analysis Score: 0.80
- Aggregated Score: 0.80

**Analysis:**

- **Score-Based Overall Analysis:**
  - *Keyword Match Score*: 0.78 indicates an above-average keyword matching. Most JD keywords are present, but some key terms like "SQL" are missing.
  - *Similarity Metrics*:
    - **BERT Similarity Score**: 0.88 represents a strong domain-specific alignment.
    - **Cosine Similarity Score**: 0.81 confirms a high overall textual overlap in experience descriptions.
    - **Jaccard Similarity Score**: Moderate score – needs improvement in overlapping keywords.
    - **NER Similarity Score**: Indicates weaker entity similarity, suggesting missing relevant certifications.
    - **LSA Analysis Score**: Suggests a good conceptual alignment.

- **Skills Match:**
  - *Aligned Skills*: Python, Machine Learning
  - *Missing Skills*: SQL, Cloud Computing Exposure

- **Experience and Education Match:**
  - *Experience Alignment*: Has two years of data analysis experience but under the required three years. Relevant experience in visualizing data is present.
  - *Education Fit*: Bachelor’s in Mathematics is somewhat relevant.

- **Summary of Strengths and Gaps:**
  - *Strengths*: Strong in Python, Machine Learning, Data Visualization.
  - *Gaps*: Needs more exposure to SQL and Cloud Computing; slightly short on data analysis experience.

- **Recommendations**:
  - Include any SQL coursework or projects.
  - Add cloud-related experience or projects.

# Notes 

- Integrate both static analysis metrics and content-specific insights for a comprehensive assessment.
- Ensure any recommendations are guided by both the textual content analysis and similarity scores.
- Make sure all function calls are accurate, and information retrieval steps are followed appropriately before analysis."""
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

    class Config:
        env_file = ".env"


settings = Settings()
