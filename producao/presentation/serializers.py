def validate_fields(data, required_fields):
    """Simple validator to ensure required fields are present in the dataset."""
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None
