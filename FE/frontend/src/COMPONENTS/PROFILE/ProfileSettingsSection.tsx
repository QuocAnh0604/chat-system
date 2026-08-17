import { Bell, Moon, Shield, Lock } from "lucide-react";
import SettingsToggleRow from "./SettingsToggleRow";
import SettingsLinkRow from "./SettingsLinkRow";

interface ProfileSettingsSectionProps {
  notifications: boolean;
  onNotificationsChange: (value: boolean) => void;
  darkMode: boolean;
  onDarkModeChange: (value: boolean) => void;
  onPrivacyClick?: () => void;
  onSecurityClick?: () => void;
}

export default function ProfileSettingsSection({
  notifications,
  onNotificationsChange,
  darkMode,
  onDarkModeChange,
  onPrivacyClick,
  onSecurityClick,
}: ProfileSettingsSectionProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <p className="text-xs font-semibold text-gray-400 tracking-wide px-5 pt-4 pb-2">
        CÀI ĐẶT
      </p>

      <SettingsToggleRow
        icon={Bell}
        label="Thông báo"
        checked={notifications}
        onChange={onNotificationsChange}
      />

      <SettingsToggleRow
        icon={Moon}
        label="Giao diện tối"
        checked={darkMode}
        onChange={onDarkModeChange}
      />

      <SettingsLinkRow icon={Shield} label="Quyền riêng tư" onClick={onPrivacyClick} />

      <SettingsLinkRow
        icon={Lock}
        label="Bảo mật tài khoản"
        onClick={onSecurityClick}
        bordered={false}
      />
    </div>
  );
}