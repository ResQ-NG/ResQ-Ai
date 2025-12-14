def encode_redis_stream_payload(payload: dict) -> dict:
    """
    Convert all values in the payload dictionary to types accepted by Redis (str, int, float, bytes).
    Converts bool to "true"/"false" strings and all other non-basic types to JSON strings.
    """
    import json

    def encode_value(value):
        if isinstance(value, bool):
            # Redis does not accept bool, convert to string
            return "true" if value else "false"
        if isinstance(value, (str, int, float, bytes)):
            return value
        # For None, convert to empty string (optional: could also use "null")
        if value is None:
            return ""
        # For all other types (like list, dict, etc), encode as JSON string
        return json.dumps(value)

    return {k: encode_value(v) for k, v in payload.items()}
