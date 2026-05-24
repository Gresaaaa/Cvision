import json
import re
from datetime import date, datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.models import JobPost
from app.services.resume_service import resume_service


class AIService:
    COMMON_SKILLS = {
        "python": "Python",
        "fastapi": "FastAPI",
        "react": "React",
        "sqlalchemy": "SQLAlchemy",
        "postgresql": "PostgreSQL",
        "redis": "Redis",
        "docker": "Docker",
        "aws": "AWS",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "git": "Git",
        "ci/cd": "CI/CD",
        "kubernetes": "Kubernetes",
        "machine learning": "Machine Learning",
        "data analysis": "Data Analysis",
        "graphql": "GraphQL",
        "rest": "REST",
        "jwt": "JWT",
        "html": "HTML",
        "css": "CSS",
        "node.js": "Node.js",
        "java": "Java",
        "spring boot": "Spring Boot",
        "c++": "C++",
        "c#": "C#",
        "microsoft word": "Microsoft Word",
        "microsoft powerpoint": "Microsoft PowerPoint",
        "microsoft excel": "Microsoft Excel",
        "microsoft access": "Microsoft Access",
        "google drive": "Google Drive",
        "social media": "Social Media",
        "time management": "Time Management",
        "project management": "Project Management",
        "decision making": "Decision Making",
        "self-motivation": "Self-motivation",
        "research skills": "Research Skills",
        "writing and editing": "Writing and Editing",
        "mathematics": "Mathematics",
        "physics": "Physics",
    }
    KNOWN_LANGUAGES = {
        "albanian",
        "arabic",
        "bosnian",
        "croatian",
        "english",
        "french",
        "german",
        "italian",
        "macedonian",
        "serbian",
        "spanish",
        "turkish",
    }
    CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

    def __init__(self) -> None:
        self.settings = get_settings()

    def _dedupe_preserve_order(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(normalized)
        return result

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _section_map(self, text: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        for section_name, content in resume_service.split_sections(text):
            cleaned = content.strip()
            if not cleaned:
                continue
            if section_name in sections:
                sections[section_name] = f"{sections[section_name]}\n{cleaned}"
            else:
                sections[section_name] = cleaned
        return sections

    def _extract_skills(self, text: str) -> list[str]:
        haystack = text.lower()
        detected: list[tuple[int, str]] = []
        for needle, display_name in self.COMMON_SKILLS.items():
            position = haystack.find(needle)
            if position >= 0:
                detected.append((position, display_name))
        detected.sort(key=lambda item: item[0])
        return self._dedupe_preserve_order([item[1] for item in detected])

    def _extract_years(self, text: str) -> int:
        matches = re.findall(r"(\d+)\+?\s+years", text.lower())
        if not matches:
            return 0
        return max(int(match) for match in matches)

    def _highest_cefr(self, text: str) -> str | None:
        matches = re.findall(r"\b(A1|A2|B1|B2|C1|C2)\b", text.upper())
        if not matches:
            return None
        return max(matches, key=lambda item: self.CEFR_ORDER[item])

    def _parse_date_value(self, value: str | None) -> date | None:
        if not value:
            return None
        cleaned = value.strip().strip("[]")
        if re.search(r"\b(current|present|ongoing)\b", cleaned, flags=re.IGNORECASE):
            return date.today()
        for fmt in ("%d/%m/%Y", "%m/%Y", "%Y"):
            try:
                parsed = datetime.strptime(cleaned, fmt)
                return parsed.date()
            except ValueError:
                continue
        return None

    def _year_from_text(self, value: str | None) -> int | None:
        if not value:
            return None
        match = re.search(r"(19|20)\d{2}", value)
        if match:
            return int(match.group(0))
        return None

    def _parse_date_range(self, line: str) -> tuple[str | None, str | None, str]:
        match = re.search(r"\[\s*(.*?)\s*[–-]\s*(.*?)\s*\](.*)", line)
        if not match:
            return None, None, line.strip()
        start_date = match.group(1).strip()
        end_date = match.group(2).strip()
        remainder = match.group(3).strip(" -–\t")
        return start_date, end_date, remainder

    def _is_metadata_line(self, line: str) -> bool:
        normalized = line.lower()
        return normalized.startswith(
            (
                "city:",
                "country:",
                "id:",
                "gender:",
                "date of birth:",
                "place of birth:",
                "birthplace:",
                "nationality:",
                "email:",
                "phone:",
                "home:",
                "location:",
            )
        )

    def _contains_personal_metadata(self, line: str) -> bool:
        normalized = line.lower()
        markers = (
            "id:",
            "gender:",
            "date of birth:",
            "place of birth:",
            "birthplace:",
            "nationality:",
            "marital status:",
            "email:",
            "phone:",
            "linkedin",
            "github",
        )
        return any(marker in normalized for marker in markers)

    def _extract_contact_details(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        phone_match = re.search(r"(\+?\d[\d\s().-]{6,}\d)", text)
        linkedin_match = re.search(r"(https?://[^\s]*linkedin[^\s]+|linkedin\.com/[^\s]+)", text, re.IGNORECASE)
        github_match = re.search(r"(https?://[^\s]*github[^\s]+|github\.com/[^\s]+)", text, re.IGNORECASE)

        location = ""
        for line in lines[:16]:
            lowered = line.lower()
            if any(marker in lowered for marker in ("home", "address", "location")) and ":" in line:
                candidate = line.split(":", 1)[1].strip(" -")
                if candidate:
                    location = candidate
                    break
        if not location:
            city_match = re.search(r"City:\s*([^\n]+)", text, re.IGNORECASE)
            country_match = re.search(r"Country:\s*([^\n]+)", text, re.IGNORECASE)
            if city_match and country_match:
                location = f"{city_match.group(1).strip()}, {country_match.group(1).strip()}"
            elif city_match:
                location = city_match.group(1).strip()

        return {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(1).strip() if phone_match else "",
            "linkedin_url": linkedin_match.group(0) if linkedin_match else "",
            "github_url": github_match.group(0) if github_match else "",
            "location": location,
        }

    def _normalize_skill_phrase(self, phrase: str) -> list[str]:
        candidate = re.sub(r"\s+", " ", phrase).strip(" -•|/")
        if not candidate:
            return []
        candidate = re.sub(
            r"^(programming language|programming languages|experience in|experience with|good knowledge of|good knowledge at)\s+",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        if not candidate:
            return []
        if candidate.lower().startswith("microsoft(") and candidate.endswith(")"):
            inner = candidate[candidate.find("(") + 1 : -1]
            return ["Microsoft", *[item.strip() for item in inner.split(",") if item.strip()]]
        if re.search(r"\bhtml and css\b", candidate, flags=re.IGNORECASE):
            return ["HTML", "CSS"]
        if len(candidate.split()) > 8 and "." in candidate:
            return []
        if len(candidate) > 70:
            return []
        normalized_lower = candidate.lower()
        if normalized_lower in self.COMMON_SKILLS:
            return [self.COMMON_SKILLS[normalized_lower]]
        return [candidate.strip().rstrip(".")]

    def _extract_section_skills(self, sections: dict[str, str]) -> list[str]:
        collected: list[str] = []
        for section_name in ("skills", "projects"):
            content = sections.get(section_name, "")
            if not content:
                continue
            for line in [item.strip() for item in content.splitlines() if item.strip()]:
                if self._is_metadata_line(line) or line.startswith("["):
                    continue
                fragments = re.split(r"[|/]", line)
                for fragment in fragments:
                    for normalized in self._normalize_skill_phrase(fragment):
                        collected.append(normalized)
        return self._dedupe_preserve_order(collected)

    def _extract_languages(self, section_text: str) -> list[dict[str, str | None]]:
        lines = [line.strip() for line in section_text.splitlines() if line.strip()]
        languages: list[dict[str, str | None]] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            lowered = line.lower()
            if "mother tongue" in lowered and ":" in line:
                raw_values = line.split(":", 1)[1]
                for value in re.split(r"[,/]", raw_values):
                    cleaned = value.strip()
                    if cleaned:
                        languages.append({"name": cleaned, "proficiency": "Native"})
                index += 1
                continue
            if lowered.startswith("other language") or lowered.startswith("levels:"):
                index += 1
                continue
            if any(marker in lowered for marker in ("listening", "reading", "writing", "spoken production", "spoken interaction")):
                if languages and not languages[-1]["proficiency"]:
                    languages[-1]["proficiency"] = self._highest_cefr(line)
                index += 1
                continue
            cleaned = re.sub(r"[^A-Za-z +#.-]", "", line).strip()
            if cleaned and cleaned.lower() in self.KNOWN_LANGUAGES:
                lookahead = " ".join(lines[index + 1 : index + 3])
                languages.append({"name": cleaned, "proficiency": self._highest_cefr(lookahead)})
            index += 1
        deduped: list[dict[str, str | None]] = []
        seen: set[str] = set()
        for item in languages:
            key = item["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _parse_education_entries(self, section_text: str) -> list[dict[str, Any]]:
        lines = [line.strip() for line in section_text.splitlines() if line.strip()]
        blocks: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        def finalize(entry: dict[str, Any] | None) -> None:
            if not entry:
                return
            details = [line for line in entry["details"] if not self._is_metadata_line(line)]
            degree = entry["headline"] or (details[0] if details else "")
            institution = details[0] if details else ""
            if degree and institution == degree and len(details) > 1:
                institution = details[1]
            field_of_study = None
            field_match = re.search(r"\b(?:in|of)\b (.+)", degree, flags=re.IGNORECASE)
            if field_match and "school" not in degree.lower():
                field_of_study = field_match.group(1).strip()
            blocks.append(
                {
                    "institution": institution or "Not specified",
                    "degree": degree or "Education",
                    "field_of_study": field_of_study,
                    "start_year": self._year_from_text(entry["start_date"]),
                    "end_year": self._year_from_text(entry["end_date"]),
                }
            )

        for line in lines:
            start_date, end_date, remainder = self._parse_date_range(line)
            if start_date or end_date:
                finalize(current)
                current = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "headline": remainder,
                    "details": [],
                }
            elif current:
                current["details"].append(line)
        finalize(current)
        return blocks

    def _parse_experience_entries(self, section_text: str) -> list[dict[str, Any]]:
        lines = [line.strip() for line in section_text.splitlines() if line.strip()]
        entries: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        def finalize(entry: dict[str, Any] | None) -> None:
            if not entry:
                return
            city = ""
            country = ""
            description_lines: list[str] = []
            detail_lines = [line for line in entry["details"] if line.strip()]
            company_name = ""
            for line in detail_lines:
                lowered = line.lower()
                if lowered.startswith("city:"):
                    city = line.split(":", 1)[1].strip()
                    continue
                if lowered.startswith("country:"):
                    country = line.split(":", 1)[1].strip()
                    continue
                if not company_name:
                    company_name = line
                    continue
                description_lines.append(line)
            location_bits = [value for value in (city, country) if value]
            if location_bits:
                description_lines.append(", ".join(location_bits))
            entries.append(
                {
                    "company_name": company_name or "Not specified",
                    "title": entry["headline"] or company_name or "Experience",
                    "description": "\n".join(description_lines).strip() or None,
                    "start_date": entry["start_date"],
                    "end_date": entry["end_date"],
                }
            )

        for line in lines:
            start_date, end_date, remainder = self._parse_date_range(line)
            if start_date or end_date:
                finalize(current)
                current = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "headline": remainder,
                    "details": [],
                }
            elif current:
                current["details"].append(line)
        finalize(current)
        return entries

    def _extract_certifications(self, section_text: str) -> list[dict[str, Any]]:
        lines = [line.strip() for line in section_text.splitlines() if line.strip()]
        certifications: list[dict[str, Any]] = []
        seen: set[str] = set()
        for line in lines:
            if line.startswith("[") or self._is_metadata_line(line):
                continue
            cleaned = re.sub(r"^[\-\u2022]+\s*", "", line).strip()
            if len(cleaned) < 4 or cleaned.lower().startswith(("city:", "country:")):
                continue
            issuer = None
            if " at " in cleaned:
                name, issuer = cleaned.split(" at ", 1)
            else:
                name = cleaned
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            certifications.append(
                {
                    "name": name[:150],
                    "issuer": issuer[:150] if issuer else None,
                    "issued_year": self._year_from_text(cleaned),
                }
            )
        return certifications

    def _years_from_experiences(self, experiences: list[dict[str, Any]]) -> int:
        total_months = 0
        for experience in experiences:
            start_value = self._parse_date_value(experience.get("start_date"))
            end_value = self._parse_date_value(experience.get("end_date"))
            if not start_value or not end_value or end_value < start_value:
                continue
            months = (end_value.year - start_value.year) * 12 + (end_value.month - start_value.month)
            total_months += max(months, 1)
        return total_months // 12 if total_months else 0

    def extract_structured_profile(self, text: str) -> dict[str, Any]:
        sections = self._section_map(text)
        contact = self._extract_contact_details(text)
        experience_entries = self._parse_experience_entries(sections.get("experience", ""))
        education_entries = self._parse_education_entries(sections.get("education", ""))
        language_entries = self._extract_languages(sections.get("languages", ""))
        certification_entries = self._extract_certifications(sections.get("certifications", ""))
        section_skills = self._extract_section_skills(sections)
        detected_skills = self._extract_skills(text)
        skills = self._dedupe_preserve_order(section_skills + detected_skills)

        resume_intro = sections.get("summary") or sections.get("resume", "")
        intro_lines = []
        for line in [item.strip() for item in resume_intro.splitlines() if item.strip()]:
            lowered = line.lower()
            if self._is_metadata_line(line) or self._contains_personal_metadata(line) or any(marker in lowered for marker in ("email", "phone", "linkedin", "github", "@")):
                continue
            intro_lines.append(line)
        summary = " ".join(intro_lines[:3]).strip()
        years = max(self._extract_years(text), self._years_from_experiences(experience_entries))
        desired_title = experience_entries[0]["title"] if experience_entries else ""

        return {
            "summary": summary,
            "phone": contact["phone"],
            "location": contact["location"],
            "linkedin_url": contact["linkedin_url"],
            "github_url": contact["github_url"],
            "desired_title": desired_title,
            "years_of_experience": years,
            "skills": skills,
            "educations": education_entries,
            "experiences": experience_entries,
            "certifications": certification_entries,
            "languages": language_entries,
        }

    def _fallback_analysis(self, text: str) -> dict[str, Any]:
        structured_profile = self.extract_structured_profile(text)
        skills = structured_profile["skills"]
        years = structured_profile["years_of_experience"]
        experience_count = len(structured_profile["experiences"])
        education_count = len(structured_profile["educations"])
        language_count = len(structured_profile["languages"])

        summary = (
            "Candidate resume analyzed successfully. "
            f"Detected {len(skills)} skills, {experience_count} experience entries, "
            f"{education_count} education entries, and {language_count} language entries."
        )
        strengths = []
        if skills:
            strengths.append(f"Detected skills include: {', '.join(skills[:8])}.")
        if experience_count:
            strengths.append(f"Work history includes {experience_count} structured experience entries.")
        if education_count:
            strengths.append(f"Education history includes {education_count} entries.")
        if language_count:
            strengths.append(
                "Language profile includes: "
                + ", ".join(
                    f"{item['name']}{f' ({item['proficiency']})' if item.get('proficiency') else ''}"
                    for item in structured_profile["languages"][:4]
                )
                + "."
            )
        if years:
            strengths.append(f"Estimated experience level is around {years} years.")
        if not strengths:
            strengths.append("Resume provides a baseline professional overview.")

        weaknesses = []
        if not structured_profile["summary"]:
            weaknesses.append("Resume does not include a clear professional summary section.")
        if len(skills) < 4:
            weaknesses.append("Resume could include a broader or more explicit technical and soft skill list.")
        if "project" not in text.lower():
            weaknesses.append("Projects or impact-oriented achievements are not clearly highlighted.")

        improvements = [
            "Quantify achievements with metrics where possible.",
            "Keep dedicated sections for experience, education, languages, and skills.",
            "Tailor the top summary toward the exact job title you want next.",
        ]
        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses or ["Resume can be improved with more measurable impact statements."],
            "suggested_improvements": improvements,
            "extracted_skills": skills,
            "structured_profile": structured_profile,
        }

    def _ollama_endpoint(self, path: str) -> str:
        base_url = self.settings.ollama_base_url.rstrip("/")
        if base_url.endswith("/api"):
            return f"{base_url}{path}"
        return f"{base_url}/api{path}"

    def _extract_json_payload(self, content: str) -> dict[str, Any] | None:
        cleaned = content.strip()
        if not cleaned:
            return None
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None

    def _prefer_structured_entries(self, generated: Any, extracted: list[dict[str, Any]]) -> list[dict[str, Any]]:
        generated_list = [item for item in generated or [] if isinstance(item, dict)] if isinstance(generated, list) else []
        if len(generated_list) >= len(extracted):
            return generated_list
        return extracted

    def _merge_structured_profile(
        self,
        extracted_profile: dict[str, Any],
        generated_profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(generated_profile, dict):
            return extracted_profile

        merged = dict(extracted_profile)
        for field_name in ("summary", "phone", "location", "linkedin_url", "github_url", "desired_title"):
            value = generated_profile.get(field_name)
            if isinstance(value, str) and value.strip():
                merged[field_name] = value.strip()

        merged["years_of_experience"] = max(
            self._safe_int(extracted_profile.get("years_of_experience")),
            self._safe_int(generated_profile.get("years_of_experience")),
        )
        merged["skills"] = self._dedupe_preserve_order(
            extracted_profile.get("skills", []) + (generated_profile.get("skills") or [])
        )
        for field_name in ("educations", "experiences", "certifications", "languages"):
            merged[field_name] = self._prefer_structured_entries(
                generated_profile.get(field_name),
                extracted_profile.get(field_name, []),
            )
        return merged

    def _ollama_json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        try:  # pragma: no cover - requires local Ollama runtime
            response = httpx.post(
                self._ollama_endpoint("/generate"),
                json={
                    "model": self.settings.ollama_model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=httpx.Timeout(
                    connect=2.5,
                    read=self.settings.ollama_timeout_seconds,
                    write=10.0,
                    pool=2.5,
                ),
            )
            response.raise_for_status()
            return self._extract_json_payload(response.json().get("response", ""))
        except Exception:
            return None

    def analyze_resume_text(self, text: str) -> dict[str, Any]:
        structured_profile = self.extract_structured_profile(text)
        system_prompt = (
            "You analyze resumes for a recruiting platform. "
            "Return JSON with keys summary, strengths, weaknesses, suggested_improvements, extracted_skills, and structured_profile. "
            "structured_profile must include summary, phone, location, linkedin_url, github_url, desired_title, years_of_experience, "
            "skills, educations, experiences, certifications, and languages. "
            "Preserve every resume detail you can find, especially language proficiency, education history, and work experience. "
            "Do not invent details that are not supported by the input."
        )
        user_prompt = (
            "Resume text:\n"
            f"{text[:12000]}\n\n"
            "Baseline extracted profile:\n"
            f"{json.dumps(structured_profile, ensure_ascii=False)}"
        )
        result = self._ollama_json_completion(system_prompt, user_prompt)
        if result:
            result.setdefault("summary", "Resume analysis completed.")
            result.setdefault("strengths", [])
            result.setdefault("weaknesses", [])
            result.setdefault("suggested_improvements", [])
            extracted_skills = result.get("extracted_skills") or []
            merged_profile = self._merge_structured_profile(structured_profile, result.get("structured_profile"))
            result["structured_profile"] = merged_profile
            result["extracted_skills"] = self._dedupe_preserve_order(extracted_skills + merged_profile["skills"])
            return result
        return self._fallback_analysis(text)

    def calculate_job_match(
        self,
        *,
        resume_text: str,
        candidate_skills: list[str],
        job: JobPost,
    ) -> dict[str, Any]:
        requirements = [req.skill.name for req in job.requirements if req.skill]
        normalized_candidate_skills = {skill.lower() for skill in candidate_skills}
        normalized_candidate_skills.update(skill.lower() for skill in self._extract_skills(resume_text))
        matched = [skill for skill in requirements if skill.lower() in normalized_candidate_skills]
        missing = [skill for skill in requirements if skill.lower() not in normalized_candidate_skills]

        if requirements:
            score = round((len(matched) / len(requirements)) * 100, 2)
        else:
            score = 75.0 if normalized_candidate_skills else 50.0

        experience_bonus = 5 if self._extract_years(resume_text) >= 3 else 0
        score = min(100.0, score + experience_bonus)

        explanation = (
            f"Matched {len(matched)} out of {len(requirements)} listed job requirements. "
            f"Experience bonus applied: {experience_bonus}."
        )
        recommendations = []
        if missing:
            recommendations.append(f"Consider strengthening: {', '.join(missing[:5])}.")
        recommendations.append("Tailor the resume summary to the specific job title and company.")
        recommendations.append("Mention concrete outcomes and stack ownership in recent experiences.")

        return {
            "score": score,
            "explanation": explanation,
            "missing_skills": missing,
            "matched_skills": matched,
            "recommended_actions": recommendations,
        }

    def generate_cover_letter(
        self,
        *,
        candidate_name: str,
        company_name: str,
        job_title: str,
        summary: str,
    ) -> str:
        system_prompt = (
            "You write short, professional cover letters for job applications. "
            "Return JSON with a single key named draft."
        )
        user_prompt = (
            f"Candidate: {candidate_name}\nCompany: {company_name}\nRole: {job_title}\n"
            f"Resume summary: {summary}\n"
            "Write a confident, natural cover letter that is ready to submit."
        )
        result = self._ollama_json_completion(system_prompt, user_prompt)
        if result and isinstance(result.get("draft"), str) and result["draft"].strip():
            return result["draft"].strip()
        return (
            f"Dear {company_name} hiring team,\n\n"
            f"My name is {candidate_name}, and I am excited to apply for the {job_title} role. "
            f"{summary} I believe this background would allow me to contribute quickly while continuing "
            "to grow with your team.\n\n"
            "Thank you for your time and consideration.\n"
        )


ai_service = AIService()
