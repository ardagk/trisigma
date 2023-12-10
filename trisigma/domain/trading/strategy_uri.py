def to_strategy_uri(base: str, config: dict) -> str:
    if not config:
        return base.lower()
    conf_tuple = sorted(config.items(), key=lambda x: x[0])
    uri = base + '?'
    for k, v in conf_tuple:
        assert '?' not in k, "key can't include '?"
        assert '&' not in k, "key can't include '&'"
        assert '?' not in str(v), "value can't include '?'"
        assert '&' not in str(v), "value can't include '&'"
        uri += f"{k}={v}&"
    uri = uri[:-1].lower().replace(' ', '_')
    return uri

def from_strategy_uri(uri: str):
    if '?' not in uri:
        return uri, {}
    base, params_line = uri.split("?")
    pair_lines = params_line.split('&')
    params = {}
    for pair in pair_lines:
        pair = pair.replace('_', ' ')
        key, value = pair.split("=")
        params[key] = value
    return base, params

