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
        if "{LINKAM}" in self.prefix:
            self.prefix = self.prefix.format(LINKAM="LINKAM")
        self._current_temp = 25.0
        self._target_temp = 25.0
        self._ramp_rate = 10.0
        self._heating = False
        
    async def device_poller(self):
        """Update temperature based on setpoint and ramp rate"""
        print("[LinkamIOC] device_poller started.")
        try:
            while True:
                if self._heating:
                    diff = self._target_temp - self._current_temp
                    if abs(diff) > 0.1:
                        # Calculate the step, and update the temperature.
                        step = min(abs(diff), self._ramp_rate * 0.1) * (1 if diff > 0 else -1)
                        self._current_temp += step
                        print(f"[LinkamIOC] Heating: _current_temp updated to {self._current_temp:.2f} (target: {self._target_temp}, diff: {diff:.2f})")
                        await self.temperature_current.write(self._current_temp)
                        # Set status to 2 if within 0.5 of setpoint, else 0.
                        status_val = 2 if abs(diff) < 0.5 else 0
                        await self.status.write(status_val)
                        print(f"[LinkamIOC] Status set to {status_val}")
                    else:
                        print(f"[LinkamIOC] At target temperature (diff: {diff:.2f}).")
                else:
                    print("[LinkamIOC] Heater is off; no temperature update.")
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("[LinkamIOC] device_poller cancelled.")
            raise

    @heater.putter
    async def heater(self, instance, value):
        """Handle heater on/off"""
        self._heating = bool(value)
        print(f"[LinkamIOC] Heater putter called: setting _heating to {self._heating}")
        return value

    @temperature_setpoint.putter
    async def temperature_setpoint(self, instance, value):
        """Handle new temperature setpoint"""
        self._target_temp = float(value)
        print(f"[LinkamIOC] Temperature setpoint putter called: new target set to {self._target_temp}")
        return value

    @temperature_rate.putter
    async def temperature_rate(self, instance, value):
        """Handle new ramp rate"""
        self._ramp_rate = float(value)
        print(f"[LinkamIOC] Temperature rate putter called: new ramp rate set to {self._ramp_rate}")
        return value

    async def shutdown(self):
        """Overridden shutdown that does not cancel the device poller."""
        print("[LinkamIOC] shutdown called; NOT cancelling device_poller.")

    async def startup(self, async_lib):
        print("[LinkamIOC] Starting device poller via group-level startup callback.")
        self._device_poller_task = asyncio.create_task(self.device_poller())


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="XF:11BM-ES:{LINKAM}:", desc="Linkam Temperature Controller Simulator"
    )
    ioc = LinkamIOC(**ioc_options)
    try:
        run(ioc.pvdb, **run_options)
    finally:
        # On shutdown, cancel the pending device_poller task
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ioc.shutdown())
