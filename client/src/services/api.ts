import type { AuthResponse, QuestionResponse } from "../types";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "https://computational-thinking-2025-26.onrender.com";

async function request<T>(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong.");
  }

  return data as T;
}

export function signup(username: string, password: string) {
  return request<AuthResponse>("/NewUser_login", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      NewPassword: password,
    }),
  });
}

export function login(username: string, password: string) {
  return request<AuthResponse>("/Old_User_login", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      Password: password,
    }),
  });
}

export function postQuestion(
  username: string,
  question: string,
  imagePath = ""
) {
  return request<QuestionResponse>("/QuestionPost", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      Question: question,
      Image_path: imagePath,
    }),
  });
}
