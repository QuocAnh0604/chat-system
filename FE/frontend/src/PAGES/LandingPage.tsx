import { MessageSquare, Users, Zap, ShieldCheck } from "lucide-react";
import type {LucideIcon} from "lucide-react";

interface Feature {
  icon: LucideIcon;
  title: string;
  desc: string;
}

const features: Feature[] = [
  {
    icon: Users,
    title: "Kết nối bạn bè",
    desc: "Trò chuyện với bạn bè, đồng nghiệp mọi lúc mọi nơi.",
  },
  {
    icon: Zap,
    title: "Nhắn tin tức thì",
    desc: "Tin nhắn gửi và nhận ngay lập tức, không độ trễ.",
  },
  {
    icon: ShieldCheck,
    title: "Bảo mật riêng tư",
    desc: "Dữ liệu của bạn được mã hoá và bảo vệ an toàn.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-blue-50 px-4 py-16">
      <div className="w-full max-w-sm flex flex-col items-center text-center">
        {/* Logo */}
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-md mb-4">
          <MessageSquare className="w-8 h-8 text-white" strokeWidth={2} />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">ChatApp</h1>
        <p className="text-sm text-gray-400 mt-2">Kết nối mọi người, mọi lúc</p>

        {/* CTA */}
        <div className="w-full mt-8 flex flex-col gap-3">
          <a
            href="/login"
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-semibold shadow-md shadow-indigo-200 hover:opacity-95 active:scale-[0.99] transition text-center"
          >
            Đăng nhập ngay
          </a>
          <a
            href="/register"
            className="w-full py-2.5 rounded-xl border border-gray-200 bg-white text-gray-700 text-sm font-semibold hover:bg-gray-50 active:scale-[0.99] transition text-center"
          >
            Tạo tài khoản mới
          </a>
        </div>
      </div>

      {/* Tính năng nổi bật */}
      <div className="w-full max-w-3xl mt-16 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {features.map((f) => (
          <div
            key={f.title}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex flex-col items-center text-center"
          >
            <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center mb-3">
              <f.icon className="w-5 h-5 text-indigo-500" />
            </div>
            <p className="text-sm font-semibold text-gray-900">{f.title}</p>
            <p className="text-xs text-gray-400 mt-1 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      <p className="text-center text-xs text-gray-400 mt-12">
        Bằng cách tiếp tục, bạn đồng ý với{" "}
        <a href="#" className="underline hover:text-gray-500">Điều khoản</a> &amp;{" "}
        <a href="#" className="underline hover:text-gray-500">Chính sách bảo mật</a>
      </p>
    </div>
  );
}
