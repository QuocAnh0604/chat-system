import { useState } from "react";
import { Mail, Phone, MapPin, Calendar } from "lucide-react";
import ProfileHeader from "../COMPONENTS/PROFILE/ProfileHeader";
import ProfileStats from "../COMPONENTS/PROFILE/ProfileStats";
import ProfileInfoSection from "../COMPONENTS/PROFILE/ProfileInfoSection";
import ProfileSettingsSection from "../COMPONENTS/PROFILE/ProfileSettingsSection";
import LogoutButton from "../COMPONENTS/PROFILE/LogoutButton";

const stats = [
  { label: "Bạn bè", value: "248" },
  { label: "Tin nhắn", value: "1.2k" },
  { label: "Nhóm", value: "32" },
];

const infoItems = [
  { icon: Mail, label: "Email", value: "hoatran@gmail.com" },
  { icon: Phone, label: "Điện thoại", value: "+84 912 345 678" },
  { icon: MapPin, label: "Vị trí", value: "Hà Nội, Việt Nam" },
  { icon: Calendar, label: "Tham gia", value: "Tháng 3, 2022" },
];

export default function ProfilePage() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  return (
    <div className="min-h-screen w-full bg-gray-50">
      <div className="max-w-2xl mx-auto pb-10">
        <ProfileHeader
          name="Trần Thị Hoa"
          bio="Yêu thích du lịch, ẩm thực và công nghệ 🌟"
          initials="TH"
        />
        <ProfileStats stats={stats} />

        <div className="px-4 sm:px-6 mt-6 flex flex-col gap-6">
          <ProfileInfoSection items={infoItems} />
          <ProfileSettingsSection
            notifications={notifications}
            onNotificationsChange={setNotifications}
            darkMode={darkMode}
            onDarkModeChange={setDarkMode}
          />
          <LogoutButton />
        </div>
      </div>
    </div>
  );
}