import sys
import os
import io
import base64
import urllib.parse

# Set project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Tell app it's in Netlify serverless environment
os.environ['NETLIFY'] = 'true'

from app import app, db, seed_database

# Pre-seed on function container boot
with app.app_context():
    db.create_all()
    seed_database()

def handler(event, context):
    """
    Netlify Serverless AWS Lambda Proxy Handler for Python Flask
    """
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')

    # Handle Netlify Function route stripping
    if path.startswith('/.netlify/functions/api'):
        path = path[len('/.netlify/functions/api'):]
    if not path:
        path = '/'

    query_params = event.get('queryStringParameters') or {}
    query_string = urllib.parse.urlencode(query_params)

    headers = event.get('headers') or {}
    body = event.get('body') or ''
    if event.get('isBase64Encoded', False):
        body_bytes = base64.b64decode(body)
    else:
        body_bytes = body.encode('utf-8') if isinstance(body, str) else body

    environ = {
        'REQUEST_METHOD': http_method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': headers.get('host', 'localhost'),
        'SERVER_PORT': headers.get('x-forwarded-port', '443'),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': headers.get('x-forwarded-proto', 'https'),
        'wsgi.input': io.BytesIO(body_bytes),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_LENGTH': str(len(body_bytes)),
        'CONTENT_TYPE': headers.get('content-type', ''),
    }

    for key, val in headers.items():
        header_key = 'HTTP_' + key.upper().replace('-', '_')
        if header_key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
            environ[header_key] = val

    response_status = [None]
    response_headers = []

    def start_response(status, response_headers_list, exc_info=None):
        response_status[0] = status
        response_headers.extend(response_headers_list)

    response_body_iterable = app(environ, start_response)
    response_body = b''.join(response_body_iterable)

    status_code = int(response_status[0].split()[0]) if response_status[0] else 200

    resp_headers_dict = {}
    multi_value_headers = {}
    for k, v in response_headers:
        if k.lower() == 'set-cookie':
            multi_value_headers.setdefault(k, []).append(v)
        else:
            resp_headers_dict[k] = v

    content_type = resp_headers_dict.get('Content-Type', '')
    is_binary = any(content_type.startswith(t) for t in ['application/pdf', 'image/', 'application/octet-stream'])

    if is_binary:
        body_out = base64.b64encode(response_body).decode('utf-8')
        is_base64 = True
    else:
        try:
            body_out = response_body.decode('utf-8')
            is_base64 = False
        except UnicodeDecodeError:
            body_out = base64.b64encode(response_body).decode('utf-8')
            is_base64 = True

    response = {
        'statusCode': status_code,
        'headers': resp_headers_dict,
        'body': body_out,
        'isBase64Encoded': is_base64
    }

    if multi_value_headers:
        response['multiValueHeaders'] = multi_value_headers

    return response
