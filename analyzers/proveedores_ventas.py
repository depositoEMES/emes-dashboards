# import pandas as pd
# from sqlalchemy import create_engine, text
# from datetime import datetime
# import os
# from typing import Dict, List, Optional, Tuple
# import logging

# # Importar configuración
# try:
#     from server import SqlSqlDatabaseConfig
# except ImportError:
#     # Fallback si no existe el módulo config
#     class SqlDatabaseConfig:
#         @classmethod
#         def get_database_url(cls):
#             return (
#                 f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
#                 f"{os.getenv('DB_PASSWORD', 'digital_emes1')}@"
#                 f"{os.getenv('DB_HOST', 'localhost')}:"
#                 f"{os.getenv('DB_PORT', '5432')}/"
#                 f"{os.getenv('DB_NAME', 'emes')}"
#             )

#         @classmethod
#         def get_engine_config(cls):
#             return {
#                 'pool_pre_ping': True,
#                 'pool_recycle': 3600,
#                 'echo': False
#             }

#         @classmethod
#         def validate_config(cls):
#             return True


# class ProveedoresVentasAnalyzer:
#     """
#     Analyzer optimizado para datos de ventas de proveedores desde PostgreSQL usando SQLAlchemy
#     """

#     # Columnas esenciales que realmente necesitamos
#     ESSENTIAL_COLUMNS = [
#         'costo_total', 'valor_utilidad', 'pct_uti', 'valor_desc', 'pct_desc',
#         'id_cliente', 'numero', 'id', 'nit', 'fecha_factura',
#         'cantidad', 'porcentaje_iva', 'precio_neto',
#         'costo_unidad', 'ciudad', 'subgrupo', 'codigo', 'descripcion',
#         'cliente', 'tipo', 'vendedor', 'vendedor_operacion',
#         'direccion', 'sigla', 'grupo'
#     ]

#     def __init__(self):
#         self._df_ventas = None
#         self._laboratorios_list = None
#         self._periodos_list = None
#         self._last_update = None
#         self._engine = None

#         # Configuración de logging
#         logging.basicConfig(level=logging.INFO)
#         self.logger = logging.getLogger(__name__)

#         # Validar configuración
#         try:
#             SqlDatabaseConfig.validate_config()
#         except ValueError as e:
#             self.logger.warning(f"⚠️ Configuración de DB incompleta: {e}")

#         # Crear engine de SQLAlchemy
#         self._create_engine()

#         # Cargar datos iniciales
#         self._load_initial_data()

#     def _create_engine(self):
#         """
#         Crear engine de SQLAlchemy usando configuración
#         """
#         try:
#             db_url = SqlDatabaseConfig.get_database_url()
#             engine_config = SqlDatabaseConfig.get_engine_config()

#             self._engine = create_engine(db_url, **engine_config)

#             # Probar conexión básica
#             with self._engine.connect() as conn:
#                 result = conn.execute(text("SELECT 1 as test"))
#                 test_result = result.fetchone()

#                 # Probar acceso al schema ventas
#                 result = conn.execute(text("""
#                     SELECT EXISTS (
#                         SELECT FROM information_schema.schemata
#                         WHERE schema_name = 'ventas'
#                     )
#                 """))
#                 schema_exists = result.fetchone()[0]

#                 if schema_exists:
#                     # Probar acceso a la tabla diarias
#                     result = conn.execute(text("""
#                         SELECT EXISTS (
#                             SELECT FROM information_schema.tables
#                             WHERE table_schema = 'ventas'
#                             AND table_name = 'diarias'
#                         )
#                     """))
#                     table_exists = result.fetchone()[0]

#                     if table_exists:
#                         # Contar registros totales
#                         result = conn.execute(
#                             text("SELECT COUNT(*) FROM ventas.diarias"))

#         except Exception as e:
#             print(f"❌ Error creando engine de SQLAlchemy: {e}")
#             print(f"   Tipo de error: {type(e)}")
#             import traceback
#             traceback.print_exc()
#             self._engine = None

#     def _get_db_engine(self):
#         """
#         Obtener engine de SQLAlchemy
#         """
#         if self._engine is None:
#             self._create_engine()
#         return self._engine

#     def _load_initial_data(self):
#         """
#         Carga inicial de datos desde PostgreSQL
#         """
#         try:
#             print("📄 Iniciando carga optimizada de datos...")
#             self.reload_data()
#             print("✅ Datos iniciales cargados desde PostgreSQL")
#         except Exception as e:
#             print(f"❌ Error en carga inicial: {e}")
#             print("⚠️ Continuando con DataFrame vacío")
#             self._df_ventas = pd.DataFrame()
#             self._laboratorios_list = ['Todos']
#             self._periodos_list = ['Todos']

#     def _build_optimized_query(self, year=2025, limit_records=None):
#         """
#         Construir query optimizada con solo las columnas necesarias
#         """
#         # Crear lista de columnas para SELECT
#         columns_str = ', '.join(self.ESSENTIAL_COLUMNS)

#         # Query base optimizada
#         base_query = f"""
#         SELECT {columns_str}
#         FROM ventas.diarias
#         WHERE EXTRACT(YEAR FROM fecha_factura) = :year
#         AND tipo IN ('Remision', 'Factura')
#         AND fecha_factura IS NOT NULL
#         ORDER BY fecha_factura DESC
#         """

#         # Agregar límite si se especifica
#         if limit_records:
#             base_query += f" LIMIT {limit_records}"

#         return base_query

#     def reload_data(self, year=2025, limit_records=None):
#         """
#         Recargar datos desde PostgreSQL usando SQLAlchemy con consulta optimizada
#         """
#         engine = self._get_db_engine()
#         if not engine:
#             print("❌ No hay engine disponible")
#             raise Exception("No se pudo conectar a la base de datos")

#         try:
#             query = f"""
#             SELECT
#                 costo_total, valor_utilidad, pct_uti, valor_desc, pct_desc,
#                 id_cliente, numero, id, nit, fecha_factura,
#                 cantidad, porcentaje_iva, precio_neto,
#                 costo_unidad, ciudad, subgrupo, codigo, descripcion,
#                 cliente, tipo, vendedor, vendedor_operacion,
#                 sigla, grupo
#             FROM ventas.diarias
#             WHERE EXTRACT(YEAR FROM fecha_factura) = {year}
#             AND tipo IN ('Remision de la FE')
#             AND fecha_factura IS NOT NULL
#             ORDER BY fecha_factura DESC
#             """

#             # Agregar límite si se especifica
#             if limit_records:
#                 query += f" LIMIT {limit_records}"

#             # CORRECCIÓN: pd.read_sql_query SIN text() y SIN params
#             df = pd.read_sql_query(query, engine)

#             if not df.empty:
#                 # Procesar datos
#                 df = self._process_data(df)

#                 self._df_ventas = df
#                 self._update_lists()
#                 self._last_update = datetime.now()

#                 # Mostrar estadísticas de memoria
#                 memory_usage = df.memory_usage(
#                     deep=True).sum() / (1024**2)  # MB
#                 print(f"💾 Uso de memoria: {memory_usage:.1f} MB")
#                 print(f"✅ Datos actualizados: {len(df):,} registros")
#             else:
#                 print("❌ pd.read_sql_query devolvió DataFrame vacío")
#                 # Debug adicional
#                 with engine.connect() as conn:
#                     result = conn.execute(text(f"""
#                         SELECT EXTRACT(YEAR FROM fecha_factura) as año, COUNT(*) as registros
#                         FROM ventas.diarias
#                         WHERE fecha_factura IS NOT NULL
#                         GROUP BY EXTRACT(YEAR FROM fecha_factura)
#                         ORDER BY año DESC
#                     """))
#                     años_disponibles = result.fetchall()
#                     print(f"📅 Años disponibles: {años_disponibles}")

#                     result = conn.execute(text(f"""
#                         SELECT tipo, COUNT(*) as cantidad
#                         FROM ventas.diarias
#                         WHERE EXTRACT(YEAR FROM fecha_factura) = {year}
#                         GROUP BY tipo
#                         ORDER BY cantidad DESC
#                     """))
#                     tipos_disponibles = result.fetchall()
#                     print(f"📋 Tipos disponibles {year}: {tipos_disponibles}")

#                 self._df_ventas = pd.DataFrame()

#         except Exception as e:
#             print(f"❌ Error ejecutando query: {e}")
#             print(f"   Tipo de error: {type(e)}")
#             import traceback
#             traceback.print_exc()
#             raise

#     def _process_data(self, df):
#         """
#         Procesar y limpiar datos de manera optimizada
#         """
#         # Convertir fecha usando método más eficiente
#         df['fecha_factura'] = pd.to_datetime(
#             df['fecha_factura'], errors='coerce')

#         # Crear campos adicionales de manera vectorizada
#         df['mes_nombre'] = df['fecha_factura'].dt.strftime('%Y-%m')
#         df['trimestre'] = df['fecha_factura'].dt.to_period('Q').astype(str)
#         df['anio'] = df['fecha_factura'].dt.year
#         df['semana'] = df['fecha_factura'].dt.isocalendar().week
#         df['dia_semana'] = df['fecha_factura'].dt.day_name()

#         # Mapeo de días a español (más eficiente con .map)
#         dias_map = {
#             'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
#             'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
#         }
#         df['dia_semana_es'] = df['dia_semana'].map(dias_map)

#         # ⭐ CAMBIO IMPORTANTE: Usar 'sigla' como cliente principal, fallback a 'cliente'
#         df['cliente_display'] = df['sigla'].fillna('').astype(str)
#         # Si sigla está vacía, usar cliente
#         mask_sigla_vacia = (df['cliente_display'] == '') | (
#             df['cliente_display'] == 'nan')
#         df.loc[mask_sigla_vacia, 'cliente_display'] = df.loc[mask_sigla_vacia,
#                                                              'cliente'].fillna('Sin Cliente')

#         # Para mantener compatibilidad, reemplazar la columna cliente
#         df['cliente'] = df['cliente_display']
#         df.drop('cliente_display', axis=1, inplace=True)

#         # Limpiar valores nulos en campos importantes
#         df['grupo'] = df['grupo'].fillna('Sin Laboratorio')
#         df['descripcion'] = df['descripcion'].fillna('Sin Descripción')

#         # Asegurar tipos numéricos de manera más eficiente
#         numeric_cols = ['precio_neto', 'costo_total',
#                         'valor_utilidad', 'cantidad', 'valor_desc']
#         for col in numeric_cols:
#             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

#         return df

#     def _update_lists(self):
#         """
#         Actualizar listas de laboratorios y períodos de manera optimizada
#         """
#         if self._df_ventas.empty:
#             print("⚠️ DataFrame vacío, usando listas por defecto")
#             self._laboratorios_list = ['Todos']
#             self._periodos_list = ['Todos']
#             return

#         # Lista de laboratorios (más eficiente)
#         laboratorios_unicos = self._df_ventas['grupo'].dropna().unique()
#         laboratorios = sorted(
#             [lab for lab in laboratorios_unicos if lab and lab != 'Sin Laboratorio'])
#         self._laboratorios_list = ['Todos'] + laboratorios

#         # Lista de períodos (mes-año) - más eficiente
#         periodos_unicos = self._df_ventas['mes_nombre'].dropna().unique()
#         periodos = sorted(periodos_unicos, reverse=True)
#         self._periodos_list = ['Todos'] + periodos

#         print(
#             f"📋 Listas actualizadas: {len(self._laboratorios_list)} laboratorios, {len(self._periodos_list)} períodos")

#     def get_data_summary(self):
#         """
#         Obtener resumen de los datos cargados
#         """
#         if self._df_ventas.empty:
#             return {
#                 'total_records': 0,
#                 'memory_usage_mb': 0,
#                 'date_range': None,
#                 'laboratorios_count': 0,
#                 'periodos_count': 0
#             }

#         memory_usage = self._df_ventas.memory_usage(
#             deep=True).sum() / (1024**2)
#         date_range = {
#             'min': self._df_ventas['fecha_factura'].min(),
#             'max': self._df_ventas['fecha_factura'].max()
#         }

#         return {
#             'total_records': len(self._df_ventas),
#             'memory_usage_mb': round(memory_usage, 2),
#             'date_range': date_range,
#             # -1 por 'Todos'
#             'laboratorios_count': len(self._laboratorios_list) - 1,
#             'periodos_count': len(self._periodos_list) - 1,  # -1 por 'Todos'
#             'columns_loaded': len(self._df_ventas.columns)
#         }

#     # ============ MÉTODOS EXISTENTES (sin cambios significativos) ============

#     @property
#     def laboratorios_list(self):
#         """Lista de laboratorios disponibles"""
#         return self._laboratorios_list or ['Todos']

#     @property
#     def periodos_list(self):
#         """Lista de períodos disponibles"""
#         return self._periodos_list or ['Todos']

#     @property
#     def df_ventas(self):
#         """DataFrame de ventas"""
#         return self._df_ventas if self._df_ventas is not None else pd.DataFrame()

#     def filter_data(self, laboratorio='Todos', periodo='Todos'):
#         """
#         Filtrar datos por laboratorio y período de manera optimizada
#         """
#         df = self.df_ventas.copy()

#         if df.empty:
#             print("❌ DataFrame está vacío")
#             return df

#         # Filtrar por laboratorio
#         if laboratorio != 'Todos':
#             initial_count = len(df)
#             df = df[df['grupo'] == laboratorio]

#         # Filtrar por período
#         if periodo != 'Todos':
#             initial_count = len(df)
#             df = df[df['mes_nombre'] == periodo]

#         return df

#     def get_resumen_ventas(self, laboratorio='Todos', periodo='Todos'):
#         """
#         Obtener resumen de ventas del laboratorio
#         """
#         df = self.filter_data(laboratorio, periodo)

#         if df.empty:
#             return {
#                 'total_ventas': 0, 'total_costo': 0, 'total_utilidad': 0,
#                 'total_descuentos': 0, 'margen_promedio': 0, 'num_facturas': 0,
#                 'num_productos': 0, 'num_clientes': 0
#             }

#         # Calcular métricas de manera vectorizada (más eficiente)
#         total_ventas = df['precio_neto'].sum()
#         total_costo = df['costo_total'].sum()
#         total_utilidad = df['valor_utilidad'].sum()
#         total_descuentos = df['valor_desc'].sum()
#         margen_promedio = (total_utilidad / total_ventas *
#                            100) if total_ventas > 0 else 0

#         return {
#             'total_ventas': total_ventas,
#             'total_costo': total_costo,
#             'total_utilidad': total_utilidad,
#             'total_descuentos': total_descuentos,
#             'margen_promedio': margen_promedio,
#             'num_facturas': df['numero'].nunique(),
#             'num_productos': df['descripcion'].nunique(),
#             'num_clientes': df['cliente'].nunique()
#         }

#     def diagnose_data(self):
#         """
#         Diagnóstico completo del analyzer
#         """
#         # Verificar engine
#         engine_ok = self._engine is not None

#         if engine_ok:
#             try:
#                 with self._engine.connect() as conn:
#                     # Verificar conexión
#                     result = conn.execute(text("SELECT 1"))
#                     connection_ok = result.fetchone()[0] == 1

#                     # Verificar tabla
#                     result = conn.execute(text("""
#                         SELECT COUNT(*) FROM ventas.diarias
#                         WHERE EXTRACT(YEAR FROM fecha_factura) = 2025
#                     """))
#                     total_2025 = result.fetchone()[0]
#                     print(f"📊 Registros 2025 disponibles: {total_2025:,}")

#             except Exception as e:
#                 print(f"❌ Error en diagnóstico de DB: {e}")

#         # Verificar datos cargados
#         data_loaded = not self._df_ventas.empty if self._df_ventas is not None else False

#         if data_loaded:
#             summary = self.get_data_summary()
#             print(f"📈 Registros en memoria: {summary['total_records']:,}")
#             print(f"💾 Uso de memoria: {summary['memory_usage_mb']} MB")
#             print(
#                 f"📅 Rango de fechas: {summary['date_range']['min']} - {summary['date_range']['max']}")
#             print(f"🏭 Laboratorios: {summary['laboratorios_count']}")
#             print(f"📆 Períodos: {summary['periodos_count']}")
#             print(f"📋 Columnas cargadas: {summary['columns_loaded']}")

#         print("="*60 + "\n")

#         return {
#             'engine_ok': engine_ok,
#             'data_loaded': data_loaded,
#             'record_count': len(self._df_ventas) if data_loaded else 0,
#             'laboratorios_count': len(self._laboratorios_list) if self._laboratorios_list else 0,
#             'periodos_count': len(self._periodos_list) if self._periodos_list else 0
#         }

#     def get_ventas_por_periodo(self, laboratorio='Todos', tipo_periodo='mensual'):
#         """Obtener evolución de ventas por período"""
#         df = self.filter_data(laboratorio, 'Todos')
#         if df.empty:
#             return pd.DataFrame()

#         grupo_col = {'mensual': 'mes_nombre', 'trimestral': 'trimestre',
#                      'anual': 'anio'}.get(tipo_periodo, 'mes_nombre')

#         resultado = df.groupby(grupo_col).agg({
#             'precio_neto': 'sum',
#             'valor_utilidad': 'sum',
#             'numero': 'nunique',
#             'cliente': 'nunique'
#         }).reset_index()

#         resultado.columns = [grupo_col, 'ventas_netas',
#                              'utilidad', 'num_facturas', 'num_clientes']
#         return resultado.sort_values(grupo_col)

#     def get_estacionalidad_semana(self, laboratorio='Todos', periodo='Todos'):
#         """Obtener datos de estacionalidad por semana"""
#         df = self.filter_data(laboratorio, periodo)
#         if df.empty:
#             return pd.DataFrame()

#         resultado = df.groupby('semana').agg({
#             'precio_neto': 'sum',
#             'valor_utilidad': 'sum',
#             'numero': 'nunique'
#         }).reset_index()

#         resultado.columns = ['semana', 'ventas_netas',
#                              'utilidad', 'num_facturas']
#         return resultado.sort_values('semana')

#     def get_top_clientes(self, laboratorio='Todos', periodo='Todos', top_n=10):
#         """Obtener top clientes del laboratorio"""
#         df = self.filter_data(laboratorio, periodo)
#         if df.empty:
#             return pd.DataFrame()

#         resultado = df.groupby('cliente').agg({
#             'precio_neto': 'sum',
#             'valor_utilidad': 'sum',
#             'numero': 'nunique',
#             'cantidad': 'sum'
#         }).reset_index()

#         resultado.columns = ['cliente', 'ventas_netas',
#                              'utilidad', 'num_facturas', 'cantidad_total']
#         return resultado.nlargest(top_n, 'ventas_netas')

#     def get_top_productos(self, laboratorio='Todos', periodo='Todos', top_n=10):
#         """Obtener top productos del laboratorio"""
#         df = self.filter_data(laboratorio, periodo)
#         if df.empty:
#             return pd.DataFrame()

#         resultado = df.groupby(['codigo', 'descripcion']).agg({
#             'precio_neto': 'sum',
#             'cantidad': 'sum',
#             'numero': 'nunique'
#         }).reset_index()

#         resultado.columns = ['codigo', 'descripcion',
#                              'ventas_netas', 'cantidad_total', 'num_facturas']
#         return resultado.nlargest(top_n, 'ventas_netas')

#     def get_matriz_ventas_clientes(self, laboratorio='Todos', fecha_inicio=None, fecha_fin=None, clientes_seleccionados=None):
#         """Obtener matriz de ventas por cliente en rango de fechas"""
#         df = self.filter_data(laboratorio, 'Todos')
#         if df.empty:
#             return pd.DataFrame()

#         # Filtrar por rango de fechas
#         if fecha_inicio and fecha_fin:
#             df = df[(df['fecha_factura'] >= fecha_inicio)
#                     & (df['fecha_factura'] <= fecha_fin)]

#         # Filtrar por clientes seleccionados
#         if clientes_seleccionados:
#             df = df[df['cliente'].isin(clientes_seleccionados)]

#         if df.empty:
#             return pd.DataFrame()

#         # Crear matriz pivote por mes
#         matriz = df.groupby(['cliente', 'mes_nombre'])[
#             'precio_neto'].sum().unstack(fill_value=0)
#         return matriz

#     def get_evolucion_cliente(self, cliente, laboratorio='Todos'):
#         """Obtener evolución de ventas de un cliente específico"""
#         df = self.filter_data(laboratorio, 'Todos')
#         if df.empty or not cliente:
#             return pd.DataFrame()

#         cliente_data = df[df['cliente'] == cliente]
#         if cliente_data.empty:
#             return pd.DataFrame()

#         resultado = cliente_data.groupby('mes_nombre').agg({
#             'precio_neto': 'sum',
#             'valor_utilidad': 'sum',
#             'numero': 'nunique',
#             'cantidad': 'sum'
#         }).reset_index()

#         resultado.columns = ['mes_nombre', 'ventas_netas',
#                              'utilidad', 'num_facturas', 'cantidad_total']
#         return resultado.sort_values('mes_nombre')

#     def get_clientes_list(self, laboratorio='Todos'):
#         """Obtener lista de clientes para dropdown"""
#         df = self.filter_data(laboratorio, 'Todos')
#         if df.empty:
#             return ['Seleccione un cliente']

#         clientes = sorted(df['cliente'].dropna().unique())
#         return ['Seleccione un cliente'] + [c for c in clientes if c and c != 'Sin Cliente']

#     def close_connection(self):
#         """Cerrar conexión de SQLAlchemy"""
#         if self._engine:
#             self._engine.dispose()
#             self.logger.info("🔌 Conexión a PostgreSQL cerrada")

#     def __del__(self):
#         """Destructor para cerrar conexiones"""
#         try:
#             self.close_connection()
#         except:
#             pass  # Evitar errores en destructor
