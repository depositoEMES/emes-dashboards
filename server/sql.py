"""
Configuración de base de datos
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class SqlDatabaseConfig:

    # Configuración PostgreSQL
    POSTGRES_HOST = os.getenv('DB_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('DB_PORT', '5432')
    POSTGRES_DB = os.getenv('DB_NAME', 'emes')
    POSTGRES_USER = os.getenv('DB_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('DB_PASSWORD', 'digital_emes1')

    # SSL Mode (opcional)
    POSTGRES_SSLMODE = os.getenv('DB_SSLMODE', 'prefer')

    @classmethod
    def get_database_url(cls):
        """
        Construir URL de conexión para SQLAlchemy
        """
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@"
            f"{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            f"?sslmode={cls.POSTGRES_SSLMODE}"
        )

    @classmethod
    def get_engine_config(cls):
        """
        Configuración para SQLAlchemy engine
        """
        return {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': 10,
            'max_overflow': 20,
            'echo': os.getenv('DB_ECHO', 'False').lower() == 'true'
        }

    @classmethod
    def validate_config(cls):
        """
        Validar que todas las variables requeridas estén configuradas
        """
        required_vars = [
            ('DB_HOST', cls.POSTGRES_HOST),
            ('DB_NAME', cls.POSTGRES_DB),
            ('DB_USER', cls.POSTGRES_USER),
            ('DB_PASSWORD', cls.POSTGRES_PASSWORD)
        ]

        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value or var_value.startswith('tu_'):
                missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(
                f"Variables de entorno requeridas no configuradas: {', '.join(missing_vars)}"
            )

        return True
