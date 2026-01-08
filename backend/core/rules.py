from config.settings import settings

def helmet_violation(helmet_detected: bool, confidence: float):
    if confidence < float(settings.HELMET_CONF_THRESHOLD):
        return False
    return not helmet_detected

def hsrp_violation(is_hsrp: bool, confidence: float):
    # Low confidence → manual review → violation
    if confidence < float(settings.HSRP_CONF_THRESHOLD):
        return True
    return not is_hsrp
