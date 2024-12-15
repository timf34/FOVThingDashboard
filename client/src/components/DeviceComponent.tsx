import React, { useState } from 'react';
import { BatteryIcon, CpuIcon, ThermometerIcon, WifiIcon } from "lucide-react";
import DeviceHistoryModal from './DeviceHistoryModal';

interface DeviceProps {
    name: string;
    wifiConnected?: boolean;
    batteryCharge?: number;
    temperature?: number;
    firmwareVersion?: string;
}

function DeviceComponent({ name, wifiConnected, batteryCharge, temperature, firmwareVersion }: DeviceProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [history, setHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    const handleClick = async () => {
        setIsModalOpen(true);
        setIsLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/device/${name}/history`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Received history:', data);  // Debug log
            setHistory(data);
        } catch (error) {
            console.error('Error fetching device history:', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <div
                className="bg-card text-card-foreground rounded-lg shadow-md p-4 flex flex-col space-y-4 cursor-pointer hover:shadow-lg transition-shadow"
                onClick={handleClick}
            >
                <h3 className="text-sm font-semibold">{name}</h3>
                <div className="flex items-center space-x-2">
                    <WifiIcon className={`h-5 w-5 ${wifiConnected ? 'text-green-500' : 'text-red-500'}`} />
                    <span>{wifiConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <BatteryIcon className="h-5 w-5" />
                            <span>Battery</span>
                        </div>
                        <span className="font-medium">{batteryCharge}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                            className="bg-green-500 h-2.5 rounded-full"
                            style={{ width: `${batteryCharge}%` }}
                        ></div>
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <ThermometerIcon className="h-5 w-5" />
                    <span>Temperature: {temperature}°C</span>
                </div>
                <div className="flex items-center space-x-2">
                    <CpuIcon className="h-5 w-5" />
                    <span>Firmware: {firmwareVersion}</span>
                </div>
            </div>

            <DeviceHistoryModal
                deviceName={name}
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                history={history}
                isLoading={isLoading}
            />
        </>
    );
}

export default DeviceComponent;