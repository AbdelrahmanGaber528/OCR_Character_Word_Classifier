import os
import httpx
import logging
import asyncio
from datetime import datetime

LOGGER_URL = os.getenv("LOGGER_URL", "http://logger:8003/log")

class RemoteLogger:

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.local_log = logging.getLogger(service_name)

    async def _send_log(self, level: str, message: str):
        payload = {
            "service": self.service_name,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(LOGGER_URL, json=payload)
        except Exception as e:
            self.local_log.error(f"Failed to send log to central logger: {e}")


    async def info(self, message: str):
        self.local_log.info(message)
        asyncio.create_task(self._send_log("INFO", message))

    async def error(self, message: str):
        self.local_log.error(message)
        asyncio.create_task(self._send_log("ERROR", message))

    async def warning(self, message: str):
        self.local_log.warning(message)
        asyncio.create_task(self._send_log("WARNING", message))
