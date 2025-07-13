import React, { useEffect, useState, useRef } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import DeviceComponent from './components/DeviceComponent';
import ChampionRelay from './components/ChampionRelay';   // NEW
import './index.css';

interface Device {
  name: string;
  wifiConnected: boolean;
  batteryCharge: number;
  temperature: number;
  firmwareVersion: string;
  otaUpdateStatus: string;
  lastMessageTime: string;
  firstSeen: string;
  latencyMs?: number;
}

type Filter = "all" | "online" | "offline";

const App: React.FC = () => {
  const [devices, setDevices] = useState<Record<string, Device>>({});
  const [relays, setRelays] = useState<Record<string, any>>({});
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...');
  const [filter, setFilter] = useState<Filter>("all");
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /** remember the toast we raised for each offline device so we can:
   *  – avoid duplicates
   *  – close it once the device is back online                                       */
  const offlineToastIds = useRef<Record<string, React.ReactText>>({});

  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const wsUrl =
      process.env.REACT_APP_WS_URL ||
      `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${
        window.location.host
    }/ws`;
      console.log('Connecting to WebSocket:', wsUrl);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connection established');
      setConnectionStatus('Connected');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionStatus('Error connecting');
      if (ws.current) {
        ws.current.close();
      }
    };

    ws.current.onmessage = (event) => {
      // Handle ping/pong messages
      if (event.data === "ping") {
        ws.current?.send("pong");
        return;
      }
      if (event.data === "pong") {
        return;
      }

      try {
        const data = JSON.parse(event.data);
        
        if (data.topic?.startsWith("relay:")) {
          const rid = data.topic.split(":")[1];
          setRelays(prev => ({ ...prev, [rid]: data.message }));
          return;
        }

        setDevices(prevDevices => {
          const prev = prevDevices[data.topic];
          const next = { ...prev, ...data.message };

          /* ---   show toast on Connected ➜ Disconnected  --- */
          if (prev && prev.wifiConnected && !next.wifiConnected) {
            // only once per device
            if (!offlineToastIds.current[next.name]) {
              const id = toast.error(`${next.name} went offline`, {
                autoClose: 300_000,            // 5 min
                closeOnClick: true,
                onClose: () => { delete offlineToastIds.current[next.name]; },
              });
              offlineToastIds.current[next.name] = id;
            }
          }

          /* optional: clear the toast when the device reconnects */
          if (prev && !prev.wifiConnected && next.wifiConnected) {
            const id = offlineToastIds.current[next.name];
            if (id) {
              toast.dismiss(id);
              delete offlineToastIds.current[next.name];
            }
          }

          return { ...prevDevices, [data.topic]: next };
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.current.onclose = (event) => {
      console.log(`WebSocket closed: ${event.code} ${event.reason}`);
      setConnectionStatus('Disconnected. Attempting to reconnect...');

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    };
  };

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const api = `${window.location.protocol}//${window.location.host}`;
        const res = await fetch(`${api}/api/devices`);
        setDevices(await res.json());
      } catch (e) {
        console.error('initial fetch failed', e);
      }
    };
  
    loadInitial();
    connectWebSocket();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="App p-4 space-y-4">
      {/* fixed top-right status of the Champion-Data relay */}
      <ChampionRelay data={relays["championdata"]} />

      <h1 className="text-2xl font-semibold">FOV Dashboard</h1>
      
      {(() => {
        const deviceEntries = Object.entries(devices);
        const onlineCount = deviceEntries.filter(([_, d]) => d.wifiConnected).length;
        const offlineCount = deviceEntries.filter(([_, d]) => !d.wifiConnected).length;
        const allCount = deviceEntries.length;
        
        return (
          <div className="flex gap-2 mt-2">
            {([
              { key: "all" as const, label: `All (${allCount})` },
              { key: "online" as const, label: `Online (${onlineCount})` },
              { key: "offline" as const, label: `Offline (${offlineCount})` }
            ]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-3 py-1 rounded-md border
                            ${filter === key ? "bg-blue-600 text-white" : "bg-white hover:bg-gray-100"}`}
              >
                {label}
              </button>
            ))}
          </div>
        );
      })()}
      
      <p>Connection Status: {connectionStatus}</p>
      
      {/* Derive filtered devices */}
      {(() => {
        const filteredDevices = Object.entries(devices).filter(([_, d]) => 
          (filter === "all") ? true : (filter === "online" ? d.wifiConnected : !d.wifiConnected)
        );
        
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDevices
              .sort(([a],[b]) => a.localeCompare(b))
              .map(([deviceName, device]) => (
                <DeviceComponent
                  key={deviceName}
                  name={device.name}
                  wifiConnected={device.wifiConnected}
                  batteryCharge={device.batteryCharge}
                  temperature={device.temperature}
                  firmwareVersion={device.firmwareVersion}
                  latencyMs={device.latencyMs}
                />
              ))}
          </div>
        );
      })()}

      {/* Toast portal */}
      <ToastContainer
        position="bottom-right"
        newestOnTop
        closeOnClick
        limit={5}          /* keep the UI tidy */
        draggable
      />
    </div>
  );
};

export default App;