class PermissionManager:
    def __init__(self, db):
        self.db = db

    def check_dashboard_permission(self, session_data, dashboard_name):
        """
        Verifica si el usuario tiene permiso para acceder a un dashboard

        Args:
            session_data: Datos de sesión del usuario
            dashboard_name: Nombre del dashboard ('cartera', 'ventas', etc.)

        Returns:
            bool: True si tiene permiso, False si no
        """
        if not session_data:
            return False

        user_id = session_data.get('user_id')
        if not user_id:
            return False

        # Obtener permisos del usuario desde Firebase
        user_permissions = self.db.get_by_path(f"permisos/cuentas/{user_id}")

        if not user_permissions:
            return False

        dashboards = user_permissions.get(
            'permissions', {}).get('dashboards', {})

        # Verificar permiso específico
        return self._has_dashboard_access(dashboards, dashboard_name)

    def _has_dashboard_access(self, dashboards, dashboard_name):
        """
        Verifica si tiene acceso a un dashboard específico, manejando subdicts

        Args:
            dashboards: Dict con permisos de dashboards
            dashboard_name: Nombre del dashboard a verificar

        Returns:
            bool: True si tiene acceso
        """
        if dashboard_name not in dashboards:
            return False

        permission = dashboards[dashboard_name]

        # Si es un entero, verificar directamente
        if isinstance(permission, int):
            return permission == 1

        # Si es un dict (subpermisos), verificar si tiene al menos uno activo
        if isinstance(permission, dict):
            return any(
                value == 1 for value in permission.values()
                if isinstance(value, int)
            )

        return False

    def get_accessible_dashboards(self, session_data):
        """
        Retorna lista de dashboards accesibles para el usuario
        Maneja tanto permisos directos (int) como subdicts
        """
        if not session_data:
            return []

        user_id = session_data.get('user_id')
        if not user_id:
            return []

        user_permissions = self.db.get_by_path(f"permisos/cuentas/{user_id}")

        if not user_permissions:
            return []

        dashboards = user_permissions.get(
            'permissions', {}).get('dashboards', {})
        accessible = []

        for dashboard_name, permission in dashboards.items():
            # Si es un entero y es 1, tiene acceso
            if isinstance(permission, int) and permission == 1:
                accessible.append(dashboard_name)

            # Si es un dict, verificar si tiene al menos un subpermiso activo
            elif isinstance(permission, dict):
                has_subpermission = any(
                    value == 1 for value in permission.values()
                    if isinstance(value, int)
                )
                if has_subpermission:
                    accessible.append(dashboard_name)

        return accessible

    def check_specific_permission(self, session_data, dashboard_name, sub_permission=None):
        """
        Verifica un permiso específico, incluyendo subpermisos

        Args:
            session_data: Datos de sesión del usuario
            dashboard_name: Nombre del dashboard ('ventas', 'cotizador', etc.)
            sub_permission: Subpermiso específico ('vendedor', 'transferencias', etc.)

        Returns:
            bool: True si tiene el permiso específico
        """
        if not session_data:
            return False

        user_id = session_data.get('user_id')
        if not user_id:
            return False

        user_permissions = self.db.get_by_path(f"permisos/cuentas/{user_id}")

        if not user_permissions:
            return False

        dashboards = user_permissions.get(
            'permissions', {}).get('dashboards', {})

        if dashboard_name not in dashboards:
            return False

        permission = dashboards[dashboard_name]

        # Si no hay subpermiso especificado, verificar acceso general al dashboard
        if sub_permission is None:
            return self._has_dashboard_access(dashboards, dashboard_name)

        # Verificar subpermiso específico
        if isinstance(permission, dict):
            return permission.get(sub_permission, 0) == 1

        # Si es un int y no hay subdicts, no puede tener subpermisos
        return False

    def get_dashboard_subpermissions(self, session_data, dashboard_name):
        """
        Obtiene todos los subpermisos activos para un dashboard específico

        Args:
            session_data: Datos de sesión del usuario
            dashboard_name: Nombre del dashboard

        Returns:
            list: Lista de subpermisos activos
        """
        if not session_data:
            return []

        user_id = session_data.get('user_id')
        if not user_id:
            return []

        user_permissions = self.db.get_by_path(f"permisos/cuentas/{user_id}")

        if not user_permissions:
            return []

        dashboards = user_permissions.get(
            'permissions', {}).get('dashboards', {})

        if dashboard_name not in dashboards:
            return []

        permission = dashboards[dashboard_name]

        # Si es un dict, retornar subpermisos activos
        if isinstance(permission, dict):
            return [
                sub_perm for sub_perm, value in permission.items()
                if isinstance(value, int) and value == 1
            ]

        # Si es un int y es 1, retornar acceso general
        if isinstance(permission, int) and permission == 1:
            return ['general']

        return []

    def get_user_permissions_summary(self, session_data):
        """
        Obtiene un resumen completo de todos los permisos del usuario

        Returns:
            dict: Resumen de permisos organizados
        """
        if not session_data:
            return {}

        user_id = session_data.get('user_id')
        if not user_id:
            return {}

        user_permissions = self.db.get_by_path(f"permisos/cuentas/{user_id}")

        if not user_permissions:
            return {}

        dashboards = user_permissions.get(
            'permissions', {}).get('dashboards', {})
        summary = {}

        for dashboard_name, permission in dashboards.items():
            if isinstance(permission, int):
                summary[dashboard_name] = {
                    'type': 'direct',
                    'access': permission == 1,
                    'subpermissions': []
                }
            elif isinstance(permission, dict):
                active_subs = [
                    sub_perm for sub_perm, value in permission.items()
                    if isinstance(value, int) and value == 1
                ]
                summary[dashboard_name] = {
                    'type': 'nested',
                    'access': len(active_subs) > 0,
                    'subpermissions': active_subs
                }

        return summary
