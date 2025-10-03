from typing import Any, List, Dict

def segment_soldiers(image: Any, detections: List[Dict[str, Any]]) -> List[str]:
    """Run SAM or similar to get masks for each detection."""
    # TODO: Integrate SAM
    # Return list of base64-encoded binary masks
    return ["<mask>"] * len(detections)
