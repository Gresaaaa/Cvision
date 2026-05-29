import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";
import { useUserData } from "../contexts/UserContext";
import { ProfileAvatar } from "./UI";

function roleLinks(role) {
  const common = [
    { to: "/", label: "Home" },
    { to: "/jobs", label: "Jobs" },
  ];
  if (role === "candidate") {
    return [
      ...common,
      { to: "/candidate/dashboard", label: "Dashboard" },
      { to: "/candidate/profile", label: "My Profile" },
      { to: "/candidate/resume", label: "My Resume" },
      { to: "/candidate/applications", label: "Applications" },
      { to: "/candidate/saved-jobs", label: "Saved Jobs" },
    ];
  }
  if (role === "company") {
    return [
      ...common,
      { to: "/company/dashboard", label: "Dashboard" },
      { to: "/company/profile", label: "Company Profile" },
      { to: "/company/create-job", label: "Create Job" },
      { to: "/company/manage-jobs", label: "Manage Jobs" },
      { to: "/company/applications", label: "Manage Candidates" },
      { to: "/company/ranking", label: "Candidate Ranking" },
    ];
  }
  if (role === "admin") {
    return [
      ...common,
      { to: "/admin/dashboard", label: "Dashboard" },
      { to: "/admin/users", label: "Users" },
      { to: "/admin/companies", label: "Companies" },
      { to: "/admin/system", label: "System" },
    ];
  }
  return common.concat([
    { to: "/login", label: "Login" },
    { to: "/register", label: "Register" },
  ]);
}

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const { unreadCount } = useNotifications();
  const { candidateProfile, companyProfile } = useUserData();
  const links = roleLinks(user?.role?.name);
  const identityName =
    user?.role?.name === "company"
      ? companyProfile?.name || user?.company?.name || user?.full_name
      : user?.full_name;
  const identitySubtitle = user?.role?.name === "company" ? "company" : user?.role?.name;
  const identityImage =
    user?.role?.name === "company"
      ? companyProfile?.logo_url || user?.company?.logo_url
      : candidateProfile?.avatar_url;

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">
            <span className="brand-orbit" />
            <span className="brand-core">CV</span>
          </span>
          <span className="brand-copy">
            <strong>CVision</strong>
          </span>
        </NavLink>

        <nav className="nav-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              end={link.to === "/"}
              to={link.to}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar-actions">
          {isAuthenticated ? (
            <>
              <NavLink
                className={({ isActive }) => `pill-link${isActive ? " active" : ""}`}
                to="/notifications"
              >
                Alerts <span>{unreadCount}</span>
              </NavLink>
              <div className="identity-chip">
                <ProfileAvatar imageUrl={identityImage} name={identityName} size="sm" shape="circle" />
                <div className="identity-copy">
                  <strong>{identityName}</strong>
                  <small>{identitySubtitle}</small>
                </div>
              </div>
              <button className="ghost-button" onClick={logout} type="button">
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink className="ghost-button" to="/login">
                Login
              </NavLink>
              <NavLink className="primary-button" to="/register">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </header>

      <main className="page-shell">
        <Outlet />
      </main>
    </div>
  );
}
