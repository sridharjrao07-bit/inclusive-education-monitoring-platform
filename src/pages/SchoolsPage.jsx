import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { fetchSchools, fetchStudents } from '../api';
import { Search, MapPin, Filter, ChevronDown, Eye, X } from 'lucide-react';

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

function SchoolDetail({ school, onClose }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudents({ school_id: school.id, limit: 50 })
      .then(setStudents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [school.id]);

  const facilityItems = school.facility ? [
    { label: 'Wheelchair Ramps', val: school.facility.has_ramps },
    { label: 'Braille Materials', val: school.facility.has_braille_materials },
    { label: 'Assistive Tech', val: school.facility.has_assistive_tech },
    { label: 'Special Educator', val: school.facility.has_special_educator },
    { label: 'Accessible Washroom', val: school.facility.has_accessible_washroom },
    { label: 'Transport', val: school.facility.has_transport },
    { label: 'Computer Lab', val: school.facility.has_computer_lab },
    { label: 'Library', val: school.facility.has_library },
  ] : [];

  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>{school.name}</h3>
            <div className="text-xs text-slate-400 mt-1">
              <MapPin size={12} className="inline align-[-2px]" /> {school.district}, {school.state} · {school.school_type} · {school.board}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="modal-body">
          {/* Score cards */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-center border border-slate-100">
              <div className="text-[11px] text-slate-400 mb-1">INCLUSION</div>
              <div className="text-2xl font-extrabold" style={{ color: school.inclusion_score >= 60 ? '#138808' : school.inclusion_score >= 40 ? '#f97f10' : '#ef4444' }}>
                {school.inclusion_score}
              </div>
            </div>
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-center border border-slate-100">
              <div className="text-[11px] text-slate-400 mb-1">ACCESSIBILITY</div>
              <div className="text-2xl font-extrabold" style={{ color: school.accessibility_score >= 60 ? '#138808' : '#f97f10' }}>
                {school.accessibility_score}%
              </div>
            </div>
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-center border border-slate-100">
              <div className="text-[11px] text-slate-400 mb-1">STUDENTS</div>
              <div className="text-2xl font-extrabold text-india-500">
                {school.total_students}
              </div>
            </div>
          </div>

          {/* Facilities */}
          {facilityItems.length > 0 && (
            <>
              <div className="card-title mb-3">Facilities</div>
              <div className="grid grid-cols-2 gap-2 mb-6">
                {facilityItems.map(f => (
                  <div key={f.label} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] border ${f.val ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                    <span className={`text-base ${f.val ? 'text-green-600' : 'text-red-400'}`}>
                      {f.val ? '✓' : '✗'}
                    </span>
                    <span className={f.val ? 'text-slate-700' : 'text-slate-400'}>{f.label}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Students */}
          <div className="card-title mb-3">
            Students {loading ? '' : `(${students.length})`}
          </div>
          {loading ? (
            <div className="skeleton" style={{ height: 120 }} />
          ) : students.length ? (
            <div className="max-h-[260px] overflow-y-auto rounded-xl border border-slate-200">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Gender</th>
                    <th>Category</th>
                    <th>Attendance</th>
                    <th>Dropout Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map(s => (
                    <tr key={s.id}>
                      <td className="font-medium">{s.name}</td>
                      <td>{s.gender}</td>
                      <td><span className="badge badge-neutral">{s.category}</span></td>
                      <td>{s.attendance_rate}%</td>
                      <td>
                        <span className={`badge ${s.dropout_risk >= 60 ? 'badge-danger' : s.dropout_risk >= 35 ? 'badge-warning' : 'badge-success'}`}>
                          {s.dropout_risk.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state py-6"><p>No students enrolled</p></div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

export default function SchoolsPage() {
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedSchool, setSelectedSchool] = useState(null);

  useEffect(() => {
    const params = {};
    if (stateFilter) params.state = stateFilter;
    if (typeFilter) params.school_type = typeFilter;
    params.limit = 200;

    setLoading(true);
    fetchSchools(params)
      .then(setSchools)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [stateFilter, typeFilter]);

  const filtered = schools.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.district.toLowerCase().includes(search.toLowerCase())
  );

  const states = [...new Set(schools.map(s => s.state))].sort();

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Schools Directory</h2>
          <p>Browse and inspect school-level data across India</p>
        </div>
        <span className="badge badge-info">{schools.length} schools</span>
      </div>

      {/* Filter Bar */}
      <div className="filter-bar">
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className="form-input pl-9" placeholder="Search schools or districts…"
            value={search} onChange={e => setSearch(e.target.value)}
            id="school-search"
          />
        </div>
        <select className="form-select w-44" value={stateFilter} onChange={e => setStateFilter(e.target.value)} id="state-filter">
          <option value="">All States</option>
          {states.map(st => <option key={st} value={st}>{st}</option>)}
        </select>
        <select className="form-select w-36" value={typeFilter} onChange={e => setTypeFilter(e.target.value)} id="type-filter">
          <option value="">All Types</option>
          <option value="Urban">Urban</option>
          <option value="Rural">Rural</option>
        </select>
      </div>

      {/* School Table */}
      {loading ? (
        <div className="skeleton" style={{ height: 400 }} />
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>School Name</th>
                  <th>District</th>
                  <th>State</th>
                  <th>Type</th>
                  <th>Students</th>
                  <th>Inclusion Score</th>
                  <th>Accessibility</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={8} className="text-center py-10 text-slate-400">No schools found</td></tr>
                ) : filtered.map(s => (
                  <tr
                    key={s.id}
                    onClick={() => setSelectedSchool(s)}
                    className="cursor-pointer hover:bg-india-50/40"
                  >
                    <td className="font-semibold text-slate-800">{s.name}</td>
                    <td>{s.district}</td>
                    <td>{s.state}</td>
                    <td>
                      <span className={`badge ${s.school_type === 'Rural' ? 'badge-warning' : 'badge-info'}`}>
                        {s.school_type}
                      </span>
                    </td>
                    <td>{s.total_students}</td>
                    <td><ScoreBar value={s.inclusion_score} /></td>
                    <td><ScoreBar value={s.accessibility_score} /></td>
                    <td className="text-right pr-4">
                      <button className="btn btn-secondary btn-sm" id={`view-school-${s.id}`} onClick={(e) => { e.stopPropagation(); setSelectedSchool(s); }}>
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedSchool && <SchoolDetail school={selectedSchool} onClose={() => setSelectedSchool(null)} />}
    </div>
  );
}
