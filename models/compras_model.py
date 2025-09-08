import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, classification_report
import warnings
warnings.filterwarnings('ignore')


class PrediccionComprasModel:
    """
    Modelo híbrido para predicciones de compras y reabastecimiento

    Combina:
    1. Predicción de demanda futura (30 días)
    2. Clasificación de urgencia de reabastecimiento
    3. Recomendación de cantidad a comprar
    """

    def __init__(self):
        self.model_demanda = RandomForestRegressor(
            n_estimators=100, random_state=42)
        self.model_urgencia = RandomForestClassifier(
            n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def create_features(self, df):
        """
        Crear features para el modelo a partir del DataFrame de compras
        """
        # Crear copia para no modificar original
        data = df.copy()

        # Features básicas de rotación y stock
        data['rotacion_inventario'] = np.where(
            data['stock'] > 0,
            data['ventas_netas'] / data['stock'],
            0
        )

        data['dias_inventario'] = np.where(
            data['ventas_netas'] > 0,
            (data['stock'] / (data['ventas_netas'] / 30)),
            999
        )

        # Features de tendencia
        data['ratio_venta_compra'] = np.where(
            data['compras_netas'] > 0,
            data['ventas_netas'] / data['compras_netas'],
            0
        )

        # Features de valor/costo
        data['margen_unitario'] = np.where(
            data['ventas_netas'] > 0,
            ((data['costo_ventas_netas'] / data['ventas_netas']) -
             data['costo_ultimo']),
            0
        )

        # Features de riesgo
        data['ratio_devolucion'] = np.where(
            data['ventas'] > 0,
            data['dev_ventas'] / data['ventas'],
            0
        )

        # Categorización de productos por valor
        data['categoria_valor'] = pd.cut(
            data['costo_stock'],
            bins=[0, data['costo_stock'].quantile(0.33),
                  data['costo_stock'].quantile(0.66),
                  data['costo_stock'].max()],
            labels=['Bajo', 'Medio', 'Alto'],
            include_lowest=True
        )

        return data

    def prepare_training_data(self, df):
        """
        Preparar datos de entrenamiento
        """
        # Crear features
        data = self.create_features(df)

        # Filtrar productos válidos
        valid_mask = (
            (data['stock'] > 0) | (data['ventas_netas'] > 0) | (
                data['compras_netas'] > 0)
        ) & (data['costo_ultimo'] > 0)

        data = data[valid_mask].copy()

        if data.empty:
            raise ValueError("No hay datos válidos para entrenar")

        # Features para el modelo
        feature_cols = [
            'rotacion_inventario', 'stock', 'ventas_netas', 'compras_netas',
            'dias_inventario', 'ratio_venta_compra', 'margen_unitario',
            'ratio_devolucion', 'costo_ultimo', 'costo_stock'
        ]

        X = data[feature_cols].fillna(0)

        # Target 1: Demanda futura estimada (basada en rotación y tendencia)
        y_demanda = np.where(
            data['rotacion_inventario'] > 0,
            data['ventas_netas'] * 1.2,  # Proyección conservadora +20%
            data['ventas_netas'] * 0.8   # Para productos sin rotación -20%
        )

        # Target 2: Urgencia de reabastecimiento
        y_urgencia = self._calculate_urgencia(data)

        return X, y_demanda, y_urgencia, feature_cols

    def _calculate_urgencia(self, data):
        """
        Calcular urgencia de reabastecimiento basado en múltiples factores
        """
        urgencia = []

        for _, row in data.iterrows():
            score = 0

            # Factor 1: Días de inventario
            if row['dias_inventario'] < 15:
                score += 3
            elif row['dias_inventario'] < 30:
                score += 2
            elif row['dias_inventario'] < 60:
                score += 1

            # Factor 2: Rotación
            if row['rotacion_inventario'] > 4:
                score += 2
            elif row['rotacion_inventario'] > 2:
                score += 1

            # Factor 3: Stock bajo + ventas altas
            if row['stock'] < 10 and row['ventas_netas'] > 50:
                score += 2

            # Factor 4: Ratio venta/compra alto (se vende más de lo que se compra)
            if row['ratio_venta_compra'] > 1.5:
                score += 1

            # Categorizar urgencia
            if score >= 5:
                urgencia.append('Alta')
            elif score >= 3:
                urgencia.append('Media')
            else:
                urgencia.append('Baja')

        return urgencia

    def train(self, df):
        """
        Entrenar los modelos
        """
        print("🔄 Preparando datos para entrenamiento...")
        X, y_demanda, y_urgencia, self.feature_cols = self.prepare_training_data(
            df)

        print(f"📊 Entrenando con {len(X)} productos...")

        # Dividir datos
        X_train, X_test, y_demanda_train, y_demanda_test, y_urgencia_train, y_urgencia_test = \
            train_test_split(X, y_demanda, y_urgencia,
                             test_size=0.2, random_state=42)

        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Entrenar modelo de demanda
        print("📈 Entrenando modelo de demanda...")
        self.model_demanda.fit(X_train_scaled, y_demanda_train)
        demanda_pred = self.model_demanda.predict(X_test_scaled)
        mae_demanda = mean_absolute_error(y_demanda_test, demanda_pred)
        print(f"   MAE Demanda: {mae_demanda:.2f}")

        # Entrenar modelo de urgencia
        print("🚨 Entrenando modelo de urgencia...")
        self.model_urgencia.fit(X_train_scaled, y_urgencia_train)
        urgencia_pred = self.model_urgencia.predict(X_test_scaled)

        # Métricas
        print("\n📋 Reporte de clasificación de urgencia:")
        print(classification_report(y_urgencia_test, urgencia_pred))

        self.is_trained = True
        print("✅ Modelos entrenados exitosamente!")

        return {
            'mae_demanda': mae_demanda,
            'total_productos': len(X),
            'feature_importance': dict(zip(self.feature_cols,
                                           self.model_demanda.feature_importances_))
        }

    def predict(self, df, laboratorio='Todos'):
        """
        Hacer predicciones para productos
        """
        if not self.is_trained:
            raise ValueError("El modelo debe ser entrenado primero")

        # Preparar datos
        data = self.create_features(df)

        # Filtrar por laboratorio si especificado
        if laboratorio != 'Todos':
            data = data[data['razon'] == laboratorio]

        if data.empty:
            return pd.DataFrame()

        # Filtrar productos válidos
        valid_mask = (
            (data['stock'] >= 0) &
            (data['costo_ultimo'] > 0) &
            ((data['ventas_netas'] > 0) |
             (data['compras_netas'] > 0) | (data['stock'] > 0))
        )
        data = data[valid_mask].copy()

        if data.empty:
            return pd.DataFrame()

        # Preparar features
        X = data[self.feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Hacer predicciones
        demanda_pred = self.model_demanda.predict(X_scaled)
        urgencia_pred = self.model_urgencia.predict(X_scaled)
        urgencia_prob = self.model_urgencia.predict_proba(X_scaled)

        # Calcular cantidad recomendada
        cantidad_recomendada = self._calculate_cantidad_recomendada(
            data, demanda_pred, urgencia_pred
        )

        # Crear DataFrame de resultados
        resultados = pd.DataFrame({
            'codigo': data['codigo'],
            'descripcion': data['descripcion'],
            'proveedor': data['razon'],
            'stock_actual': data['stock'],
            'ventas_actuales': data['ventas_netas'],
            'rotacion_actual': data['rotacion_inventario'],
            'dias_inventario': data['dias_inventario'],
            'demanda_predicha_30d': demanda_pred.round(0),
            'urgencia': urgencia_pred,
            'urgencia_score': urgencia_prob.max(axis=1),
            'cantidad_recomendada': cantidad_recomendada,
            'valor_compra_sugerido': cantidad_recomendada * data['costo_ultimo'],
            'costo_unitario': data['costo_ultimo']
        }).round(2)

        return resultados

    def _calculate_cantidad_recomendada(self, data, demanda_pred, urgencia_pred):
        """
        Calcular cantidad recomendada de compra
        """
        cantidad = []

        for i, (_, row) in enumerate(data.iterrows()):
            demanda = demanda_pred[i]
            urgencia = urgencia_pred[i]
            stock_actual = row['stock']

            # Stock de seguridad basado en urgencia
            if urgencia == 'Alta':
                safety_factor = 2.0  # 2 meses de stock
                lead_time_factor = 1.5
            elif urgencia == 'Media':
                safety_factor = 1.5  # 1.5 meses de stock
                lead_time_factor = 1.2
            else:
                safety_factor = 1.0  # 1 mes de stock
                lead_time_factor = 1.0

            # Demanda para período + stock de seguridad
            demanda_total = demanda * safety_factor * lead_time_factor

            # Cantidad a comprar = demanda total - stock actual
            cantidad_comprar = max(0, demanda_total - stock_actual)

            # Redondear a números manejables
            if cantidad_comprar > 0:
                if cantidad_comprar < 10:
                    cantidad_comprar = max(5, int(cantidad_comprar))
                else:
                    # Redondear a múltiplos de 5
                    cantidad_comprar = int(cantidad_comprar / 5) * 5

            cantidad.append(cantidad_comprar)

        return cantidad

    def get_feature_importance(self):
        """
        Obtener importancia de features para interpretabilidad
        """
        if not self.is_trained:
            return {}

        importance = dict(zip(
            self.feature_cols,
            self.model_demanda.feature_importances_
        ))

        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    def get_predictions_summary(self, predictions_df):
        """
        Obtener resumen de predicciones para dashboards
        """
        if predictions_df.empty:
            return {}

        return {
            'total_productos': len(predictions_df),
            'productos_alta_urgencia': len(predictions_df[predictions_df['urgencia'] == 'Alta']),
            'productos_media_urgencia': len(predictions_df[predictions_df['urgencia'] == 'Media']),
            'productos_baja_urgencia': len(predictions_df[predictions_df['urgencia'] == 'Baja']),
            'valor_total_compras': predictions_df['valor_compra_sugerido'].sum(),
            'productos_sin_stock': len(predictions_df[predictions_df['stock_actual'] <= 0]),
            'demanda_total_predicha': predictions_df['demanda_predicha_30d'].sum()
        }
