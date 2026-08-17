import axiosClient from "./axiosClient";

const readStatusAPI = {
  markAsRead: (conversationId: string, messageId: string) =>
    axiosClient.patch(`/conversations/${conversationId}/read`, {
      message_id: messageId,
    }),

  getUnreadCount: (conversationId: string) =>
    axiosClient.get(`/conversations/${conversationId}/unread-count`),
};

export default readStatusAPI;
