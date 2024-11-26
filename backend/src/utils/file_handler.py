from pathlib import Path
from fastapi import UploadFile
import aiofiles
import shutil
from typing import Optional
import os
from datetime import datetime
import asyncio


class FileHandler:
    def __init__(self, base_path: str = "data/storage"):
        """Initialize FileHandler with base storage path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.cv_path = self.base_path / "cvs"
        self.cv_path.mkdir(exist_ok=True)

        self.template_path = self.base_path / "templates"
        self.template_path.mkdir(exist_ok=True)

        self.pdf_path = self.base_path / "pdfs"
        self.pdf_path.mkdir(exist_ok=True)

    async def save_cv(self, file: UploadFile, cv_id: str) -> Path:
        """
        Save uploaded CV file.
        Returns the path where the file was saved.
        """
        # Create directory for this CV
        cv_dir = self.cv_path / cv_id
        cv_dir.mkdir(exist_ok=True)

        # Save original extension
        extension = Path(file.filename).suffix
        file_path = cv_dir / f"cv{extension}"

        try:
            # Save file
            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)

            return file_path

        except Exception as e:
            # Cleanup on failure
            if cv_dir.exists():
                shutil.rmtree(cv_dir)
            raise Exception(f"Failed to save CV: {str(e)}")

    async def get_cv_content(self, file_path: Path) -> str:
        """
        Read and return the content of a CV file.
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
                return await file.read()
        except Exception as e:
            raise Exception(f"Failed to read CV content: {str(e)}")

    async def save_pdf(self, cv_id: str, pdf_content: bytes) -> Path:
        """
        Save generated PDF.
        """
        pdf_dir = self.pdf_path / cv_id
        pdf_dir.mkdir(exist_ok=True)

        file_path = pdf_dir / f"cv.pdf"

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(pdf_content)

        return file_path

    async def get_cv_versions(self, cv_id: str) -> list[Path]:
        """
        Get all versions of a CV.
        """
        cv_dir = self.cv_path / cv_id
        if not cv_dir.exists():
            return []

        return sorted(cv_dir.glob("cv*"))

    async def save_improved_cv(self, cv_id: str, content: str, version: int) -> Path:
        """
        Save an improved version of a CV.
        """
        cv_dir = self.cv_path / cv_id
        cv_dir.mkdir(exist_ok=True)

        file_path = cv_dir / f"cv_v{version}.tex"

        async with aiofiles.open(file_path, "w", encoding="utf-8") as out_file:
            await out_file.write(content)

        return file_path

    async def cleanup_old_files(self, max_age_days: int = 7):
        """
        Remove files older than max_age_days.
        """
        current_time = datetime.now().timestamp()

        # Clean up CVs
        for cv_dir in self.cv_path.iterdir():
            if not cv_dir.is_dir():
                continue

            dir_time = cv_dir.stat().st_mtime
            age_days = (current_time - dir_time) / (24 * 3600)

            if age_days > max_age_days:
                shutil.rmtree(cv_dir)

        # Clean up PDFs
        for pdf_dir in self.pdf_path.iterdir():
            if not pdf_dir.is_dir():
                continue

            dir_time = pdf_dir.stat().st_mtime
            age_days = (current_time - dir_time) / (24 * 3600)

            if age_days > max_age_days:
                shutil.rmtree(pdf_dir)

    async def delete_cv(self, cv_id: str):
        """
        Delete a CV and all its associated files.
        """
        # Remove CV files
        cv_dir = self.cv_path / cv_id
        if cv_dir.exists():
            shutil.rmtree(cv_dir)

        # Remove PDF files
        pdf_dir = self.pdf_path / cv_id
        if pdf_dir.exists():
            shutil.rmtree(pdf_dir)

    async def save_template(self, name: str, content: str) -> Path:
        """
        Save a CV template.
        """
        file_path = self.template_path / f"{name}.tex"

        async with aiofiles.open(file_path, "w", encoding="utf-8") as out_file:
            await out_file.write(content)

        return file_path

    async def get_template_content(self, name: str) -> Optional[str]:
        """
        Get content of a template.
        """
        file_path = self.template_path / f"{name}.tex"
        if not file_path.exists():
            return None

        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            return await file.read()

    async def list_templates(self) -> list[str]:
        """
        List all available templates.
        """
        return [f.stem for f in self.template_path.glob("*.tex")]
