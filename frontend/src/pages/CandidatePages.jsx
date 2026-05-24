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