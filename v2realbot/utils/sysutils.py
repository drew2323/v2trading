import socket
from v2realbot.enums.enums import Env
from v2realbot.config import PROD_SERVER_HOSTNAMES, TEST_SERVER_HOSTNAMES

def get_environment():
    """Determine if the current server is production or test based on hostname."""
    hostname = socket.gethostname()
    if hostname in PROD_SERVER_HOSTNAMES:
        return Env.PROD
    else:
        return Env.TEST
