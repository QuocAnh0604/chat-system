import { useState } from "react";
import type { FormEvent } from "react"
import { useNavigate } from "react-router-dom";
import { Mail, Lock, User, AtSign, Eye, EyeOff, MessageSquare } from "lucide-react";
import authAPI from "../API/authAPI";

interface RegisterForm {
  displayName: string;
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

type RegisterField = keyof RegisterForm;

type RegisterErrors = Partial<Record<RegisterField, string>> & { server?: string };

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterForm>({
    displayName: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirm, setShowConfirm] = useState<boolean>(false);
  const [errors, setErrors] = useState<RegisterErrors>({});
  const [loading, setLoading] = useState<boolean>(false);

  const update =
    (field: RegisterField) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const validate = (): boolean => {
    const next: RegisterErrors = {};

    if (!form.displayName.trim()) {
      next.displayName = "Vui lòng nhập tên hiển thị";
    }

    if (!form.username.trim()) {
      next.username = "Vui lòng nhập tên đăng nhập";
    } else if (!/^[a-zA-Z0-9_]{3,20}$/.test(form.username)) {
      next.username = "3-20 ký tự, chỉ gồm chữ, số và dấu gạch dưới";
    }

    if (!form.email.trim()) {
      next.email = "Vui lòng nhập email";
    } else if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      next.email = "Email không hợp lệ";
    }

    if (!form.password) {
      next.password = "Vui lòng nhập mật khẩu";
    } else if (form.password.length < 8) {
      next.password = "Mật khẩu phải có ít nhất 8 ký tự";
    }

    if (!form.confirmPassword) {
      next.confirmPassword = "Vui lòng xác nhận mật khẩu";
    } else if (form.confirmPassword !== form.password) {
      next.confirmPassword = "Mật khẩu xác nhận không khớp";
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
      await authAPI.register({
        display_name: form.displayName,
        username: form.username,
        email: form.email,
        password: form.password,
      });
      
      // Đăng ký thành công, chuyển sang trang login
      alert("Đăng ký thành công! Vui lòng đăng nhập.");
      navigate("/login");
    } catch (error: any) {
      const serverError = error.response?.data?.detail || "Đăng ký thất bại, vui lòng thử lại";
      setErrors({ server: serverError });
      console.error("Lỗi đăng ký:", error);
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

        {/* Form đăng ký */}
        <div className="bg-white rounded-2xl shadow-xl shadow-indigo-100/50 p-8">
          <h2 className="text-lg font-bold text-gray-900">Tạo tài khoản mới</h2>
          <p className="text-sm text-gray-400 mt-1 mb-6">Đăng ký để bắt đầu trò chuyện</p>

          <form onSubmit={handleSubmit} noValidate>
            {/* Lỗi từ server */}
            {errors.server && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200">
                <p className="text-sm text-red-600">{errors.server}</p>
              </div>
            )}
            
            {/* Tên hiển thị */}
            <div className="mb-4">
              <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-1.5">
                Tên hiển thị
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="displayName"
                  type="text"
                  value={form.displayName}
                  onChange={update("displayName")}
                  placeholder="Trần Thị Hoa"
                  className={`w-full pl-9 pr-3 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.displayName ? "border-red-400" : "border-gray-200"
                  }`}
                />
              </div>
              {errors.displayName && (
                <p className="text-xs text-red-500 mt-1">{errors.displayName}</p>
              )}
            </div>

            {/* Tên đăng nhập */}
            <div className="mb-4">
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1.5">
                Tên đăng nhập
              </label>
              <div className="relative">
                <AtSign className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="username"
                  type="text"
                  value={form.username}
                  onChange={update("username")}
                  placeholder="hoatran"
                  className={`w-full pl-9 pr-3 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.username ? "border-red-400" : "border-gray-200"
                  }`}
                />
              </div>
              {errors.username && (
                <p className="text-xs text-red-500 mt-1">{errors.username}</p>
              )}
            </div>

            {/* Email */}
            <div className="mb-4">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={update("email")}
                  placeholder="hoatran@gmail.com"
                  className={`w-full pl-9 pr-3 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.email ? "border-red-400" : "border-gray-200"
                  }`}
                />
              </div>
              {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
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
                  value={form.password}
                  onChange={update("password")}
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

            {/* Xác nhận mật khẩu */}
            <div className="mb-6">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1.5">
                Xác nhận mật khẩu
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="confirmPassword"
                  type={showConfirm ? "text" : "password"}
                  value={form.confirmPassword}
                  onChange={update("confirmPassword")}
                  placeholder="••••••••••"
                  className={`w-full pl-9 pr-9 py-2.5 rounded-xl border text-sm text-gray-800 placeholder:text-gray-400 outline-none transition focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 ${
                    errors.confirmPassword ? "border-red-400" : "border-gray-200"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((s) => !s)}
                  aria-label={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-xs text-red-500 mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Nút đăng ký */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-semibold shadow-md shadow-indigo-200 hover:opacity-95 active:scale-[0.99] transition disabled:opacity-60"
            >
              {loading ? "Đang đăng ký..." : "Đăng ký"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Đã có tài khoản?{" "}
            <a href="/login" className="text-indigo-500 font-semibold hover:text-indigo-600">
              Đăng nhập luôn!
            </a>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Bằng cách đăng ký, bạn đồng ý với{" "}
          <a href="#" className="underline hover:text-gray-500">Điều khoản</a> &amp;{" "}
          <a href="#" className="underline hover:text-gray-500">Chính sách bảo mật</a>
        </p>
      </div>
    </div>
  );
}
