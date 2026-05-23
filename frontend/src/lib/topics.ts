export const TOPICS = [
  "Artificial Intelligence & Machine Learning",
  "Web Development & Frontend",
  "DevOps & Infrastructure",
  "Programming Languages & Tooling",
  "Cybersecurity",
  "Open Source & Linux",
  "Hardware & Electronics",
  "Science & Research",
] as const;

export type Topic = (typeof TOPICS)[number];

export const TOPIC_META: Record<string, { label: string; color: string; dot: string }> = {
  "Artificial Intelligence & Machine Learning": {
    label: "AI / ML",
    color: "bg-purple-100 text-purple-700 border-purple-200",
    dot: "bg-purple-500",
  },
  "Web Development & Frontend": {
    label: "Web Dev",
    color: "bg-blue-100 text-blue-700 border-blue-200",
    dot: "bg-blue-500",
  },
  "DevOps & Infrastructure": {
    label: "DevOps",
    color: "bg-orange-100 text-orange-700 border-orange-200",
    dot: "bg-orange-500",
  },
  "Programming Languages & Tooling": {
    label: "Programming",
    color: "bg-green-100 text-green-700 border-green-200",
    dot: "bg-green-500",
  },
  // biome-ignore lint/style/useNamingConvention: topic name matches backend DB value
  Cybersecurity: {
    label: "Security",
    color: "bg-red-100 text-red-700 border-red-200",
    dot: "bg-red-500",
  },
  "Open Source & Linux": {
    label: "Open Source",
    color: "bg-yellow-100 text-yellow-700 border-yellow-200",
    dot: "bg-yellow-500",
  },
  "Hardware & Electronics": {
    label: "Hardware",
    color: "bg-slate-100 text-slate-700 border-slate-200",
    dot: "bg-slate-500",
  },
  "Science & Research": {
    label: "Science",
    color: "bg-teal-100 text-teal-700 border-teal-200",
    dot: "bg-teal-500",
  },
};

export function getTopicMeta(topic: string) {
  return (
    TOPIC_META[topic] ?? {
      label: topic,
      color: "bg-gray-100 text-gray-700 border-gray-200",
      dot: "bg-gray-400",
    }
  );
}

export function formatDate(dateStr: string | null, locale = "en-US"): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const hours = Math.floor((now.getTime() - date.getTime()) / 3_600_000);
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(locale, { month: "short", day: "numeric" });
}
