import numpy as np

def make_serializable(obj):
    """
    Recursively convert an object to a JSON-serializable format.
    """
    if isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, "__dict__"):  # For custom objects
        return make_serializable(vars(obj))
    else:
        return obj  # Return as-is if already serializable