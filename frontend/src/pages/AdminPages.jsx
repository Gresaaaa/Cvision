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
}export function ManageUsersPage() {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState("");

  const loadUsers = async () => {
    const { data } = await api.get("/admin/users");
    setUsers(data);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const updateUserStatus = async (userId, action) => {
    try {
      await api.patch(`/admin/users/${userId}/${action}`);
      await loadUsers();
      setMessage(action === "deactivate" ? "User deactivated." : "User reactivated.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to update this user."));
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Delete ${user.email}? This removes their linked profile and related records.`)) {
      return;
    }
    try {
      await api.delete(`/admin/users/${user.id}`);
      await loadUsers();
      setMessage("User deleted.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to delete this user."));
    }
  };
    return (
    <div className="page-grid">
      <PageHero
        eyebrow="Users"
        title="Review account distribution and access roles."
        description="Admin-level user management is wired to the protected backend endpoints."
      />
      <Panel title="All users">
        {message ? <p className="info-text">{message}</p> : null}
        {users.length ? (
          <div className="data-table">
            <div className="table-head">
              <span>Name</span>
              <span>Email</span>
              <span>Role</span>
              <span>Status</span>
              <span>Actions</span>
            </div>
            {users.map((user) => (
              <div className="table-row" key={user.id}>
                <span>{user.full_name}</span>
                <span>{user.email}</span>
                <span>{user.role?.name}</span>
                <span>{user.is_active ? "Active" : "Inactive"}</span>
                <div className="action-row table-actions">
                  {user.is_active ? (
                    <button className="ghost-button" onClick={() => updateUserStatus(user.id, "deactivate")} type="button">
                      Deactivate
                    </button>
                  ) : (
                    <button className="ghost-button" onClick={() => updateUserStatus(user.id, "reactivate")} type="button">
                      Reactivate
                    </button>
                  )}
                  <button className="ghost-button" onClick={() => deleteUser(user)} type="button">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No users found" body="Seed data or new registrations will populate this table." />
        )}
      </Panel>
    </div>
  );
}

export function ManageCompaniesPage() {
  const [companies, setCompanies] = useState([]);
  const [message, setMessage] = useState("");

  const loadCompanies = async () => {
    const { data } = await api.get("/admin/companies");
    setCompanies(data);
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  const deleteCompany = async (company) => {
    if (
      !window.confirm(
        `Delete ${company.name}? This also removes the company jobs, linked recruiter accounts, and related applications.`,
      )
    ) {
      return;
    }
    try {
      await api.delete(`/admin/companies/${company.id}`);
      await loadCompanies();
      setMessage("Company deleted.");
    } catch (error) {
      setMessage(getErrorMessage(error, "Unable to delete this company."));
    }
  };

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="Companies"
        title="Monitor tenant entries across the platform."
        description="This list gives admins a clear view of active company records."
      />
      <Panel title="All companies">
        {message ? <p className="info-text">{message}</p> : null}
        {companies.length ? (
          <div className="data-table">
            <div className="table-head">
              <span>Name</span>
              <span>Industry</span>
              <span>Location</span>
              <span>Status</span>
              <span>Actions</span>
            </div>
            {companies.map((company) => (
              <div className="table-row" key={company.id}>
                <span>{company.name}</span>
                <span>{company.industry || "-"}</span>
                <span>{company.location || "-"}</span>
                <span>{company.is_active ? "Active" : "Inactive"}</span>
                <div className="action-row table-actions">
                  <button className="ghost-button" onClick={() => deleteCompany(company)} type="button">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No companies found" body="Company registrations will appear here." />
        )}
      </Panel>
    </div>
  );
}
export function SystemOverviewPage() {
  const [overview, setOverview] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);

  useEffect(() => {
    Promise.all([api.get("/admin/system-overview"), api.get("/admin/audit-logs")]).then(
      ([overviewRes, auditRes]) => {
        setOverview(overviewRes.data);
        setAuditLogs(auditRes.data);
      },
    );
  }, []);

  return (
    <div className="page-grid">
      <PageHero
        eyebrow="System overview"
        title="Operational stats and recent audit activity."
        description="This is where the backend monitoring requirement becomes visible in the UI."
      />
      {overview ? (
        <MetricStrip
          items={[
            { label: "Total jobs", value: overview.total_jobs },
            { label: "Active jobs", value: overview.active_jobs },
            { label: "Skills", value: overview.total_skills },
            { label: "Unread alerts", value: overview.unread_notifications },
          ]}
        />
      ) : null}
      <Panel title="Recent audit activity">
        {auditLogs.length ? (
          <div className="stack-list">
            {auditLogs.map((log) => (
              <article className="stack-item" key={log.id}>
                <div>
                  <strong>{log.action}</strong>
                  <p>
                    {log.entity_type} #{log.entity_id}
                  </p>
                </div>
                <small>{new Date(log.created_at).toLocaleString()}</small>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="No audit events yet" body="Activity logs appear once the system starts receiving actions." />
        )}
      </Panel>
    </div>
  );
}