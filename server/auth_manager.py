import hashlib
from typing import List
from .database_manager import get_db


class AuthManager:

    def __init__(self):
        self.db = get_db()

    def validate_user(self, username, password):
        """
        Validate user credentials against Firebase.
        Returns: (is_valid, user_info)
        """
        try:
            # Obtener datos de permisos/cuentas
            accounts = self.db.get_by_path("permisos/cuentas")

            if not accounts:
                return False, None

            # Buscar usuario
            for user_id, user_data in accounts.items():
                stored_username = user_data.get('username', '')
                stored_password = user_data.get('password', '')

                if stored_username == username:
                    # Verify password
                    if self._verify_password(password, stored_password):
                        return \
                            (
                                True,
                                {
                                    'user_id': user_id,
                                    'username': username,
                                    'role': user_data.get('role', 'user'),
                                    'permissions': user_data.get('permissions', {}),
                                    'full_name': user_data.get('full_name', username),
                                    'seller': user_data.get('seller', 'Todos')
                                }
                            )

            return False, None

        except Exception as e:
            print(f"Error validating user: {e}")
            return False, None

    def _verify_password(self, plain_password, stored_password):
        """
        Verify password. Ajusta según como tengas las contraseñas en Firebase.
        """
        # Si las contraseñas están en texto plano (NO recomendado)
        if stored_password == plain_password:
            return True

        # Si están hasheadas con SHA256
        hashed = \
            hashlib.sha256(plain_password.encode()).hexdigest()

        return hashed == stored_password

    def get_user_permissions(self, username: str) -> List[int]:
        """
        Get user permissions for dashboard access.
        """
        try:
            accounts = self.db.get_by_path("permisos/cuentas")

            for _, user_data in accounts.items():
                if user_data.get('username') == username:
                    return user_data.get('permissions', [])

            return []
        except Exception as e:
            print(f"Error getting permissions: {e}")
            return []
