from functools import partial
import trio
from hypercorn.trio import serve
from hypercorn.config import Config
from quart import send_from_directory
from quart_trio import QuartTrio
from os import path

# this defines the root folder containing our DASH dataset
dash_content_path = '/var/www/html/'

# define the config setup for our testbed
config = Config()
config.quic_bind = ["10.0.0.1:4444"]  # port number to use for HTTP
config.bind = ["10.0.0.1:443"]  # port number to use for HTTPS
config.insecure_bind = ["10.0.0.1:80"]  # port number to use for QUIC

# locations for the cert and key
config.certfile = "../goDASH/godash/http/certs/cert.pem"
config.keyfile = "../goDASH/godash/http/certs/key.pem"

# this 'root_path' is needed by QuartTrio to point to the DASH video content folder
app = QuartTrio(__name__, root_path=dash_content_path)

# return 404, if file not found
@app.errorhandler(404)
# @app.route('/')
async def page_not_found(error):
    return ' File not found', 404

# this return index.html if nothing is added to the url and port
@app.route('/')
async def root():

    print("returning index.html",)
    return await send_from_directory(dash_content_path, 'index.html'), 200


# this return a file if a path is added after the url and port
@app.route('/<path:path_to_DASH_files>')
async def index(path_to_DASH_files=dash_content_path):

    # if the file does not exist, return 404
    path_to_file = path.join(dash_content_path, path_to_DASH_files)
    if not path.isfile(path_to_file):
        print("This file does not exist:", path.isfile(path_to_file))
        return path_to_file + ' : File not found', 404

    # we need the await or we get coroutine error
    print("File downloaded", path_to_file)
    return await send_from_directory(dash_content_path, path_to_DASH_files), 200

# use trio to get our files
trio.run(partial(serve, app, config))
