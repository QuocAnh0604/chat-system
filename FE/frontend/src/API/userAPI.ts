import axiosClient from "./axiosClient";

const userAPI = {
  searchUsers: (q: string, limit = 20) =>
    axiosClient.get("/users/search", {
      params: {
        q,
        limit,
      },
    }),

  getMe: () =>
    axiosClient.get("/users/me"),

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
