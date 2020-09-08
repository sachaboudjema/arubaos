
def filter_config(config, flags=[]):
    if isinstance(config, list):
        return [filter_config(c, flags=flags) for c in config if filter_config(c, flags=flags)]
    if isinstance(config, dict):
        if '_flags' in config:
            if not (set(config['_flags']) == set(flags)):
                return None
        return {k: filter_config(v, flags=flags) for k, v in config.items() if filter_config(v, flags=flags)}
    return config

