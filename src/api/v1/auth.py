import os
import jwt
import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from pydantic import ValidationError

from src.domain.user.interface import IUser
from src.domain.auth.interface import IAuth
from src.domain.user.model import UserCreateDTO
from src.util.middlewares.decorator_api import get_token_required_decorator, get_admin_required_decorator


def create_auth_blueprint(user_use_case: IUser, auth_use_case: IAuth, secret_key: str, secret_api: str) -> Blueprint:
    auth_controller = Blueprint('auth', __name__)
    token_required = get_token_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────────────────────────────────
    # POST /auth/register
    # ──────────────────────────────────────────────────────────────────────
    @auth_controller.route('/auth/register', methods=['POST'])
    def register():
        """
        Register a new user
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
                - name
                - age
                - domicile
                - phone_number
                - estimated_delivery_date
                - pregnancy_count
              properties:
                email:
                  type: string
                  example: "user@example.com"
                password:
                  type: string
                  example: "SecretPass123!"
                name:
                  type: string
                  example: "Siti Aminah"
                age:
                  type: integer
                  example: 27
                domicile:
                  type: string
                  example: "Jakarta Selatan"
                phone_number:
                  type: string
                  example: "081234567890"
                estimated_delivery_date:
                  type: string
                  format: date
                  example: "2026-11-20"
                pregnancy_count:
                  type: integer
                  example: 2
                medical_history:
                  type: string
                  example: "Alergi obat amoxicillin"
        responses:
          201:
            description: User registered successfully
          400:
            description: Invalid JSON body
          409:
            description: Conflict (e.g. email already exists)
          422:
            description: Validation Error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        try:
            # Validasi input menggunakan Pydantic DTO secara ketat
            create_dto = UserCreateDTO(**data)
            
            # Panggil use case create yang meng-handle hashing internal
            user_response = user_use_case.create(create_dto)
            
            return jsonify({
                'success': True,
                'message': 'Registrasi user berhasil',
                'data': user_response.model_dump()
            }), 201

        except ValidationError as pydantic_err:
            return jsonify({
                'success': False, 
                'message': 'Validasi input gagal', 
                'errors': pydantic_err.errors(include_url=False)
            }), 422
        except ValueError as val_err:
            return jsonify({'success': False, 'message': str(val_err)}), 409
        except Exception:
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # POST /auth/login
    # ──────────────────────────────────────────────────────────────────────
    @auth_controller.route('/auth/login', methods=['POST'])
    def login():
        """
        Login and get JWT Token
        ---
        tags:
          - Authentication
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  example: "user@example.com"
                password:
                  type: string
                  example: "SecretPass123!"
        responses:
          200:
            description: Login successful
          401:
            description: Incorrect email or password
          422:
            description: Missing credentials
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email dan password wajib diisi'}), 422

        user = auth_use_case.login(email, password)
        if not user:
            return jsonify({'success': False, 'message': 'Email atau password salah'}), 401

        # Generate JWT Token dengan claim 'user_id' dan 'role'
        payload = {
            'user_id': str(user.id),
            'role': user.role,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        return jsonify({
            'success': True,
            'message': 'Login berhasil',
            'data': {
                'access_token': token,
                'token_type': 'Bearer',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'role': user.role,
                }
            }
        }), 200

    # ──────────────────────────────────────────────────────────────────────
    # GET /auth/me
    # ──────────────────────────────────────────────────────────────────────
    @auth_controller.route('/auth/me', methods=['GET'])
    @token_required
    def me():
        """
        Get current authenticated user info
        ---
        tags:
          - Authentication
        security:
          - Bearer: []
          - ApiKey: []
        responses:
          200:
            description: Current user information
          401:
            description: Unauthorized
        """
        # Mengembalikan data context user yang didapat dari token atau API Key
        return jsonify({
            'success': True,
            'data': {
                'user_id': request.current_user.get('user_id'),
                'role': request.current_user.get('role'),
            }
        }), 200

    return auth_controller