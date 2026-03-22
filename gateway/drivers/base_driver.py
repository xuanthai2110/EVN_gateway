from abc import ABC, abstractmethod

class BaseDriver(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def read_data(self):
        """Reads monitoring data from the device."""
        pass

    @abstractmethod
    async def write_power_pct(self, value):
        """Writes power limit percentage to the device."""
        pass
