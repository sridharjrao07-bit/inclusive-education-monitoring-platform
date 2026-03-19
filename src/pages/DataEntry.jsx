import { useState, useEffect } from 'react';
import { createSchool, createStudent, createTeacher, createFeedback, updateFacility, fetchSchools } from '../api';
import { CheckCircle, AlertCircle, School, Users, GraduationCap, MessageSquare, Wrench } from 'lucide-react';

function Toast({ message, type, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3200);
    return () => clearTimeout(t);
  }, [onDone]);
  return <div className={`toast toast-${type}`}>{type === 'success' ? <CheckCircle size={16}/> : <AlertCircle size={16}/>} {message}</div>;
}

// ─── Tab Forms ──────────────────────────────────────────
function SchoolForm({ schools, setSchools, showToast }) {
  const [form, setForm] = useState({ name: '', district: '', state: '', school_type: 'Urban', board: 'State Board', medium: 'Hindi' });
  const [submitting, setSubmitting] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await createSchool(form);
      showToast('School created successfully!', 'success');
      setSchools(old => [...old, res]);
      setForm({ name: '', district: '', state: '', school_type: 'Urban', board: 'State Board', medium: 'Hindi' });
    } catch (err) {
      showToast('Failed to create school', 'error');
    }
    setSubmitting(false);
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">School Name *</label>
          <input className="form-input" required value={form.name} onChange={e => set('name', e.target.value)} id="school-name" placeholder="e.g. Kendriya Vidyalaya #3" />
        </div>
        <div className="form-group">
          <label className="form-label">District *</label>
          <input className="form-input" required value={form.district} onChange={e => set('district', e.target.value)} id="school-district" placeholder="e.g. Lucknow" />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">State *</label>
          <input className="form-input" required value={form.state} onChange={e => set('state', e.target.value)} id="school-state" placeholder="e.g. Uttar Pradesh" />
        </div>
        <div className="form-group">
          <label className="form-label">School Type</label>
          <select className="form-select" value={form.school_type} onChange={e => set('school_type', e.target.value)} id="school-type">
            <option>Urban</option><option>Rural</option>
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Board</label>
          <select className="form-select" value={form.board} onChange={e => set('board', e.target.value)} id="school-board">
            <option>State Board</option><option>CBSE</option><option>ICSE</option><option>Other</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Medium</label>
          <select className="form-select" value={form.medium} onChange={e => set('medium', e.target.value)} id="school-medium">
            <option>Hindi</option><option>English</option><option>Regional</option><option>Bilingual</option>
          </select>
        </div>
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting} id="submit-school">
        <School size={15}/> {submitting ? 'Creating…' : 'Create School'}
      </button>
    </form>
  );
}

function StudentForm({ schools, showToast }) {
  const [form, setForm] = useState({
    school_id: '', name: '', gender: 'Male', category: 'General',
    disability_type: 'None', socio_economic: 'Middle', enrollment_status: 'Active',
    attendance_rate: 85, grade_level: 1, academic_score: 50,
  });
  const [submitting, setSubmitting] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createStudent({ ...form, school_id: parseInt(form.school_id) });
      showToast('Student enrolled successfully!', 'success');
      setForm(f => ({ ...f, name: '' }));
    } catch (err) {
      showToast('Failed to enroll student', 'error');
    }
    setSubmitting(false);
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">School *</label>
          <select className="form-select" required value={form.school_id} onChange={e => set('school_id', e.target.value)} id="student-school">
            <option value="">Select a school…</option>
            {schools.map(s => <option key={s.id} value={s.id}>{s.name} ({s.district})</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Student Name *</label>
          <input className="form-input" required value={form.name} onChange={e => set('name', e.target.value)} id="student-name" placeholder="e.g. Priya Sharma" />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Gender</label>
          <select className="form-select" value={form.gender} onChange={e => set('gender', e.target.value)} id="student-gender">
            <option>Male</option><option>Female</option><option>Other</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Category</label>
          <select className="form-select" value={form.category} onChange={e => set('category', e.target.value)} id="student-category">
            <option>General</option><option>SC</option><option>ST</option><option>OBC</option>
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Disability Type</label>
          <select className="form-select" value={form.disability_type} onChange={e => set('disability_type', e.target.value)} id="student-disability">
            <option>None</option><option>Visual</option><option>Hearing</option><option>Locomotor</option><option>Cognitive</option><option>Multiple</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Socio-economic</label>
          <select className="form-select" value={form.socio_economic} onChange={e => set('socio_economic', e.target.value)} id="student-socio">
            <option>BPL</option><option>Lower</option><option>Middle</option><option>Upper</option>
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Grade Level</label>
          <select className="form-select" value={form.grade_level} onChange={e => set('grade_level', parseInt(e.target.value))} id="student-grade">
            {[1,2,3,4,5,6,7,8,9,10,11,12].map(g => <option key={g} value={g}>Grade {g}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Enrollment Status</label>
          <select className="form-select" value={form.enrollment_status} onChange={e => set('enrollment_status', e.target.value)} id="student-enrollment">
            <option>Active</option><option>Dropped Out</option><option>Transferred</option>
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Attendance Rate (%)</label>
          <input className="form-input" type="number" min="0" max="100" value={form.attendance_rate} onChange={e => set('attendance_rate', parseFloat(e.target.value))} id="student-attendance" />
        </div>
        <div className="form-group">
          <label className="form-label">Academic Score (%)</label>
          <input className="form-input" type="number" min="0" max="100" value={form.academic_score} onChange={e => set('academic_score', parseFloat(e.target.value))} id="student-score" />
        </div>
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting} id="submit-student">
        <Users size={15}/> {submitting ? 'Enrolling…' : 'Enroll Student'}
      </button>
    </form>
  );
}

function TeacherForm({ schools, showToast }) {
  const [form, setForm] = useState({ school_id: '', name: '', subject: 'General', trained_in_special_ed: false, years_experience: 0 });
  const [submitting, setSubmitting] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createTeacher({ ...form, school_id: parseInt(form.school_id) });
      showToast('Teacher added successfully!', 'success');
      setForm(f => ({ ...f, name: '' }));
    } catch (err) {
      showToast('Failed to add teacher', 'error');
    }
    setSubmitting(false);
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">School *</label>
          <select className="form-select" required value={form.school_id} onChange={e => set('school_id', e.target.value)} id="teacher-school">
            <option value="">Select a school…</option>
            {schools.map(s => <option key={s.id} value={s.id}>{s.name} ({s.district})</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Teacher Name *</label>
          <input className="form-input" required value={form.name} onChange={e => set('name', e.target.value)} id="teacher-name" placeholder="e.g. Dr. Rajesh Kumar" />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Subject</label>
          <input className="form-input" value={form.subject} onChange={e => set('subject', e.target.value)} id="teacher-subject" placeholder="e.g. Mathematics" />
        </div>
        <div className="form-group">
          <label className="form-label">Years Experience</label>
          <input className="form-input" type="number" min="0" value={form.years_experience} onChange={e => set('years_experience', parseInt(e.target.value))} id="teacher-experience" />
        </div>
      </div>
      <div className="form-group">
        <div className="form-checkbox">
          <input type="checkbox" id="teacher-special-ed" checked={form.trained_in_special_ed}
            onChange={e => set('trained_in_special_ed', e.target.checked)} />
          <label htmlFor="teacher-special-ed">Trained in Special Education</label>
        </div>
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting} id="submit-teacher">
        <GraduationCap size={15}/> {submitting ? 'Adding…' : 'Add Teacher'}
      </button>
    </form>
  );
}

function FeedbackForm({ schools, showToast }) {
  const [form, setForm] = useState({ school_id: '', user_role: 'Parent', rating: 3, comments: '' });
  const [submitting, setSubmitting] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createFeedback({ ...form, school_id: parseInt(form.school_id) });
      showToast('Feedback submitted!', 'success');
      setForm(f => ({ ...f, comments: '' }));
    } catch (err) {
      showToast('Failed to submit feedback', 'error');
    }
    setSubmitting(false);
  };

  return (
    <form onSubmit={submit}>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">School *</label>
          <select className="form-select" required value={form.school_id} onChange={e => set('school_id', e.target.value)} id="feedback-school">
            <option value="">Select a school…</option>
            {schools.map(s => <option key={s.id} value={s.id}>{s.name} ({s.district})</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Your Role</label>
          <select className="form-select" value={form.user_role} onChange={e => set('user_role', e.target.value)} id="feedback-role">
            <option>Parent</option><option>Student</option><option>Teacher</option><option>Administrator</option>
          </select>
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Rating (1-5)</label>
        <div style={{ display: 'flex', gap: 8 }}>
          {[1,2,3,4,5].map(n => (
            <button key={n} type="button" className={`btn btn-sm ${form.rating === n ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => set('rating', n)} style={{ width: 42 }} id={`rating-${n}`}>
              {n}
            </button>
          ))}
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Comments</label>
        <textarea className="form-textarea" value={form.comments} onChange={e => set('comments', e.target.value)}
          id="feedback-comments" placeholder="Share your thoughts on the school's inclusivity…" />
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting} id="submit-feedback">
        <MessageSquare size={15}/> {submitting ? 'Submitting…' : 'Submit Feedback'}
      </button>
    </form>
  );
}

function FacilityForm({ schools, showToast }) {
  const [schoolId, setSchoolId] = useState('');
  const [form, setForm] = useState({
    has_ramps: false, has_braille_materials: false, has_assistive_tech: false,
    has_special_educator: false, has_accessible_washroom: false, has_transport: false,
    has_computer_lab: false, has_library: false,
  });
  const [submitting, setSubmitting] = useState(false);

  const selectedSchool = schools.find(s => s.id === parseInt(schoolId));

  useEffect(() => {
    if (selectedSchool?.facility) {
      setForm({
        has_ramps: selectedSchool.facility.has_ramps,
        has_braille_materials: selectedSchool.facility.has_braille_materials,
        has_assistive_tech: selectedSchool.facility.has_assistive_tech,
        has_special_educator: selectedSchool.facility.has_special_educator,
        has_accessible_washroom: selectedSchool.facility.has_accessible_washroom,
        has_transport: selectedSchool.facility.has_transport,
        has_computer_lab: selectedSchool.facility.has_computer_lab,
        has_library: selectedSchool.facility.has_library,
      });
    }
  }, [schoolId]);

  const submit = async e => {
    e.preventDefault();
    if (!schoolId) return;
    setSubmitting(true);
    try {
      await updateFacility(parseInt(schoolId), form);
      showToast('Facility updated!', 'success');
    } catch (err) {
      showToast('Failed to update facility', 'error');
    }
    setSubmitting(false);
  };

  const facilityLabels = [
    ['has_ramps', 'Wheelchair Ramps'],
    ['has_braille_materials', 'Braille Materials'],
    ['has_assistive_tech', 'Assistive Technology'],
    ['has_special_educator', 'Special Educator'],
    ['has_accessible_washroom', 'Accessible Washroom'],
    ['has_transport', 'Accessible Transport'],
    ['has_computer_lab', 'Computer Lab'],
    ['has_library', 'Library'],
  ];

  return (
    <form onSubmit={submit}>
      <div className="form-group">
        <label className="form-label">School *</label>
        <select className="form-select" required value={schoolId} onChange={e => setSchoolId(e.target.value)} id="facility-school">
          <option value="">Select a school…</option>
          {schools.map(s => <option key={s.id} value={s.id}>{s.name} ({s.district})</option>)}
        </select>
      </div>
      {schoolId && (
        <>
          <div className="card-title" style={{ marginBottom: 14, marginTop: 8 }}>Facility Checkboxes</div>
          <div className="form-checkbox-group" style={{ marginBottom: 20 }}>
            {facilityLabels.map(([key, label]) => (
              <div className="form-checkbox" key={key}>
                <input type="checkbox" id={`facility-${key}`} checked={form[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))} />
                <label htmlFor={`facility-${key}`}>{label}</label>
              </div>
            ))}
          </div>
          <button className="btn btn-accent" type="submit" disabled={submitting} id="submit-facility">
            <Wrench size={15}/> {submitting ? 'Updating…' : 'Update Facility'}
          </button>
        </>
      )}
    </form>
  );
}

// ─── Main DataEntry Page ────────────────────────────────
export default function DataEntry() {
  const [tab, setTab] = useState('school');
  const [schools, setSchools] = useState([]);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchSchools({ limit: 500 }).then(setSchools).catch(console.error);
  }, []);

  const showToast = (message, type) => setToast({ message, type });

  const tabs = [
    { id: 'school', label: 'New School', icon: School },
    { id: 'student', label: 'Enroll Student', icon: Users },
    { id: 'teacher', label: 'Add Teacher', icon: GraduationCap },
    { id: 'feedback', label: 'Feedback', icon: MessageSquare },
    { id: 'facility', label: 'Facility', icon: Wrench },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h2>Data Entry</h2>
          <p>Add schools, enroll students, update facilities</p>
        </div>
      </div>

      <div className="card">
        <div className="tab-bar">
          {tabs.map(t => (
            <button key={t.id}
              className={`tab-btn ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
              id={`tab-${t.id}`}
            >
              <t.icon size={14} style={{ verticalAlign: -2, marginRight: 6 }} />
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'school'   && <SchoolForm schools={schools} setSchools={setSchools} showToast={showToast} />}
        {tab === 'student'  && <StudentForm schools={schools} showToast={showToast} />}
        {tab === 'teacher'  && <TeacherForm schools={schools} showToast={showToast} />}
        {tab === 'feedback' && <FeedbackForm schools={schools} showToast={showToast} />}
        {tab === 'facility' && <FacilityForm schools={schools} showToast={showToast} />}
      </div>

      {toast && <Toast {...toast} onDone={() => setToast(null)} />}
    </div>
  );
}
