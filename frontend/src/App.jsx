import { BrowserRouter, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./contexts/AuthContext";
import { JobProvider } from "./contexts/JobContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import { UserProvider } from "./contexts/UserContext";
import {
  AdminDashboardPage,
  ManageCompaniesPage,
  ManageUsersPage,
  SystemOverviewPage,
} from "./pages/AdminPages";
import {
  CandidateAnalysisPage,
  CandidateApplicationsPage,
  CandidateDashboardPage,
  CandidateProfilePage,
  CandidateResumePage,
  RecommendedJobsPage,
  SavedJobsPage,
} from "./pages/CandidatePages";
import {
  CandidateRankingPage,
  CompanyDashboardPage,
  CompanyProfilePage,
  CreateJobPage,
  JobApplicationsPage,
  ManageJobsPage,
} from "./pages/CompanyPages";
import {
  CompanyDetailsPage,
  HomePage,
  JobDetailsPage,
  JobsPage,
  LoginPage,
  NotFoundPage,
  NotificationsPage,
  RegisterPage,
} from "./pages/PublicPages";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <UserProvider>
            <JobProvider>
              <Routes>
                <Route element={<Layout />}>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/jobs" element={<JobsPage />} />
                  <Route path="/jobs/:id" element={<JobDetailsPage />} />
                  <Route path="/companies/:companyId" element={<CompanyDetailsPage />} />
                  <Route
                    path="/notifications"
                    element={
                      <ProtectedRoute roles={["candidate", "company", "admin"]}>
                        <NotificationsPage />
                      </ProtectedRoute>
                    }
                  />

                  <Route
                    path="/candidate/dashboard"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <CandidateDashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/profile"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <CandidateProfilePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/resume"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <CandidateResumePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/analysis"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <CandidateAnalysisPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/recommended-jobs"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <RecommendedJobsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/applications"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <CandidateApplicationsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/candidate/saved-jobs"
                    element={
                      <ProtectedRoute roles={["candidate"]}>
                        <SavedJobsPage />
                      </ProtectedRoute>
                    }
                  />

                  <Route
                    path="/company/dashboard"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <CompanyDashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/company/profile"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <CompanyProfilePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/company/create-job"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <CreateJobPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/company/manage-jobs"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <ManageJobsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/company/applications"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <JobApplicationsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/company/ranking"
                    element={
                      <ProtectedRoute roles={["company"]}>
                        <CandidateRankingPage />
                      </ProtectedRoute>
                    }
                  />

                  <Route
                    path="/admin/dashboard"
                    element={
                      <ProtectedRoute roles={["admin"]}>
                        <AdminDashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/users"
                    element={
                      <ProtectedRoute roles={["admin"]}>
                        <ManageUsersPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/companies"
                    element={
                      <ProtectedRoute roles={["admin"]}>
                        <ManageCompaniesPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/system"
                    element={
                      <ProtectedRoute roles={["admin"]}>
                        <SystemOverviewPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </JobProvider>
          </UserProvider>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
