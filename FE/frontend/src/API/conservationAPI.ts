import axiosClient from "./axiosClient";
import type { ConversationSummary } from "../types/chat";

const conservationAPI = {
  list: (offset = 0, limit = 50) =>
    axiosClient.get<ConversationSummary[]>("/conversations", {
      params: { offset, limit },
    }),

  searchConversations: (q: string, limit = 20) =>
    axiosClient.get<ConversationSummary[]>("/conversations/search", {
      params: {
        q,
        limit,
      },
    }),
};

export default conservationAPI;
