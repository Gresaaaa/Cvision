import { useEffect, useState } from "react";

import api, { getErrorMessage } from "../api/client";
import { EmptyState, MetricStrip, PageHero, Panel } from "../components/UI";

export function AdminDashboardPage() {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    api.get("/admin/system-overview").then(({ data }) => setOverview(data));
  }, []);

  if (!overview) {
    return <div className="center-card">Loading admin dashboard...</div>;
  }

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Admin control plane"
        title="Keep users, companies, taxonomies, and metrics in view."
        description="This dashboard is backed by the admin-only API surface and audit-aware data model."
      />
      <MetricStrip
        items={[
          { label: "Users", value: overview.total_users },
          { label: "Companies", value: overview.total_companies },
          { label: "Candidates", value: overview.total_candidates },
          { label: "Applications", value: overview.total_applications },
        ]}
      />
    </div>
  );
}
