"""
Ultra-light in-memory relay tracker.
No DB – we only need current state for the dashboard.
"""

from datetime import datetime, timedelta


class RelayManager:
    def __init__(self, timeout_s: int = 90):
        self._timeout = timeout_s
        self.relays: dict[str, dict] = {}     # relay-id → state dict

    # ---------- update from each heartbeat --------------------------------
    def upsert(self, rid: str, pkt: dict):
        pkt["last_seen"] = datetime.utcnow()
        pkt["alive"]     = True
        self.relays[rid] = pkt

    # ---------- called periodically to flip 'alive' -----------------------
    def refresh(self):
        cut = datetime.utcnow() - timedelta(seconds=self._timeout)
        for rid, st in self.relays.items():
            st["alive"] = st["last_seen"] > cut 