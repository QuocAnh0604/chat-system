import axiosClient from "./axiosClient";

const messageAPI = {
  getMessages: (conversationId: string, lastId?: string, limit = 50) =>
    axiosClient.get(`/conversations/${conversationId}/messages`, {
      params: {
        last_id: lastId,
        limit,
      },
    }),

  sendMessage: (conversationId: string, content: string) =>
    axiosClient.post(`/conversations/${conversationId}/messages`, {
      content,
    }),

  uploadImage: (conversationId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return axiosClient.post(
      `/conversations/${conversationId}/messages/images`,
      formData
    );
  },

  uploadFile: (conversationId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return axiosClient.post(
      `/conversations/${conversationId}/messages/files`,
      formData
    );
  },

  uploadVideo: (conversationId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return axiosClient.post(
      `/conversations/${conversationId}/messages/videos`,
      formData
    );
  },

  downloadAttachment: (conversationId: string, messageId: string) =>
    axiosClient.get(
      `/conversations/${conversationId}/messages/${messageId}/attachment`,
      {
        responseType: "blob",
      }
    ),

  replyToMessage: (
    conversationId: string,
    messageId: string,
    content: string
  ) =>
    axiosClient.post(
      `/conversations/${conversationId}/messages/${messageId}/replies`,
      { content }
    ),

  editMessage: (
    conversationId: string,
    messageId: string,
    content: string
  ) =>
    axiosClient.patch(
      `/conversations/${conversationId}/messages/${messageId}`,
      { content }
    ),

  deleteMessage: (conversationId: string, messageId: string) =>
    axiosClient.delete(
      `/conversations/${conversationId}/messages/${messageId}`
    ),
};

export default messageAPI;
