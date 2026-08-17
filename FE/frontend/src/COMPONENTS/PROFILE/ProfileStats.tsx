interface StatItem {
  label: string;
  value: string;
}

interface ProfileStatsProps {
  stats: StatItem[];
}

export default function ProfileStats({ stats }: ProfileStatsProps) {
  return (
    <div className="flex items-center justify-center gap-10 mt-6 pb-6 border-b border-gray-100">
      {stats.map((s) => (
        <div key={s.label} className="text-center">
          <p className="text-lg font-bold text-gray-900">{s.value}</p>
          <p className="text-xs text-gray-400 mt-0.5">{s.label}</p>
        </div>
      ))}
    </div>
  );
}