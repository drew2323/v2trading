import socket
from v2realbot.enums.enums import Env
import v2realbot.utils.config_handler as cfh

def get_environment():
    """Determine if the current server is production or test based on hostname."""
    hostname = socket.gethostname()
    if hostname in cfh.config_handler.get_val('PROD_SERVER_HOSTNAMES'):
        return Env.PROD
    else:
        return Env.TEST
