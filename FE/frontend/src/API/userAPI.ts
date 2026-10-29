import axiosClient from "./axiosClient";
import type { PresenceStatus, User } from "../types/chat";

export type UserProfile = User;

const userAPI = {
  searchUsers: (q: string, limit = 20) =>
    axiosClient.get<User[]>("/users/search", {
      params: {
        q,
        limit,
      },
    }),

  getMe: () =>
    axiosClient.get<UserProfile>("/users/me"),

  getPresence: (userIds: string[]) =>
    axiosClient.get<PresenceStatus[]>("/users/presence", {
      params: userIds.reduce((params, userId) => {
        params.append("user_ids", userId);
        return params;
      }, new URLSearchParams()),
    }),

  updateProfile: (data: {
    display_name?: string;
    avatar_url?: string;
  }) =>
    axiosClient.patch("/users/me", data),

  changePassword: (data: {
    current_password: string;
    new_password: string;
  }) =>
    axiosClient.patch("/users/me/password", data),

  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return axiosClient.post("/users/me/avatar", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default userAPI;
