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
