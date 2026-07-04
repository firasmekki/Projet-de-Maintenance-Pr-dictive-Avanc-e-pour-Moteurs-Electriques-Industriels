from app.db.models.analysis_report import AnalysisReport
from app.db.models.fault_history import FaultHistory
from app.db.models.maintenance_history import MaintenanceHistory
from app.db.models.motor import Motor
from app.db.models.prediction_history import PredictionHistory
from app.db.models.recommendation import Recommendation
from app.db.models.sensor_data import SensorData

__all__ = [
    "AnalysisReport",
    "FaultHistory",
    "MaintenanceHistory",
    "Motor",
    "PredictionHistory",
    "Recommendation",
    "SensorData",
]
