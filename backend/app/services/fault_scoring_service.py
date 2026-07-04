from dataclasses import dataclass
from decimal import Decimal

from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from app.schemas.diagnostics import TrendAnalysisResponse


@dataclass(frozen=True)
class FaultScore:
    fault: str
    severity: str
    confidence: int
    risk_level: str
    recommendation: str
    description: str


class FaultScoringService:
    RECOMMENDATIONS = {
        "Bearing Wear": "Inspect bearing, check lubrication, and schedule replacement if vibration remains elevated.",
        "Misalignment": "Perform shaft alignment, inspect coupling, and verify soft foot condition.",
        "Unbalance": "Inspect rotor balance, clean fan or impeller surfaces, and check for looseness.",
        "Rotor Fault": "Check rotor bars, inspect current signature, and schedule electrical testing.",
        "Insulation Fault": "Perform insulation resistance testing, check cooling paths, and inspect winding condition.",
        "Overload": "Reduce load, verify motor sizing, inspect driven equipment, and review duty cycle.",
        "No Fault Detected": "Continue normal monitoring and review trends during the next inspection round.",
    }

    def score(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        candidates = [
            self._bearing_wear(motor, latest, trends),
            self._misalignment(motor, latest, trends),
            self._unbalance(motor, latest, trends),
            self._rotor_fault(motor, latest, trends),
            self._insulation_fault(motor, latest, trends),
            self._overload(motor, latest, trends),
        ]
        best = max(candidates, key=lambda item: item.confidence)

        if best.confidence <= 45:
            return FaultScore(
                fault="No Fault Detected",
                severity="LOW",
                confidence=best.confidence,
                risk_level="LOW",
                recommendation=self.RECOMMENDATIONS["No Fault Detected"],
                description="No diagnostic rule exceeded the minimum confidence threshold.",
            )

        return best

    def _bearing_wear(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 35 if self._high_vibration(latest) else 0
        confidence += 30 if self._high_temperature(latest) else 0
        confidence += 15 if self._medium_current(motor, latest) else 0
        confidence += self._trend_boost(trends, "vibration")
        confidence += self._trend_boost(trends, "temperature")
        return self._build("Bearing Wear", confidence, "High vibration and high temperature indicate probable bearing degradation.")

    def _misalignment(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 45 if self._very_high_vibration(latest) else 0
        confidence += 20 if self._medium_temperature(latest) else 0
        confidence += 20 if self._normal_current(motor, latest) else 0
        confidence += self._trend_boost(trends, "vibration")
        return self._build("Misalignment", confidence, "Very high vibration with normal current suggests shaft or coupling misalignment.")

    def _unbalance(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 40 if self._high_vibration(latest) else 0
        confidence += 25 if self._normal_temperature(latest) else 0
        confidence += 20 if self._normal_current(motor, latest) else 0
        confidence += self._trend_boost(trends, "vibration")
        return self._build("Unbalance", confidence, "High vibration with otherwise normal thermal and current behavior suggests mechanical unbalance.")

    def _rotor_fault(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 40 if self._high_current(motor, latest) else 0
        confidence += 20 if self._medium_vibration(latest) else 0
        confidence += 20 if self._medium_temperature(latest) else 0
        confidence += self._trend_boost(trends, "current")
        return self._build("Rotor Fault", confidence, "High current with moderate vibration and heating may indicate rotor electrical defects.")

    def _insulation_fault(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 35 if self._high_temperature(latest) else 0
        confidence += 25 if self._low_vibration(latest) else 0
        confidence += 30 if self._high_current(motor, latest) else 0
        confidence += self._trend_boost(trends, "temperature")
        return self._build("Insulation Fault", confidence, "High temperature and high current with low vibration suggests winding or insulation stress.")

    def _overload(self, motor: Motor, latest: SensorData, trends: TrendAnalysisResponse) -> FaultScore:
        confidence = 0
        confidence += 40 if self._very_high_current(motor, latest) else 0
        confidence += 25 if self._high_temperature(latest) else 0
        confidence += 25 if latest.load > Decimal("95") else 0
        confidence += self._trend_boost(trends, "current")
        return self._build("Overload", confidence, "Very high current, high load, and high temperature indicate motor overload.")

    def _build(self, fault: str, confidence: int, description: str) -> FaultScore:
        confidence = min(confidence, 100)
        severity = self._severity(confidence)
        return FaultScore(
            fault=fault,
            severity=severity,
            confidence=confidence,
            risk_level=severity,
            recommendation=self.RECOMMENDATIONS[fault],
            description=description,
        )

    @staticmethod
    def _severity(confidence: int) -> str:
        if confidence >= 90:
            return "CRITICAL"
        if confidence >= 75:
            return "HIGH"
        if confidence >= 55:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _trend_boost(trends: TrendAnalysisResponse, field: str) -> int:
        values = [
            getattr(trends.last_24h, field),
            getattr(trends.last_7d, field),
            getattr(trends.last_30d, field),
        ]
        return values.count("RISING") * 5

    @staticmethod
    def _normal_temperature(latest: SensorData) -> bool:
        return latest.temperature <= Decimal("80")

    @staticmethod
    def _medium_temperature(latest: SensorData) -> bool:
        return Decimal("75") < latest.temperature <= Decimal("90")

    @staticmethod
    def _high_temperature(latest: SensorData) -> bool:
        return latest.temperature > Decimal("90")

    @staticmethod
    def _low_vibration(latest: SensorData) -> bool:
        return latest.vibration < Decimal("3")

    @staticmethod
    def _medium_vibration(latest: SensorData) -> bool:
        return Decimal("3") <= latest.vibration <= Decimal("7")

    @staticmethod
    def _high_vibration(latest: SensorData) -> bool:
        return latest.vibration > Decimal("6")

    @staticmethod
    def _very_high_vibration(latest: SensorData) -> bool:
        return latest.vibration > Decimal("7.5")

    @staticmethod
    def _normal_current(motor: Motor, latest: SensorData) -> bool:
        return latest.current <= motor.rated_current

    @staticmethod
    def _medium_current(motor: Motor, latest: SensorData) -> bool:
        return motor.rated_current * Decimal("0.85") <= latest.current <= motor.rated_current * Decimal("1.05")

    @staticmethod
    def _high_current(motor: Motor, latest: SensorData) -> bool:
        return latest.current > motor.rated_current * Decimal("1.05")

    @staticmethod
    def _very_high_current(motor: Motor, latest: SensorData) -> bool:
        return latest.current > motor.rated_current * Decimal("1.15")
