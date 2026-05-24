import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import api, { getErrorMessage } from "../api/client";
import { EmptyState, MetricStrip, PageHero, Panel, ProfileAvatar, StatusBadge } from "../components/UI";
import { useJobs } from "../contexts/JobContext";
import { useNotifications } from "../contexts/NotificationContext";
import { useAuth } from "../contexts/AuthContext";
import { useUserData } from "../contexts/UserContext";

export function CandidateDashboardPage() {
  const { user } = useAuth();
  const { candidateProfile } = useUserData();
  const { applications, savedJobs, fetchMyApplications, fetchSavedJobs } = useJobs();
  const { unreadCount } = useNotifications();

  useEffect(() => {
    fetchMyApplications();
    fetchSavedJobs();
  }, []);

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Candidate workspace"
        title={`Welcome, ${user?.full_name || "candidate"}`}
        description="Track applications, upload resumes, and keep your profile aligned with the jobs you want next."
      />
      <MetricStrip
        items={[
          { label: "Applications", value: applications.length },
          { label: "Saved jobs", value: savedJobs.length },
          { label: "Alerts", value: unreadCount },
          { label: "Experience", value: `${candidateProfile?.years_of_experience || 0} years` },
        ]}
      />
      <div className="content-grid">
        <Panel title="Next actions">
          <ul className="feature-list">
            <li>Upload your latest CV for AI feedback.</li>
            <li>Check application statuses and recruiter movement.</li>
            <li>Use job match previews before you apply.</li>
          </ul>
        </Panel>
        <Panel title="Quick links">
          <div className="action-row">
            <Link className="ghost-button" to="/candidate/resume">
              Manage resume
            </Link>
            <Link className="ghost-button" to="/candidate/analysis">
              View analysis
            </Link>
            <Link className="ghost-button" to="/jobs">
              Browse jobs
            </Link>
          </div>
        </Panel>
      </div>
    </div>
  );
}

export function CandidateProfilePage() {
  const { candidateProfile, updateCandidateProfile, uploadCandidateAvatar } = useUserData();
  const [form, setForm] = useState({
    phone: "",
    location: "",
    bio: "",
    years_of_experience: 0,
    linkedin_url: "",
    github_url: "",
    desired_title: "",
  });
  const [message, setMessage] = useState("");
  const [avatarFile, setAvatarFile] = useState(null);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);

  useEffect(() => {
    if (candidateProfile) {
      setForm({
        phone: candidateProfile.phone || "",
        location: candidateProfile.location || "",
        bio: candidateProfile.bio || "",
        years_of_experience: candidateProfile.years_of_experience || 0,
        linkedin_url: candidateProfile.linkedin_url || "",
        github_url: candidateProfile.github_url || "",
        desired_title: candidateProfile.desired_title || "",
      });
    }
  }, [candidateProfile?.id]);

  const submit = async (event) => {
    event.preventDefault();
    try {
      await updateCandidateProfile({ ...form, years_of_experience: Number(form.years_of_experience) });
      setMessage("Profile updated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to update profile."));
    }
  };

  
  const uploadAvatar = async (event) => {
    event.preventDefault();
    if (!avatarFile) return;
    setIsUploadingAvatar(true);
    try {
      await uploadCandidateAvatar(avatarFile);
      setAvatarFile(null);
      setMessage("Profile photo updated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to upload profile photo."));
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Profile"
        title="Shape your professional narrative."
        description="Everything here improves search visibility, AI summaries, and recruiter context."
      />
      <Panel title="Profile editor">
        <div className="media-upload-card">
          <div className="media-upload-preview">
            <ProfileAvatar
              imageUrl={candidateProfile?.avatar_url}
              name={candidateProfile?.user?.full_name}
              size="xl"
              shape="circle"
            />
            <div>
              <h3>Profile photo</h3>
              <p>Add a clear photo so recruiters can recognize your profile quickly.</p>
            </div>
          </div>
          <form className="media-upload-form" onSubmit={uploadAvatar}>
            <input
              accept=".png,.jpg,.jpeg,.webp"
              onChange={(event) => setAvatarFile(event.target.files?.[0] || null)}
              type="file"
            />
            <button className="ghost-button" disabled={!avatarFile || isUploadingAvatar} type="submit">
              {isUploadingAvatar ? "Uploading photo..." : "Upload photo"}
            </button>
          </form>
        </div>
        <form className="form-grid" onSubmit={submit}>
          <div className="inline-grid">
            <label>
              Phone
              <input
                pattern="\+?[0-9()\-\s]{7,20}"
                title="Use a valid phone number such as +383 44 123 456."
                value={form.phone}
                onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))}
              />
            </label>
            <label>
              Location
              <input value={form.location} onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))} />
            </label>
          </div>
          <label>
            Desired title
            <input
              value={form.desired_title}
              onChange={(event) => setForm((current) => ({ ...current, desired_title: event.target.value }))}
            />
          </label>
          <label>
            Short bio
            <textarea rows="6" value={form.bio} onChange={(event) => setForm((current) => ({ ...current, bio: event.target.value }))} />
          </label>
          <div className="inline-grid">
            <label>
              Years of experience
              <input
                type="number"
                value={form.years_of_experience}
                onChange={(event) =>
                  setForm((current) => ({ ...current, years_of_experience: event.target.value }))
                }
              />
            </label>
            <label>
              LinkedIn
              <input
                type="url"
                placeholder="https://linkedin.com/in/your-profile"
                value={form.linkedin_url}
                onChange={(event) => setForm((current) => ({ ...current, linkedin_url: event.target.value }))}
              />
            </label>
          </div>
          <label>
            GitHub
            <input
              type="url"
              placeholder="https://github.com/your-profile"
              value={form.github_url}
              onChange={(event) => setForm((current) => ({ ...current, github_url: event.target.value }))}
            />
          </label>
          {message ? <p className="info-text">{message}</p> : null}
          <button className="primary-button" type="submit">
            Save profile
          </button>
        </form>
      </Panel>
    </div>
  );
}

export function CandidateResumePage() {
  const [resumes, setResumes] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const loadResumes = async () => {
    const { data } = await api.get("/resumes/my");
    setResumes(data);
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const uploadResume = async (event) => {
    event.preventDefault();
    if (!selectedFile) return;
    const payload = new FormData();
    payload.set("file", selectedFile);
    setIsUploading(true);
    try {
      await api.post("/resumes/upload", payload, { headers: { "Content-Type": "multipart/form-data" } });
      setMessage("Resume uploaded. Background analysis is running.");
      setSelectedFile(null);
      await loadResumes();
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to upload resume."));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Resume management"
        title="Upload versions, keep history, and trigger AI analysis."
        description="Every upload is versioned and analyzed in the background."
      />
      <Panel title="Upload CV">
        <form className="inline-form" onSubmit={uploadResume}>
          <input accept=".pdf,.doc,.docx,.txt" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} type="file" />
          <button className="primary-button" disabled={!selectedFile || isUploading} type="submit">
            {isUploading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {message ? <p className="info-text">{message}</p> : null}
      </Panel>
      <Panel title="Resume versions">
        {resumes.length ? (
          <div className="stack-list">
            {resumes.map((resume) => (
              <article className="stack-item" key={resume.id}>
                <div>
                  <strong>{resume.original_filename}</strong>
                  <p>Version {resume.version}</p>
                </div>
                <div className="action-row">
                  <Link className="inline-link" to={`/candidate/analysis?resumeId=${resume.id}`}>
                    View analysis
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No resume uploaded yet" body="Upload your first CV to unlock analysis and matching." />
        )}
      </Panel>
    </div>
  );
}

export function CandidateAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [message, setMessage] = useState("");
  const [isLoadingSavedAnalysis, setIsLoadingSavedAnalysis] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const requestedResumeId = searchParams.get("resumeId") || "";

  useEffect(() => {
    api.get("/resumes/my").then(({ data }) => {
      setResumes(data);
      const preferredResumeId =
        requestedResumeId && data.some((resume) => String(resume.id) === requestedResumeId)
          ? requestedResumeId
          : data[0]
            ? String(data[0].id)
            : "";
      setSelectedResumeId(preferredResumeId);
    });
  }, []);

  useEffect(() => {
    if (!resumes.length || !requestedResumeId) return;
    const hasRequestedResume = resumes.some((resume) => String(resume.id) === requestedResumeId);
    if (hasRequestedResume && requestedResumeId !== selectedResumeId) {
      setSelectedResumeId(requestedResumeId);
    }
  }, [requestedResumeId, resumes, selectedResumeId]);

  const loadSavedAnalysis = async (resumeId) => {
    if (!resumeId) return;
    setIsLoadingSavedAnalysis(true);
    try {
      const { data } = await api.get(`/ai/resume-analysis/${resumeId}`);
      setAnalysis(data);
      setMessage("Showing saved analysis.");
    } catch (error) {
      if (error?.response?.status === 404) {
        setAnalysis(null);
        setMessage("No saved analysis yet for this CV. Click Analyze now to create one.");
      } else {
        setMessage(getErrorMessage(error, "Unable to load the saved analysis."));
      }
    } finally {
      setIsLoadingSavedAnalysis(false);
    }
  };

  useEffect(() => {
    if (!selectedResumeId) {
      setAnalysis(null);
      return;
    }
    const nextParams = new URLSearchParams(searchParams);
    if (nextParams.get("resumeId") !== selectedResumeId) {
      nextParams.set("resumeId", selectedResumeId);
      setSearchParams(nextParams, { replace: true });
    }
    void loadSavedAnalysis(selectedResumeId);
  }, [selectedResumeId]);

  const loadAnalysis = async () => {
    if (!selectedResumeId) return;
    setIsAnalyzing(true);
    try {
      const { data } = await api.post("/ai/analyze-resume", null, { params: { resume_id: selectedResumeId } });
      setAnalysis(data);
      setMessage("Analysis loaded.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to load analysis."));
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="AI insights"
        title="Understand how your CV reads to the system."
        description="Review your summary, extracted skills, strengths, gaps, and practical improvements before you apply."
      />
      <Panel
        title="Choose a resume"
        action={
          <button className="primary-button" disabled={!selectedResumeId || isAnalyzing} onClick={loadAnalysis} type="button">
            {isAnalyzing ? "Analyzing..." : analysis ? "Analyze again" : "Analyze now"}
          </button>
        }
      >
        <label>
          Resume version
          <select value={selectedResumeId} onChange={(event) => setSelectedResumeId(event.target.value)}>
            <option value="">Select one</option>
            {resumes.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.original_filename} (v{resume.version})
              </option>
            ))}
          </select>
        </label>
        {message ? <p className="info-text">{message}</p> : null}
        {isLoadingSavedAnalysis ? <p className="info-text">Loading saved analysis...</p> : null}
      </Panel>
      {analysis ? (
        <div className="content-grid">
          <Panel title="Summary">
            <p>{analysis.summary}</p>
          </Panel>
          <Panel title="Strengths">
            <ul className="feature-list">{analysis.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
          </Panel>
          <Panel title="Weaknesses">
            <ul className="feature-list">{analysis.weaknesses.map((item) => <li key={item}>{item}</li>)}</ul>
          </Panel>
          <Panel title="Improvement suggestions">
            <ul className="feature-list">
              {analysis.suggested_improvements.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </Panel>
          <Panel title="Extracted skills">
            <div className="tag-cloud">
              {analysis.extracted_skills.map((item) => (
                <span className="tag" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}
    </div>
  );
}