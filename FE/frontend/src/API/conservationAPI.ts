import axiosClient from "./axiosClient";

const conservationAPI = {
  searchConversations: (q: string, limit = 20) =>
    axiosClient.get("/conversations/search", {
      params: {
        q,
        limit,
      },
    }),
};

export default conservationAPI;
