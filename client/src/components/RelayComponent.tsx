import { ActivitySquareIcon } from "lucide-react";

export default function RelayComponent({ id, alive, stats, last_seen }: any) {
  const colour = alive ? "bg-green-100" : "bg-red-100";
  return (
    <div className={`p-4 rounded shadow ${colour}`}>
      <h3 className="font-semibold flex items-center gap-2">
        <ActivitySquareIcon className="w-4 h-4" /> relay – {id}
      </h3>
      <p className="text-sm">
        {alive ? "online" : "offline"} · last&nbsp;
        {last_seen ? new Date(last_seen).toLocaleTimeString() : "never"}
      </p>
      {stats && (
        <p className="text-xs mt-1 text-gray-600">
          rx {stats.total_received} / tx {stats.total_published}
        </p>
      )}
    </div>
  );
} 