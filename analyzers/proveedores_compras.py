import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from typing import Dict, List, Optional, Tuple
import logging

from models import PrediccionComprasModel

# Importar configuración
try:
    from server import SqlDatabaseConfig
except ImportError:
    # Fallback si no existe el módulo config
    class SqlDatabaseConfig:
        @classmethod
        def get_database_url(cls):
            return (
                f"postgresql://{os.getenv('DB_USER', 'postgres')}:"
                f"{os.getenv('DB_PASSWORD', 'digital_emes1')}@"
                f"{os.getenv('DB_HOST', 'localhost')}:"
                f"{os.getenv('DB_PORT', '5432')}/"
                f"{os.getenv('DB_NAME', 'emes')}"
            )

        @classmethod
        def get_engine_config(cls):
            return {
                'pool_pre_ping': True,
                'pool_recycle': 3600,
                'echo': False
            }

        @classmethod
        def validate_config(cls):
            return True


class ProveedoresComprasAnalyzer:
    """
    Analyzer optimizado para datos de compras de proveedores desde PostgreSQL usando SQLAlchemy
    """

    # Columnas esenciales que realmente necesitamos
    ESSENTIAL_COLUMNS = [
        'id', 'codigo', 'descripcion', 'compras', 'costo_compras',
        'dev_compras', 'costo_dev_compras', 'ventas', 'costo_ventas',
        'dev_ventas', 'costo_dev_ventas', 'stock', 'costo_stock',
        'costo_ultimo', 'nit', 'razon'
    ]

    def __init__(self):
        self._df_compras = None
        self._laboratorios_list = None
        self._periodos_list = None
        self._last_update = None
        self._engine = None

        # Configuración de logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Validar configuración
        try:
            SqlDatabaseConfig.validate_config()
        except ValueError as e:
            self.logger.warning(f"⚠️ Configuración de DB incompleta: {e}")

        # Crear engine de SQLAlchemy
        self._create_engine()

        # Cargar datos iniciales
        self._load_initial_data()

        self.prediccion_model = PrediccionComprasModel()
        self.model_trained = False

    def _create_engine(self):
        """
        Crear engine de SQLAlchemy usando configuración
        """
        try:
            db_url = SqlDatabaseConfig.get_database_url()
            engine_config = SqlDatabaseConfig.get_engine_config()

            self._engine = create_engine(db_url, **engine_config)

            # Probar conexión básica
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()

                # Probar acceso al schema compras
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.schemata
                        WHERE schema_name = 'compras'
                    )
                """))
                schema_exists = result.fetchone()[0]

                if schema_exists:
                    # Probar acceso a la tabla mensuales
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'compras'
                            AND table_name = 'mensuales'
                        )
                    """))
                    table_exists = result.fetchone()[0]

                    if table_exists:
                        # Contar registros totales
                        result = conn.execute(
                            text("SELECT COUNT(*) FROM compras.mensuales"))

        except Exception as e:
            print(f"❌ Error creando engine de SQLAlchemy: {e}")
            print(f"   Tipo de error: {type(e)}")
            import traceback
            traceback.print_exc()
            self._engine = None

    def _get_db_engine(self):
        """
        Obtener engine de SQLAlchemy
        """
        if self._engine is None:
            self._create_engine()
        return self._engine

    def _load_initial_data(self):
        """
        Carga inicial de datos desde PostgreSQL
        """
        try:
            print("📄 Iniciando carga optimizada de datos de compras...")
            self.reload_data()
            print("✅ Datos iniciales cargados desde PostgreSQL")
        except Exception as e:
            print(f"❌ Error en carga inicial: {e}")
            print("⚠️ Continuando con DataFrame vacío")
            self._df_compras = pd.DataFrame()
            self._laboratorios_list = ['Todos']
            self._periodos_list = ['Todos']

    def reload_data(self, year=2025, limit_records=None):
        """
        Recargar datos desde PostgreSQL usando SQLAlchemy con consulta optimizada
        """
        engine = self._get_db_engine()
        if not engine:
            print("❌ No hay engine disponible")
            raise Exception("No se pudo conectar a la base de datos")

        try:
            # Query para obtener todos los datos relevantes
            columns_str = ', '.join(self.ESSENTIAL_COLUMNS)
            query = f"""
            SELECT {columns_str}
            FROM compras.mensuales
            WHERE razon IS NOT NULL
            AND codigo IS NOT NULL
            ORDER BY razon, codigo
            """

            # Agregar límite si se especifica
            if limit_records:
                query += f" LIMIT {limit_records}"

            # Leer datos usando pandas
            df = pd.read_sql_query(query, engine)

            if not df.empty:
                # Procesar datos
                df = self._process_data(df)

                self._df_compras = df
                self._update_lists()
                self._last_update = datetime.now()

                # Mostrar estadísticas de memoria
                memory_usage = df.memory_usage(
                    deep=True).sum() / (1024**2)  # MB
                print(f"💾 Uso de memoria: {memory_usage:.1f} MB")
                print(f"✅ Datos actualizados: {len(df):,} registros")
            else:
                print("❌ pd.read_sql_query devolvió DataFrame vacío")
                self._df_compras = pd.DataFrame()

        except Exception as e:
            print(f"❌ Error ejecutando query: {e}")
            print(f"   Tipo de error: {type(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _process_data(self, df):
        """
        Procesar y limpiar datos de manera optimizada
        """
        # Limpiar valores nulos en campos importantes
        df['razon'] = df['razon'].fillna('Sin Laboratorio')
        df['descripcion'] = df['descripcion'].fillna('Sin Descripción')

        # Asegurar tipos numéricos de manera más eficiente
        numeric_cols = [
            'compras', 'costo_compras', 'dev_compras', 'costo_dev_compras',
            'ventas', 'costo_ventas', 'dev_ventas', 'costo_dev_ventas',
            'stock', 'costo_stock', 'costo_ultimo'
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Calcular métricas derivadas
        df['compras_netas'] = df['compras'] - df['dev_compras']
        df['costo_compras_netas'] = df['costo_compras'] - df['costo_dev_compras']
        df['ventas_netas'] = df['ventas'] - df['dev_ventas']
        df['costo_ventas_netas'] = df['costo_ventas'] - df['costo_dev_ventas']

        # Calcular rotación de inventario (ventas/stock)
        df['rotacion_inventario'] = df.apply(
            lambda row: row['ventas_netas'] / row['stock'] if row['stock'] > 0 else 0, axis=1
        )

        # Calcular margen de contribución
        df['margen_unitario'] = df.apply(
            lambda row: (row['costo_ventas_netas'] /
                         row['ventas_netas'] - row['costo_ultimo'])
            if row['ventas_netas'] > 0 else 0, axis=1
        )

        # Categorizar productos por rotación
        df['categoria_rotacion'] = pd.cut(
            df['rotacion_inventario'],
            bins=[0, 1, 3, 6, float('inf')],
            labels=['Muy Baja', 'Baja', 'Media', 'Alta'],
            include_lowest=True
        )

        # Identificar productos críticos (bajo stock + alta rotación)
        df['critico'] = (df['stock'] <= 10) & (df['rotacion_inventario'] > 2)

        # Calcular días de inventario estimados
        df['dias_inventario'] = df.apply(
            lambda row: (row['stock'] / (row['ventas_netas'] / 30))
            if row['ventas_netas'] > 0 else 999, axis=1
        )

        return df

    def _update_lists(self):
        """
        Actualizar listas de laboratorios y períodos de manera optimizada
        """
        if self._df_compras.empty:
            print("⚠️ DataFrame vacío, usando listas por defecto")
            self._laboratorios_list = ['Todos']
            self._periodos_list = ['Todos']
            return

        # Lista de laboratorios (más eficiente)
        laboratorios_unicos = self._df_compras['razon'].dropna().unique()
        laboratorios = sorted(
            [lab for lab in laboratorios_unicos if lab and lab != 'Sin Laboratorio'])
        self._laboratorios_list = ['Todos'] + laboratorios

        # Para períodos, como no tenemos fecha específica, creamos categorías
        self._periodos_list = ['Todos', 'Último Mes',
                               'Trimestre Actual', 'Año Actual']

        print(
            f"📋 Listas actualizadas: {len(self._laboratorios_list)} laboratorios, {len(self._periodos_list)} períodos")

    @property
    def laboratorios_list(self):
        """Lista de laboratorios disponibles"""
        return self._laboratorios_list or ['Todos']

    @property
    def periodos_list(self):
        """Lista de períodos disponibles"""
        return self._periodos_list or ['Todos']

    @property
    def df_compras(self):
        """DataFrame de compras"""
        return self._df_compras if self._df_compras is not None else pd.DataFrame()

    def filter_data(self, laboratorio='Todos', periodo='Todos'):
        """
        Filtrar datos por laboratorio y período de manera optimizada
        """
        df = self.df_compras.copy()

        if df.empty:
            print("❌ DataFrame está vacío")
            return df

        # Filtrar por laboratorio
        if laboratorio != 'Todos':
            df = df[df['razon'] == laboratorio]

        # Para período, como no tenemos fechas específicas, aplicamos filtros lógicos
        if periodo == 'Último Mes':
            # Filtrar productos con actividad reciente (ventas > 0)
            df = df[df['ventas'] > 0]
        elif periodo == 'Trimestre Actual':
            # Filtrar productos con compras o ventas significativas
            df = df[(df['compras'] > 0) | (df['ventas'] > 10)]
        elif periodo == 'Año Actual':
            # Todos los productos activos
            df = df[(df['compras'] > 0) | (
                df['ventas'] > 0) | (df['stock'] > 0)]

        return df

    def get_resumen_compras(self, laboratorio='Todos', periodo='Todos'):
        """
        Obtener resumen de compras del laboratorio
        """
        df = self.filter_data(laboratorio, periodo)

        if df.empty:
            return {
                'total_compras': 0, 'total_costo_compras': 0, 'total_stock': 0,
                'valor_inventario': 0, 'productos_criticos': 0, 'num_productos': 0,
                'rotacion_promedio': 0, 'dias_inventario_promedio': 0
            }

        # Calcular métricas de manera vectorizada
        total_compras = df['compras_netas'].sum()
        total_costo_compras = df['costo_compras_netas'].sum()
        total_stock = df['stock'].sum()
        valor_inventario = df['costo_stock'].sum()
        productos_criticos = df['critico'].sum()
        rotacion_promedio = df['rotacion_inventario'].mean()
        dias_inventario_promedio = df[df['dias_inventario']
                                      < 999]['dias_inventario'].mean()

        return {
            'total_compras': total_compras,
            'total_costo_compras': total_costo_compras,
            'total_stock': total_stock,
            'valor_inventario': valor_inventario,
            'productos_criticos': productos_criticos,
            'num_productos': df['codigo'].nunique(),
            'rotacion_promedio': rotacion_promedio if not pd.isna(rotacion_promedio) else 0,
            'dias_inventario_promedio': dias_inventario_promedio if not pd.isna(dias_inventario_promedio) else 0
        }

    def get_productos_criticos(self, laboratorio='Todos', periodo='Todos', top_n=20):
        """
        Obtener productos críticos que necesitan reabastecimiento urgente
        """
        df = self.filter_data(laboratorio, periodo)
        if df.empty:
            return pd.DataFrame()

        # Filtrar productos críticos y ordenar por urgencia
        criticos = df[df['critico'] == True].copy()
        if criticos.empty:
            # Si no hay críticos, mostrar los de menor stock con rotación media
            criticos = df[(df['stock'] <= 50) & (
                df['rotacion_inventario'] > 1)].copy()

        if not criticos.empty:
            # Calcular score de urgencia
            criticos['urgencia_score'] = (
                criticos['rotacion_inventario'] * 0.4 +
                (100 - criticos['stock']) * 0.3 +
                criticos['ventas_netas'] * 0.3
            )

            resultado = criticos.nlargest(top_n, 'urgencia_score')[
                ['codigo', 'descripcion', 'razon', 'stock', 'ventas_netas',
                 'rotacion_inventario', 'dias_inventario', 'costo_ultimo']
            ]
            return resultado

        return pd.DataFrame()

    def get_analisis_rotacion(self, laboratorio='Todos', periodo='Todos'):
        """
        Obtener análisis de rotación de inventarios
        """
        df = self.filter_data(laboratorio, periodo)
        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby('categoria_rotacion').agg({
            'codigo': 'count',
            'stock': 'sum',
            'costo_stock': 'sum',
            'ventas_netas': 'sum',
            'rotacion_inventario': 'mean'
        }).reset_index()

        resultado.columns = [
            'categoria', 'num_productos', 'stock_total',
            'valor_inventario', 'ventas_totales', 'rotacion_promedio'
        ]

        return resultado.sort_values('rotacion_promedio', ascending=False)

    def get_top_proveedores(self, laboratorio='Todos', periodo='Todos', top_n=10):
        """
        Obtener top proveedores por volumen de compras
        """
        df = self.filter_data(laboratorio, periodo)
        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby('razon').agg({
            'costo_compras_netas': 'sum',
            'compras_netas': 'sum',
            'codigo': 'nunique',
            'costo_stock': 'sum'
        }).reset_index()

        resultado.columns = [
            'proveedor', 'valor_compras', 'cantidad_compras',
            'num_productos', 'valor_inventario'
        ]

        return resultado.nlargest(top_n, 'valor_compras')

    def get_productos_sin_rotacion(self, laboratorio='Todos', periodo='Todos', top_n=20):
        """
        Obtener productos sin rotación (inventario muerto)
        """
        df = self.filter_data(laboratorio, periodo)
        if df.empty:
            return pd.DataFrame()

        # Productos con stock pero sin ventas
        sin_rotacion = df[
            (df['stock'] > 0) &
            (df['ventas_netas'] == 0) &
            (df['costo_stock'] > 0)
        ].copy()

        if not sin_rotacion.empty:
            resultado = sin_rotacion.nlargest(top_n, 'costo_stock')[
                ['codigo', 'descripcion', 'razon',
                    'stock', 'costo_stock', 'costo_ultimo']
            ]
            return resultado

        return pd.DataFrame()

    def get_oportunidades_compra(self, laboratorio='Todos', periodo='Todos', top_n=15):
        """
        Identificar oportunidades de compra (productos con alta rotación y stock bajo)
        """
        df = self.filter_data(laboratorio, periodo)
        if df.empty:
            return pd.DataFrame()

        # Productos con alta rotación pero stock relativamente bajo
        oportunidades = df[
            (df['rotacion_inventario'] > 1.5) &
            (df['dias_inventario'] < 60) &
            (df['stock'] > 0)
        ].copy()

        if not oportunidades.empty:
            # Calcular score de oportunidad
            oportunidades['oportunidad_score'] = (
                oportunidades['rotacion_inventario'] * 0.5 +
                oportunidades['ventas_netas'] * 0.3 +
                (60 - oportunidades['dias_inventario']) * 0.2
            )

            resultado = oportunidades.nlargest(top_n, 'oportunidad_score')[
                ['codigo', 'descripcion', 'razon', 'stock', 'ventas_netas',
                 'rotacion_inventario', 'dias_inventario', 'costo_ultimo']
            ]
            return resultado

        return pd.DataFrame()

    def get_comparacion_laboratorios(self, periodo='Todos'):
        """
        Comparar performance de compras por laboratorio
        """
        df = self.filter_data('Todos', periodo)
        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby('razon').agg({
            'costo_compras_netas': 'sum',
            'costo_stock': 'sum',
            'codigo': 'nunique',
            'rotacion_inventario': 'mean',
            'ventas_netas': 'sum'
        }).reset_index()

        resultado.columns = [
            'laboratorio', 'valor_compras', 'valor_inventario',
            'num_productos', 'rotacion_promedio', 'ventas_totales'
        ]

        # Calcular eficiencia de inventario
        resultado['eficiencia_inventario'] = (
            resultado['ventas_totales'] / resultado['valor_inventario']
        ).fillna(0)

        return resultado.sort_values('valor_compras', ascending=False)

    def train_prediction_model(self):
        """
        Entrenar modelo de predicciones
        """
        if self._df_compras is None or self._df_compras.empty:
            print("❌ No hay datos para entrenar el modelo")
            return False

        try:
            print("🤖 Iniciando entrenamiento del modelo de predicciones...")
            metrics = self.prediccion_model.train(self._df_compras)
            self.model_trained = True
            print("✅ Modelo entrenado exitosamente!")
            return metrics
        except Exception as e:
            print(f"❌ Error entrenando modelo: {e}")
            return False

    def get_predicciones_compras(self, laboratorio='Todos', top_n=50):
        """
        Obtener predicciones de compras para productos
        """
        if not self.model_trained:
            print("⚠️ Entrenando modelo por primera vez...")
            if not self.train_prediction_model():
                return pd.DataFrame()

        try:
            df = self.filter_data(laboratorio, 'Todos')
            predicciones = self.prediccion_model.predict(df, laboratorio)

            # Ordenar por urgencia y valor de compra
            urgencia_order = {'Alta': 3, 'Media': 2, 'Baja': 1}
            predicciones['urgencia_num'] = predicciones['urgencia'].map(
                urgencia_order)

            predicciones_sorted = predicciones.sort_values(
                ['urgencia_num', 'valor_compra_sugerido'],
                ascending=[False, False]
            ).drop('urgencia_num', axis=1)

            return predicciones_sorted.head(top_n)

        except Exception as e:
            print(f"❌ Error generando predicciones: {e}")
            return pd.DataFrame()

    def get_resumen_predicciones(self, laboratorio='Todos'):
        """
        Obtener resumen de predicciones para métricas
        """
        predicciones = self.get_predicciones_compras(laboratorio, top_n=1000)

        if predicciones.empty:
            return {
                'total_productos': 0, 'productos_alta_urgencia': 0,
                'productos_media_urgencia': 0, 'valor_total_compras': 0,
                'demanda_total_predicha': 0, 'productos_sin_stock': 0
            }

        return self.prediccion_model.get_predictions_summary(predicciones)

    def get_analisis_urgencia_predicciones(self, laboratorio='Todos'):
        """
        Análisis de urgencia para gráficos
        """
        predicciones = self.get_predicciones_compras(laboratorio, top_n=500)

        if predicciones.empty:
            return pd.DataFrame()

        # Agrupar por urgencia
        urgencia_analysis = predicciones.groupby('urgencia').agg({
            'codigo': 'count',
            'valor_compra_sugerido': 'sum',
            'demanda_predicha_30d': 'sum',
            'stock_actual': 'sum'
        }).reset_index()

        urgencia_analysis.columns = [
            'urgencia', 'num_productos', 'valor_compras_sugerido',
            'demanda_total', 'stock_total'
        ]

        return urgencia_analysis

    def get_predicciones_por_proveedor(self, laboratorio='Todos', top_n=10):
        """
        Predicciones agrupadas por proveedor
        """
        predicciones = self.get_predicciones_compras(laboratorio, top_n=500)

        if predicciones.empty:
            return pd.DataFrame()

        proveedor_analysis = predicciones.groupby('proveedor').agg({
            'codigo': 'count',
            'valor_compra_sugerido': 'sum',
            'cantidad_recomendada': 'sum',
            # Contar productos de alta urgencia
            'urgencia': lambda x: (x == 'Alta').sum()
        }).reset_index()

        proveedor_analysis.columns = [
            'proveedor', 'num_productos', 'valor_total_compras',
            'cantidad_total', 'productos_urgentes'
        ]

        return proveedor_analysis.nlargest(top_n, 'valor_total_compras')

    def get_feature_importance_data(self):
        """
        Obtener importancia de features para interpretabilidad
        """
        if not self.model_trained:
            return {}

        return self.prediccion_model.get_feature_importance()

    def close_connection(self):
        """Cerrar conexión de SQLAlchemy"""
        if self._engine:
            self._engine.dispose()
            self.logger.info("🔌 Conexión a PostgreSQL cerrada")

    def __del__(self):
        """Destructor para cerrar conexiones"""
        try:
            self.close_connection()
        except:
            pass  # Evitar errores en destructor
