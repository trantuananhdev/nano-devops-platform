import { useEffect, useMemo, useState } from "react";

const defaultApiBase = `${window.location.protocol}//${window.location.hostname}:8008`;
const API_BASE = import.meta.env.VITE_API_BASE_URL || defaultApiBase;
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

async function api(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options
    });
    const text = await res.text();
    let payload = {};
    try {
      payload = text ? JSON.parse(text) : {};
    } catch (e) {
      console.error("Failed to parse JSON:", text);
      throw new Error("Server returned invalid JSON");
    }
    if (!res.ok) throw new Error(payload.detail || payload.message || "API error");
    return payload;
  } catch (err) {
    console.error("API Call Failed:", err);
    throw err;
  }
}

export default function App() {
  const [parents, setParents] = useState([]);
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [msg, setMsg] = useState("");
  const [insightJson, setInsightJson] = useState("");

  const [parentForm, setParentForm] = useState({ name: "", phone: "", email: "" });
  const [studentForm, setStudentForm] = useState({
    name: "",
    dob: "",
    gender: "",
    current_grade: "",
    parent_id: ""
  });
  const [classForm, setClassForm] = useState({
    name: "",
    subject: "",
    day_of_week: 0,
    time_slot: "18:00-19:00",
    teacher_name: "",
    max_students: 2
  });
  const [subForm, setSubForm] = useState({
    student_id: "",
    package_name: "Goi 8 buoi",
    start_date: "",
    end_date: "",
    total_sessions: 8
  });
  const [registerForm, setRegisterForm] = useState({ class_id: "", student_id: "" });
  const [sessionText, setSessionText] = useState("");
  const [loading, setLoading] = useState(false);

  async function refreshAll() {
    const [p, s, c, sub] = await Promise.all([
      api("/api/parents"),
      api("/api/students"),
      api("/api/classes"),
      api("/api/subscriptions")
    ]);
    setParents(p);
    setStudents(s);
    setClasses(c);
    setSubscriptions(sub);
  }

  useEffect(() => {
    refreshAll().catch((e) => setMsg(e.message));
  }, []);

  const classesByDay = useMemo(() => {
    const data = Array.from({ length: 7 }, () => []);
    classes.forEach((c) => data[c.day_of_week].push(c));
    data.forEach((arr) => arr.sort((a, b) => a.time_slot.localeCompare(b.time_slot)));
    return data;
  }, [classes]);

  async function onCreateParent(e) {
    e.preventDefault();
    try {
      await api("/api/parents", { method: "POST", body: JSON.stringify(parentForm) });
      setParentForm({ name: "", phone: "", email: "" });
      await refreshAll();
      setMsg("Created parent");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onCreateStudent(e) {
    e.preventDefault();
    try {
      await api("/api/students", {
        method: "POST",
        body: JSON.stringify({ ...studentForm, parent_id: Number(studentForm.parent_id) })
      });
      setStudentForm({ name: "", dob: "", gender: "", current_grade: "", parent_id: "" });
      await refreshAll();
      setMsg("Created student");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onCreateClass(e) {
    e.preventDefault();
    try {
      await api("/api/classes", {
        method: "POST",
        body: JSON.stringify({
          ...classForm,
          day_of_week: Number(classForm.day_of_week),
          max_students: Number(classForm.max_students)
        })
      });
      await refreshAll();
      setMsg("Created class");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onCreateSubscription(e) {
    e.preventDefault();
    try {
      await api("/api/subscriptions", {
        method: "POST",
        body: JSON.stringify({
          ...subForm,
          student_id: Number(subForm.student_id),
          total_sessions: Number(subForm.total_sessions)
        })
      });
      await refreshAll();
      setMsg("Created subscription");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onRegisterClass(e) {
    e.preventDefault();
    try {
      await api(`/api/classes/${Number(registerForm.class_id)}/register`, {
        method: "POST",
        body: JSON.stringify({ student_id: Number(registerForm.student_id) })
      });
      await refreshAll();
      setMsg("Registered student to class");
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function onCreateSessionFromText(e) {
    e.preventDefault();
    setLoading(true);
    setMsg("Generating insight... Please wait.");
    try {
      const out = await api("/api/sessions", {
        method: "POST",
        body: JSON.stringify({ raw_transcript: sessionText })
      });
      setInsightJson(out.insight_json || "");
      setMsg("Generated insight from transcript text");
    } catch (err) {
      console.error("Pipeline Error:", err);
      setMsg(`AI Pipeline Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function onImportFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setMsg("Uploading and analyzing... Please wait.");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/import`, { method: "POST", body: formData });
      const out = await res.json();
      if (!res.ok) throw new Error(out.detail || "Import failed");
      setInsightJson(out.insight_json || "");
      setMsg("Generated insight from uploaded .txt");
    } catch (err) {
      console.error("Import Error:", err);
      setMsg(`Import Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>TeenCare LMS Mini Web</h1>
      <div className="msg">API: {API_BASE} | {msg}</div>

      <div className="grid">
        <form className="card" onSubmit={onCreateParent}>
          <h3>Create Parent</h3>
          <label>Name<input value={parentForm.name} onChange={(e) => setParentForm({ ...parentForm, name: e.target.value })} required /></label>
          <label>Phone<input value={parentForm.phone} onChange={(e) => setParentForm({ ...parentForm, phone: e.target.value })} /></label>
          <label>Email<input value={parentForm.email} onChange={(e) => setParentForm({ ...parentForm, email: e.target.value })} /></label>
          <button type="submit">Create Parent</button>
        </form>

        <form className="card" onSubmit={onCreateStudent}>
          <h3>Create Student</h3>
          <label>Name<input value={studentForm.name} onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })} required /></label>
          <label>DOB<input type="date" value={studentForm.dob} onChange={(e) => setStudentForm({ ...studentForm, dob: e.target.value })} /></label>
          <label>Gender<input value={studentForm.gender} onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value })} /></label>
          <label>Current Grade<input value={studentForm.current_grade} onChange={(e) => setStudentForm({ ...studentForm, current_grade: e.target.value })} /></label>
          <label>Parent
            <select value={studentForm.parent_id} onChange={(e) => setStudentForm({ ...studentForm, parent_id: e.target.value })} required>
              <option value="">Select parent</option>
              {parents.map((p) => <option key={p.id} value={p.id}>{p.id} - {p.name}</option>)}
            </select>
          </label>
          <button type="submit">Create Student</button>
        </form>

        <form className="card" onSubmit={onCreateClass}>
          <h3>Create Class</h3>
          <label>Name<input value={classForm.name} onChange={(e) => setClassForm({ ...classForm, name: e.target.value })} required /></label>
          <label>Subject<input value={classForm.subject} onChange={(e) => setClassForm({ ...classForm, subject: e.target.value })} required /></label>
          <label>Day of week (0-6)<input type="number" min="0" max="6" value={classForm.day_of_week} onChange={(e) => setClassForm({ ...classForm, day_of_week: e.target.value })} required /></label>
          <label>Time slot<input value={classForm.time_slot} onChange={(e) => setClassForm({ ...classForm, time_slot: e.target.value })} required /></label>
          <label>Teacher<input value={classForm.teacher_name} onChange={(e) => setClassForm({ ...classForm, teacher_name: e.target.value })} required /></label>
          <label>Max students<input type="number" min="1" value={classForm.max_students} onChange={(e) => setClassForm({ ...classForm, max_students: e.target.value })} required /></label>
          <button type="submit">Create Class</button>
        </form>

        <form className="card" onSubmit={onCreateSubscription}>
          <h3>Create Subscription</h3>
          <label>Student
            <select value={subForm.student_id} onChange={(e) => setSubForm({ ...subForm, student_id: e.target.value })} required>
              <option value="">Select student</option>
              {students.map((s) => <option key={s.id} value={s.id}>{s.id} - {s.name}</option>)}
            </select>
          </label>
          <label>Package<input value={subForm.package_name} onChange={(e) => setSubForm({ ...subForm, package_name: e.target.value })} required /></label>
          <label>Start date<input type="date" value={subForm.start_date} onChange={(e) => setSubForm({ ...subForm, start_date: e.target.value })} required /></label>
          <label>End date<input type="date" value={subForm.end_date} onChange={(e) => setSubForm({ ...subForm, end_date: e.target.value })} required /></label>
          <label>Total sessions<input type="number" min="1" value={subForm.total_sessions} onChange={(e) => setSubForm({ ...subForm, total_sessions: e.target.value })} required /></label>
          <button type="submit">Create Subscription</button>
        </form>

        <form className="card" onSubmit={onRegisterClass}>
          <h3>Register Student To Class</h3>
          <label>Class
            <select value={registerForm.class_id} onChange={(e) => setRegisterForm({ ...registerForm, class_id: e.target.value })} required>
              <option value="">Select class</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.id} - {c.name} ({DAYS[c.day_of_week]} {c.time_slot})</option>)}
            </select>
          </label>
          <label>Student
            <select value={registerForm.student_id} onChange={(e) => setRegisterForm({ ...registerForm, student_id: e.target.value })} required>
              <option value="">Select student</option>
              {students.map((s) => <option key={s.id} value={s.id}>{s.id} - {s.name}</option>)}
            </select>
          </label>
          <button type="submit">Register</button>
        </form>

        <form className="card" onSubmit={onCreateSessionFromText}>
          <h3>Session Insight</h3>
          <label>Transcript text
            <textarea rows="7" value={sessionText} onChange={(e) => setSessionText(e.target.value)} placeholder="Paste session transcript..." required />
          </label>
          <button type="submit" disabled={loading}>{loading ? "Analyzing..." : "Generate Insight (Text)"}</button>
          <label>Or import .txt<input type="file" accept=".txt" onChange={onImportFile} disabled={loading} /></label>
        </form>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2>Classes by Weekday</h2>
        <table>
          <thead>
            <tr>{DAYS.map((d) => <th key={d}>{d}</th>)}</tr>
          </thead>
          <tbody>
            <tr>
              {classesByDay.map((dayItems, idx) => (
                <td key={idx}>
                  {dayItems.map((c) => (
                    <div key={c.id}>
                      <b>{c.time_slot}</b> - {c.name}<br />
                      {c.subject} / {c.teacher_name}
                      <hr />
                    </div>
                  ))}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="grid" style={{ marginTop: 14 }}>
        <div className="card">
          <h3>Students</h3>
          <pre>{JSON.stringify(students, null, 2)}</pre>
        </div>
        <div className="card">
          <h3>Subscriptions</h3>
          <pre>{JSON.stringify(subscriptions, null, 2)}</pre>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h3>Latest Insight JSON</h3>
        <pre>{insightJson || "No insight yet"}</pre>
      </div>
    </div>
  );
}
