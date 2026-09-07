import { useEffect, useState } from "react";
import { ArrowLeft, Mail, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import userAPI, { type UserProfile } from "../API/userAPI";
import ProfileHeader from "../COMPONENTS/PROFILE/ProfileHeader";
import ProfileInfoSection from "../COMPONENTS/PROFILE/ProfileInfoSection";
import LogoutButton from "../COMPONENTS/PROFILE/LogoutButton";

const getInitials = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "U";

export default function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const user = await userAPI.getMe();
        setProfile(user);
      } catch (error) {
        console.error("Không thể lấy thông tin người dùng:", error);
      }
    };

    fetchProfile();
  }, []);

  const displayName = profile?.display_name || profile?.username || "User";
  const infoItems = profile
    ? [
        { icon: Mail, label: "Email", value: profile.email },
        { icon: UserRound, label: "Tên hiển thị", value: profile.display_name },
      ]
    : [];

  return (
    <div className="min-h-screen w-full bg-gray-50">
      <div className="max-w-2xl mx-auto pb-10">
        <div className="px-4 sm:px-6 pt-4">
          <button
            type="button"
            aria-label="Quay lại trang chat"
            onClick={() => navigate("/chat")}
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Quay lại
          </button>
        </div>
        <ProfileHeader
          name={displayName}
          bio={profile?.username ? `@${profile.username}` : "Đang tải thông tin..."}
          initials={getInitials(displayName)}
        />

        <div className="px-4 sm:px-6 mt-6 flex flex-col gap-6">
          {profile ? (
            <ProfileInfoSection items={infoItems} />
          ) : (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-6 text-sm text-gray-400">
              Đang tải thông tin...
            </div>
          )}
          <LogoutButton />
        </div>
      </div>
    </div>
  );
}