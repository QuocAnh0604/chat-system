import axios from "axios";
import type { AxiosInstance, AxiosRequestConfig } from "axios";
import { API_URL } from "../config";

// Vì interceptor bên dưới trả thẳng `response.data` (bỏ lớp bọc AxiosResponse),
// ta định nghĩa lại type cho axiosClient để các method get/post/put/patch/delete
// trả về Promise<T> thay vì Promise<AxiosResponse<T>>.
interface CustomAxiosInstance extends Omit<
  AxiosInstance,
  "get" | "post" | "put" | "patch" | "delete"
> {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

const axiosClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
}) as CustomAxiosInstance;

axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

axiosClient.interceptors.response.use(
  // Trả thẳng response.data (không còn lớp bọc AxiosResponse)
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");

      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default axiosClient;