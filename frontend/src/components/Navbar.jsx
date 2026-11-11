import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Bell, LogOut, Menu, User, X, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { publicApi } from '../api/client';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    let cancelled = false;
    const loadNotifs = () => {
      publicApi
        .notifications()
        .then((res) => {
          if (!cancelled) {
            setNotifications(res.notifications || []);
            setUnreadCount(res.unread_count || 0);
          }
        })
        .catch(() => {});
    };

    loadNotifs();
    const timer = setInterval(loadNotifs, 12000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [user, location.pathname]);

  const handleMarkRead = async () => {
    try {
      await publicApi.markNotificationsRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navLinks = !user
    ? [
        { to: '/', label: 'Home' },
        { to: '/electricians', label: 'Find Electricians' },
        { to: '/login', label: 'Sign In' },
      ]
    : user.role === 'customer'
    ? [
        { to: '/customer/dashboard', label: 'Dashboard' },
        { to: '/request-service', label: 'Request Service' },
        { to: '/electricians', label: 'Directory' },
        { to: '/customer/profile', label: 'Profile' },
      ]
    : user.role === 'electrician'
    ? [
        { to: '/electrician/dashboard', label: 'Workspace' },
        { to: '/electrician/profile', label: 'Profile & Hours' },
      ]
    : [
        { to: '/admin/dashboard', label: 'Admin Console' },
        { to: '/electricians', label: 'Directory' },
      ];

  return (
    <header className="sticky top-0 z-40 bg-navy text-ivory border-b border-white/10 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-electric text-navy flex items-center justify-center shadow group-hover:scale-105 transition-transform">
            <Zap className="w-5 h-5 fill-navy" />
          </div>
          <div>
            <span className="font-extrabold tracking-tight text-lg text-white">BIJLI</span>
            <span className="font-extrabold tracking-tight text-lg text-electric">BUDDY</span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-2">
          {navLinks.map((link) => {
            const active = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                  active ? 'bg-white/15 text-electric' : 'text-ivory/85 hover:text-white hover:bg-white/10'
                }`}
              >
                {link.label}
              </Link>
            );
          })}

          {!user ? (
            <Link
              to="/register"
              className="ml-2 px-4 py-2 rounded-xl bg-electric hover:bg-electric-hover text-navy font-bold text-sm transition-colors"
            >
              Get Started
            </Link>
          ) : (
            <div className="flex items-center gap-2 ml-2 pl-3 border-l border-white/15 relative">
              <button
                onClick={() => setNotifOpen((v) => !v)}
                className="relative p-2 rounded-xl hover:bg-white/10 text-ivory transition-colors"
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-electric text-navy text-[10px] font-extrabold flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {notifOpen && (
                <div className="absolute right-0 top-12 w-80 bg-white text-navy rounded-2xl shadow-elevated border border-[#E8E4D8] overflow-hidden z-50">
                  <div className="px-4 py-3 bg-[#FAF9F5] border-b border-[#E8E4D8] flex items-center justify-between">
                    <span className="font-bold text-sm">Notifications</span>
                    {unreadCount > 0 && (
                      <button onClick={handleMarkRead} className="text-xs font-semibold text-navy underline">
                        Mark all read
                      </button>
                    )}
                  </div>
                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="p-4 text-xs text-slate-500 text-center">No notifications yet.</div>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          onClick={() => {
                            setNotifOpen(false);
                            if (n.related_booking_id) navigate(`/bookings/${n.related_booking_id}`);
                          }}
                          className={`p-3 text-xs cursor-pointer hover:bg-[#FAF9F5] ${
                            !n.is_read ? 'bg-amber-50/70' : ''
                          }`}
                        >
                          <div className="font-bold text-navy">{n.title}</div>
                          <div className="text-slate-600 mt-0.5">{n.message}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 text-xs">
                <User className="w-3.5 h-3.5 text-electric" />
                <span className="font-semibold truncate max-w-[120px]">{user.full_name}</span>
                <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-electric text-navy font-bold">
                  {user.role}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="p-2 rounded-xl hover:bg-rose-500/20 text-ivory/80 hover:text-rose-200 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </nav>

        {/* Mobile menu trigger */}
        <button
          onClick={() => setMobileOpen((v) => !v)}
          className="md:hidden p-2 rounded-xl hover:bg-white/10"
          aria-label="Toggle Menu"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-navy-light border-t border-white/10 px-4 py-3 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-xl text-sm font-semibold hover:bg-white/10"
            >
              {link.label}
            </Link>
          ))}
          {!user ? (
            <Link
              to="/register"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-xl bg-electric text-navy font-bold text-sm text-center"
            >
              Get Started
            </Link>
          ) : (
            <button
              onClick={() => {
                setMobileOpen(false);
                handleLogout();
              }}
              className="w-full text-left px-3 py-2 rounded-xl text-sm font-semibold text-rose-200 hover:bg-white/10"
            >
              Sign Out ({user.full_name})
            </button>
          )}
        </div>
      )}
    </header>
  );
}
