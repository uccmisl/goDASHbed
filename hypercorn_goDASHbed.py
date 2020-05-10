from quart import make_response, Quart, render_template, url_for, request, send_file, abort
from os import path
from hypercorn.middleware import HTTPToHTTPSRedirectMiddleware

dash_content_path='/var/www/html/'

# this 'root_path' is needed by Quart to point to the DASH video content folder
app = Quart(__name__, root_path=dash_content_path)

# return 404, if file not found
@app.errorhandler(404)
# @app.route('/')
async def page_not_found(error):
    print(error)
    return ' File not found', 404
    # return await render_template('/404.html', title = '404'), 404

@app.route('/<path:path_to_DASH_files>')
async def index(path_to_DASH_files):

    # path to this file
    path_to_file = path.join(dash_content_path, path_to_DASH_files)

    # if the file does not exist, return 404
    if not path.isfile(path_to_file):
        print("This file does not exist:", path.isfile(path_to_file))
        return path_to_file +' : File not found', 404
        # abort(404, path_to_file)

    # we need the await or we get coroutine error
    # return await send_file(path_to_file, as_attachment=True)
    print("File downloaded", path_to_file)
    return await send_file(path_to_file), 200

# for http/https redirection
redirected_app = HTTPToHTTPSRedirectMiddleware(app, "www.goDASHbed.org")

# this option
#return await render_template('index.html')

# and this option, seem to be the same
# result = await render_template('index.html')
# response = await make_response(result)
# return response
