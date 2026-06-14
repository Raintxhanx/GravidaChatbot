import jwt
from functools import wraps
from flask import request, jsonify

def get_token_required_decorator(secret_key: str, secret_api: str):
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization', '')

            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            elif auth_header.startswith('ApiKey '):
                api_key = auth_header.split(' ')[1]
                if api_key == secret_api:
                    request.current_user = {'user_id': 'api_client', 'role': 'admin'}
                    return f(*args, **kwargs)
                else:
                    return jsonify({'success': False, 'message': 'API key tidak valid'}), 401

            if not token:
                return jsonify({'success': False, 'message': 'Token tidak ditemukan'}), 401

            try:
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                request.current_user = payload
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': 'Token sudah kadaluarsa'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': 'Token tidak valid'}), 401

            return f(*args, **kwargs)
        return decorated
    return token_required

def get_admin_required_decorator(secret_key: str, secret_api: str):
    token_required = get_token_required_decorator(secret_key, secret_api)
    def admin_required(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user.get('role') != 'admin':
                return jsonify({'success': False, 'message': 'Akses ditolak: hanya admin'}), 403
            return f(*args, **kwargs)
        return decorated
    return admin_required