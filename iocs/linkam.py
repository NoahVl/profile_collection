"""
A simulated Linkam temperature controller IOC.
"""

import asyncio
import sys
import time
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run

class LinkamIOC(PVGroup):
    """
    Simulated Lakeshore IOC with put completion on the setpoint.
    """

    """A simulated Linkam temperature controller"""
    
    # Temperature control
    temperature_setpoint = pvproperty(value=25.0, name="SETPOINT:SET", doc="Temperature setpoint")
    temperature_current = pvproperty(value=25.0, name="TEMP", doc="Current temperature", read_only=True)
    temperature_rate = pvproperty(value=10.0, name="RAMPRATE:SET", doc="Temperature ramp rate")
    
    # Status
    status = pvproperty(value=0, name="STATUS", doc="Device status", read_only=True)
    heater = pvproperty(value=0, name="STARTHEAT", doc="Heater on/off")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_temp = 25.0
        self._target_temp = 25.0
        self._ramp_rate = 10.0
        self._heating = False
        
    async def device_poller(self):
        """Update temperature based on setpoint and ramp rate"""
        while True:
            if self._heating:
                # Simple temperature ramping simulation
                diff = self._target_temp - self._current_temp
                if abs(diff) > 0.1:
                    step = min(abs(diff), self._ramp_rate * 0.1) * (1 if diff > 0 else -1)
                    self._current_temp += step
                    await self.temperature_current.write(self._current_temp)
                    # Set status bit 2 when at setpoint
                    if abs(diff) < 0.5:
                        await self.status.write(2)
                    else:
                        await self.status.write(0)
            await asyncio.sleep(0.1)

    @heater.putter
    async def heater(self, instance, value):
        """Handle heater on/off"""
        self._heating = bool(value)
        return value

    @temperature_setpoint.putter
    async def temperature_setpoint(self, instance, value):
        """Handle new temperature setpoint"""
        self._target_temp = float(value)
        return value

    @temperature_rate.putter
    async def temperature_rate(self, instance, value):
        """Handle new ramp rate"""
        self._ramp_rate = float(value)
        return value

    @status.startup
    async def status(self, instance, async_lib):
        await self.device_poller()



if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="XF:11BM-ES:{LINKAM}:", desc="Linkam Temperature Controller Simulator"
    )
    ioc = LinkamIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
