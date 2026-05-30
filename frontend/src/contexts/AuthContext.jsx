import { createContext, useContext, useEffect, useState } from "react";

import api, { getErrorMessage, setAuthToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("cvision-token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("cvision-user");
    return raw ? JSON.parse(raw) : null;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    setAuthToken(token);
    if (!token) {
      setIsLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then(({ data }) => {
        setUser(data);
        localStorage.setItem("cvision-user", JSON.stringify(data));
      })
      .catch(() => {
        setToken(null);
        setUser(null);
        localStorage.removeItem("cvision-token");
        localStorage.removeItem("cvision-user");
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const persistSession = (nextToken, nextUser) => {
    setToken(nextToken);
    setUser(nextUser);
    setAuthToken(nextToken);
    localStorage.setItem("cvision-token", nextToken);
    localStorage.setItem("cvision-user", JSON.stringify(nextUser));
  };

  const login = async ({ email, password }) => {
    setAuthError("");
    const payload = new URLSearchParams();
    payload.set("username", email);
    payload.set("password", password);
    try {
      const { data } = await api.post("/auth/login", payload, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      persistSession(data.access_token, data.user);
      return data.user;
    } catch (error) {
      const message = getErrorMessage(error, "Unable to log in.");
      setAuthError(message);
      throw new Error(message);
    }
  };

  const register = async (payload) => {
    setAuthError("");
    try {
      const { data } = await api.post("/auth/register", payload);
      persistSession(data.access_token, data.user);
      return data.user;
    } catch (error) {
      const message = getErrorMessage(error, "Unable to register.");
      setAuthError(message);
      throw new Error(message);
    }
  };

  const refreshMe = async () => {
    if (!token) return null;
    const { data } = await api.get("/auth/me");
    setUser(data);
    localStorage.setItem("cvision-user", JSON.stringify(data));
    return data;
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post("/auth/logout");
      }
    } catch {
      // The client owns JWT deletion, so this failure is non-blocking.
    } finally {
      setToken(null);
      setUser(null);
      setAuthToken(null);
      localStorage.removeItem("cvision-token");
      localStorage.removeItem("cvision-user");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: Boolean(token && user),
        isLoading,
        authError,
        login,
        register,
        refreshMe,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
