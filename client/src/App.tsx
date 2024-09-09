import React, { useEffect, useState } from 'react';
import DeviceComponent from './components/DeviceComponent';
import './index.css';

interface Device {
  name: string;
  wifiConnected?: boolean;  // Optional because WebSocket might not update this immediately
  batteryCharge?: number;
  temperature?: number;
  firmwareVersion?: string;
}

const App: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);

  useEffect(() => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connection established');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received data:', message);

      // Extract device name from the topic
      const deviceName = message.topic.split('/')[2];  // Assuming topic follows 'fov-marvel-tablet-{n}/{type}'

      setDevices((prevDevices) => {
        const existingDevice = prevDevices.find(device => device.name === deviceName);

        const updatedDevice: Device = {
          ...existingDevice,  // Preserve existing device data
          name: deviceName,
          // Update only the relevant field based on the message type
          ...(message.message.type === 'battery' && { batteryCharge: message.message.value }),
          ...(message.message.type === 'temperature' && { temperature: message.message.value }),
        };

        if (existingDevice) {
          // Update the existing device with the new information
          return prevDevices.map(device =>
            device.name === deviceName ? updatedDevice : device
          );
        } else {
          // Add a new device if it doesn't exist
          return [...prevDevices, updatedDevice];
        }
      });
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="App p-4 space-y-4">
      <h1 className="text-2xl font-semibold">FOV Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((device) => (
          <DeviceComponent
            key={device.name}
            name={device.name}
            wifiConnected={device.wifiConnected ?? false}  // Default to false if undefined
            batteryCharge={device.batteryCharge ?? 0}  // Default to 0 if undefined
            temperature={device.temperature ?? 0}  // Default to 0 if undefined
            firmwareVersion={device.firmwareVersion ?? 'N/A'}  // Default to 'N/A' if undefined
          />
        ))}
      </div>
    </div>
  );
};

export default App;
