import { useEffect, useMemo, useState } from "react";

import api, { getErrorMessage } from "../api/client";
import { EmptyState, MetricStrip, PageHero, Panel, ProfileAvatar, StatusBadge } from "../components/UI";
import { INDUSTRY_OPTIONS } from "../constants/options";
import { useAuth } from "../contexts/AuthContext";
import { useJobs } from "../contexts/JobContext";
import { useUserData } from "../contexts/UserContext";

export function CompanyDashboardPage() {
  const { user } = useAuth();
  const { companyProfile } = useUserData();
  const { fetchJobs } = useJobs();
  const [jobs, setJobs] = useState([]);
  const displayCompany = companyProfile || user?.company || null;

  useEffect(() => {
    fetchJobs().then((data) => {
      setJobs(data.filter((job) => job.company?.id === user?.company?.id));
    });
  }, [user?.company?.id]);

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Company workspace"
        title={displayCompany?.name || "Recruiter dashboard"}
        description="Publish roles, review applications, and keep candidate data scoped to your own tenant."
      />
      <MetricStrip
        items={[
          { label: "Published jobs", value: jobs.length },
          { label: "Industry", value: displayCompany?.industry || "Not set" },
          { label: "Location", value: displayCompany?.location || "Not set" },
          { label: "Tenant scope", value: "Company-owned data" },
        ]}
      />
      <Panel title="Current positions">
        {jobs.length ? (
          <div className="stack-list">
            {jobs.map((job) => (
              <article className="stack-item" key={job.id}>
                <div>
                  <strong>{job.title}</strong>
                  <p>{job.location}</p>
                </div>
                <StatusBadge value={job.is_active ? "active" : "inactive"} />
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No company jobs yet" body="Create a job post to start collecting applications." />
        )}
      </Panel>
    </div>
  );
}
export function CompanyProfilePage() {
  const { user } = useAuth();
  const { companyProfile, updateCompanyProfile, uploadCompanyLogo } = useUserData();
  const [form, setForm] = useState({
    name: "",
    description: "",
    website: "",
    industry: "",
    location: "",
  });
  const [message, setMessage] = useState("");
  const [logoFile, setLogoFile] = useState(null);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);

  useEffect(() => {
    const profileSource = companyProfile || user?.company;
    if (profileSource) {
      setForm({
        name: profileSource.name || "",
        description: profileSource.description || "",
        website: profileSource.website || "",
        industry: profileSource.industry || "",
        location: profileSource.location || "",
      });
    }
  }, [companyProfile?.id, user?.company?.id]);

  const submit = async (event) => {
    event.preventDefault();
    try {
      await updateCompanyProfile(form);
      setMessage("Company profile updated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to update company profile."));
    }
  };

  const uploadLogo = async (event) => {
    event.preventDefault();
    if (!logoFile) return;
    setIsUploadingLogo(true);
    try {
      await uploadCompanyLogo(logoFile);
      setLogoFile(null);
      setMessage("Company logo updated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to upload company logo."));
    } finally {
      setIsUploadingLogo(false);
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Company profile"
        title="Own the way candidates meet your brand."
        description="This profile powers company cards in job listings and recruiter context across the platform."
      />
      <Panel title="Edit company profile">
        <div className="media-upload-card">
          <div className="media-upload-preview">
            <ProfileAvatar
              imageUrl={companyProfile?.logo_url || user?.company?.logo_url}
              name={companyProfile?.name || user?.company?.name}
              size="xl"
              shape="rounded"
            />
            <div>
              <h3>Company logo</h3>
              <p>Upload your logo so candidates instantly recognize your company in jobs and applications.</p>
            </div>
          </div>
          <form className="media-upload-form" onSubmit={uploadLogo}>
            <input
              accept=".png,.jpg,.jpeg,.webp"
              onChange={(event) => setLogoFile(event.target.files?.[0] || null)}
              type="file"
            />
            <button className="ghost-button" disabled={!logoFile || isUploadingLogo} type="submit">
              {isUploadingLogo ? "Uploading logo..." : "Upload logo"}
            </button>
          </form>
        </div>
        <form className="form-grid" onSubmit={submit}>
          <div className="inline-grid">
            <label>
              Company name
              <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
            </label>
            <label>
              Website
              <input
                type="url"
                placeholder="https://company.com"
                value={form.website}
                onChange={(event) => setForm((current) => ({ ...current, website: event.target.value }))}
              />
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Industry
              <input
                list="company-industry-options"
                value={form.industry}
                onChange={(event) => setForm((current) => ({ ...current, industry: event.target.value }))}
                placeholder="Choose from the list or type your own"
              />
            </label>
            <label>
              Location
              <input value={form.location} onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))} />
            </label>
          </div>
          <datalist id="company-industry-options">
            {INDUSTRY_OPTIONS.map((industry) => (
              <option key={industry} value={industry} />
            ))}
          </datalist>
          <label>
            Description
            <textarea rows="6" value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} />
          </label>
          {message ? <p className="info-text">{message}</p> : null}
          <button className="primary-button" type="submit">
            Save company profile
          </button>
        </form>
      </Panel>
    </div>
  );
}

export function CreateJobPage() {
  const { createJob } = useJobs();
  const [categories, setCategories] = useState([]);
  const [skills, setSkills] = useState([]);
  const [message, setMessage] = useState("");
  const emptyRequirement = () => ({
    skill_id: "",
    skill_name: "",
    required_level: "mid",
    is_mandatory: true,
  });
  const [form, setForm] = useState({
    title: "",
    description: "",
    location: "",
    category_id: "",
    employment_type: "full_time",
    work_mode: "hybrid",
    salary_min: "",
    salary_max: "",
    experience_level: "mid",
    requirements: [emptyRequirement()],
  });

  useEffect(() => {
    Promise.all([api.get("/taxonomy/categories"), api.get("/taxonomy/skills")]).then(([categoryRes, skillRes]) => {
      setCategories(categoryRes.data);
      setSkills(skillRes.data);
    });
  }, []);

  const updateRequirement = (index, field, value) => {
    setForm((current) => ({
      ...current,
      requirements: current.requirements.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item,
      ),
    }));
  };

  const updateRequirementSkill = (index, value) => {
    setForm((current) => ({
      ...current,
      requirements: current.requirements.map((item, itemIndex) =>
        itemIndex === index ? { ...item, skill_id: value, skill_name: value ? "" : item.skill_name } : item,
      ),
    }));
  };

  const updateRequirementName = (index, value) => {
    setForm((current) => ({
      ...current,
      requirements: current.requirements.map((item, itemIndex) =>
        itemIndex === index ? { ...item, skill_name: value, skill_id: value ? "" : item.skill_id } : item,
      ),
    }));
  };

  const addRequirement = () => {
    setForm((current) => ({
      ...current,
      requirements: [...current.requirements, emptyRequirement()],
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    const normalizedTitle = form.title.trim();
    const normalizedLocation = form.location.trim();
    const normalizedDescription = form.description.trim();
    const normalizedRequirements = form.requirements
      .map((item) => ({
        ...item,
        skill_name: item.skill_name.trim(),
        required_level: item.required_level.trim(),
      }))
      .filter((item) => item.skill_id || item.skill_name);

    if (normalizedTitle.length < 2) {
      setMessage("Job title must be at least 2 characters.");
      return;
    }
    if (normalizedLocation.length < 2) {
      setMessage("Location must be at least 2 characters.");
      return;
    }
    if (normalizedDescription.length < 20) {
      setMessage("Description must be at least 20 characters so candidates clearly understand the role.");
      return;
    }
    if (form.salary_min && form.salary_max && Number(form.salary_max) < Number(form.salary_min)) {
      setMessage("Salary max must be greater than or equal to salary min.");
      return;
    }

    try {
      setMessage("");
      await createJob({
        ...form,
        title: normalizedTitle,
        description: normalizedDescription,
        location: normalizedLocation,
        category_id: form.category_id ? Number(form.category_id) : null,
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
        requirements: normalizedRequirements
          .map((item) => ({
            required_level: item.required_level,
            is_mandatory: item.is_mandatory,
            skill_id: item.skill_id ? Number(item.skill_id) : null,
            skill_name: item.skill_id ? null : item.skill_name,
          })),
      });
      setMessage("Job created successfully.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to create job."));
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Create a job"
        title="Publish roles that match the way your team hires."
        description="Choose from saved skills or type your own requirements when you need something more specific."
      />
      <Panel title="Job creation form">
        <form className="form-grid" onSubmit={submit}>
          <div className="inline-grid">
            <label>
              Title
              <input
                minLength={2}
                value={form.title}
                onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                required
              />
            </label>
            <label>
              Location
              <input
                minLength={2}
                value={form.location}
                onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
                required
              />
            </label>
          </div>
          <label>
            Description
            <textarea
              minLength={20}
              rows="7"
              value={form.description}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              required
            />
          </label>
          <div className="inline-grid">
            <label>
              Category
              <select value={form.category_id} onChange={(event) => setForm((current) => ({ ...current, category_id: event.target.value }))}>
                <option value="">Select one</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Experience level
              <select value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}>
                <option value="junior">Junior</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
              </select>
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Employment type
              <select value={form.employment_type} onChange={(event) => setForm((current) => ({ ...current, employment_type: event.target.value }))}>
                <option value="full_time">Full time</option>
                <option value="part_time">Part time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </label>
            <label>
              Work mode
              <select value={form.work_mode} onChange={(event) => setForm((current) => ({ ...current, work_mode: event.target.value }))}>
                <option value="remote">Remote</option>
                <option value="onsite">Onsite</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </label>
          </div>
          <div className="inline-grid">
            <label>
              Salary min
              <input
                min="0"
                type="number"
                value={form.salary_min}
                onChange={(event) => setForm((current) => ({ ...current, salary_min: event.target.value }))}
              />
            </label>
            <label>
              Salary max
              <input
                min="0"
                type="number"
                value={form.salary_max}
                onChange={(event) => setForm((current) => ({ ...current, salary_max: event.target.value }))}
              />
            </label>
          </div>
          <div className="nested-panel">
            <div className="panel-header">
              <div>
                <h2>Requirements</h2>
                <p>Pick a saved skill or write a custom requirement for this role.</p>
              </div>
              <button className="ghost-button" onClick={addRequirement} type="button">
                Add requirement
              </button>
            </div>
            {form.requirements.map((requirement, index) => (
              <div className="inline-grid" key={`req-${index}`}>
                <label>
                  Skill
                  <select
                    value={requirement.skill_id}
                    onChange={(event) => updateRequirementSkill(index, event.target.value)}
                  >
                    <option value="">Select a skill</option>
                    {skills.map((skill) => (
                      <option key={skill.id} value={skill.id}>
                        {skill.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Custom requirement
                  <input
                    value={requirement.skill_name}
                    onChange={(event) => updateRequirementName(index, event.target.value)}
                    placeholder="Type your own if it is not listed"
                  />
                </label>
                <label>
                  Level
                  <input
                    value={requirement.required_level}
                    onChange={(event) => updateRequirement(index, "required_level", event.target.value)}
                  />
                </label>
              </div>
            ))}
          </div>
          {message ? <p className="info-text">{message}</p> : null}
          <button className="primary-button" type="submit">
            Publish job
          </button>
        </form>
      </Panel>
    </div>
  );
}

export function ManageJobsPage() {
  const { user } = useAuth();
  const { fetchJobs } = useJobs();
  const [jobs, setJobs] = useState([]);
  const [message, setMessage] = useState("");

  const loadJobs = async () => {
    const allJobs = await fetchJobs();
    setJobs(allJobs.filter((job) => job.company?.id === user?.company?.id));
  };

  useEffect(() => {
    loadJobs();
  }, [user?.company?.id]);

  const deactivate = async (jobId) => {
    try {
      await api.delete(`/jobs/${jobId}`);
      await loadJobs();
      setMessage("Job deactivated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to update this job."));
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Manage jobs"
        title="Review, monitor, and retire job postings."
        description="Recruiters can only operate on jobs belonging to their own company tenant."
      />
      <Panel title="Your jobs">
        {message ? <p className="info-text">{message}</p> : null}
        {jobs.length ? (
          <div className="stack-list">
            {jobs.map((job) => (
              <article className="stack-item" key={job.id}>
                <div>
                  <strong>{job.title}</strong>
                  <p>{job.location}</p>
                </div>
                <div className="action-row">
                  <StatusBadge value={job.is_active ? "active" : "inactive"} />
                  <button className="ghost-button" onClick={() => deactivate(job.id)} type="button">
                    Deactivate
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No jobs to manage" body="Create your first job post to populate this workspace." />
        )}
      </Panel>
    </div>
  );
}