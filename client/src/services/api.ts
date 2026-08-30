import type {
  AuthResponse,
  LearnAgainResponse,
  QuestionResponse,
} from "../types";

const API_URL = (import.meta.env.VITE_API_URL ?? "").trim().replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function friendlyHttpMessage(status: number, serverMessage?: string): string {
  if (serverMessage) {
    if (serverMessage.includes("Failed to get response from Gemini API")) {
      return "Nova AI could not generate a practice session. Please try again.";
    }
    if (serverMessage.includes("Database")) {
      return "Nova AI is having trouble accessing your account. Please try again.";
    }
    return serverMessage;
  }

  switch (status) {
    case 400:
      return "Please check the information you entered.";
    case 401:
      return "Incorrect password.";
    case 404:
      return "Username not found.";
    case 409:
      return "That username already exists.";
    case 500:
      return "Nova AI is temporarily unavailable. Please try again.";
    default:
      return "Unable to connect to Nova AI. Please try again.";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  if (!API_URL) {
    throw new ApiError("Nova AI is not configured. Set VITE_API_URL in the frontend environment.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError("Unable to connect to Nova AI. Please try again.");
  }

  const raw = await response.text();
  let data: unknown = {};
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      throw new ApiError("Nova AI returned an invalid response.", response.status);
    }
  }

  if (!response.ok) {
    const message =
      typeof data === "object" &&
      data !== null &&
      "error" in data &&
      typeof data.error === "string"
        ? data.error
        : undefined;
    throw new ApiError(friendlyHttpMessage(response.status, message), response.status);
  }

  return data as T;
}

export function signup(username: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/NewUser_login", {
    method: "POST",
    body: JSON.stringify({ Username: username, NewPassword: password }),
  });
}

export function login(username: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/Old_User_login", {
    method: "POST",
    body: JSON.stringify({ Username: username, Password: password }),
  });
}

export function postQuestion(
  username: string,
  question: string,
  imagePath = "",
): Promise<QuestionResponse> {
  const allowedTypes = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
  ];

  if (!imagePath || !allowedTypes.includes(imagePath.split("/")[imagePath.split("/").length - 1])) {
    throw new ApiError("Invalid image path or type.");
  }

  return request<QuestionResponse>("/QuestionPost", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      Question: question,
      Image_path: imagePath,
    }),
  });
}

export function postDoubtQuestion(
  username: string,
  wrongAnsweredQuestion: string,
  questionJson: string,
): Promise<LearnAgainResponse> {
  return request<LearnAgainResponse>("/DoubtQuestionPost", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      WrongAnsweredquestion: wrongAnsweredQuestion,
      QuestionJson: questionJson,
    }),
  });
}
