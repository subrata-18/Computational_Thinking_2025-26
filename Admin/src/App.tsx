import { useState } from "react";
import { adminLogin, getStudentHistory, getStudentHistoryDetail, type AdminUser, type HistoryDetail, type HistoryEntry } from "./api";
import "./App.css";

type View = "login" | "search" | "detail";
type StoredAdminSession = { admin: AdminUser; password: string };

const ADMIN_SESSION_KEY = "nova_ai_admin_session";

function readStoredAdminSession(): StoredAdminSession | null {
  try {
    const raw = localStorage.getItem(ADMIN_SESSION_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      !("admin" in parsed) ||
      !("password" in parsed) ||
      typeof parsed.password !== "string" ||
      !parsed.password ||
      typeof parsed.admin !== "object" ||
      parsed.admin === null ||
      !("id" in parsed.admin) ||
      !("username" in parsed.admin) ||
      typeof parsed.admin.id !== "number" ||
      typeof parsed.admin.username !== "string" ||
      !parsed.admin.username.trim()
    ) {
      localStorage.removeItem(ADMIN_SESSION_KEY);
      return null;
    }
    return parsed as StoredAdminSession;
  } catch {
    localStorage.removeItem(ADMIN_SESSION_KEY);
    return null;
  }
}

function parseStoredList(value: string): string[] {
  try {
    const parsed: unknown = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    // Fall through to the legacy comma-separated format.
  }
  return value.split(", ").map((item) => item.trim()).filter(Boolean);
}

function scorePercent(score: string): number {
  const [correct, total] = score.split("/").map(Number);
  return total > 0 ? Math.round((correct / total) * 100) : 0;
}

export default function App() {
  const [storedSession] = useState<StoredAdminSession | null>(() => readStoredAdminSession());
  const [view, setView] = useState<View>(() => storedSession ? "search" : "login");
  const [admin, setAdmin] = useState<AdminUser | null>(() => storedSession?.admin ?? null);
  const [adminPassword, setAdminPassword] = useState(() => storedSession?.password ?? "");
  const [studentUsername, setStudentUsername] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!username.trim() || !password) {
      setError("Enter your admin username and password.");
      return;
    }
    setLoading(true);
    try {
      const response = await adminLogin(username.trim(), password);
      setAdmin(response.data);
      setAdminPassword(password);
      localStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify({ admin: response.data, password } satisfies StoredAdminSession));
      setView("search");
      setPassword("");
      setHasSearched(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Admin login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!admin || !studentUsername.trim()) {
      setError("Enter a student username.");
      return;
    }
    setError("");
    setLoading(true);
    setDetail(null);
    try {
      const response = await getStudentHistory(admin.username, adminPassword, studentUsername.trim());
      setStudentUsername(studentUsername.trim());
      setHistory(response.data);
      setHasSearched(true);
    } catch (err) {
      setHistory([]);
      setError(err instanceof Error ? err.message : "Unable to load student history.");
    } finally {
      setLoading(false);
    }
  }

  async function openHistory(entry: HistoryEntry) {
    if (!admin) return;
    setError("");
    setLoading(true);
    try {
      const response = await getStudentHistoryDetail(admin.username, adminPassword, studentUsername, entry.id);
      setDetail(response.data);
      setView("detail");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load performance details.");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(ADMIN_SESSION_KEY);
    setAdmin(null);
    setAdminPassword("");
    setStudentUsername("");
    setHistory([]);
    setDetail(null);
    setHasSearched(false);
    setView("login");
  }

  function resetStudentSearch() {
    setStudentUsername("");
    setHistory([]);
    setDetail(null);
    setError("");
    setHasSearched(false);
  }

  return (
    <div className="admin-shell">
      <header className="topbar">
        <div className="brand">nova ai <span>admin</span></div>
        {admin && <button className="text-button" onClick={logout}>Log out</button>}
      </header>

      <main className="admin-main">
        {view === "login" && (
          <section className="auth-card">
            <span className="eyebrow">Restricted access</span>
            <h1>Admin sign in</h1>
            <p className="muted">Review student learning sessions and performance.</p>
            <form onSubmit={handleLogin}>
              <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" disabled={loading} /></label>
              <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" disabled={loading} /></label>
              {error && <div className="error">{error}</div>}
              <button className="primary full" disabled={loading}>{loading ? "Signing in..." : "Log in"}</button>
            </form>
          </section>
        )}

        {view === "search" && (
          <section className="workspace">
            {hasSearched && <button className="back-button" onClick={resetStudentSearch}>← Back</button>}
            <div className="page-heading">
              <div><span className="eyebrow">Student performance</span><h1>Find a student</h1></div>
              <span className="admin-badge">{admin?.username}</span>
            </div>
            <form className="search-form" onSubmit={handleSearch}>
              <input value={studentUsername} onChange={(event) => { setStudentUsername(event.target.value); setHasSearched(false); }} placeholder="Enter student username" aria-label="Student username" />
              <button className="primary" disabled={loading}>{loading ? "Loading..." : "Search"}</button>
            </form>
            {error && <div className="error">{error}</div>}
            {history.length > 0 && <section className="history-panel"><div className="section-heading"><h2>{studentUsername}'s questions</h2><span>{history.length} sessions</span></div><div className="history-list">{history.map((entry) => <button className="history-item" key={entry.id} onClick={() => void openHistory(entry)}><span>{entry.user_question}</span><small>{entry.score}</small></button>)}</div></section>}
            {!loading && hasSearched && history.length === 0 && !error && <div className="empty-state">No questions found for this username.</div>}
          </section>
        )}

        {view === "detail" && detail && (
          <section className="workspace">
            <button className="back-button" onClick={() => setView("search")}>← Back to questions</button>
            <div className="result-card"><span className="eyebrow">Performance review</span><h1>{studentUsername}</h1><div className="score">{detail.score}</div><div className="progress"><div style={{ width: `${scorePercent(detail.score)}%` }} /></div><p>{scorePercent(detail.score)}% correct</p></div>
            <section className="detail-section"><span className="eyebrow">Original question</span><h2>{detail.user_question}</h2></section>
            <section className="detail-section"><div className="section-heading"><h2>Question review</h2><span>{parseStoredList(detail.ai_questions).length} questions</span></div><div className="review-list">{parseStoredList(detail.ai_questions).map((question, index) => <article className="review-item" key={`${index}-${question}`}><div className="review-number">Question {index + 1}</div><div className="review-question">{question}</div><div className="review-answer">Correct answer: <strong>{parseStoredList(detail.ai_answers)[index] || "Not recorded"}</strong></div></article>)}</div></section>
            <section className="remarks"><span className="eyebrow">Remarks</span><p>{detail.remarks || "No remarks were recorded for this session."}</p></section>
          </section>
        )}
      </main>
    </div>
  );
}
