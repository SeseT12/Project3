# Contributor(s): sregitz
def json_keys_to_int(x):
    if isinstance(x, dict):
        return {int(k): v for k, v in x.items()}
    return x