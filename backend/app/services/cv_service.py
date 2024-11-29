import subprocess
from app.models.cv import CV
from app.database import SessionLocal
from sqlalchemy.orm import Session
from app.utils.file_management import PDF_DIR
import os


def process_cv(cv_id: int):
    db: Session = SessionLocal()
    try:
        cv_entry = db.query(CV).filter(CV.id == cv_id).first()
        if not cv_entry:
            raise Exception("CV not found in database.")

        # Compile LaTeX to PDF
        compile_latex(cv_entry.filepath)

    except Exception as e:
        print(f"Error processing CV: {e}")
    finally:
        db.close()


def compile_latex(tex_file_path: str):
    try:
        subprocess.run(
            ["pdflatex", "-output-directory", PDF_DIR, tex_file_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"LaTeX compilation failed: {e.stderr.decode()}")
