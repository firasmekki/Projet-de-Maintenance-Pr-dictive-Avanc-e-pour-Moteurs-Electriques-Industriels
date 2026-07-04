from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from app.db.models.motor import Motor
    from app.db.models.sensor_data import SensorData

FEATURE_NAMES: list[str] = [
    "temperature",
    "vibration",
    "current",
    "voltage",
    "power",
    "load",
    "power_factor",
    "thd",
    "current_ratio",
    "temperature_mean",
    "vibration_mean",
    "temperature_std",
    "vibration_std",
]

NUM_FEATURES: int = len(FEATURE_NAMES)


@dataclass
class MotorFeatures:
    temperature: float
    vibration: float
    current: float
    voltage: float
    power: float
    load: float
    power_factor: float
    thd: float
    current_ratio: float
    temperature_mean: float
    vibration_mean: float
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
                self.power_factor,
                self.thd,
                self.current_ratio,
                self.temperature_mean,
                self.vibration_mean,
                self.temperature_std,
                self.vibration_std,
            ],
            dtype=np.float32,
        )

    def to_dict(self) -> dict[str, float]:
        return {name: float(val) for name, val in zip(FEATURE_NAMES, self.to_array())}


class FeatureEngineer:
    """Extracts and engineers features from a window of SensorData records."""

    def extract(
        self,
        readings: Sequence[SensorData],
        motor: Motor,
    ) -> MotorFeatures | None:
        if not readings:
            return None

        latest = readings[0]  # most recent first (ordered by timestamp DESC)

        rated_current = float(motor.rated_current)
        current = float(latest.current)
        current_ratio = current / rated_current if rated_current > 0 else 0.0

        temps = [float(r.temperature) for r in readings]
        vibs = [float(r.vibration) for r in readings]
        temp_mean = float(np.mean(temps))
        vib_mean = float(np.mean(vibs))
        temp_std = float(np.std(temps)) if len(temps) > 1 else 0.0
        vib_std = float(np.std(vibs)) if len(vibs) > 1 else 0.0

        return MotorFeatures(
            temperature=float(latest.temperature),
            vibration=float(latest.vibration),
            current=current,
            voltage=float(latest.voltage),
            power=float(latest.power),
            load=float(latest.load),
            power_factor=float(latest.power_factor),
            thd=float(latest.thd),
            current_ratio=current_ratio,
            temperature_mean=temp_mean,
            vibration_mean=vib_mean,
            temperature_std=temp_std,
            vibration_std=vib_std,
        )
