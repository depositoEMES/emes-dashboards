import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import gc


class CacheManager:

    def __init__(self, default_ttl_minutes=15):
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}
        self.default_ttl = default_ttl_minutes * 60  # Convert to seconds
        self._lock = threading.Lock()

        # Configuración de limpieza automática
        self.max_cache_size = 50  # Máximo número de elementos en cache
        self.cleanup_interval = 300  # Limpiar cada 5 minutos
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener dato del cache si está válido

        Args:
            key: Clave del cache

        Returns:
            Dato del cache o None si no existe/expiró
        """
        with self._lock:
            # Limpiar cache si es necesario
            self._cleanup_if_needed()

            if key not in self._cache:
                return None

            # Verificar si ha expirado
            if self._is_expired(key):
                self._remove_key(key)
                return None

            # Actualizar contador de acceso
            self._access_count[key] = self._access_count.get(key, 0) + 1

            print(
                f"📦 Cache HIT para '{key}' (accesos: {self._access_count[key]})")
            return self._cache[key]

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """
        Guardar dato en cache

        Args:
            key: Clave del cache
            value: Valor a guardar
            ttl_minutes: Tiempo de vida en minutos (opcional)
        """
        with self._lock:
            ttl = (ttl_minutes * 60) if ttl_minutes else self.default_ttl

            self._cache[key] = value
            self._timestamps[key] = time.time() + ttl
            self._access_count[key] = 0

            print(f"💾 Cache SET para '{key}' (TTL: {ttl//60} min)")

            # Limpiar si el cache está muy lleno
            if len(self._cache) > self.max_cache_size:
                self._cleanup_old_entries()

    def invalidate(self, key: str) -> bool:
        """
        Invalidar una entrada específica del cache

        Args:
            key: Clave a invalidar

        Returns:
            True si se invalidó, False si no existía
        """
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                print(f"🗑️ Cache INVALIDATED para '{key}'")
                return True
            return False

    def clear(self) -> None:
        """Limpiar todo el cache"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            self._access_count.clear()
            gc.collect()  # Forzar garbage collection
            print(f"🧹 Cache CLEARED - {count} elementos eliminados")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(
                1 for key in self._cache.keys() if self._is_expired(key))

            return {
                'total_entries': total_entries,
                'expired_entries': expired_count,
                'active_entries': total_entries - expired_count,
                'access_counts': dict(self._access_count),
                'cache_keys': list(self._cache.keys())
            }

    def _is_expired(self, key: str) -> bool:
        """Verificar si una entrada ha expirado"""
        return key in self._timestamps and time.time() > self._timestamps[key]

    def _remove_key(self, key: str) -> None:
        """Remover una clave del cache completamente"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_count.pop(key, None)

    def _cleanup_if_needed(self) -> None:
        """Limpiar cache si ha pasado el intervalo de limpieza"""
        current_time = time.time()
        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self._last_cleanup = current_time

    def _cleanup_old_entries(self) -> None:
        """Limpiar entradas expiradas y menos usadas"""
        expired_keys = [key for key in self._cache.keys()
                        if self._is_expired(key)]

        # Remover entradas expiradas
        for key in expired_keys:
            self._remove_key(key)

        print(
            f"🧽 Cache cleanup - {len(expired_keys)} entradas expiradas eliminadas")

        # Si aún hay demasiadas entradas, remover las menos usadas
        if len(self._cache) > self.max_cache_size:
            # Ordenar por número de accesos (ascendente)
            sorted_keys = sorted(
                self._access_count.items(),
                key=lambda x: x[1]
            )

            # Remover las menos usadas
            keys_to_remove = sorted_keys[:len(
                self._cache) - self.max_cache_size + 5]
            for key, _ in keys_to_remove:
                self._remove_key(key)

            print(
                f"🗑️ Cache cleanup - {len(keys_to_remove)} entradas menos usadas eliminadas")

        # Forzar garbage collection después de limpieza
        gc.collect()


# Instancia global del cache manager
cache_manager = CacheManager(default_ttl_minutes=15)


def get_cache_manager() -> CacheManager:
    """Obtener la instancia global del cache manager"""
    return cache_manager


# Decorador para cachear resultados de funciones
def cached(ttl_minutes: int = 15, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones

    Args:
        ttl_minutes: Tiempo de vida del cache en minutos
        key_prefix: Prefijo para la clave del cache
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Crear clave del cache basada en función y argumentos
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Intentar obtener del cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Ejecutar función y cachear resultado
            print(f"🔄 Ejecutando función '{func.__name__}' - no está en cache")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_minutes)

            return result
        return wrapper
    return decorator
