import {BatteryIcon, CpuIcon, ThermometerIcon, WifiIcon} from "lucide-react";

interface DeviceProps {
    name: string
    wifiConnected: boolean
    batteryCharge: number
    temperature: number
    firmwareVersion: string
}

function DeviceComponent({ name, wifiConnected, batteryCharge, temperature, firmwareVersion }: DeviceProps) {
    return (
        <div className="bg-card text-card-foreground rounded-lg shadow-md p-4 flex flex-col space-y-4">
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
    )
}

export default DeviceComponent;