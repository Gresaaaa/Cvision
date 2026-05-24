import { createContext, useContext, useState } from "react";

import api from "../api/client";

const JobContext = createContext(null);

function toQueryString(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, value);
    }
  });
  return params.toString();
}

export function JobProvider({ children }) {
  const [jobs, setJobs] = useState([]);
  const [savedJobs, setSavedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchJobs = async (filters = {}) => {
    setIsLoading(true);
    try {
      const query = toQueryString(filters);
      const { data } = await api.get(query ? `/search/jobs?${query}` : "/jobs");
      setJobs(data);
      return data;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSavedJobs = async () => {
    const { data } = await api.get("/saved-jobs");
    setSavedJobs(data);
    return data;
  };

  const fetchMyApplications = async () => {
    const { data } = await api.get("/applications/my");
    setApplications(data);
    return data;
  };