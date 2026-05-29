from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models import (
    AIAnalysis,
    Application,
    Certification,
    CandidateProfile,
    CandidateSkill,
    Education,
    Experience,
    JobMatchScore,
    JobPost,
    JobRequirement,
    Language,
    Notification,
    Resume,
    Skill,
)
from app.services.ai_service import ai_service
from app.services.cache_service import cache_service


def _bio_needs_refresh(profile: CandidateProfile) -> bool:
    current_bio = (profile.bio or "").lower()
    if not current_bio.strip():
        return True
    noisy_markers = (
        "id:",
        "gender:",
        "date of birth:",
        "place of birth:",
        "birthplace:",
        "nationality:",
    )
    return any(marker in current_bio for marker in noisy_markers)


def _sync_candidate_profile(db, profile: CandidateProfile, structured_profile: dict) -> None:
    if not structured_profile:
        return

    if structured_profile.get("phone"):
        profile.phone = structured_profile["phone"]
    if structured_profile.get("location"):
        profile.location = structured_profile["location"]
    if structured_profile.get("linkedin_url"):
        profile.linkedin_url = structured_profile["linkedin_url"]
    if structured_profile.get("github_url"):
        profile.github_url = structured_profile["github_url"]
    if structured_profile.get("desired_title"):
        profile.desired_title = structured_profile["desired_title"]
    if structured_profile.get("summary") and _bio_needs_refresh(profile):
        profile.bio = structured_profile["summary"]
    if structured_profile.get("years_of_experience"):
        profile.years_of_experience = max(profile.years_of_experience or 0, structured_profile["years_of_experience"])

    db.query(CandidateSkill).filter(CandidateSkill.candidate_id == profile.id).delete(synchronize_session=False)
    db.query(Education).filter(Education.candidate_id == profile.id).delete(synchronize_session=False)
    db.query(Experience).filter(Experience.candidate_id == profile.id).delete(synchronize_session=False)
    db.query(Certification).filter(Certification.candidate_id == profile.id).delete(synchronize_session=False)
    db.query(Language).filter(Language.candidate_id == profile.id).delete(synchronize_session=False)

    for skill_name in structured_profile.get("skills", []):
        skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
        if not skill:
            skill = Skill(name=skill_name, category="Extracted")
            db.add(skill)
            db.flush()
        db.add(
            CandidateSkill(
                candidate_id=profile.id,
                skill_id=skill.id,
                level="intermediate",
            )
        )

    for education in structured_profile.get("educations", []):
        if not education.get("degree") and not education.get("institution"):
            continue
        db.add(
            Education(
                candidate_id=profile.id,
                institution=education.get("institution") or "Not specified",
                degree=education.get("degree") or "Education",
                field_of_study=education.get("field_of_study"),
                start_year=education.get("start_year"),
                end_year=education.get("end_year"),
            )
        )

    for experience in structured_profile.get("experiences", []):
        if not experience.get("title") and not experience.get("company_name"):
            continue
        db.add(
            Experience(
                candidate_id=profile.id,
                company_name=experience.get("company_name") or "Not specified",
                title=experience.get("title") or "Experience",
                description=experience.get("description"),
                start_date=experience.get("start_date"),
                end_date=experience.get("end_date"),
            )
        )

    for certification in structured_profile.get("certifications", []):
        if not certification.get("name"):
            continue
        db.add(
            Certification(
                candidate_id=profile.id,
                name=certification.get("name"),
                issuer=certification.get("issuer"),
                issued_year=certification.get("issued_year"),
            )
        )

    for language in structured_profile.get("languages", []):
        if not language.get("name"):
            continue
        db.add(
            Language(
                candidate_id=profile.id,
                name=language.get("name"),
                proficiency=language.get("proficiency"),
            )
        )


def process_resume_analysis(resume_id: int) -> None:
    db = SessionLocal()
    try:
        resume = (
            db.query(Resume)
            .options(joinedload(Resume.candidate).joinedload(CandidateProfile.user))
            .filter(Resume.id == resume_id)
            .first()
        )
        if not resume:
            return

        analysis_payload = ai_service.analyze_resume_text(resume.extracted_text)
        structured_profile = analysis_payload.get("structured_profile") or ai_service.extract_structured_profile(
            resume.extracted_text
        )
        analysis_record_payload = {
            key: value
            for key, value in analysis_payload.items()
            if key in {"summary", "strengths", "weaknesses", "suggested_improvements", "extracted_skills"}
        }
        analysis = (
            db.query(AIAnalysis)
            .filter(AIAnalysis.resume_id == resume.id, AIAnalysis.application_id.is_(None))
            .first()
        )
        if not analysis:
            analysis = AIAnalysis(resume_id=resume.id, **analysis_record_payload)
            db.add(analysis)
        else:
            analysis.summary = analysis_record_payload["summary"]
            analysis.strengths = analysis_record_payload["strengths"]
            analysis.weaknesses = analysis_record_payload["weaknesses"]
            analysis.suggested_improvements = analysis_record_payload["suggested_improvements"]
            analysis.extracted_skills = analysis_record_payload["extracted_skills"]

        if resume.candidate:
            _sync_candidate_profile(db, resume.candidate, structured_profile)

        if resume.candidate and resume.candidate.user:
            db.add(
                Notification(
                    user_id=resume.candidate.user.id,
                    title="Resume analysis completed",
                    body="Your uploaded CV was analyzed and new suggestions are available.",
                    notification_type="resume_analysis",
                )
            )
        db.commit()
        cache_service.delete(f"ai:resume:{resume_id}")
    finally:
        db.close()


def process_application_scoring(application_id: int) -> None:
    db = SessionLocal()
    try:
        application = (
            db.query(Application)
            .options(
                joinedload(Application.job)
                .joinedload(JobPost.requirements)
                .joinedload(JobRequirement.skill),
                joinedload(Application.candidate)
                .joinedload(CandidateProfile.skills)
                .joinedload(CandidateSkill.skill),
                joinedload(Application.candidate).joinedload(CandidateProfile.resumes),
            )
            .filter(Application.id == application_id)
            .first()
        )
        if not application or not application.candidate.resumes:
            return

        latest_resume = sorted(application.candidate.resumes, key=lambda item: item.version, reverse=True)[0]
        candidate_skill_names = [
            skill_link.skill.name
            for skill_link in application.candidate.skills
            if skill_link.skill and skill_link.skill.name
        ]
        result = ai_service.calculate_job_match(
            resume_text=latest_resume.extracted_text,
            candidate_skills=candidate_skill_names,
            job=application.job,
        )

        match = db.query(JobMatchScore).filter(JobMatchScore.application_id == application.id).first()
        if not match:
            match = JobMatchScore(application_id=application.id, **result)
            db.add(match)
        else:
            match.score = result["score"]
            match.explanation = result["explanation"]
            match.missing_skills = result["missing_skills"]
            match.matched_skills = result["matched_skills"]
            match.recommended_actions = result["recommended_actions"]

        db.add(
            AIAnalysis(
                application_id=application.id,
                summary=f"Application scored at {result['score']} out of 100.",
                strengths=[f"Matched skills: {', '.join(result['matched_skills'])}" or "Profile has relevant overlap."],
                weaknesses=[f"Missing skills: {', '.join(result['missing_skills'])}" or "No major skill gaps detected."],
                suggested_improvements=result["recommended_actions"],
                extracted_skills=result["matched_skills"],
            )
        )

        candidate_user_id = application.candidate.user.id if application.candidate and application.candidate.user else None
        if candidate_user_id:
            db.add(
                Notification(
                    user_id=candidate_user_id,
                    title="Application scored",
                    body=f"Your application for {application.job.title} has a current match score of {result['score']}.",
                    notification_type="application_score",
                )
            )
        db.commit()
        cache_service.delete(f"ai:application:{application_id}")
    finally:
        db.close()


def notify_application_status(application_id: int, status: str) -> None:
    db = SessionLocal()
    try:
        application = (
            db.query(Application)
            .options(
                joinedload(Application.candidate).joinedload(CandidateProfile.user),
                joinedload(Application.job).joinedload(JobPost.company),
                joinedload(Application.interviews),
            )
            .filter(Application.id == application_id)
            .first()
        )
        if not application or not application.candidate or not application.candidate.user:
            return
        title = "Application status updated"
        body = f"Your application for {application.job.title} is now marked as {status}."
        notification_type = "application_status"
        payload = {
            "application_id": application.id,
            "job_id": application.job_id,
            "job_title": application.job.title,
            "company_name": application.job.company.name if application.job.company else None,
            "status": status,
        }
        if status == "interview":
            latest_interview = max(
                application.interviews,
                key=lambda interview: interview.id,
                default=None,
            )
            title = "Interview invitation received"
            body = f"You were invited to an interview for the job {application.job.title}."
            notification_type = "interview_invite"
            payload.update(
                {
                    "scheduled_at": latest_interview.scheduled_at.isoformat()
                    if latest_interview and latest_interview.scheduled_at
                    else None,
                    "mode": latest_interview.mode if latest_interview else None,
                    "location": latest_interview.location if latest_interview else None,
                    "meeting_link": latest_interview.meeting_link if latest_interview else None,
                    "notes": latest_interview.notes if latest_interview else None,
                    "contact_email": latest_interview.contact_email if latest_interview else None,
                    "contact_phone": latest_interview.contact_phone if latest_interview else None,
                }
            )
        db.add(
            Notification(
                user_id=application.candidate.user.id,
                title=title,
                body=body,
                notification_type=notification_type,
                payload=payload,
            )
        )
        db.commit()
    finally:
        db.close()
