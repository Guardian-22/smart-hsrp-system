from config.settings import settings
from backend.models.helmet_detector import HelmetDetector
from backend.models.plate_detector import PlateDetector
from backend.models.hsrp_classifier import HSRPClassifier
from backend.models.vehicle_detector import VehicleDetector
from backend.models.ocr import PlateOCR

helmet_model = HelmetDetector(settings.HELMET_MODEL_PATH)
plate_model = PlateDetector(settings.PLATE_MODEL_PATH)
hsrp_model = HSRPClassifier(settings.HSRP_MODEL_PATH)
vehicle_model = VehicleDetector(settings.VEHICLE_MODEL_PATH)
ocr_model = PlateOCR()

