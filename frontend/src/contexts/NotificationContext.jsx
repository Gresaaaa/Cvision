import { createContext, useContext, useEffect, useState } from "react";

import api from "../api/client";
import { useAuth } from "./AuthContext";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);

  const refreshNotifications = async () => {
    if (!isAuthenticated) {
      setNotifications([]);
      return [];
    }
    const { data } = await api.get("/notifications");
    setNotifications(data);
    return data;
  };

  const markAsRead = async (notificationId) => {
    const { data } = await api.patch(`/notifications/${notificationId}/read`);
    setNotifications((current) =>
      current.map((notification) => (notification.id === notificationId ? data : notification)),
    );
    return data;
  };

  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      return undefined;
    }
    refreshNotifications();
    const timer = setInterval(refreshNotifications, 25000);
    return () => clearInterval(timer);
  }, [isAuthenticated]);

  const unreadCount = notifications.filter((item) => !item.is_read).length;

  return (
    <NotificationContext.Provider
      value={{ notifications, unreadCount, refreshNotifications, markAsRead }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used inside NotificationProvider");
  }
  return context;
}