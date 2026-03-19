import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchAttendanceStats, fetchStudents } from '../api';
import { ArrowLeft, AlertTriangle, TrendingDown, Users, Clock, ChevronDown, ChevronUp } from 'lucide-react';

export default function AttendancePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | low | critical
  const [expandedSchool, setExpandedSchool] = useState(null);
  const [schoolStudents, setSchoolStudents] = useState({});
  const [loadingStudents, setLoadingStudents] = useState({});

  useEffect(() => {
    fetchAttendanceStats()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Lazy-load students only when a school is expanded
  const toggleSchool = async (schoolId) => {
    if (expandedSchool === schoolId) {
      setExpandedSchool(null);
      return;
    }
    setExpandedSchool(schoolId);

    if (!schoolStudents[schoolId]) {
      setLoadingStudents(prev => ({ ...prev, [schoolId]: true }));
      try {
        const students = await fetchStudents({ school_id: schoolId, limit: 50 });
        setSchoolStudents(prev => ({ ...prev, [schoolId]: students }));
      } catch (err) {
        console.error(err);
      }
      setLoadingStudents(prev => ({ ...prev, [schoolId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="fade-in">
        <div className="page-header">
          <div>
            <h2>Attendance Overview</h2>
            <p>Loading attendance data…</p>
          </div>
        </div>
        <div className="attendance-summary">
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    );
  }

  if (!data) return null;

  const { summary, school_stats, low_students } = data;

  const getAttColor = (rate) => {
    if (rate >= 80) return '#138808';
    if (rate >= 60) return '#f97f10';
    return '#ef4444';
  };

  // Filter schools based on filter selection
  const filteredSchools = school_stats.filter(s => {
    if (filter === 'low') return s.low_count > 0;
    if (filter === 'critical') return s.critical_count > 0;
    return true;
  });

  // Filter students for a specific school when expanded
  const getFilteredStudents = (students) => {
    if (filter === 'low') return students.filter(s => s.attendance_rate < 60);
    if (filter === 'critical') return students.filter(s => s.attendance_rate < 40);
    return students;
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <Link to="/" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-india-500 no-underline transition-colors mb-1.5">
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
          <h2>Attendance Overview</h2>
          <p>Detailed attendance analytics across all schools</p>
        </div>
      </div>

      {/* ── Summary Cards ── */}
      <div className="attendance-summary">
        <div className="att-stat-card">
          <div className="att-stat-value" style={{ color: '#8b5cf6' }}>{summary.avg_attendance}%</div>
          <div className="att-stat-label">Average Attendance</div>
        </div>
        <div className="att-stat-card">
          <div className="att-stat-value" style={{ color: '#138808' }}>{summary.good_count}</div>
          <div className="att-stat-label">Good (&ge; 60%)</div>
        </div>
        <div className="att-stat-card">
          <div className="att-stat-value" style={{ color: '#f97f10' }}>{summary.low_count}</div>
          <div className="att-stat-label">Low (&lt; 60%)</div>
        </div>
        <div className="att-stat-card">
          <div className="att-stat-value" style={{ color: '#ef4444' }}>{summary.critical_count}</div>
          <div className="att-stat-label">Critical (&lt; 40%)</div>
        </div>
      </div>

      {/* ── Filter Tabs ── */}
      <div className="tab-bar mb-6">
        <button className={`tab-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
          <Users size={13} className="inline align-[-2px] mr-1.5" /> All Schools
        </button>
        <button className={`tab-btn ${filter === 'low' ? 'active' : ''}`} onClick={() => setFilter('low')}>
          <TrendingDown size={13} className="inline align-[-2px] mr-1.5" /> Low Attendance
        </button>
        <button className={`tab-btn ${filter === 'critical' ? 'active' : ''}`} onClick={() => setFilter('critical')}>
          <AlertTriangle size={13} className="inline align-[-2px] mr-1.5" /> Critical
        </button>
      </div>

      {/* ── School Groups (accordion-style, lazy load students) ── */}
      {filteredSchools.map(school => (
        <div key={school.id} className="att-school-group">
          <div
            className="att-school-header cursor-pointer hover:bg-slate-50 transition-colors"
            onClick={() => toggleSchool(school.id)}
          >
            <div>
              <div className="att-school-name">{school.name}</div>
              <div className="att-school-meta">{school.district}, {school.state} · {school.school_type}</div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-lg font-extrabold" style={{ color: getAttColor(school.avg_attendance) }}>
                  {school.avg_attendance}%
                </div>
                <div className="att-school-meta">
                  {school.total_students} students · {school.low_count} low
                </div>
              </div>
              {expandedSchool === school.id
                ? <ChevronUp size={18} className="text-slate-400" />
                : <ChevronDown size={18} className="text-slate-400" />
              }
            </div>
          </div>

          {expandedSchool === school.id && (
            <div className="bg-white border border-t-0 border-slate-200 rounded-b-xl overflow-hidden">
              {loadingStudents[school.id] ? (
                <div className="skeleton m-4" style={{ height: 120 }} />
              ) : schoolStudents[school.id] ? (
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Gender</th>
                        <th>Category</th>
                        <th>Grade</th>
                        <th>Attendance</th>
                        <th>Dropout Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getFilteredStudents(schoolStudents[school.id]).slice(0, 20).map(s => (
                        <tr key={s.id}>
                          <td className="font-medium">{s.name}</td>
                          <td>{s.gender}</td>
                          <td><span className="badge badge-neutral">{s.category}</span></td>
                          <td>{s.grade_level}</td>
                          <td>
                            <span className="font-bold" style={{ color: getAttColor(s.attendance_rate) }}>
                              {s.attendance_rate}%
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${s.dropout_risk >= 60 ? 'badge-danger' : s.dropout_risk >= 35 ? 'badge-warning' : 'badge-success'}`}>
                              {s.dropout_risk.toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                      {getFilteredStudents(schoolStudents[school.id]).length > 20 && (
                        <tr>
                          <td colSpan={6} className="text-center text-slate-400 italic py-3">
                            + {getFilteredStudents(schoolStudents[school.id]).length - 20} more students
                          </td>
                        </tr>
                      )}
                      {getFilteredStudents(schoolStudents[school.id]).length === 0 && (
                        <tr>
                          <td colSpan={6} className="text-center text-slate-400 py-6">
                            No students match the current filter
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
