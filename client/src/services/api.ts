const API_URL =
  import.meta.env.VITE_API_URL || "https://computational-thinking-2025-26.onrender.com";

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
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

  return data;
}

export function signup(username: string, password: string) {
  return request<{
    message: string;
    data: {
      id: number | string;
      username: string;
    };
  }>("/NewUser_login", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      NewPassword: password,
    }),
  });
}

export function login(username: string, password: string) {
  return request<{
    message: string;
    data: {
      id: number | string;
      username: string;
    };
  }>("/Old_User_login", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      Password: password,
    }),
  });
}

export function PostQuestion(username: string, question: string, img_path: string) {
  return request<{
    message: string;
    data: {
      ai_questions: {
        correct_option: number;
        hint: string;
        options: string[];
        question: string;
      }[];
      error_message: string;
      is_relevant: boolean;
      user_question: {
        correct_option: number;
        hint: string;
        options: string[];
        question: string;
      };
    };
  }>("/QuestionPost", {
    method: "POST",
    body: JSON.stringify({
      Username: username,
      Question: question,
      ImagePath: img_path
    }),
  });
}
