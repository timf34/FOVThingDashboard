import React from 'react';
import { X } from 'lucide-react';

interface HistoryEntry {
  timestamp: string;
  metricType: string;
  value: string;
}

interface DeviceHistoryModalProps {
  deviceName: string;
  isOpen: boolean;
  onClose: () => void;
  history: HistoryEntry[];
  isLoading: boolean;
}

const DeviceHistoryModal: React.FC<DeviceHistoryModalProps> = ({
  deviceName,
  isOpen,
  onClose,
  history,
  isLoading
}) => {
  if (!isOpen) return null;

  const formatValue = (entry: HistoryEntry) => {
    try {
      const parsed = JSON.parse(entry.value);
      if (entry.metricType === 'battery') {
        return `${parsed['Battery Percentage']}%`;
      } else if (entry.metricType === 'temperature') {
        return `${parsed['Temperature']}°C`;
      }
      return entry.value;
    } catch {
      return entry.value;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">{deviceName} History</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4 overflow-auto max-h-[calc(80vh-8rem)]">
          {isLoading ? (
            <div className="text-center py-4">Loading history...</div>
          ) : history.length === 0 ? (
            <div className="text-center py-4">No history available</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Time</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Value</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-2">{formatTimestamp(entry.timestamp)}</td>
                    <td className="p-2">{entry.metricType}</td>
                    <td className="p-2">{formatValue(entry)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default DeviceHistoryModal;