export type User = {
  id: number | string;
  username: string;
};

export type AuthResponse = {
  message: string;
  data: User;
};