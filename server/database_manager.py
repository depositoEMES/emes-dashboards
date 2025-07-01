from .db import Database

_db_instance = None


def get_db():
    global _db_instance

    if _db_instance is None:
        try:
            _db_instance = Database()
            print("✅ Singleton de base de datos inicializada")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            _db_instance = None

    return _db_instance


def close_db():
    global _db_instance

    if _db_instance:
        _db_instance.stop_connection()
        _db_instance = None
