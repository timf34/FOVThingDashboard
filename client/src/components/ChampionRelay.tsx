import { ActivitySquareIcon } from "lucide-react";

interface ChampionRelayProps {
  /** relay heartbeat object coming from the WS – may be undefined */
  data?: {
    alive?: boolean;
    last_seen?: string;   // ISO string from backend
  };
}

export default function ChampionRelay({ data }: ChampionRelayProps) {
  /* fall-back to "offline / never" until the first heartbeat arrives */
  const alive     = data?.alive ?? false;
  const lastSeen  = data?.last_seen
      ? new Date(data.last_seen).toLocaleTimeString()
      : "never";

  return (
    <div
      className="
        fixed top-4 right-4 z-50
        flex items-center gap-2
        bg-white/90 backdrop-blur-sm shadow rounded-lg
        px-3 py-2 text-sm"
    >
      <ActivitySquareIcon className="w-4 h-4 text-gray-600" />
	  <span>Champion Data Relay</span>
      <span className={alive ? "text-green-600" : "text-red-600"}>
        {alive ? "online" : "offline"}
      </span>
      <span className="text-gray-500">· last {lastSeen} UTC</span>
    </div>
  );
} 