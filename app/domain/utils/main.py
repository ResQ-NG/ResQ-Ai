# TODO: Consider code organization as this utils folder expands


def flatten_json_to_string(payload) -> str:
    """
    Recursively flattens a dictionary (possibly nested) or a list into a readable string.
    This is useful for extracting meaningful text from JSON for summarization.

    Args:
        payload: A dict or list (or value) to flatten and concatenate.

    Returns:
        str: Concatenated string representation of the data.
    """
    if isinstance(payload, dict):
        parts = []
        for k, v in payload.items():
            parts.append(f"{k}: {flatten_json_to_string(v)}")
        return "; ".join(parts)
    elif isinstance(payload, list):
        return "; ".join([flatten_json_to_string(item) for item in payload])
    else:
        # Assume primitive
        return str(payload)
