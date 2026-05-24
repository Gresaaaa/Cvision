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
