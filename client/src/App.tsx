import { useEffect, useState } from "react";
import { login, postQuestion, signup } from "./services/api";
import type { Question, User } from "./types";
import "./App.css";

type Page = "landing" | "login" | "signup" | "app";
type Stage = "home" | "loading" | "quiz" | "result" | "original" | "evaluation";

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
    return <Landing onLogin={() => setPage("login")} onSignup={() => setPage("signup")} />;
  }

  if (page === "login" || page === "signup") {
    return (
      <Auth
        mode={page}
        onBack={() => setPage("landing")}
        onSwitch={() => setPage(page === "login" ? "signup" : "login")}
        onAuthenticated={authenticate}
      />
    );
  }

  if (!user) return null;

  return (
    <NovaAI
      user={user}
      onLogout={() => {
        setUser(null);
        setPage("landing");
      }}
    />
  );
}

function Landing({ onLogin, onSignup }: { onLogin: () => void; onSignup: () => void }) {
  return (
    <main className="landing">
      <div className="landing-content">
        <div className="logo">nova ai</div>
        <h1>Learn by understanding.</h1>
        <p>Ask a question, practice the concept, and discover whether you really understood it.</p>
        <div className="landing-actions">
          <button className="primary" onClick={onSignup}>Get started</button>
          <button className="secondary" onClick={onLogin}>Log in</button>
        </div>
      </div>
    </main>
  );
}

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <button type="button" className="back" onClick={onBack}>← Back</button>
        <div className="logo">nova ai</div>
        <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>
        <p className="muted">{isLogin ? "Log in to continue learning." : "Start your learning journey."}</p>

        <label>Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Enter username" autoComplete="username" />
        </label>

        <label>Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" autoComplete={isLogin ? "current-password" : "new-password"} />
        </label>

        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? "Please wait..." : isLogin ? "Log in" : "Create account"}</button>
        <button type="button" className="switch-auth" onClick={onSwitch}>
          {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
        </button>
      </form>
    </main>
  );
}

function NovaAI({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [stage, setStage] = useState<Stage>("home");
  const [quote, setQuote] = useState(() => quotes[Math.floor(Math.random() * quotes.length)]);
  const [questionText, setQuestionText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [originalQuestion, setOriginalQuestion] = useState<Question | null>(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [showHint, setShowHint] = useState(false);
  const [error, setError] = useState("");
  const [score, setScore] = useState(0);
  const [finalAnswer, setFinalAnswer] = useState<number | null>(null);

  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  function removeImage() {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImage(null);
    setImagePreview(null);
  }

  function newChat() {
    removeImage();
    setQuestionText("");
    setQuestions([]);
    setOriginalQuestion(null);
    setCurrent(0);
    setAnswers({});
    setShowHint(false);
    setScore(0);
    setFinalAnswer(null);
    setError("");
    setQuote(quotes[Math.floor(Math.random() * quotes.length)]);
    setStage("home");
  }

  function selectImage(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("Only JPG, JPEG and PNG images are supported.");
      return;
    }

    setError("");
    removeImage();
    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  }

  async function submitQuestion() {
    if (!questionText.trim() && !image) {
      setError("Enter a question or upload an image.");
      return;
    }

    if (image) {
      setError("The current backend does not expose an image-upload endpoint yet. Text questions are ready to use.");
      return;
    }

    setError("");
    setStage("loading");

    try {
      const response = await postQuestion(user.username, questionText.trim());
      const data = response;

      if (!data.is_relevant) {
        setError(data.error_message || "This question could not be processed.");
        setStage("home");
        return;
      }

      setQuestions(data.ai_questions);
      setOriginalQuestion(data.user_question);
      setCurrent(0);
      setAnswers({});
      setShowHint(false);
      setStage("quiz");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to connect to Nova AI.");
      setStage("home");
    }
  }

  function chooseAnswer(option: number) {
    setAnswers((previous) => ({ ...previous, [current]: option }));
  }

  function nextQuestion() {
    if (answers[current] == null) return;

    if (current < questions.length - 1) {
      setCurrent((value) => value + 1);
      setShowHint(false);
      return;
    }

    const finalScore = questions.reduce(
      (total, item, index) => total + (answers[index] === item.correct_option ? 1 : 0),
      0
    );
    setScore(finalScore);
    setStage("result");
  }

  function previousQuestion() {
    if (current === 0) return;
    setCurrent((value) => value - 1);
    setShowHint(false);
  }

  function startOriginal() {
    setFinalAnswer(null);
    setShowHint(false);
    setStage("original");
  }

  function submitOriginal() {
    if (!originalQuestion || finalAnswer == null) return;
    setStage("evaluation");
  }

  const progress = questions.length ? ((current + 1) / questions.length) * 100 : 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">nova ai</div>
        <button className="new-chat" onClick={newChat}>＋ New Chat</button>
        <div className="sidebar-bottom">
          <div className="username">{user.username}</div>
          <button className="logout" onClick={onLogout}>Log out</button>
        </div>
      </aside>

      <main className="main">
        {stage === "home" && (
          <>
            <div className="welcome">
              <h1>Hi, {user.username} 👋</h1>
              <p>“{quote}”</p>
            </div>

            <div className="composer-wrapper">
              {imagePreview && (
                <div className="image-preview">
                  <img src={imagePreview} alt="Question preview" />
                  <button onClick={removeImage} aria-label="Remove image">×</button>
                </div>
              )}

              {error && <div className="error composer-error">{error}</div>}

              <Composer
                value={questionText}
                onChange={setQuestionText}
                onSubmit={submitQuestion}
                onImage={selectImage}
                disabled={false}
              />
            </div>
          </>
        )}

        {stage === "loading" && (
          <div className="center-state">
            <div className="spinner" />
            <h2>Understanding your question...</h2>
            <p>Generating a personalized practice session...</p>
          </div>
        )}

        {stage === "quiz" && questions[current] && (
          <Quiz
            question={questions[current]}
            current={current}
            total={questions.length}
            progress={progress}
            selected={answers[current] ?? null}
            showHint={showHint}
            onSelect={chooseAnswer}
            onHint={() => setShowHint(true)}
            onNext={nextQuestion}
            onPrevious={previousQuestion}
          />
        )}

        {stage === "result" && (
          <div className="result-card">
            <span className="eyebrow">Practice complete</span>
            <h1>Quiz Complete!</h1>
            <div className="score">{score} / {questions.length}</div>
            <div className="progress-track"><div style={{ width: `${questions.length ? (score / questions.length) * 100 : 0}%` }} /></div>
            <p>{questions.length ? Math.round((score / questions.length) * 100) : 0}% Correct</p>
            <button className="primary" onClick={startOriginal}>Try Original Question</button>
          </div>
        )}

        {stage === "original" && originalQuestion && (
          <Quiz
            question={originalQuestion}
            current={0}
            total={1}
            progress={100}
            selected={finalAnswer}
            showHint={showHint}
            finalQuestion
            onSelect={setFinalAnswer}
            onHint={() => setShowHint(true)}
            onNext={submitOriginal}
            onPrevious={() => setStage("result")}
          />
        )}

        {stage === "evaluation" && originalQuestion && finalAnswer != null && (
          <div className="result-card">
            {finalAnswer === originalQuestion.correct_option ? (
              <>
                <div className="result-icon">✓</div>
                <h1>Correct!</h1>
                <p>You understood the concept.</p>
              </>
            ) : (
              <>
                <div className="result-icon">×</div>
                <h1>Not quite.</h1>
                <p>Review the concept and try again.</p>
              </>
            )}
            <button className="primary" onClick={newChat}>Start New Chat</button>
          </div>
        )}
      </main>
    </div>
  );
}

function Composer({
  value,
  onChange,
  onSubmit,
  onImage,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onImage: (event: React.ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}) {
  return (
    <div className="composer">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
          }
        }}
        placeholder="Ask your question..."
        disabled={disabled}
      />
      <label className="icon-button" aria-label="Upload image">
        📎
        <input type="file" accept=".jpg,.jpeg,.png,image/jpeg,image/png" hidden onChange={onImage} />
      </label>
      <button className="send" onClick={onSubmit} disabled={disabled} aria-label="Send">➤</button>
    </div>
  );
}

function Quiz({
  question,
  current,
  total,
  progress,
  selected,
  showHint,
  finalQuestion = false,
  onSelect,
  onHint,
  onNext,
  onPrevious,
}: {
  question: Question;
  current: number;
  total: number;
  progress: number;
  selected: number | null;
  showHint: boolean;
  finalQuestion?: boolean;
  onSelect: (option: number) => void;
  onHint: () => void;
  onNext: () => void;
  onPrevious: () => void;
}) {
  return (
    <div className="quiz-page">
      <div className="quiz-header">
        <span>{finalQuestion ? "Your original question" : `Question ${current + 1} of ${total}`}</span>
        {!finalQuestion && <div className="progress-track"><div style={{ width: `${progress}%` }} /></div>}
      </div>

      <section className="quiz-card">
        <h1>{question.question}</h1>
        <div className="options">
          {question.options.map((option, index) => {
            const number = index + 1;
            return (
              <button
                key={option}
                className={`option ${selected === number ? "selected" : ""}`}
                onClick={() => onSelect(number)}
              >
                <span className="option-letter">{String.fromCharCode(64 + number)}</span>
                <span>{option}</span>
              </button>
            );
          })}
        </div>

        <div className="hint-area">
          {!showHint ? (
            <button className="hint-button" onClick={onHint}>💡 Need a hint?</button>
          ) : (
            <div className="hint"><strong>💡 Hint</strong><span>{question.hint}</span></div>
          )}
        </div>

        <div className="quiz-actions">
          {current > 0 || finalQuestion ? <button className="secondary" onClick={onPrevious}>← Previous</button> : <span />}
          <button className="primary" onClick={onNext} disabled={selected == null}>{finalQuestion ? "Submit Answer" : current === total - 1 ? "Finish →" : "Next →"}</button>
        </div>
      </section>
    </div>
  );
}

export default App;
