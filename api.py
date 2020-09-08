import requests


class ArubaOsApi:

    LOGIN_PATH = '/api/login'
    LOGOUT_PATH = '/api/logout'
    OBJECT_PATH  = '/configuration/object'

    def __init__(self, host, port=4343, username=None, password=None, version=1, verify=False):
        self.host = host
        self.username = username
        self.password = password
        self.version = version
        self.session = requests.Session()
        self.session.verify = verify
        self.session.hooks['response'].append(self.handle_response)
        self.base_url = f'https://{host}:{port}/v{version}'

    def __enter__(self):
        self.login(self.username, self.password)
        return self

    def __exit__(self, type, value, traceback):
        self.logout()
        self.session.close()

    def handle_response(self, r, *args, **kwargs):
        r.raise_for_status()
        return r

    def login(self, username, password):
        r = self.session.post(f'{self.base_url}{self.LOGIN_PATH}', data={'username': username, 'password': password})
        result = r.json()['_global_result']
        if result['status'] != '0':
            raise AuthenticationError(result['status'], result['status_str'])

        self.session.params.update(UIDARUBA=r.json()['_global_result']['UIDARUBA'])
        return r

    def logout(self):
        return self.session.get(f'{self.base_url}{self.LOGOUT_PATH}')

    def get(self, endpoint, config_path):
        url = f'{self.base_url}{self.OBJECT_PATH}{endpoint}'
        params = {'config_path': config_path}
        r = self.session.request('GET', url, params=params)
        return r.json()


def filter_config(config, flags=[]):
    if isinstance(config, list):
        return [filter_config(c, flags=flags) for c in config if filter_config(c, flags=flags)]
    if isinstance(config, dict):
        if '_flags' in config:
            if not (set(config['_flags']) == set(flags)):
                return None
        return {k: filter_config(v, flags=flags) for k, v in config.items() if filter_config(v, flags=flags)}
    return config


def diff_config(src, dst):
    diff = dict()
    if isinstance(dst, dict):
        for k in dst:
            if k in src:
                diff[k] = diff_config(src[k], dst.pop(k))
            else:
                diff[k] = dst[k]
                if isinstance(diff[k], dict):
                    diff[k].update({'_action': 'add'})
    if isinstance(dst, list):
        return [diff_config(s, d) for s, d in zip(src, dst)]
    return dst


class Error(Exception):
    pass


class AuthenticationError(Error):
    def __init__(self, status, message):
        self.status = status
        self.message = message
