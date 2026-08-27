export type User = {
  id: number | string;
  username: string;
};

export type AuthResponse = {
  message: string;
  data: User;
};

export type Question = {
  question: string;
  options: string[];
  hint: string;
  correct_option: number;
};

export type QuestionResponse = {
  is_relevant: boolean;
  error_message: string;
  ai_questions: Question[];
  user_question: Question;
};
