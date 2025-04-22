import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, sessionmaker
from database import Device, DeviceLog


class DeviceManager:
    def __init__(self, session_factory: sessionmaker):
        """
        Initialize DeviceManager with a session factory instead of a single session
        to ensure thread-safe database operations
        """
        self.session_factory = session_factory
        self.devices: Dict[str, Dict] = {}  # In-memory cache
        self._load_devices_from_db()

    def _serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Convert datetime to ISO format string"""
        return dt.isoformat() if dt else None

    def _load_devices_from_db(self):
        """Load existing devices from database into memory cache"""
        session = self.session_factory()
        try:
            db_devices = session.query(Device).all()
            for device in db_devices:
                self.devices[device.name] = self._device_to_dict(device)
        finally:
            session.close()

    def _device_to_dict(self, device: Device) -> Dict:
        """Convert device database object to dictionary format"""
        latest_values = json.loads(device.last_metric_values) if device.last_metric_values else {}
        return {
            'name': device.name,
            'wifiConnected': device.wifi_connected,
            'batteryCharge': float(latest_values.get('battery', 0)),
            'temperature': float(latest_values.get('temperature', 0)),
            'latencyMs': float(latest_values.get('latency', -1)),   #  -1 = unknown
            'firmwareVersion': latest_values.get('version', 'N/A'),
            'otaStatus': latest_values.get('ota', 'N/A'),
            'lastMessageTime': self._serialize_datetime(device.last_message_time),
            'firstSeen': self._serialize_datetime(device.first_seen)
        }

    def get_or_create_device(self, name: str) -> Device:
        """Get existing device or create new one if it doesn't exist"""
        session = self.session_factory()
        try:
            device = session.query(Device).filter(Device.name == name).first()
            if not device:
                device = Device(
                    name=name,
                    first_seen=datetime.utcnow(),
                    last_metric_values=json.dumps({})
                )
                session.add(device)
                session.commit()
                self.devices[name] = self._device_to_dict(device)
            return device
        finally:
            session.close()

    def update_device(self, name: str, metric_type: str, value: str) -> Dict:
        """Update device information and log the update"""
        session = self.session_factory()
        try:
            device = session.query(Device).filter(Device.name == name).first()
            if not device:
                device = Device(name=name, first_seen=datetime.utcnow())
                session.add(device)
                session.flush()  # Get ID without committing

            # Create log entry
            log = DeviceLog(
                device_id=device.id,
                metric_type=metric_type,
                metric_value=value,
                timestamp=datetime.utcnow()
            )
            session.add(log)

            # Update device's last known state
            current_values = json.loads(device.last_metric_values) if device.last_metric_values else {}

            # Parse the value if it's JSON
            try:
                parsed_value = json.loads(value)
                if metric_type == 'battery':
                    actual_value = str(parsed_value.get('Battery Percentage', 0))
                elif metric_type == 'temperature':
                    actual_value = str(parsed_value.get('Temperature', 0))
                else:
                    actual_value = value
            except json.JSONDecodeError:
                actual_value = value

            current_values[metric_type] = actual_value
            device.last_metric_values = json.dumps(current_values)
            device.last_message_time = datetime.utcnow()

            # Update wifi status
            device.wifi_connected = True  # We just got a message

            session.commit()

            # Update in-memory cache
            device_dict = self._device_to_dict(device)
            self.devices[name] = device_dict
            return device_dict

        finally:
            session.close()

    def get_device_history(self, device_name: str,
                           metric_type: Optional[str] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           page_size: int = 100,
                           last_id: Optional[int] = None) -> Tuple[List[Dict], bool]:
        """
        Retrieve historical logs for a device with pagination
        Returns: Tuple of (logs, has_more)
        """
        session = self.session_factory()
        try:
            device = session.query(Device).filter(Device.name == device_name).first()
            if not device:
                return [], False

            query = session.query(DeviceLog).filter(DeviceLog.device_id == device.id)

            if metric_type:
                query = query.filter(DeviceLog.metric_type == metric_type)
            if start_time:
                query = query.filter(DeviceLog.timestamp >= start_time)
            if end_time:
                query = query.filter(DeviceLog.timestamp <= end_time)
            if last_id:
                query = query.filter(DeviceLog.id < last_id)

            # Order by id descending to get most recent first
            query = query.order_by(DeviceLog.id.desc())

            # Get one extra item to check if there are more results
            logs = query.limit(page_size + 1).all()

            has_more = len(logs) > page_size
            logs = logs[:page_size]  # Remove the extra item if it exists

            return [{
                'id': log.id,
                'timestamp': self._serialize_datetime(log.timestamp),
                'metricType': log.metric_type,
                'value': log.metric_value
            } for log in logs], has_more
        finally:
            session.close()

    def check_wifi_status(self):
        """Update wifi status for all devices based on last message time"""
        session = self.session_factory()
        try:
            threshold = datetime.utcnow() - timedelta(seconds=61)
            devices = session.query(Device).all()

            for device in devices:
                was_connected = device.wifi_connected
                is_connected = device.last_message_time and device.last_message_time > threshold

                if was_connected != is_connected:
                    device.wifi_connected = is_connected
                    self.devices[device.name]['wifiConnected'] = is_connected

            session.commit()
        finally:
            session.close()