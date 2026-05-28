import { useDeferredValue, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import api, { getErrorMessage } from "../api/client";
import { EmptyState, MetricStrip, PageHero, Panel, ProfileAvatar, StatusBadge } from "../components/UI";
import { INDUSTRY_OPTIONS } from "../constants/options";
import { useAuth } from "../contexts/AuthContext";
import { useJobs } from "../contexts/JobContext";
import { useNotifications } from "../contexts/NotificationContext";

export function HomePage() {
  const journeys = [
    {
      title: "Candidates",
      body: "Upload a CV, build your profile, get AI suggestions, and apply with a tailored cover letter.",
    },
    {
      title: "Companies",
      body: "Publish roles, review applicants, invite interviews, and keep hiring activity in one place.",
    },
  ];
  const steps = [
    "Create an account as a candidate or company.",
    "Build your profile and upload your latest CV.",
    "Search roles, generate a cover letter, and apply.",
    "Track alerts, interviews, and decisions from one dashboard.",
  ];

  return (
    <div className="page-grid home-page">
      <PageHero
        eyebrow="Smarter recruiting, simpler hiring"
        title="CVision helps people get hired and teams hire with confidence."
        description="Create a profile, upload your CV, discover openings, generate better applications, and keep every interview update in one place."
        action={
          <div className="hero-stack">
            <Link className="primary-button" to="/register">
              Get started
            </Link>
            <Link className="ghost-button" to="/jobs">
              Explore jobs
            </Link>
          </div>
        }
      />

      <MetricStrip
        items={[
          { label: "Guided applications", value: "CV + cover letter", note: "Send better applications faster" },
          { label: "Interview updates", value: "Useful alerts", note: "See the date, place, and meeting link" },
          { label: "Company workspaces", value: "One hiring hub", note: "Roles, candidates, and invites together" },
          { label: "Clear dashboards", value: "Role-based views", note: "Dedicated spaces for candidates and companies" },
        ]}
      />

      <div className="showcase-grid">
        {journeys.map((journey) => (
          <article className="showcase-card" key={journey.title}>
            <span className="eyebrow">For {journey.title}</span>
            <h3>{journey.title} workflow</h3>
            <p>{journey.body}</p>
          </article>
        ))}
      </div>

      <div className="content-grid">
        <Panel title="How to use CVision" subtitle="A quick path from sign-up to interview tracking.">
          <div className="journey-grid">
            {steps.map((step, index) => (
              <article className="journey-step" key={step}>
                <strong>0{index + 1}</strong>
                <p>{step}</p>
              </article>
            ))}
          </div>
        </Panel>

        <Panel title="What CVision offers" subtitle="The essentials for job seekers and hiring teams.">
          <ul className="feature-list">
            <li>Versioned CV uploads with structured analysis and profile suggestions.</li>
            <li>Job discovery with saved jobs, application tracking, and interview alerts.</li>
            <li>Company dashboards for publishing roles, reviewing candidates, and sending invites.</li>
            <li>Clear company profiles and candidate profiles to support better hiring decisions.</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}

export function LoginPage() {
  const navigate = useNavigate();
  const { login, authError } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const user = await login(form);
      navigate(defaultRouteForRole(user.role.name));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <Panel title="Welcome back" subtitle="Log in with your CVision account.">
        <form className="form-grid" onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
            />
          </label>
          {authError ? <p className="error-text">{authError}</p> : null}
          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Login"}
          </button>
        </form>
      </Panel>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, authError } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "candidate",
    company_name: "",
    company_description: "",
    industry: "",
    location: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        role: form.role,
        location: form.location.trim() || null,
      };
      if (form.role === "company") {
        payload.company_name = form.company_name.trim();
        payload.company_description = form.company_description.trim() || null;
        payload.industry = form.industry.trim() || null;
      }
      const user = await register(payload);
      navigate(defaultRouteForRole(user.role.name));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <Panel title="Create your workspace" subtitle="Candidate and company onboarding share the same flow.">
        <form className="form-grid" onSubmit={submit}>
          <div className="inline-grid">
            <label>
              Full name
              <input
                value={form.full_name}
                onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
                required
              />
            </label>
            <label>
              Location
              <input
                value={form.location}
                onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
              />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                minLength="8"
                pattern="(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}"
                title="Use at least 8 characters with uppercase, lowercase, and a number."
                value={form.password}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                required
              />
            </label>
          </div>
          <label>
            Account type
            <select
              value={form.role}
              onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
            >
              <option value="candidate">Candidate</option>
              <option value="company">Company / Recruiter</option>
            </select>
          </label>
          {form.role === "company" ? (
            <>
              <label>
                Company name
                <input
                  value={form.company_name}
                  onChange={(event) => setForm((current) => ({ ...current, company_name: event.target.value }))}
                  required={form.role === "company"}
                />
              </label>
              <div className="inline-grid">
                <label>
                  Industry
                  <input
                    list="industry-options"
                    value={form.industry}
                    onChange={(event) => setForm((current) => ({ ...current, industry: event.target.value }))}
                    placeholder="Choose from the list or type your own"
                  />
                </label>
                <label>
                  Company description
                  <input
                    value={form.company_description}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, company_description: event.target.value }))
                    }
                  />
                </label>
              </div>
              <datalist id="industry-options">
                {INDUSTRY_OPTIONS.map((industry) => (
                  <option key={industry} value={industry} />
                ))}
              </datalist>
            </>
          ) : null}
          {authError ? <p className="error-text">{authError}</p> : null}
          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating..." : "Register"}
          </button>
        </form>
      </Panel>
    </div>
  );
}

export function JobsPage() {
  const { jobs, fetchJobs, isLoading } = useJobs();
  const [filters, setFilters] = useState({ title: "", location: "", work_mode: "" });
  const deferredTitle = useDeferredValue(filters.title);

  useEffect(() => {
    fetchJobs({ ...filters, title: deferredTitle });
  }, [deferredTitle, filters.location, filters.work_mode]);

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Open positions"
        title="Find the roles that match your next move."
        description="Browse opportunities by title, location, and work style, then open the role to prepare your application."
      />
      <Panel title="Filters">
        <div className="inline-grid">
          <label>
            Title
            <input
              value={filters.title}
              onChange={(event) => setFilters((current) => ({ ...current, title: event.target.value }))}
              placeholder="Backend engineer"
            />
          </label>
          <label>
            Location
            <input
              value={filters.location}
              onChange={(event) => setFilters((current) => ({ ...current, location: event.target.value }))}
              placeholder="Prishtina"
            />
          </label>
          <label>
            Work mode
            <select
              value={filters.work_mode}
              onChange={(event) => setFilters((current) => ({ ...current, work_mode: event.target.value }))}
            >
              <option value="">Any</option>
              <option value="remote">Remote</option>
              <option value="onsite">Onsite</option>
              <option value="hybrid">Hybrid</option>
            </select>
          </label>
        </div>
      </Panel>
      {isLoading ? <div className="center-card">Loading jobs...</div> : null}
      <div className="job-list">
        {jobs.length ? (
          jobs.map((job) => (
            <article className="job-card" key={job.id}>
              <div className="job-card-top">
                <div>
                  <h3>{job.title}</h3>
                  <div className="entity-inline">
                    <ProfileAvatar
                      imageUrl={job.company?.logo_url}
                      name={job.company?.name}
                      size="xs"
                      shape="rounded"
                    />
                    {job.company?.id ? (
                      <Link className="inline-link" to={`/companies/${job.company.id}`}>
                        {job.company?.name}
                      </Link>
                    ) : (
                      <p>{job.company?.name}</p>
                    )}
                  </div>
                </div>
                <StatusBadge value={job.work_mode} />
              </div>
              <p>{job.description.slice(0, 180)}...</p>
              <div className="job-meta">
                <span>{job.location}</span>
                <span>{job.experience_level}</span>
                <span>{job.employment_type}</span>
              </div>
              <Link className="inline-link" to={`/jobs/${job.id}`}>
                View details
              </Link>
            </article>
          ))
        ) : (
          <EmptyState title="No jobs yet" body="Try widening the filters or add seed/demo jobs from the company dashboard." />
        )}
      </div>
    </div>
  );
}

export function JobDetailsPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { saveJob, applyToJob } = useJobs();
  const [job, setJob] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [feedback, setFeedback] = useState("");
  const [isPreviewingMatch, setIsPreviewingMatch] = useState(false);
  const [isGeneratingCoverLetter, setIsGeneratingCoverLetter] = useState(false);

  useEffect(() => {
    api.get(`/jobs/${id}`).then(({ data }) => setJob(data));
  }, [id]);

  const previewMatch = async () => {
    setIsPreviewingMatch(true);
    try {
      const { data } = await api.post(`/ai/job-match/${id}`);
      setAnalysis(data);
      setFeedback("");
    } catch (error) {
      setFeedback(getErrorMessage(error, "Unable to preview match."));
    } finally {
      setIsPreviewingMatch(false);
    }
  };

  const generateCoverLetter = async () => {
    setIsGeneratingCoverLetter(true);
    try {
      const { data } = await api.post(`/ai/cover-letter/${id}`);
      setCoverLetter(data.draft);
      setFeedback("");
    } catch (error) {
      setFeedback(getErrorMessage(error, "Unable to generate a cover letter."));
    } finally {
      setIsGeneratingCoverLetter(false);
    }
  };

  const saveCurrentJob = async () => {
    try {
      await saveJob(id);
      setFeedback("Job saved to your shortlist.");
    } catch (error) {
      setFeedback(getErrorMessage(error, "Unable to save this job."));
    }
  };

  const apply = async () => {
    try {
      await applyToJob({ job_id: Number(id), cover_letter: coverLetter || null });
      setFeedback(
        coverLetter
          ? "Application submitted successfully. Your generated cover letter was included."
          : "Application submitted successfully.",
      );
    } catch (error) {
      setFeedback(getErrorMessage(error, "Unable to apply to this job."));
    }
  };

  if (!job) {
    return <div className="center-card">Loading job details...</div>;
  }

  return (
    <div className="page-grid">
      <PageHero
        eyebrow={job.company?.name}
        title={job.title}
        description={job.description}
        action={
          <div className="hero-stack">
            <ProfileAvatar
              imageUrl={job.company?.logo_url}
              name={job.company?.name}
              size="md"
              shape="rounded"
            />
            <StatusBadge value={job.work_mode} />
            {job.company?.id ? (
              <Link className="inline-link" to={`/companies/${job.company.id}`}>
                View company profile
              </Link>
            ) : null}
          </div>
        }
      />
      <MetricStrip
        items={[
          { label: "Location", value: job.location },
          { label: "Experience", value: job.experience_level },
          { label: "Employment", value: job.employment_type },
          { label: "Salary", value: `${job.salary_min || "-"} to ${job.salary_max || "-"}` },
        ]}
      />
      <Panel title="Requirements">
        {job.requirements?.length ? (
          <ul className="feature-list">
            {job.requirements.map((requirement) => (
              <li key={requirement.id}>
                {requirement.skill?.name} {requirement.required_level ? `(${requirement.required_level})` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No explicit requirements" body="This posting currently has no structured skill requirements." />
        )}
      </Panel>
      {user?.role?.name === "candidate" ? (
        <Panel title="Candidate actions" subtitle="Preview your fit, generate a cover letter, and submit one strong application.">
          <div className="action-row">
            <button className="ghost-button" disabled={isPreviewingMatch} onClick={previewMatch} type="button">
              {isPreviewingMatch ? "Analyzing..." : "Preview job match"}
            </button>
            <button className="ghost-button" disabled={isGeneratingCoverLetter} onClick={generateCoverLetter} type="button">
              {isGeneratingCoverLetter ? "Generating..." : "Generate cover letter"}
            </button>
            <button className="ghost-button" onClick={saveCurrentJob} type="button">
              Save job
            </button>
            <button className="primary-button" onClick={apply} type="button">
              Apply now
            </button>
          </div>
          {feedback ? <p className="info-text">{feedback}</p> : null}
          {analysis ? (
            <div className="analysis-grid">
              <div>
                <h3>Match score</h3>
                <p className="score-callout">{analysis.score}</p>
                <p>{analysis.explanation}</p>
              </div>
              <div>
                <h3>Matched skills</h3>
                <p>{analysis.matched_skills.join(", ") || "No direct matches detected yet."}</p>
              </div>
              <div>
                <h3>Missing skills</h3>
                <p>{analysis.missing_skills.join(", ") || "No major skill gaps detected."}</p>
              </div>
            </div>
          ) : null}
          {coverLetter ? (
            <label>
              Draft cover letter
              <textarea rows="8" value={coverLetter} onChange={(event) => setCoverLetter(event.target.value)} />
              <small className="info-text">This draft will be sent with your application when you click Apply now.</small>
            </label>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}

export function CompanyDetailsPage() {
  const { companyId } = useParams();
  const [company, setCompany] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .get(`/companies/${companyId}`)
      .then(({ data }) => {
        setCompany(data);
        setMessage("");
      })
      .catch((error) => {
        setMessage(getErrorMessage(error, "Unable to load this company profile."));
      });
  }, [companyId]);

  if (!company && message) {
    return (
      <div className="center-card">
        <h2>Company profile unavailable</h2>
        <p>{message}</p>
      </div>
    );
  }

  if (!company) {
    return <div className="center-card">Loading company profile...</div>;
  }

  return (
    <div className="page-grid">
      <PageHero
        eyebrow={company.industry || "Company profile"}
        title={company.name}
        description={company.description || "This company has not added a full description yet."}
        action={
          <div className="hero-stack">
            <ProfileAvatar
              imageUrl={company.logo_url}
              name={company.name}
              size="lg"
              shape="rounded"
            />
            {company.website ? (
              <a className="inline-link" href={company.website} rel="noreferrer" target="_blank">
                Visit website
              </a>
            ) : null}
          </div>
        }
      />
      <MetricStrip
        items={[
          { label: "Industry", value: company.industry || "Not set" },
          { label: "Location", value: company.location || "Not set" },
          { label: "Status", value: company.is_active ? "Active" : "Inactive" },
        ]}
      />
      <Panel title="About this company">
        <p>{company.description || "No company description has been added yet."}</p>
      </Panel>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="center-card">
      <h2>Nothing here</h2>
      <p>The page you requested does not exist.</p>
    </div>
  );
}

export function NotificationsPage() {
  const { notifications, markAsRead } = useNotifications();
  const [selectedNotificationId, setSelectedNotificationId] = useState(null);

  const toggleNotification = async (notification) => {
    if (notification.notification_type === "interview_invite") {
      setSelectedNotificationId((current) => (current === notification.id ? null : notification.id));
    }
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
  };

  const handleNotificationKeyDown = (event, notification) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      void toggleNotification(notification);
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Notifications"
        title="See every important update in one place."
        description="Open interview invites to view the schedule, meeting link, location, and notes connected to your application."
      />
      <Panel title="Inbox">
        {notifications.length ? (
          <div className="stack-list">
            {notifications.map((notification) => (
              <article
                className={`stack-item ${notification.notification_type === "interview_invite" ? "interactive-card" : ""}`}
                key={notification.id}
                onClick={
                  notification.notification_type === "interview_invite"
                    ? () => void toggleNotification(notification)
                    : undefined
                }
                onKeyDown={
                  notification.notification_type === "interview_invite"
                    ? (event) => handleNotificationKeyDown(event, notification)
                    : undefined
                }
                role={notification.notification_type === "interview_invite" ? "button" : undefined}
                tabIndex={notification.notification_type === "interview_invite" ? 0 : undefined}
              >
                <div>
                  <strong>{notification.title}</strong>
                  <p>{notification.body}</p>
                </div>
                <div className="application-side" onClick={(event) => event.stopPropagation()}>
                  <StatusBadge value={notification.notification_type} />
                  {notification.notification_type === "interview_invite" ? (
                    <button
                      className="ghost-button"
                      onClick={() => void toggleNotification(notification)}
                      type="button"
                    >
                      {selectedNotificationId === notification.id ? "Hide details" : "Open details"}
                    </button>
                  ) : !notification.is_read ? (
                    <button
                      className="ghost-button"
                      onClick={() => markAsRead(notification.id)}
                      type="button"
                    >
                      Mark read
                    </button>
                  ) : (
                    <small>Read</small>
                  )}
                </div>
                {notification.notification_type === "interview_invite" &&
                selectedNotificationId === notification.id ? (
                  <div className="notification-detail">
                    <div className="detail-grid">
                      <div>
                        <span>Job</span>
                        <strong>{notification.payload?.job_title || "Interview"}</strong>
                      </div>
                      <div>
                        <span>Company</span>
                        <strong>{notification.payload?.company_name || "Company not specified"}</strong>
                      </div>
                      <div>
                        <span>Date and time</span>
                        <strong>
                          {notification.payload?.scheduled_at
                            ? new Date(notification.payload.scheduled_at).toLocaleString()
                            : "To be confirmed"}
                        </strong>
                      </div>
                      <div>
                        <span>Mode</span>
                        <strong>{notification.payload?.mode || "Not specified"}</strong>
                      </div>
                      <div>
                        <span>Location</span>
                        <strong>{notification.payload?.location || "Shared in notes or meeting link"}</strong>
                      </div>
                      <div>
                        <span>Meeting link</span>
                        {notification.payload?.meeting_link ? (
                          <a
                            className="inline-link"
                            href={notification.payload.meeting_link}
                            onClick={(event) => event.stopPropagation()}
                            rel="noreferrer"
                            target="_blank"
                          >
                            Open meeting
                          </a>
                        ) : (
                          <strong>No link added yet</strong>
                        )}
                      </div>
                      <div>
                        <span>Contact email</span>
                        <strong>{notification.payload?.contact_email || "Not provided"}</strong>
                      </div>
                      <div>
                        <span>Contact phone</span>
                        <strong>{notification.payload?.contact_phone || "Not provided"}</strong>
                      </div>
                    </div>
                    {notification.payload?.notes ? (
                      <p className="detail-note">{notification.payload.notes}</p>
                    ) : null}
                    {notification.payload?.job_id ? (
                      <Link
                        className="inline-link"
                        onClick={(event) => event.stopPropagation()}
                        to={`/jobs/${notification.payload.job_id}`}
                      >
                        Review job post
                      </Link>
                    ) : null}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No notifications yet" body="Upload a resume or submit an application to start receiving alerts." />
        )}
      </Panel>
    </div>
  );
}

function defaultRouteForRole(role) {
  if (role === "candidate") return "/candidate/dashboard";
  if (role === "company") return "/company/dashboard";
  if (role === "admin") return "/admin/dashboard";
  return "/";
}
