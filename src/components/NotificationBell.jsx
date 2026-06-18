import React, { useState, useEffect } from 'react';
import { Bell, Check, AlertTriangle, Info } from 'lucide-react';
import { getNotifications, markNotificationRead } from '../api';
import { useAuth } from '../AuthContext';

export default function NotificationBell() {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  const fetchNotifs = async () => {
    if (!isAuthenticated) return;
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch (e) {
      console.error("Failed to fetch notifications", e);
    }
  };

  useEffect(() => {
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const handleMarkRead = async (id, e) => {
    e.stopPropagation();
    try {
      await markNotificationRead(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="relative" style={{ marginRight: '1rem' }}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-full hover:bg-slate-100 transition-colors focus:outline-none"
      >
        <Bell size={20} className="text-slate-600" />
        {notifications.length > 0 && (
          <span className="absolute top-1 right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-slate-200 z-50">
          <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-lg">
            <h3 className="font-semibold text-slate-800">Notifications</h3>
            <span className="text-xs text-slate-500">{notifications.length} unread</span>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-slate-500 text-sm">
                No new notifications
              </div>
            ) : (
              notifications.map(notif => (
                <div key={notif.id} className="p-3 border-b border-slate-50 hover:bg-slate-50 flex gap-3 items-start group">
                  <div className="mt-0.5">
                    {notif.notification_type === 'alert' ? 
                      <AlertTriangle size={16} className="text-red-500" /> : 
                      <Info size={16} className="text-blue-500" />
                    }
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-800">{notif.message}</p>
                    <span className="text-xs text-slate-400 block mt-1">
                      {new Date(notif.created_at).toLocaleString()}
                    </span>
                  </div>
                  <button 
                    onClick={(e) => handleMarkRead(notif.id, e)}
                    className="p-1 rounded-full hover:bg-slate-200 text-slate-400 hover:text-green-600 transition-colors opacity-0 group-hover:opacity-100"
                    title="Mark as read"
                  >
                    <Check size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
