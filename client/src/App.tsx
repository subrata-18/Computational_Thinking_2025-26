import { useEffect, useMemo, useState } from "react";
import { login, postDoubtQuestion, postQuestion, signup } from "./services/api";
import { uploadQuestionImage } from "./services/supabase";
import type { LearnAgainResponse, Question, QuestionResponse, User } from "./types";
import "./App.css";

type Page = "landing" | "login" | "signup" | "app";
type Stage = "home" | "loading" | "quiz" | "result" | "learnAgain" | "original" | "evaluation";

type StoredSession = {
  id: number | string;
  username: string;
};

const SESSION_KEY = "nova_ai_session";
const MAX_IMAGE_SIZE = 10 * 1024 * 1024;

const quotes = [
  "Every expert was once a beginner.",
  "The important thing is not to stop questioning.",
  "Learning never exhausts the mind.",
  "Small steps lead to big discoveries.",
  "Curiosity is the beginning of understanding.",
];

function readStoredSession(): User | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      !("id" in parsed) ||
      !("username" in parsed) ||
      (typeof parsed.id !== "string" && typeof parsed.id !== "number") ||
      typeof parsed.username !== "string" ||
      !parsed.username.trim()
    ) {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
    return parsed as StoredSession;
  } catch {
    localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function isQuestion(value: unknown): value is Question {
  if (typeof value !== "object" || value === null) return false;
  if (!("question" in value) || !("options" in value) || !("hint" in value) || !("correct_option" in value)) {
    return false;
  }

  const question = value.question;
  const options = value.options;
  const hint = value.hint;
  const correctOption = value.correct_option;

  return (
    typeof question === "string" &&
    question.trim().length > 0 &&
    Array.isArray(options) &&
    options.length === 4 &&
    options.every((option) => typeof option === "string") &&
    typeof hint === "string" &&
    typeof correctOption === "number" &&
    Number.isInteger(correctOption) &&
    correctOption >= 1 &&
    correctOption <= 4
  );
}

function validateQuestionResponse(value: unknown): QuestionResponse | null {
  if (typeof value !== "object" || value === null) return null;
  if (!("is_relevant" in value) || typeof value.is_relevant !== "boolean") return null;
  if (!("error_message" in value) || typeof value.error_message !== "string") return null;

  if (!value.is_relevant) {
    return value as QuestionResponse;
  }

  if (
    !("ai_questions" in value) ||
    !Array.isArray(value.ai_questions) ||
    value.ai_questions.length === 0 ||
    !value.ai_questions.every(isQuestion) ||
    !("user_question" in value) ||
    !isQuestion(value.user_question)
  ) {
    return null;
  }

  return value as QuestionResponse;
}

function validateLearnAgainResponse(value: unknown): LearnAgainResponse | null {
  if (typeof value !== "object" || value === null) return null;
  if (
    !("ai_questions" in value) ||
    !Array.isArray(value.ai_questions) ||
    value.ai_questions.length === 0 ||
    !value.ai_questions.every(isQuestion)
  ) {
    return null;
  }
  if (!("user_question" in value) || !isQuestion(value.user_question)) return null;
  return value as LearnAgainResponse;
}

function App() {
  const [page, setPage] = useState<Page>(() => (readStoredSession() ? "app" : "landing"));
  const [user, setUser] = useState<User | null>(() => readStoredSession());

  function authenticate(userData: User) {
    const safeUser = { id: userData.id, username: userData.username.trim() };
    localStorage.setItem(SESSION_KEY, JSON.stringify(safeUser));
    setUser(safeUser);
    setPage("app");
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    setUser(null);
    setPage("landing");
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

  if (!user) {
    return <Landing onLogin={() => setPage("login")} onSignup={() => setPage("signup")} />;
  }

  return <NovaAI user={user} onLogout={logout} />;
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

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const cleanUsername = username.trim();
    if (!cleanUsername || !password) {
      setError("Username and password are required.");
      return;
    }

    setLoading(true);
    try {
      const response = isLogin
        ? await login(cleanUsername, password)
        : await signup(cleanUsername, password);
      if (!response.data || typeof response.data.username !== "string") {
        throw new Error("Nova AI returned an invalid account response.");
      }
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

        <label htmlFor="username">Username
          <input
            id="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter username"
            autoComplete="username"
            disabled={loading}
          />
        </label>

        <label htmlFor="password">Password
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            autoComplete={isLogin ? "current-password" : "new-password"}
            disabled={loading}
          />
        </label>

        {error && <div className="error" role="alert">{error}</div>}
        <button className="primary full" disabled={loading}>
          {loading ? (isLogin ? "Signing in..." : "Creating account...") : isLogin ? "Log in" : "Create account"}
        </button>
        <button type="button" className="switch-auth" onClick={onSwitch} disabled={loading}>
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
  const [imagePath, setImagePath] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Understanding your question...");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [originalQuestion, setOriginalQuestion] = useState<Question | null>(null);
  const [sessionResponse, setSessionResponse] = useState<QuestionResponse | null>(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [showHint, setShowHint] = useState(false);
  const [error, setError] = useState("");
  const [score, setScore] = useState(0);
  const [finalAnswer, setFinalAnswer] = useState<number | null>(null);
  const [learnAnswers, setLearnAnswers] = useState<Record<number, number>>({});
  const [learnCurrent, setLearnCurrent] = useState(0);
  const [learnQuestions, setLearnQuestions] = useState<Question[]>([]);
  const [learnError, setLearnError] = useState("");
  const [learnLoadingIndex, setLearnLoadingIndex] = useState<number | null>(null);

  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  function removeImage() {
    setImage(null);
    setImagePath("");
    setImagePreview((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return null;
    });
  }

  function newChat() {
    removeImage();
    setQuestionText("");
    setQuestions([]);
    setOriginalQuestion(null);
    setSessionResponse(null);
    setCurrent(0);
    setAnswers({});
    setShowHint(false);
    setScore(0);
    setFinalAnswer(null);
    setError("");
    setLearnError("");
    setLearnQuestions([]);
    setLearnAnswers({});
    setLearnCurrent(0);
    setLearnLoadingIndex(null);
    setQuote(quotes[Math.floor(Math.random() * quotes.length)]);
    setStage("home");
  }

  async function selectImage(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/heic",
      "image/heif",
    ];
    const fileExtension = file.name.split(".").pop()?.toLowerCase();
    const allowedExtensions = ["jpg", "jpeg", "png", "webp", "heic", "heif"];
    if (
      (file.type && !allowedTypes.includes(file.type)) ||
      (!file.type && !fileExtension) ||
      (fileExtension && !allowedExtensions.includes(fileExtension))
    ) {
      setError("Please choose a JPG, PNG, WEBP, HEIC or HEIF image.");
      return;
    }
    if (file.size > MAX_IMAGE_SIZE) {
      setError("Image is too large. Please choose an image up to 10 MB.");
      return;
    }

    setError("");
    removeImage();
    setImage(file);
    setImagePreview(URL.createObjectURL(file));

    setImageUploading(true);
    try {
      const uploadedPath = await uploadQuestionImage(file);
      setImagePath(uploadedPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image upload failed. Please try again.");
      removeImage();
    } finally {
      setImageUploading(false);
    }
  }

  async function submitQuestion() {
    const cleanQuestion = questionText.trim();
    if (!cleanQuestion && !image) {
      setError("Enter a question or upload an image.");
      return;
    }

    if (imageUploading || stage === "loading") return;

    setError("");
    setStage("loading");

    try {
      setLoadingMessage("Understanding your question...");
      await new Promise<void>((resolve) => window.setTimeout(resolve, 100));
      setLoadingMessage("Generating a personalized practice session...");

      const rawResponse = await postQuestion(user.username, cleanQuestion, imagePath);
      const response = validateQuestionResponse(rawResponse);

      if (!response) {
        throw new Error("Something went wrong while preparing your practice session. Please try again.");
      }

      if (response.is_relevant !== true) {
        setError(response.error_message || "This question could not be processed.");
        setStage("home");
        return;
      }

      setSessionResponse(response);
      setQuestions(response.ai_questions);
      setOriginalQuestion(response.user_question);
      setCurrent(0);
      setAnswers({});
      setShowHint(false);
      setStage("quiz");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to connect to Nova AI. Please try again.");
      setStage("home");
    } finally {
      setImageUploading(false);
    }
  }

  function chooseAnswer(option: number) {
    setAnswers((previous) => ({ ...previous, [current]: option }));
  }

  function finishPractice() {
    const finalScore = questions.reduce(
      (total, item, index) => total + (answers[index] === item.correct_option ? 1 : 0),
      0,
    );
    setScore(finalScore);
    setShowHint(false);
    setStage("result");
  }

  function nextQuestion() {
    if (answers[current] == null) return;

    if (current < questions.length - 1) {
      setCurrent((value) => value + 1);
      setShowHint(false);
      return;
    }

    finishPractice();
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

  async function learnAgain(question: Question, reviewIndex: number) {
    if (!sessionResponse || learnLoadingIndex !== null) return;

    setLearnError("");
    setLearnLoadingIndex(reviewIndex);
    setLoadingMessage("Preparing easier practice...");
    setStage("loading");

    try {
      const rawResponse = await postDoubtQuestion(
        user.username,
        question.question,
        JSON.stringify(sessionResponse),
      );
      const response = validateLearnAgainResponse(rawResponse);
      if (!response) {
        throw new Error("Something went wrong while preparing the new practice session. Please try again.");
      }

      setLearnQuestions(response.ai_questions);
      setLearnAnswers({});
      setLearnCurrent(0);
      setShowHint(false);
      setLearnError("");
      setStage("learnAgain");
    } catch (err) {
      setLearnError(err instanceof Error ? err.message : "Unable to prepare easier practice. Please try again.");
      setStage("result");
    } finally {
      setLearnLoadingIndex(null);
    }
  }

  function chooseLearnAnswer(option: number) {
    setLearnAnswers((previous) => ({ ...previous, [learnCurrent]: option }));
  }

  function nextLearnQuestion() {
    if (learnAnswers[learnCurrent] == null) return;
    if (learnCurrent < learnQuestions.length - 1) {
      setLearnCurrent((value) => value + 1);
      setShowHint(false);
      return;
    }
    setShowHint(false);
    setStage("result");
  }

  const progress = questions.length ? ((current + 1) / questions.length) * 100 : 0;
  const learnProgress = learnQuestions.length ? ((learnCurrent + 1) / learnQuestions.length) * 100 : 0;

  const review = useMemo(
    () => questions.map((question, index) => ({
      question,
      index,
      selected: answers[index] ?? null,
      correct: answers[index] === question.correct_option,
    })),
    [answers, questions],
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">nova ai</div>
        <button className="new-chat" onClick={newChat}>＋ New Chat</button>
        <div className="sidebar-bottom">
          <div className="username" title={user.username}>{user.username}</div>
          <button className="logout" onClick={onLogout}>Log out</button>
        </div>
      </aside>

      <main className="main">
        {stage === "home" && (
          <div className="home-content">
            <div className="welcome">
              <h1>Hi, {user.username} 👋</h1>
              <p>“{quote}”</p>
            </div>

            <div className="composer-wrapper">
              {imagePreview && (
                <div className="image-preview">
                  <img src={imagePreview} alt="Selected question preview" />
                  <button type="button" onClick={removeImage} aria-label="Remove image">×</button>
                </div>
              )}

              {error && <div className="error composer-error" role="alert">{error}</div>}

              <Composer
                value={questionText}
                onChange={setQuestionText}
                onSubmit={submitQuestion}
                onImage={selectImage}
                disabled={imageUploading}
              />
              {image && (
                <p className="attachment-name">
                  {imageUploading ? "Uploading image..." : image.name}
                </p>
              )}
            </div>
          </div>
        )}

        {stage === "loading" && (
          <LoadingState message={loadingMessage} />
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
          <div className="result-page">
            <div className="result-card">
              <span className="eyebrow">Practice complete</span>
              <h1>Quiz Complete!</h1>
              <div className="score">{score} / {questions.length}</div>
              <div className="progress-track" aria-label={`${questions.length ? Math.round((score / questions.length) * 100) : 0}% correct`}>
                <div style={{ width: `${questions.length ? (score / questions.length) * 100 : 0}%` }} />
              </div>
              <p>{questions.length ? Math.round((score / questions.length) * 100) : 0}% Correct</p>
            </div>

            {learnError && <div className="error review-error" role="alert">{learnError}</div>}

            <QuestionReview
              review={review}
              loadingIndex={learnLoadingIndex}
              onLearnAgain={learnAgain}
            />

            <button className="primary result-next" onClick={startOriginal}>Try Original Question</button>
          </div>
        )}

        {stage === "learnAgain" && learnQuestions[learnCurrent] && (
          <Quiz
            question={learnQuestions[learnCurrent]}
            current={learnCurrent}
            total={learnQuestions.length}
            progress={learnProgress}
            selected={learnAnswers[learnCurrent] ?? null}
            showHint={showHint}
            learnAgain
            onSelect={chooseLearnAnswer}
            onHint={() => setShowHint(true)}
            onNext={nextLearnQuestion}
            onPrevious={() => {
              if (learnCurrent > 0) {
                setLearnCurrent((value) => value - 1);
                setShowHint(false);
              } else {
                setStage("result");
              }
            }}
          />
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
          <div className="result-card final-result">
            {finalAnswer === originalQuestion.correct_option ? (
              <>
                <div className="result-icon">✓</div>
                <h1>Correct! 🎉</h1>
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

function LoadingState({ message }: { message: string }) {
  return (
    <div className="center-state" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <h2>{message}</h2>
      <p>Please wait while Nova AI prepares your session.</p>
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
        aria-label="Ask your question"
        disabled={disabled}
      />
      <label className="icon-button" aria-label="Upload image">
        📎
        <input
          type="file"
          accept="image/*,.jpg,.jpeg,.png,.webp,.heic,.heif"
          hidden
          onChange={onImage}
          disabled={disabled}
        />
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
  learnAgain = false,
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
  learnAgain?: boolean;
  onSelect: (option: number) => void;
  onHint: () => void;
  onNext: () => void;
  onPrevious: () => void;
}) {
  return (
    <div className="quiz-page">
      <div className="quiz-header">
        <span>
          {finalQuestion
            ? "Your original question"
            : learnAgain
              ? `Learn Again · Question ${current + 1} of ${total}`
              : `Question ${current + 1} of ${total}`}
        </span>
        {!finalQuestion && <div className="progress-track"><div style={{ width: `${progress}%` }} /></div>}
      </div>

      <section className="quiz-card">
        <h1>{question.question}</h1>
        <div className="options" role="radiogroup" aria-label="Answer options">
          {question.options.map((option, index) => {
            const number = index + 1;
            const selectedClass = selected === number ? " selected" : "";
            return (
              <button
                key={`${number}-${option}`}
                type="button"
                role="radio"
                aria-checked={selected === number}
                className={`option${selectedClass}`}
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
            <button type="button" className="hint-button" onClick={onHint}>💡 Need a hint?</button>
          ) : (
            <div className="hint">
              <strong>💡 Hint</strong>
              <span>{question.hint}</span>
            </div>
          )}
        </div>

        <div className="quiz-actions">
          {current > 0 || finalQuestion ? (
            <button type="button" className="secondary" onClick={onPrevious}>← Previous</button>
          ) : <span />}
          <button
            type="button"
            className="primary"
            onClick={onNext}
            disabled={selected == null}
          >
            {finalQuestion ? "Submit Answer" : current === total - 1 ? "Finish →" : "Next →"}
          </button>
        </div>
      </section>
    </div>
  );
}

type ReviewItem = {
  question: Question;
  index: number;
  selected: number | null;
  correct: boolean;
};

function QuestionReview({
  review,
  loadingIndex,
  onLearnAgain,
}: {
  review: ReviewItem[];
  loadingIndex: number | null;
  onLearnAgain: (question: Question, index: number) => void;
}) {
  return (
    <section className="review-section" aria-labelledby="review-title">
      <div className="review-heading">
        <div>
          <span className="eyebrow">Performance</span>
          <h2 id="review-title">Question Review</h2>
        </div>
        <span className="review-count">{review.length} questions</span>
      </div>

      <div className="review-list">
        {review.map((item) => (
          <article className="review-item" key={item.index}>
            <div className={`review-status ${item.correct ? "correct" : "incorrect"}`} aria-label={item.correct ? "Correct" : "Incorrect"}>
              {item.correct ? "✓" : "×"}
            </div>
            <div className="review-content">
              <div className="review-number">Question {item.index + 1}</div>
              <div className="review-question">{item.question.question}</div>
              {item.selected != null && (
                <div className="review-answer">
                  Your answer: <strong>{item.question.options[item.selected - 1]}</strong>
                  {!item.correct && <> · Correct: <strong>{item.question.options[item.question.correct_option - 1]}</strong></>}
                </div>
              )}
            </div>
            <button
              type="button"
              className="secondary learn-button"
              onClick={() => onLearnAgain(item.question, item.index)}
              disabled={loadingIndex !== null}
            >
              {loadingIndex === item.index ? "Preparing..." : "Learn Again"}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

export default App;
