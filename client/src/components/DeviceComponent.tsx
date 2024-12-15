import React, { useState } from 'react';
import { BatteryIcon, CpuIcon, ThermometerIcon, WifiIcon } from "lucide-react";
import DeviceHistoryModal from './DeviceHistoryModal';

interface HistoryEntry {
  id: number;
  timestamp: string;
  metricType: string;
  value: string;
}

interface DeviceProps {
    name: string;
    wifiConnected?: boolean;
    batteryCharge?: number;
    temperature?: number;
    firmwareVersion?: string;
}

function DeviceComponent({ name, wifiConnected, batteryCharge, temperature, firmwareVersion }: DeviceProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [history, setHistory] = useState<HistoryEntry[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    const handleClick = async () => {
        setIsModalOpen(true);
        setIsLoading(true);
        const data = await fetchHistory();
        setHistory(data.logs);
        setHasMore(data.hasMore);
        setIsLoading(false);
    };

    const handleLoadMore = async (lastId: number) => {
        const data = await fetchHistory(lastId);
        setHistory(prev => [...prev, ...data.logs]);
        setHasMore(data.hasMore);
    };

        const fetchHistory = async (lastId?: number) => {
        try {
            const url = new URL(`${API_URL}/api/device/${name}/history`);
            if (lastId) {
                url.searchParams.append('last_id', lastId.toString());
            }

            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Fetched device history:', data);
            return {
                logs: data.logs || [],
                hasMore: !!data.hasMore
            };
        } catch (error) {
            console.error('Error fetching device history:', error);
            return { logs: [], hasMore: false };
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
                hasMore={hasMore}
                onLoadMore={handleLoadMore}
            />
        </>
    );
}

export default DeviceComponent;