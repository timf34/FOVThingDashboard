import React, { useEffect, useState } from 'react';
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

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws'); // Adjust WebSocket URL for local/prod

    ws.onopen = () => {
      console.log('WebSocket connection established');
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event);
    };


    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received data:', message);

      // Extract device name from the topic
      const deviceName = message.topic.split('/')[2];  // Assuming topic follows 'fov-marvel-tablet-{n}/{type}'

      // Define updatedField as an object that can hold multiple types
      const updatedField: Partial<Device> = {};

      // Identify the field to update based on message type (e.g., battery or temperature)
      if (message.message.type === 'battery') {
        updatedField.batteryCharge = Number(message.message.value);  // Ensure correct type
      } else if (message.message.type === 'temperature') {
        updatedField.temperature = Number(message.message.value);  // Ensure correct type
      } else if (message.message.type === 'firmwareVersion') {
        updatedField.firmwareVersion = message.message.value;  // For strings, no need to convert
      }

      setDevices((prevDevices) => {
        const existingDevice = prevDevices.find(device => device.name === deviceName);

        if (existingDevice) {
          // Update the existing device with new information, preserving other fields
          return prevDevices.map(device =>
              device.name === deviceName ? { ...device, ...updatedField } : device
          );
        } else {
          // Add a new device if it doesn't exist, initialize with the current field
          return [...prevDevices, { name: deviceName, ...updatedField }];
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
