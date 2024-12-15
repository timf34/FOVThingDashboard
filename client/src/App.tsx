import React, { useEffect, useState, useRef } from 'react';
import DeviceComponent from './components/DeviceComponent';
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
}

const App: React.FC = () => {
  const [devices, setDevices] = useState<Record<string, Device>>({});
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...');
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
    console.log('Connecting to WebSocket:', wsUrl);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connection established');
      setConnectionStatus('Connected');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionStatus('Error connecting');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setDevices(prevDevices => ({
        ...prevDevices,
        [data.topic]: data.message
      }));
    };

    ws.current.onclose = () => {
      console.log('WebSocket connection closed');
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
      <h1 className="text-2xl font-semibold">FOV Dashboard</h1>
      <p>Connection Status: {connectionStatus}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(devices).map(([deviceName, device]) => (
          <DeviceComponent
            key={deviceName}
            name={device.name}
            wifiConnected={device.wifiConnected}
            batteryCharge={device.batteryCharge}
            temperature={device.temperature}
            firmwareVersion={device.firmwareVersion}
          />
        ))}
      </div>
    </div>
  );
};

export default App;