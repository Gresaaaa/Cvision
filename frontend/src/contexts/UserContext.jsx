import { createContext, useContext, useEffect, useState } from "react";

import api from "../api/client";
import { useAuth } from "./AuthContext";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const { isAuthenticated, isLoading: authLoading, user, refreshMe } = useAuth();
  const [candidateProfile, setCandidateProfile] = useState(null);
  const [companyProfile, setCompanyProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshUserData = async () => {
    if (!isAuthenticated || !user) return;
    if (user.role.name === "company" && user.company) {
      setCompanyProfile((current) => current || user.company);
    }
    setIsLoading(true);
    try {
      if (user.role.name === "candidate") {
        const { data } = await api.get("/users/profile");
        setCandidateProfile(data);
        setCompanyProfile(null);
      } else if (user.role.name === "company") {
        const { data } = await api.get("/companies/me");
        setCompanyProfile(data);
        setCandidateProfile(null);
      } else {
        setCandidateProfile(null);
        setCompanyProfile(null);
      }
    } catch {
      setCandidateProfile(null);
      setCompanyProfile(user.role.name === "company" ? user.company || null : null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      refreshUserData();
    }
  }, [authLoading, isAuthenticated, user?.id]);

  const updateCandidateProfile = async (payload) => {
    const { data } = await api.put("/users/profile", payload);
    setCandidateProfile(data);
    return data;
  };

  const uploadCandidateAvatar = async (file) => {
    const payload = new FormData();
    payload.set("file", file);
    const { data } = await api.post("/users/profile/avatar", payload, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setCandidateProfile(data);
    return data;
  };

  const updateCompanyProfile = async (payload) => {
    const { data } = await api.put("/companies/me", payload);
    setCompanyProfile(data);
    await refreshMe();
    return data;
  };

  const uploadCompanyLogo = async (file) => {
    const payload = new FormData();
    payload.set("file", file);
    const { data } = await api.post("/companies/me/logo", payload, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setCompanyProfile(data);
    await refreshMe();
    return data;
  };

  return (
    <UserContext.Provider
      value={{
        candidateProfile,
        companyProfile,
        isLoading,
        refreshUserData,
        updateCandidateProfile,
        uploadCandidateAvatar,
        updateCompanyProfile,
        uploadCompanyLogo,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUserData() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUserData must be used inside UserProvider");
  }
  return context;
}
