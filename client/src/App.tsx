import React, { useEffect, useState } from 'react';
import DeviceComponent from './components/DeviceComponent';
import './index.css';

interface Device {
  name: string;
  wifiConnected: boolean;
  batteryCharge: number;
  temperature: number;
  firmwareVersion: string;
}

const App: React.FC = () => {
  // Initialize state for devices
  const [devices, setDevices] = useState<Device[]>([]);

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws'); // Replace 'your-backend-ip' with your actual backend IP or domain

    ws.onopen = () => {
      console.log('WebSocket connection established');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received data:', message);

      // Extract device name from the topic
      const deviceName = message.topic.split('/')[2];  // Assuming topic follows the format 'fov-marvel-tablet-{n}'
      const updatedDevice = {
        name: deviceName,
        wifiConnected: message.wifiConnected,
        batteryCharge: message.batteryCharge,
        temperature: message.temperature,
        firmwareVersion: message.firmwareVersion,
      };

      // Update the state
      setDevices((prevDevices) => {
        // Check if the device already exists
        const existingDevice = prevDevices.find(device => device.name === deviceName);
        if (existingDevice) {
          // Update the existing device
          return prevDevices.map(device =>
            device.name === deviceName ? updatedDevice : device
          );
        } else {
          // Add a new device
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
