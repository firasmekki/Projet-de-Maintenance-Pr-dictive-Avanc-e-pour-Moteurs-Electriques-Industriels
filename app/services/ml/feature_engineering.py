from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from app.database.models.sensor_data import SensorData

FEATURE_NAMES = [
    "temperature",
    "vibration",
    "current",
    "voltage",
    "power",
    "load",
    "current_ratio",
    "power_factor",
    "temperature_rolling_mean",
    "vibration_rolling_mean",
    "temperature_std",
    "vibration_std",
]

NUM_FEATURES = len(FEATURE_NAMES)


@dataclass
class MotorFeatures:
    temperature: float
    vibration: float
    current: float
    voltage: float
    power: float
    load: float
    current_ratio: float
    power_factor: float
    temperature_rolling_mean: float
    vibration_rolling_mean: float
    temperature_std: float
    vibration_std: float

    def to_array(self) -> np.ndarray:
        return np.array(
            [
                self.temperature,
                self.vibration,
                self.current,
                self.voltage,
                self.power,
                self.load,
                self.current_ratio,
                self.power_factor,
                self.temperature_rolling_mean,
                self.vibration_rolling_mean,
                self.temperature_std,
                self.vibration_std,
            ],
            dtype=np.float32,
        )

    def to_dict(self) -> Dict[str, float]:
        return {name: float(val) for name, val in zip(FEATURE_NAMES, self.to_array())}


class FeatureEngineer:
    """Extracts and engineers features from raw SensorData records."""

    def extract(
        self,
        readings: List[SensorData],
        rated_current: float,
        rated_voltage: float,
    ) -> Optional[MotorFeatures]:
        if not readings:
            return None

        latest = readings[0]  # Most recent first

        temp = latest.temperature or 0.0
        vib = latest.vibration or 0.0
        cur = latest.current or 0.0
        volt = latest.voltage or rated_voltage or 380.0
        pwr = latest.power or 0.0
        load = latest.load_percentage or 0.0

        current_ratio = cur / rated_current if rated_current > 0 else 0.0
        apparent_power = volt * cur
        power_factor = float(np.clip(pwr / apparent_power, 0.0, 1.0)) if apparent_power > 0 else 0.0

        temps = [r.temperature for r in readings if r.temperature is not None]
        vibs = [r.vibration for r in readings if r.vibration is not None]

        temp_mean = float(np.mean(temps)) if temps else temp
        vib_mean = float(np.mean(vibs)) if vibs else vib
        temp_std = float(np.std(temps)) if len(temps) > 1 else 0.0
        vib_std = float(np.std(vibs)) if len(vibs) > 1 else 0.0

        return MotorFeatures(
            temperature=temp,
            vibration=vib,
            current=cur,
            voltage=volt,
            power=pwr,
            load=load,
            current_ratio=current_ratio,
            power_factor=power_factor,
            temperature_rolling_mean=temp_mean,
            vibration_rolling_mean=vib_mean,
            temperature_std=temp_std,
            vibration_std=vib_std,
        )

    @staticmethod
    def build_training_row(
        temperature: float,
        vibration: float,
        current: float,
        voltage: float,
        power: float,
        load: float,
        rated_current: float,
    ) -> np.ndarray:
        """Convenience method for building a training row without ORM objects."""
        current_ratio = current / rated_current if rated_current > 0 else 0.0
        apparent = voltage * current
        pf = float(np.clip(power / apparent, 0.0, 1.0)) if apparent > 0 else 0.0
        return np.array(
            [temperature, vibration, current, voltage, power, load,
             current_ratio, pf, temperature, vibration, 0.0, 0.0],
            dtype=np.float32,
        )
