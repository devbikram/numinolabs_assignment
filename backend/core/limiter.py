from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter instance imported by endpoint modules.
# NOTE: get_remote_address trusts the X-Forwarded-For header when present.
# If this service is exposed directly to the internet (not behind a trusted
# reverse proxy), clients can spoof their source IP and bypass rate limits.
# Mitigate by configuring trusted proxies in uvicorn (--forwarded-allow-ips)
# or replacing get_remote_address with a custom key_func reading request.client.host.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
