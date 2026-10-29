import axios from "axios";
import type { AxiosInstance, AxiosRequestConfig } from "axios";
import { API_URL } from "../config";

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

interface RetryableRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

// Vì interceptor bên dưới trả thẳng `response.data` (bỏ lớp bọc AxiosResponse),
// ta định nghĩa lại type cho axiosClient để các method get/post/put/patch/delete
// trả về Promise<T> thay vì Promise<AxiosResponse<T>>.
interface CustomAxiosInstance extends Omit<
  AxiosInstance,
  "get" | "post" | "put" | "patch" | "delete"
> {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

const axiosClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
}) as CustomAxiosInstance;

let refreshPromise: Promise<string> | null = null;

const clearSession = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
};

const refreshAccessToken = async (): Promise<string> => {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) throw new Error("Refresh token is missing.");
    refreshPromise = axios
      .post<TokenPair>(`${API_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        return data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

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
    const config = error.config as RetryableRequestConfig | undefined;
    const requestUrl = config?.url ?? "";
    if (
      error.response?.status === 401 &&
      config &&
      !config._retry &&
      !requestUrl.includes("/auth/login") &&
      !requestUrl.includes("/auth/refresh")
    ) {
      config._retry = true;
      return refreshAccessToken()
        .then((token) => {
          config.headers = config.headers ?? {};
          config.headers.Authorization = `Bearer ${token}`;
          return axiosClient.request(config);
        })
        .catch((refreshError) => {
          clearSession();
          return Promise.reject(refreshError);
        });
    }
    if (error.response?.status === 401) {
      clearSession();
    }

    return Promise.reject(error);
  }
);

export default axiosClient;
