import re
import shutil
from pathlib import Path
from uuid import uuid4

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models import Resume, ResumeSection


class ResumeService:
    SECTION_ALIASES = {
        "summary": "summary",
        "profile": "summary",
        "aboutme": "summary",
        "objective": "summary",
        "professionalsummary": "summary",
        "professionalprofile": "summary",
        "experience": "experience",
        "workexperience": "experience",
        "professionalexperience": "experience",
        "employmenthistory": "experience",
        "education": "education",
        "educationandtraining": "education",
        "academicbackground": "education",
        "languages": "languages",
        "language": "languages",
        "languageskills": "languages",
        "skills": "skills",
        "digitalskills": "skills",
        "technicalskills": "skills",
        "otherskills": "skills",
        "organisationalskills": "skills",
        "organizationalskills": "skills",
        "communicationandinterpersonalskills": "skills",
        "interpersonalskills": "skills",
        "projects": "projects",
        "certifications": "certifications",
        "certification": "certifications",
        "licenses": "certifications",
        "courses": "certifications",
        "volunteering": "certifications",
        "awards": "certifications",
    }

    def save_upload(self, upload: UploadFile, upload_dir: str) -> Path:
        suffix = Path(upload.filename or "").suffix.lower() or ".bin"
        filename = f"{uuid4().hex}{suffix}"
        destination = Path(upload_dir) / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return destination

    def extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(str(file_path))
            extracted_pages = []
            for page in reader.pages:
                text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
                extracted_pages.append(text)
            return "\n".join(extracted_pages).strip()
        if suffix == ".docx":
            document = Document(str(file_path))
            return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()

    def _normalize_heading(self, line: str) -> str:
        return re.sub(r"[^a-z]", "", line.lower())

    def _match_heading(self, lines: list[str], index: int) -> tuple[str | None, int]:
        for span in (3, 2, 1):
            if index + span > len(lines):
                continue
            combined = "".join(self._normalize_heading(lines[index + offset]) for offset in range(span))
            section_name = self.SECTION_ALIASES.get(combined)
            if section_name:
                return section_name, span
        return None, 0

    def split_sections(self, text: str) -> list[tuple[str, str]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return [("resume", "")]
        sections: list[tuple[str, str]] = []
        current_heading = "resume"
        current_lines: list[str] = []
        index = 0
        while index < len(lines):
            section_name, consumed = self._match_heading(lines, index)
            if section_name:
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines)))
                current_heading = section_name
                current_lines = []
                index += consumed
            else:
                current_lines.append(lines[index])
                index += 1
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines)))
        return sections

    def create_sections(self, db: Session, resume: Resume, text: str) -> None:
        for index, (section_name, content) in enumerate(self.split_sections(text), start=1):
            db.add(
                ResumeSection(
                    resume_id=resume.id,
                    section_name=section_name[:120],
                    content=content,
                    sort_order=index,
                )
            )


resume_service = ResumeService()
