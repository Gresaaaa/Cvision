SAMPLE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00"
    b"\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def register_candidate(
    client,
    *,
    full_name="Jane Candidate",
    email="jane@example.com",
    password="Secret123!",
    location="Prishtina",
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "candidate",
            "location": location,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload["user"]


def register_company(
    client,
    *,
    full_name="Acme Recruiter",
    email="recruiter@example.com",
    password="Secret123!",
    company_name="Acme",
    industry="Technology",
    location="Prishtina",
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "company",
            "company_name": company_name,
            "industry": industry,
            "location": location,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload["user"]


def test_candidate_and_company_flow(client):
    candidate_token, candidate_user = register_candidate(client)
    company_token, company_user = register_company(client)

    sample_resume_text = """
Jon Jashari
Email: jonjashari32@gmail.com
Phone: (+383) 44988709
Home: Prishtina, Kosovo
LinkedIn: https://linkedin.com/in/jonjashari
GitHub: https://github.com/jonjashari

WORK EXPERIENCE
[ 01/11/2023 – Current ] Junior Web Developer
Certivity
City: Prishtina
Country: Kosovo
Built landing pages with HTML, CSS, Git, React, and FastAPI support.

EDUCATION AND TRAINING
[ 01/10/2023 – Current ] Bachelor Degree in Computer and Software Engineering
University of Prishtina "Hasan Prishtina"
City: Prishtina
Country: Kosovo

[ 01/09/2020 – 20/06/2023 ] High School
Xhevdet Doda
City: Prishtina
Country: Kosovo

LANGUAGE SKILLS
Mother tongue(s): Albanian
English
LISTENING C1 READING C1 WRITING C1 SPOKEN PRODUCTION C1 SPOKEN INTERACTION C1
German
LISTENING B2 READING B2 WRITING B2 SPOKEN PRODUCTION B2 SPOKEN INTERACTION B2

DIGITAL SKILLS
Programming language C++
Experience in HTML and CSS
Git
React
FastAPI
Microsoft Word
Time management
""".strip()

    admin_login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@cvision.io", "password": "Admin123!"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    skills = client.get("/api/v1/admin/skills", headers={"Authorization": f"Bearer {admin_token}"})
    assert skills.status_code == 200
    skill_id = skills.json()[0]["id"]

    categories = client.get(
        "/api/v1/admin/categories", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert categories.status_code == 200
    category_id = categories.json()[0]["id"]

    upload_avatar = client.post(
        "/api/v1/users/profile/avatar",
        headers={"Authorization": f"Bearer {candidate_token}"},
        files={"file": ("candidate-avatar.png", SAMPLE_PNG, "image/png")},
    )
    assert upload_avatar.status_code == 200
    avatar_url = upload_avatar.json()["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")

    upload_logo = client.post(
        "/api/v1/companies/me/logo",
        headers={"Authorization": f"Bearer {company_token}"},
        files={"file": ("company-logo.png", SAMPLE_PNG, "image/png")},
    )
    assert upload_logo.status_code == 200
    logo_url = upload_logo.json()["logo_url"]
    assert logo_url.startswith("/uploads/logos/")

    candidate_profile = client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert candidate_profile.status_code == 200
    assert candidate_profile.json()["avatar_url"] == avatar_url

    avatar_asset = client.get(avatar_url)
    assert avatar_asset.status_code == 200
    assert avatar_asset.content == SAMPLE_PNG

    logo_asset = client.get(logo_url)
    assert logo_asset.status_code == 200
    assert logo_asset.content == SAMPLE_PNG

    upload_resume = client.post(
        "/api/v1/resumes/upload",
        headers={"Authorization": f"Bearer {candidate_token}"},
        files={"file": ("jon-jashari-resume.txt", sample_resume_text.encode("utf-8"), "text/plain")},
    )
    assert upload_resume.status_code == 200
    resume_id = upload_resume.json()["id"]

    analyze_resume = client.post(
        "/api/v1/ai/analyze-resume",
        headers={"Authorization": f"Bearer {candidate_token}"},
        params={"resume_id": resume_id},
    )
    assert analyze_resume.status_code == 200
    saved_analysis = client.get(
        f"/api/v1/ai/resume-analysis/{resume_id}",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert saved_analysis.status_code == 200
    assert saved_analysis.json()["resume_id"] == resume_id

    create_job = client.post(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {company_token}"},
        json={
            "title": "  Backend Engineer  ",
            "description": "  Build APIs with FastAPI and PostgreSQL.  ",
            "location": "  Prishtina  ",
            "category_id": category_id,
            "employment_type": "full_time",
            "work_mode": "hybrid",
            "salary_min": 1000,
            "salary_max": 1800,
            "experience_level": "mid",
            "requirements": [
                {"skill_id": skill_id, "required_level": "mid", "is_mandatory": True},
                {"skill_name": "Stakeholder Management", "required_level": "nice to have", "is_mandatory": False},
            ],
        },
    )
    assert create_job.status_code == 200
    job_id = create_job.json()["id"]
    assert create_job.json()["title"] == "Backend Engineer"
    assert create_job.json()["description"] == "Build APIs with FastAPI and PostgreSQL."
    assert create_job.json()["location"] == "Prishtina"
    returned_requirements = {requirement["skill"]["name"] for requirement in create_job.json()["requirements"]}
    assert "Stakeholder Management" in returned_requirements

    public_company_profile = client.get(f"/api/v1/companies/{company_user['company']['id']}")
    assert public_company_profile.status_code == 200
    assert public_company_profile.json()["industry"] == "Technology"
    assert public_company_profile.json()["logo_url"] == logo_url

    jobs = client.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert len(jobs.json()) >= 1
    created_job_payload = next((job for job in jobs.json() if job["id"] == job_id), None)
    assert created_job_payload is not None
    assert created_job_payload["company"]["logo_url"] == logo_url

    apply_response = client.post(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"job_id": job_id, "cover_letter": "I would love to contribute."},
    )
    assert apply_response.status_code == 200
    application_payload = apply_response.json()
    application_id = application_payload["id"]
    candidate_id = application_payload["candidate_id"]
    assert application_payload["cover_letter"] == "I would love to contribute."
    assert application_payload["job"]["company"]["logo_url"] == logo_url

    company_candidate_profile = client.get(
        f"/api/v1/candidates/{candidate_id}",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert company_candidate_profile.status_code == 200
    profile_payload = company_candidate_profile.json()
    assert profile_payload["user"]["email"] == candidate_user["email"]
    assert profile_payload["avatar_url"] == avatar_url
    assert profile_payload["experiences"][0]["title"] == "Junior Web Developer"
    assert profile_payload["educations"][0]["institution"] == 'University of Prishtina "Hasan Prishtina"'
    extracted_languages = {language["name"]: language["proficiency"] for language in profile_payload["languages"]}
    assert extracted_languages["Albanian"] == "Native"
    assert extracted_languages["English"] == "C1"
    assert extracted_languages["German"] == "B2"
    extracted_skills = {skill_link["skill"]["name"] for skill_link in profile_payload["skills"]}
    assert {"HTML", "CSS", "Git", "React", "FastAPI"}.issubset(extracted_skills)

    company_resume_file = client.get(
        f"/api/v1/resumes/{resume_id}/file",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert company_resume_file.status_code == 200
    assert b"Computer and Software Engineering" in company_resume_file.content

    job_applications = client.get(
        f"/api/v1/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {company_token}"},
    )
    assert job_applications.status_code == 200
    assert job_applications.json()[0]["candidate_id"] == candidate_id
    assert job_applications.json()[0]["candidate"]["avatar_url"] == avatar_url
    assert job_applications.json()[0]["interviews"] == []
    assert job_applications.json()[0]["cover_letter"] == "I would love to contribute."

    update_status = client.patch(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {company_token}"},
        json={"status": "under_review", "notes": "Good initial fit."},
    )
    assert update_status.status_code == 200
    assert update_status.json()["status"] == "under_review"

    deactivate_user = client.patch(
        f"/api/v1/admin/users/{candidate_user['id']}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deactivate_user.status_code == 200

    inactive_login = client.post(
        "/api/v1/auth/login",
        data={"username": candidate_user["email"], "password": "Secret123!"},
    )
    assert inactive_login.status_code == 403

    reactivate_user = client.patch(
        f"/api/v1/admin/users/{candidate_user['id']}/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reactivate_user.status_code == 200

    active_login = client.post(
        "/api/v1/auth/login",
        data={"username": candidate_user["email"], "password": "Secret123!"},
    )
    assert active_login.status_code == 200

    invite_response = client.post(
        f"/api/v1/applications/{application_id}/invite-interview",
        headers={"Authorization": f"Bearer {company_token}"},
        json={
            "scheduled_at": "2026-05-10T09:00:00",
            "mode": "video",
            "meeting_link": "https://meet.example.com/cvision-intro",
            "contact_email": "hiring@acme.example",
            "contact_phone": "+383 44 555 222",
            "notes": "We would like to discuss the role and your backend experience.",
        },
    )
    assert invite_response.status_code == 200
    assert invite_response.json()["mode"] == "video"
    assert invite_response.json()["contact_email"] == "hiring@acme.example"
    assert invite_response.json()["contact_phone"] == "+383 44 555 222"

    candidate_notifications = client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert candidate_notifications.status_code == 200
    interview_notifications = [
        notification
        for notification in candidate_notifications.json()
        if notification["notification_type"] == "interview_invite"
    ]
    assert interview_notifications
    interview_notification = interview_notifications[0]
    assert "Backend Engineer" in interview_notification["body"]
    assert interview_notification["payload"]["job_title"] == "Backend Engineer"
    assert interview_notification["payload"]["mode"] == "video"
    assert interview_notification["payload"]["meeting_link"] == "https://meet.example.com/cvision-intro"
    assert interview_notification["payload"]["contact_email"] == "hiring@acme.example"
    assert interview_notification["payload"]["contact_phone"] == "+383 44 555 222"

    delete_user = client.delete(
        f"/api/v1/admin/users/{candidate_user['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_user.status_code == 200

    delete_company = client.delete(
        f"/api/v1/admin/companies/{company_user['company']['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert delete_company.status_code == 200

    users_after_delete = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert users_after_delete.status_code == 200
    remaining_emails = {user["email"] for user in users_after_delete.json()}
    assert candidate_user["email"] not in remaining_emails
    assert company_user["email"] not in remaining_emails

    companies_after_delete = client.get(
        "/api/v1/admin/companies",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert companies_after_delete.status_code == 200
    remaining_company_ids = {company["id"] for company in companies_after_delete.json()}
    assert company_user["company"]["id"] not in remaining_company_ids
