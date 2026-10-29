import axiosClient from "./axiosClient";
import type { ApiMessage, MessagePage } from "../types/chat";

const messageAPI = {
  getMessages: (conversationId: string, lastId?: string, limit = 50) =>
    axiosClient.get<MessagePage>(`/conversations/${conversationId}/messages`, {
      params: {
        last_id: lastId,
        limit,
      },
    }),

  sendMessageToUser: (targetUserId: string, content: string, clientMessageId?: string) =>
    axiosClient.post<ApiMessage>("/messages", {
      target_user_id: targetUserId,
      content,
      client_message_id: clientMessageId,
    }),

  sendMessage: (conversationId: string, content: string, clientMessageId?: string) =>
    axiosClient.post<ApiMessage>(`/conversations/${conversationId}/messages`, {
      content,
      client_message_id: clientMessageId,
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
