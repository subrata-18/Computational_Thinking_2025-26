import { useState } from "react";
import { login, signup } from "./services/api";
import type { User } from "./types";

type Page = "landing" | "login" | "signup" | "app";

const quotes = [
  "Every expert was once a beginner.",
  "The important thing is not to stop questioning.",
  "Learning never exhausts the mind.",
  "Small steps lead to big discoveries.",
  "Curiosity is the beginning of understanding.",
];

function App() {
  const [page, setPage] = useState<Page>("landing");
  const [user, setUser] = useState<User | null>(null);

  function authenticate(userData: User) {
    setUser(userData);
    setPage("app");
  }

  if (page === "landing") {
    return (
      <Landing
        onLogin={() => setPage("login")}
        onSignup={() => setPage("signup")}
      />
    );
  }

  if (page === "login") {
    return (
      <Auth
        mode="login"
        onBack={() => setPage("landing")}
        onSwitch={() => setPage("signup")}
        onAuthenticated={authenticate}
      />
    );
  }

  if (page === "signup") {
    return (
      <Auth
        mode="signup"
        onBack={() => setPage("landing")}
        onSwitch={() => setPage("login")}
        onAuthenticated={authenticate}
      />
    );
  }

  if (!user) {
    return null;
  }

  return (
    <DLDApp
      user={user}
      onLogout={() => {
        setUser(null);
        setPage("landing");
      }}
    />
  );
}

/* ---------------- Landing ---------------- */

function Landing({
  onLogin,
  onSignup,
}: {
  onLogin: () => void;
  onSignup: () => void;
}) {
  return (
    <main className="landing">
      <div className="landing-content">
        <div className="logo">DLD</div>

        <h1>Learn by understanding.</h1>

        <p>
          Ask a question, practice the concept, and discover
          whether you really understood it.
        </p>

        <div className="landing-actions">
          <button className="primary" onClick={onSignup}>
            Get started
          </button>

          <button className="secondary" onClick={onLogin}>
            Log in
          </button>
        </div>
      </div>
    </main>
  );
}

/* ---------------- Authentication ---------------- */

function Auth({
  mode,
  onBack,
  onSwitch,
  onAuthenticated,
}: {
  mode: "login" | "signup";
  onBack: () => void;
  onSwitch: () => void;
  onAuthenticated: (user: User) => void;
}) {
  const isLogin = mode === "login";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();

    setError("");

    if (!username.trim() || !password) {
      setError("Username and password are required.");
      return;
    }

    setLoading(true);

    try {
      const response = isLogin
        ? await login(username.trim(), password)
        : await signup(username.trim(), password);

      onAuthenticated(response.data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <button type="button" className="back" onClick={onBack}>
          ← Back
        </button>

        <div className="logo">DLD</div>

        <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>

        <p className="muted">
          {isLogin
            ? "Log in to continue learning."
            : "Start your learning journey."}
        </p>

        <label>
          Username

          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter username"
            autoComplete="username"
          />
        </label>

        <label>
          Password

          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            autoComplete={
              isLogin ? "current-password" : "new-password"
            }
          />
        </label>

        {error && <div className="error">{error}</div>}

        <button className="primary full" disabled={loading}>
          {loading
            ? "Please wait..."
            : isLogin
              ? "Log in"
              : "Create account"}
        </button>

        <button
          type="button"
          className="switch-auth"
          onClick={onSwitch}
        >
          {isLogin
            ? "Don't have an account? Sign up"
            : "Already have an account? Log in"}
        </button>
      </form>
    </main>
  );
}

/* ---------------- Main DLD App ---------------- */

function DLDApp({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const [quote] = useState(
    () => quotes[Math.floor(Math.random() * quotes.length)]
  );

  const [question, setQuestion] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(
    null
  );

  const [error, setError] = useState("");

  function handleImage(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("Only JPG, JPEG and PNG images are supported.");
      return;
    }

    setError("");
    setImage(file);

    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }

    setImagePreview(URL.createObjectURL(file));
  }

  function removeImage() {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }

    setImage(null);
    setImagePreview(null);
  }

  function newChat() {
    setQuestion("");
    removeImage();
    setError("");
  }

  function submitQuestion() {
    if (!question.trim() && !image) {
      setError("Enter a question or upload an image.");
      return;
    }

    /*
      The learning-session backend endpoint has not been
      provided yet.

      We intentionally do not fake the request.
    */

    setError("Learning session API is not connected yet.");
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">DLD</div>

        <button className="new-chat" onClick={newChat}>
          + New Chat
        </button>

        <div className="history">
          <div className="section-title">History</div>
        </div>

        <div className="sidebar-bottom">
          <button className="username">
            {user.username}
          </button>

          <button className="logout" onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="welcome">
          <h1>Hi, {user.username} 👋</h1>
          <p>"{quote}"</p>
        </div>

        <div className="composer-wrapper">
          {imagePreview && (
            <div className="image-preview">
              <img src={imagePreview} alt="Question preview" />

              <button onClick={removeImage}>×</button>
            </div>
          )}

          {error && (
            <div className="error composer-error">
              {error}
            </div>
          )}

          <div className="composer">
            <input
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  submitQuestion();
                }
              }}
              placeholder="Ask your question..."
            />

            <label className="icon-button">
              📎

              <input
                type="file"
                accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                hidden
                onChange={handleImage}
              />
            </label>

            <button className="send" onClick={submitQuestion}>
              ➤
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
