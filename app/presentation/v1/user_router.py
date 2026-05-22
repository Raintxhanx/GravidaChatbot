from flask import Blueprint, request, jsonify
from functools import wraps
import jwt

def create_user_blueprint(user_use_case, secret_key: str) -> Blueprint:
    """
    Factory function — menerima UserUseCase yang sudah di-inject dari luar.
    """
    user_bp = Blueprint('user', __name__)

    # ──────────────────────────────────────────
    # Helper: JWT Auth Decorator
    # ──────────────────────────────────────────
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization', '')

            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

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

    # ──────────────────────────────────────────
    # POST /auth/register
    # ──────────────────────────────────────────
    @user_bp.route('/auth/register', methods=['POST'])
    def register():
        """
        User Registration
        ---
        tags:
          - Authentication
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                  example: "user@example.com"
                password:
                  type: string
                  example: "password123"
                role:
                  type: string
                  enum: [user, admin]
                  default: user
        responses:
          201:
            description: User registered successfully
          400:
            description: Invalid JSON body
          409:
            description: Email already exists
          422:
            description: Validation error (missing fields or invalid role)
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        email    = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role     = data.get('role', 'user').strip()

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email dan password wajib diisi'}), 422

        if role not in ('user', 'admin'):
            return jsonify({'success': False, 'message': 'Role tidak valid'}), 422

        user, message = user_use_case.register(email, password, role)
        if not user:
            return jsonify({'success': False, 'message': message}), 409

        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'id':    str(user.id),
                'email': user.email,
                'role':  user.role,
            }
        }), 201

    # ──────────────────────────────────────────
    # POST /auth/login
    # ──────────────────────────────────────────
    @user_bp.route('/auth/login', methods=['POST'])
    def login():
        """
        User Login
        ---
        tags:
          - Authentication
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                  example: "user@example.com"
                password:
                  type: string
                  example: "password123"
        responses:
          200:
            description: Login successful, returns JWT token
          401:
            description: Invalid credentials
          422:
            description: Missing email or password
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        email    = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email dan password wajib diisi'}), 422

        token, result = user_use_case.login(email, password)
        if not token:
            return jsonify({'success': False, 'message': result}), 401

        return jsonify({
            'success': True,
            'message': 'Login berhasil',
            'data': {
                'access_token': token,
                'token_type':   'Bearer',
                'user': {
                    'id':    str(result.id),
                    'email': result.email,
                    'role':  result.role,
                }
            }
        }), 200

    # ──────────────────────────────────────────
    # GET /auth/me
    # ──────────────────────────────────────────
    @user_bp.route('/auth/me', methods=['GET'])
    @token_required
    def me():
        """
        Get Current User Profile
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
        responses:
          200:
            description: Profile details from token
          401:
            description: Unauthorized (Token missing or expired)
        """
        return jsonify({
            'success': True,
            'data': {
                'user_id': request.current_user.get('user_id'),
                'role':    request.current_user.get('role'),
            }
        }), 200

    return user_bp