import React from 'react';
import DeviceComponent from './components/DeviceComponent';
import './index.css';

const App: React.FC = () => {
  // Hardcoded sample data for devices
  const devices = [
    {
      name: 'fov-marvel-tablet-1',
      wifiConnected: true,
      batteryCharge: 75,
      temperature: 60,
      firmwareVersion: '1.1.0',
    },
    {
      name: 'fov-marvel-tablet-2',
      wifiConnected: false,
      batteryCharge: 45,
      temperature: 55,
      firmwareVersion: '1.0.8',
    },
    {
      name: 'fov-marvel-tablet-3',
      wifiConnected: true,
      batteryCharge: 90,
      temperature: 65,
      firmwareVersion: '1.2.1',
    },
    {
      name: 'fov-marvel-tablet-4',
      wifiConnected: true,
      batteryCharge: 30,
      temperature: 72,
      firmwareVersion: '1.1.5',
    },
    // Add more devices as needed
  ];

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
