import json
from random import randint
from typing import Dict

from app.utils.system import check_port
from app.xray.config import XRayConfig
from app.xray.core import XRayCore
from xray_api import XRay
from xray_api import exceptions
from xray_api import exceptions as exc
from xray_api import types

from config import (XRAY_ASSETS_PATH, XRAY_EXCLUDE_INBOUND_TAGS,
                    XRAY_EXECUTABLE_PATH, XRAY_FALLBACK_INBOUND_TAG, XRAY_JSON)

# Search for a free API port
try:
    for api_port in range(randint(10000, 60000), 65536):
        if not check_port(api_port):
            break
finally:
    config = XRayConfig(XRAY_JSON, api_port=api_port)
    del api_port


core = XRayCore(config, XRAY_EXECUTABLE_PATH, XRAY_ASSETS_PATH)
api = XRay(config.api_host, config.api_port)


# protocol: list_of_inbounds
# inbound contains tag, port, stream settings
# stream settings contains net, tls, sni, path
INBOUNDS: Dict[str, list] = {}
FALLBACK_INBOUND = config.get_inbound(XRAY_FALLBACK_INBOUND_TAG)


for inbound in config['inbounds']:
    if inbound.get('protocol') == "dokodemo-door":
        continue

    settings = {}

    try:
        settings['tag'] = inbound['tag']
    except KeyError:
        raise ValueError("one inbound have no tag")

    if inbound['tag'] in XRAY_EXCLUDE_INBOUND_TAGS:
        continue

    try:
        settings['port'] = inbound['port']
    except KeyError as _exc:
        if not FALLBACK_INBOUND:
            raise ValueError(f"{_exc.args[0]} missing on {inbound['tag']}"
                             "\nset XRAY_FALLBACK_INBOUND_TAG if you're using fallbacks"
                             "\nor you may have set it wrong")
        settings['port'] = FALLBACK_INBOUND['port']

    # default
    settings['stream'] = {
        "net": "tcp",
        "tls": False,
        "sni": "",
        "path": "",
        "host": "",
        "header_type": ""
    }

    if stream := inbound.get('streamSettings'):
        net = stream.get('network', 'tcp')
        net_settings = stream.get(f"{net}Settings", {})
        security = stream.get("security")
        tls_settings = stream.get(f"{security}Settings")

        if net_settings.get('acceptProxyProtocol') == True and inbound['tag'] != XRAY_FALLBACK_INBOUND_TAG:
            # probably this is a fallback
            security = FALLBACK_INBOUND.get('streamSettings', {}).get('security')
            tls_settings = FALLBACK_INBOUND.get('streamSettings', {}).get(f"{security}Settings")

        settings['stream']['net'] = net
        settings['stream']['tls'] = security in ('tls', 'xtls')

        if tls_settings:
            settings['stream']['sni'] = tls_settings.get('serverName', '')

        if net == 'tcp':
            header = net_settings.get('header', {})
            request = header.get('request', {})
            path = request.get('path')
            host = request.get('headers', {}).get('Host')

            settings['stream']['header_type'] = header.get('type', '')

            if isinstance(path, str) or isinstance(host, str):
                raise ValueError(f"Settings of {inbound['tag']} for path and host must be list, not str\n"
                                 "https://xtls.github.io/config/transports/tcp.html#httpheaderobject")

            if path and isinstance(path, list):
                settings['stream']['path'] = path[0]

            if host and isinstance(host, list):
                settings['stream']['host'] = host[0]

        elif net == 'ws':
            path = net_settings.get('path', '')
            host = net_settings.get('headers', {}).get('Host')

            settings['stream']['header_type'] = ''

            if isinstance(path, list) or isinstance(host, list):
                raise ValueError(f"Settings of {inbound['tag']} for path and host must be str, not list\n"
                                 "https://xtls.github.io/config/transports/websocket.html#websocketobject")

            if isinstance(path, str):
                settings['stream']['path'] = path

            if isinstance(host, str):
                settings['stream']['host'] = host

        elif net == 'grpc':
            settings['stream']['header_type'] = ''
            settings['stream']['path'] = net_settings.get('serviceName', '')
            settings['stream']['host'] = ''

        else:
            settings['stream']['path'] = net_settings.get('path', '')
            host = net_settings.get('host', {}) or net_settings.get('Host', {})
            if host and isinstance(host, list):
                settings['stream']['path'] = host[0]
            elif host and isinstance(host, str):
                settings['stream']['path'] = host

    try:
        INBOUNDS[inbound['protocol']].append(settings)
    except KeyError:
        INBOUNDS[inbound['protocol']] = [settings]


__all__ = [
    "config",
    "core",
    "api",
    "exceptions",
    "exc",
    "types",
    "INBOUNDS"
]
