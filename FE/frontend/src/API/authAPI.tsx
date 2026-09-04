import axiosClient from "./axiosClient";

const authAPI = {
  register: (data: {
    email: string;
    password: string;
    display_name: string;
  }) =>
    axiosClient.post("/auth/register", data),

  login: (data: {
    email: string;
    password: string;
  }) =>
    axiosClient.post("/auth/login", data),

  refresh: (refresh_token: string) =>
    axiosClient.post("/auth/refresh", {
      refresh_token,
    }),

  logout: (refresh_token: string) =>
    axiosClient.post("/auth/logout", {
      refresh_token,
    }),
};

export default authAPI;