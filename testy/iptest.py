import socket
from v2realbot.enums.enums import Env
from v2realbot.config import PROD_SERVER_IPS, TEST_SERVER_IPS

# def get_server_ip():
#     """Retrieve the current server's IP address."""
#     hostname = socket.gethostname()
#     current_ip = socket.gethostbyname(hostname)
#     print("Current IP:", current_ip, hostname)
#     return current_ip

def get_environment():
    """Determine if the current server is production or test based on IP."""
    current_ip = get_server_ip()
    if current_ip in PROD_SERVER_IPS:
        return Env.PROD
    else:
        return Env.TEST

def get_server_ip():
    """Get the IP address of the server."""
    try:
        # Create a dummy socket and connect to an external address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google's DNS server
            return s.getsockname()[0]
    except Exception as e:
        return f"Error: {e}"

# Test the function
#print(get_server_ip())

hostname = socket.gethostname()
print(hostname)
current_ip = socket.gethostbyname(hostname)
print(hostname, current_ip)