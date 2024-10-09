from api_server import create_app
from paste.translogger import TransLogger

application = TransLogger(create_app(), setup_console_handler=False)
