import os
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from uuid import UUID

# Import Interface dan DTO (Sesuaikan path dengan struktur project Anda)
from src.domain.collection.interface import ICollection
from src.domain.collection.model import CollectionCreateDTO, CollectionGetDTO
from src.util.middlewares.decorator_api import get_admin_required_decorator


def create_collection_blueprint(collection_use_case: ICollection, secret_key: str, secret_api: str) -> Blueprint:
    collection_controller = Blueprint('collection', __name__)
    admin_required = get_admin_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────────────────────────────────
    # POST /collections
    # ──────────────────────────────────────────────────────────────────────
    @collection_controller.route('/collections', methods=['POST'])
    @admin_required
    def create_collection():
        """
        Create a new collection (Admin Only)
        ---
        tags:
          - Collection Management
        security:
          - Bearer: []
          - ApiKey: []
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - name
              properties:
                name:
                  type: string
                  example: "Dokumen_Hukum_2026"
                is_active:
                  type: boolean
                  example: true
        responses:
          201:
            description: Collection created successfully
          400:
            description: Invalid JSON body
          409:
            description: Conflict (e.g. name already exists)
          422:
            description: Validation Error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        try:
            create_dto = CollectionCreateDTO(**data)
            collection_response = collection_use_case.create(create_dto)
            
            return jsonify({
                'success': True,
                'message': 'Collection berhasil dibuat',
                'data': collection_response.model_dump()
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
    # GET /collections
    # ──────────────────────────────────────────────────────────────────────
    @collection_controller.route('/collections', methods=['GET'])
    @admin_required
    def get_all_collections():
        """
        Get list of collections with filtering and pagination (Admin Only)
        ---
        tags:
          - Collection Management
        security:
          - Bearer: []
          - ApiKey: []
        parameters:
          - in: query
            name: search
            type: string
            description: Search partial name
          - in: query
            name: limit
            type: integer
            default: 10
          - in: query
            name: skip
            type: integer
            default: 0
        responses:
          200:
            description: Success retrieve collections
          422:
            description: Validation Error query parameters
        """
        # Konversi request args ke dictionary untuk validasi Pydantic
        query_params = request.args.to_dict()
        
        # Handler casting primitive types dari query string
        if 'limit' in query_params:
            query_params['limit'] = int(query_params['limit']) if query_params['limit'].isdigit() else query_params['limit']
        if 'skip' in query_params:
            query_params['skip'] = int(query_params['skip']) if query_params['skip'].isdigit() else query_params['skip']

        try:
            get_dto = CollectionGetDTO(**query_params)
            collections = collection_use_case.get_all(get_dto)
            
            return jsonify({
                'success': True,
                'message': 'Berhasil mengambil list collection',
                'data': [col.model_dump() for col in collections]
            }), 200

        except ValidationError as pydantic_err:
            return jsonify({
                'success': False, 
                'message': 'Validasi query param gagal', 
                'errors': pydantic_err.errors(include_url=False)
            }), 422
        except Exception:
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # GET /collections/active
    # ──────────────────────────────────────────────────────────────────────
    @collection_controller.route('/collections/active', methods=['GET'])
    @admin_required
    def get_active_collection():
        """
        Get the current active collection (Admin Only)
        ---
        tags:
          - Collection Management
        security:
          - Bearer: []
          - ApiKey: []
        responses:
          200:
            description: Active collection data
          404:
            description: No active collection found
        """
        try:
            collection_response = collection_use_case.get_active()
            return jsonify({
                'success': True,
                'message': 'Berhasil mengambil collection aktif',
                'data': collection_response.model_dump()
            }), 200
        except ValueError as val_err:
            return jsonify({'success': False, 'message': str(val_err)}), 404
        except Exception:
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # POST /collections/<id>/active
    # ──────────────────────────────────────────────────────────────────────
    @collection_controller.route('/collections/<uuid:id>/active', methods=['POST'])
    @admin_required
    def set_active_collection(id: UUID):
        """
        Set a collection status to active and deactivate others (Admin Only)
        ---
        tags:
          - Collection Management
        security:
          - Bearer: []
          - ApiKey: []
        parameters:
          - in: path
            name: id
            required: true
            type: string
            format: uuid
        responses:
          200:
            description: Collection activated successfully
          404:
            description: Collection not found
        """
        try:
            collection_response = collection_use_case.active(id)
            return jsonify({
                'success': True,
                'message': 'Collection berhasil diaktifkan',
                'data': collection_response.model_dump()
            }), 200
        except ValueError as val_err:
            return jsonify({'success': False, 'message': str(val_err)}), 404
        except Exception:
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # DELETE /collections/<id>
    # ──────────────────────────────────────────────────────────────────────
    @collection_controller.route('/collections/<uuid:id>', methods=['DELETE'])
    @admin_required
    def delete_collection(id: UUID):
        """
        Delete collection from apps database only (Admin Only)
        ---
        tags:
          - Collection Management
        security:
          - Bearer: []
          - ApiKey: []
        parameters:
          - in: path
            name: id
            required: true
            type: string
            format: uuid
        responses:
          200:
            description: Collection deleted successfully
          404:
            description: Collection not found
        """
        try:
            collection_response = collection_use_case.delete(id)
            return jsonify({
                'success': True,
                'message': 'Collection berhasil dihapus dari database aplikasi',
                'data': collection_response.model_dump()
            }), 200
        except ValueError as val_err:
            return jsonify({'success': False, 'message': str(val_err)}), 404
        except Exception:
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    return collection_controller