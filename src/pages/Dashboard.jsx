import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchStats } from '../api';
import {
  School, Users, TrendingUp, Shield, AlertTriangle, Clock,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';

const COLORS = ['#2b4acb', '#f97f10', '#138808', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899'];

function KpiCard({ icon: Icon, label, value, sub, color, bg, delay }) {
  return (
    <div
      className={`kpi-card fade-in`}
      style={{ '--kpi-color': color, '--kpi-bg': bg }}
    >
      <div className="kpi-icon"><Icon /></div>
      <div className="kpi-content">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {sub && <div className="kpi-subtext">{sub}</div>}
      </div>
    </div>
  );
}

function ScoreBar({ value, max = 100 }) {
  const pct = Math.min(Math.max(value, 0), max);
  const color = pct >= 70 ? '#138808' : pct >= 40 ? '#f97f10' : '#ef4444';
  return (
    <div className="score-bar-container">
      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-bar-value">{pct.toFixed(1)}</span>
    </div>
  );
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs shadow-md">
        <p className="font-semibold text-slate-800">{payload[0].name || payload[0].payload?.name}</p>
        <p className="text-slate-500">{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="fade-in">
        <div className="kpi-grid">
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 110 }} />)}
        </div>
        <div className="kpi-grid">
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 110 }} />)}
        </div>
        <div className="charts-grid">
          {[1,2].map(i => <div key={i} className="skeleton" style={{ height: 300 }} />)}
        </div>
      </div>
    );
  }

  if (!stats) return <div className="empty-state"><h3>No data available</h3></div>;

  const genderData = Object.entries(stats.gender_distribution).map(([name, value]) => ({ name, value }));
  const categoryData = Object.entries(stats.category_distribution).map(([name, value]) => ({ name, value }));
  const stateData = stats.state_wise_inclusion || [];

  return (
    <div className="fade-in">

      {/* ── SECTION: Overview ── */}
      <div className="section-title">Overview</div>
      <div className="kpi-grid">
        <Link to="/schools" className="kpi-card-link">
          <KpiCard icon={School} label="Total Schools" value={stats.total_schools}
            color="#2b4acb" bg="rgba(43,74,203,0.08)" delay={1} />
        </Link>
        <Link to="/schools" className="kpi-card-link">
          <KpiCard icon={Users} label="Total Students" value={stats.total_students.toLocaleString()}
            color="#138808" bg="rgba(19,136,8,0.08)" delay={2} />
        </Link>
        <Link to="/schools" className="kpi-card-link">
          <KpiCard icon={TrendingUp} label="Inclusion Score" value={stats.avg_inclusion_score}
            sub="National Average" color="#f97f10" bg="rgba(249,127,16,0.08)" delay={3} />
        </Link>
      </div>

      {/* ── SECTION: Health Metrics ── */}
      <div className="section-title">Health Metrics</div>
      <div className="kpi-grid">
        <Link to="/schools" className="kpi-card-link">
          <KpiCard icon={Shield} label="Accessibility" value={`${stats.avg_accessibility_score}%`}
            sub="Avg facility score" color="#3b82f6" bg="rgba(59,130,246,0.08)" delay={1} />
        </Link>
        <Link to="/schools" className="kpi-card-link">
          <KpiCard icon={AlertTriangle} label="High Dropout Risk" value={stats.dropout_risk_high_count}
            sub="Students ≥ 60% risk" color="#ef4444" bg="rgba(239,68,68,0.08)" delay={2} />
        </Link>
        <Link to="/attendance" className="kpi-card-link">
          <KpiCard icon={Clock} label="Attendance" value={`${stats.avg_attendance}%`}
            sub="Avg attendance rate" color="#8b5cf6" bg="rgba(139,92,246,0.08)" delay={3} />
        </Link>
      </div>

      <div className="section-divider" />

      {/* ── SECTION: Demographics ── */}
      <div className="section-title">Demographics</div>
      <div className="charts-grid">
        {/* Gender Distribution */}
        <div className="card fade-in">
          <div className="card-header">
            <div><div className="card-title">Gender Distribution</div>
            <div className="card-subtitle">Student demographics</div></div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={genderData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                paddingAngle={4} dataKey="value" strokeWidth={0}>
                {genderData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex gap-4 justify-center mt-2">
            {genderData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[i] }} />
                <span className="text-slate-500">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Category Distribution */}
        <div className="card fade-in">
          <div className="card-header">
            <div><div className="card-title">Category Distribution</div>
            <div className="card-subtitle">General / SC / ST / OBC</div></div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={categoryData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                paddingAngle={4} dataKey="value" strokeWidth={0}>
                {categoryData.map((_, i) => <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex gap-3.5 justify-center mt-2 flex-wrap">
            {categoryData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <div className="w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[(i+2)%COLORS.length] }} />
                <span className="text-slate-500">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-divider" />

      {/* ── SECTION: State Performance ── */}
      <div className="section-title">State Performance</div>
      <div className="charts-grid charts-grid-full">
        <div className="card fade-in">
          <div className="card-header">
            <div><div className="card-title">State-wise Inclusion Index</div>
            <div className="card-subtitle">Average inclusion score per state</div></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stateData} margin={{ left: 0, right: 10, top: 10, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="state" angle={-35} textAnchor="end" tick={{ fill: '#94a3b8', fontSize: 10 }}
                height={60} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="avg_inclusion" radius={[6, 6, 0, 0]} maxBarSize={28}>
                {stateData.map((entry, i) => (
                  <Cell key={i} fill={entry.avg_inclusion >= 60 ? '#138808' : entry.avg_inclusion >= 40 ? '#f97f10' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── SECTION: Schools Needing Intervention ── */}
      {stats.top_risk_schools && stats.top_risk_schools.length > 0 && (
        <>
          <div className="section-divider" />
          <div className="section-title">Schools Needing Intervention</div>
          <div className="card fade-in">
            <div className="card-header">
              <div><div className="card-title">⚠️ Highest Dropout Risk</div>
              <div className="card-subtitle">Schools with highest average student dropout risk</div></div>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>School</th>
                    <th>District</th>
                    <th>State</th>
                    <th>Students</th>
                    <th>Avg Dropout Risk</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.top_risk_schools.map(s => (
                    <tr key={s.id}>
                      <td className="font-semibold">{s.name}</td>
                      <td>{s.district}</td>
                      <td>{s.state}</td>
                      <td>{s.student_count}</td>
                      <td><ScoreBar value={s.avg_dropout_risk} /></td>
                      <td>
                        {s.avg_dropout_risk >= 60
                          ? <span className="badge badge-danger">Critical</span>
                          : <span className="badge badge-warning">At Risk</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
