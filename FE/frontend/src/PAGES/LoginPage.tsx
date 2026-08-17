import { useState  } from "react";
import type {FormEvent} from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, MessageSquare } from "lucide-react";
import authAPI from "../API/authAPI";

interface LoginErrors {
  username?: string;
  password?: string;
  server?: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [remember, setRemember] = useState<boolean>(true);
  const [errors, setErrors] = useState<LoginErrors>({});
  const [loading, setLoading] = useState<boolean>(false);

  const validate = (): boolean => {
    const next: LoginErrors = {};
    if (!username.trim()) {
      next.username = "Vui lòng nhập tên đăng nhập";
    }
    if (!password) {
      next.password = "Vui lòng nhập mật khẩu";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setErrors({});
    try {
      const response = await authAPI.login({ username, password });
      const { access_token, refresh_token } = response;
      
      // Lưu token vào localStorage
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      if (remember) {
        localStorage.setItem("remember_username", username);
      }
      
      // Chuyển hướng sang trang chat
      navigate("/chat");
    } catch (error: any) {
      let serverError = "Đăng nhập thất bại, vui lòng thử lại";
      
      const detail = error.response?.data?.detail;
      if (detail) {
        if (typeof detail === "string") {
          serverError = detail;
        } else if (Array.isArray(detail)) {
          // Xử lý lỗi validation từ Pydantic
          serverError = detail.map((err: any) => err.msg || err).join(", ");
        }
      }
      
      setErrors({ server: serverError });
      console.error("Lỗi đăng nhập:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-blue-50 px-4 py-10">
      <div className="w-full max-w-sm">
        {/* Logo + Tiêu đề */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-md mb-3">
            <MessageSquare className="w-7 h-7 text-white" strokeWidth={2} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">ChatApp</h1>
          <p className="text-sm text-gray-400 mt-1">Kết nối mọi người, mọi lúc</p>
        </div>

        {/* Form đăng nhập */}
        <div className="bg-white rounded-2xl shadow-xl shadow-indigo-100/50 p-8">
          <h2 className="text-lg font-bold text-gray-900">Chào mừng trở lại!</h2>
          <p className="text-sm text-gray-400 mt-1 mb-6">Đăng nhập để tiếp tục trò chuyện</p>

          <form onSubmit={handleSubmit} noValidate>
            {/* Lỗi từ server */}
            {errors.server && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200">
                <p className="text-sm text-red-600">{errors.server}</p>
              </div>
            )}
            
            {/* Username */}
            <div className="mb-4">
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1.5">
                Tên đăng nhập
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="username123"
                  className={`w-full pl-9 pr-3 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.username ? "border-red-400" : "border-gray-200"
                  }`}
                />
              </div>
              {errors.username && (
                <p className="text-xs text-red-500 mt-1">{errors.username}</p>
              )}
            </div>

            {/* Mật khẩu */}
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                Mật khẩu
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••"
                  className={`w-full pl-9 pr-9 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.password ? "border-red-400" : "border-gray-200"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-red-500 mt-1">{errors.password}</p>
              )}
            </div>

            {/* Ghi nhớ + Quên mật khẩu */}
            <div className="flex items-center justify-between mb-6">
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-indigo-500 focus:ring-indigo-300"
                />
                Ghi nhớ đăng nhập
              </label>
              <a href="#" className="text-sm font-medium text-indigo-500 hover:text-indigo-600">
                Quên mật khẩu?
              </a>
            </div>

            {/* Nút đăng nhập */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-semibold shadow-md shadow-indigo-200 hover:opacity-95 active:scale-[0.99] transition disabled:opacity-60"
            >
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Chưa có tài khoản?{" "}
            <a href="/register" className="text-indigo-500 font-semibold hover:text-indigo-600">
              Đăng ký ngay
            </a>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Bằng cách đăng nhập, bạn đồng ý với{" "}
          <a href="#" className="underline hover:text-gray-500">Điều khoản</a> &amp;{" "}
          <a href="#" className="underline hover:text-gray-500">Chính sách bảo mật</a>
        </p>
      </div>
    </div>
  );
}
