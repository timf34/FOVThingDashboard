import React, { useEffect, useState, useRef } from 'react';
import DeviceComponent from './components/DeviceComponent';
import './index.css';

interface Device {
  name: string;
  wifiConnected?: boolean;
  batteryCharge?: number;
  temperature?: number;
  firmwareVersion?: string;
}

const App: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...');
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      console.log('WebSocket connection established');
      setConnectionStatus('Connected');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionStatus('Error connecting');
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received data:', message);

      const deviceName = message.topic.split('/')[2];
      const updatedField: Partial<Device> = {};

      // Extract the type from the topic
      const messageType = message.topic.split('/').pop();

      // Parse the message value
      const messageValue = message.message.split(': ')[1];

      switch (messageType) {
        case 'battery':
          updatedField.batteryCharge = Number(messageValue);
          break;
        case 'temperature':
          updatedField.temperature = Number(messageValue);
          break;
        case 'version':
          updatedField.firmwareVersion = messageValue;
          break;
        default:
          console.log("Message type not recognized:", messageType);
      }

      setDevices((prevDevices) => {
        const existingDevice = prevDevices.find(device => device.name === deviceName);
        if (existingDevice) {
          return prevDevices.map(device =>
              device.name === deviceName ? { ...device, ...updatedField } : device
          );
        } else {
          return [...prevDevices, { name: deviceName, ...updatedField }];
        }
      });
    };

    ws.current.onclose = (event) => {
      console.log('WebSocket closed:', event);
      setConnectionStatus('Disconnected. Attempting to reconnect...');

      // Attempt to reconnect after 5 seconds
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
          {devices.map((device) => (
              <DeviceComponent
                  key={device.name}
                  name={device.name}
                  wifiConnected={device.wifiConnected ?? false}
                  batteryCharge={device.batteryCharge ?? 0}
                  temperature={device.temperature ?? 0}
                  firmwareVersion={device.firmwareVersion ?? 'N/A'}
              />
          ))}
        </div>
      </div>
  );
};

export default App;