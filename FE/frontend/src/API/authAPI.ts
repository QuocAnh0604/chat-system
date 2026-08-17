import axiosClient from "./axiosClient";

// Khớp với schema TokenPair bên FastAPI (BE/schemas/auth.py)
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

// Khớp với schema UserResponse bên FastAPI (BE/schemas/users.py)
export interface UserResponse {
  id: string;
  username: string;
  email: string;
  display_name: string;
  is_active?: boolean;
  created_at?: string;
  // ... thêm field khác nếu backend có
}

const authAPI = {
  register: (data: {
    username: string;
    email: string;
    password: string;
    display_name: string;
  }) => axiosClient.post<UserResponse>("/auth/register", data),

  login: (data: { username: string; password: string }) =>
    axiosClient.post<TokenPair>("/auth/login", data),

  refresh: (refresh_token: string) =>
    axiosClient.post<TokenPair>("/auth/refresh", { refresh_token }),

  logout: (refresh_token: string) =>
    axiosClient.post<void>("/auth/logout", { refresh_token }),
};

export default authAPI;