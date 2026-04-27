import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple


class FidelizacionAnalyzer:
    def __init__(self):
        from . import get_unified_analyzer
        self._ua = get_unified_analyzer()
        self._cache = {}
        self._last_update = None

    def _get_db(self):
        return self._ua._get_db()

    def load_data(self, force_reload=False) -> Dict:
        if (not force_reload and self._cache and self._last_update
                and (datetime.now() - self._last_update).seconds < 300):
            return self._cache
        db = self._get_db()
        raw = db.get("fidelizacion") or {}
        self._cache = raw
        self._last_update = datetime.now()
        return raw

    # ── Índice de Fidelización ─────────────────────────────────────────────
    # Regularidad (35%) y consistencia (25%) usan el período propio del cliente
    # (desde su primera compra hasta el último mes del dataset), no el período
    # global. Así un cliente "Nuevo" con 2/2 meses activos = regularidad 1.0,
    # no 2/24 = 0.08.

    def _compute_indice(self, ventas: Dict, all_months: List[str]) -> Dict:
        active = {k: v for k, v in ventas.items() if v and v > 0}
        if not active:
            return {
                'regularidad': 0.0, 'recencia': 0.0,
                'consistencia': 0.0, 'tendencia': 0.5,
                'indice': 0.0, 'meses_activos': 0,
                'ultimo_mes': '', 'ventas_promedio': 0.0, 'ventas_total': 0.0,
            }

        vals = list(active.values())
        sorted_items = sorted(active.items())

        # ── Período propio: desde primera compra hasta último mes del dataset ──
        first_purchase = min(active.keys())
        last_dataset   = max(all_months) if all_months else max(active.keys())
        # Meses del dataset dentro del período propio del cliente
        client_span = [m for m in all_months if m >= first_purchase]

        # Regularidad: compras en período propio
        regularidad = (len([m for m in client_span if m in active])
                       / max(1, len(client_span)))

        # Recencia (decay lineal a 0 en 6 meses de inactividad)
        last_month_str = max(active.keys())
        try:
            last_dt = datetime.strptime(last_month_str, "%Y%m")
            now_dt  = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            months_ago = (now_dt.year - last_dt.year) * 12 + (now_dt.month - last_dt.month)
        except Exception:
            months_ago = 99
        recencia = max(0.0, 1.0 - months_ago / 6.0)

        # Consistencia: CV calculado solo sobre meses dentro del período propio
        vals_span = [active[m] for m in client_span if m in active]
        if len(vals_span) >= 2:
            mean_v = np.mean(vals_span)
            cv = np.std(vals_span) / mean_v if mean_v > 0 else 1.0
            consistencia = float(max(0.0, 1.0 - min(cv, 1.0)))
        elif len(vals_span) == 1:
            consistencia = 0.5   # neutral para clientes con un solo mes
        else:
            consistencia = 0.0

        # Tendencia: últimos vs primeros tercio (requiere ≥6 meses activos)
        if len(sorted_items) >= 6:
            n3 = max(1, len(sorted_items) // 3)
            old_avg = np.mean([v for _, v in sorted_items[:n3]])
            new_avg = np.mean([v for _, v in sorted_items[-n3:]])
            growth  = (new_avg - old_avg) / old_avg if old_avg > 0 else 0
            tendencia = float(min(1.0, max(0.0, 0.5 + growth * 0.5)))
        else:
            tendencia = 0.5

        indice = round(
            0.35 * regularidad +
            0.30 * recencia +
            0.25 * consistencia +
            0.10 * tendencia, 4)

        return {
            'regularidad':     round(regularidad, 3),
            'recencia':        round(recencia, 3),
            'consistencia':    round(consistencia, 3),
            'tendencia':       round(tendencia, 3),
            'indice':          indice,
            'meses_activos':   len(active),
            'span_meses':      len(client_span),  # período propio
            'ultimo_mes':      last_month_str,
            'ventas_promedio': round(float(np.mean(vals)), 2),
            'ventas_total':    round(float(sum(vals)), 2),
        }

    @staticmethod
    def _categoria(indice: float, tendencia: float = 0.5, meses_activos: int = 0) -> str:
        # Fiel Creciente: índice alto + pendiente positiva (tendencia > 0.55 requiere ≥6 meses)
        if indice >= 0.75 and tendencia > 0.55 and meses_activos >= 6:
            return 'Fiel Creciente'
        elif indice >= 0.75:   return 'Fiel'
        elif indice >= 0.55:   return 'Activo'
        elif indice >= 0.35:   return 'En riesgo'
        else:                   return 'Dormido'

    # ── Métodos públicos ───────────────────────────────────────────────────

    def get_resumen(self, vendedor='Todos', clasificacion='Todos') -> pd.DataFrame:
        raw = self.load_data()
        if not raw:
            return pd.DataFrame()

        all_months = sorted({m for cdata in raw.values() for m in cdata.get('ventas', {})})

        rows = []
        for cid, cdata in raw.items():
            v_asig = cdata.get('vendedor', '')
            clf    = cdata.get('clasificacion', '')
            if vendedor != 'Todos' and v_asig != vendedor:
                continue
            if clasificacion != 'Todos' and clf != clasificacion:
                continue

            metricas = self._compute_indice(cdata.get('ventas', {}), all_months)
            rows.append({
                'id':             cid,
                'cliente':        cdata.get('cliente', cid),
                'vendedor':       v_asig,
                'clasificacion':  clf,
                'fecha_creacion': cdata.get('fecha_creacion', ''),
                **metricas,
                'categoria': self._categoria(metricas['indice'], metricas['tendencia'], metricas['meses_activos']),
            })

        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def get_evolucion_cliente(self, cliente_id: str) -> pd.DataFrame:
        raw   = self.load_data()
        cdata = raw.get(str(cliente_id), {})
        ventas = cdata.get('ventas', {})
        if not ventas:
            return pd.DataFrame()

        rows = [{'mes': k, 'ventas': v} for k, v in ventas.items() if v]
        df = pd.DataFrame(rows).sort_values('mes').reset_index(drop=True)
        df['mes_dt']    = pd.to_datetime(df['mes'], format='%Y%m')
        df['mes_label'] = df['mes_dt'].dt.strftime('%b %Y')
        return df

    def get_comparacion_mensual_anual(self, vendedor='Todos', clasificacion='Todos') -> pd.DataFrame:
        """
        Suma de ventas por mes calendario (1-12) y año para comparar
        ej. Abril 2024 vs Abril 2025 vs Abril 2026.
        """
        raw = self.load_data()
        if not raw:
            return pd.DataFrame()

        rows = []
        for cid, cdata in raw.items():
            if vendedor != 'Todos' and cdata.get('vendedor') != vendedor:
                continue
            if clasificacion != 'Todos' and cdata.get('clasificacion') != clasificacion:
                continue
            for mes_key, valor in cdata.get('ventas', {}).items():
                if not valor:
                    continue
                try:
                    year  = int(mes_key[:4])
                    month = int(mes_key[4:6])
                    rows.append({'year': str(year), 'month': month, 'ventas': float(valor)})
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        result = df.groupby(['year', 'month'])['ventas'].sum().reset_index()
        result['month_label'] = pd.to_datetime(result['month'], format='%m').dt.strftime('%b')
        return result.sort_values(['month', 'year'])

    def get_clientes_criticos(self, top_n=15) -> pd.DataFrame:
        """
        Clientes Dormidos con mayor ticket histórico promedio.
        Ordenados por ventas_promedio desc — los que más vendían y ahora no compran.
        """
        df = self.get_resumen()
        if df.empty:
            return pd.DataFrame()

        dormidos = df[df['categoria'] == 'Dormido'].copy()
        if dormidos.empty:
            return pd.DataFrame()

        cols = ['cliente', 'vendedor', 'clasificacion', 'ventas_promedio',
                'ventas_total', 'meses_activos', 'ultimo_mes', 'recencia', 'indice']
        return dormidos[cols].sort_values('ventas_promedio', ascending=False).head(top_n).reset_index(drop=True)

    def get_dbscan_clusters(self, vendedor='Todos', clasificacion='Todos') -> Tuple[pd.DataFrame, int, str]:
        """
        DBSCAN sobre comportamiento de compra.
        Features: regularidad, recencia, consistencia, log(ventas_promedio), meses_activos_norm.
        Retorna (df con columna 'cluster_label', n_clusters, mensaje).
        """
        try:
            from sklearn.cluster import DBSCAN
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            df = self.get_resumen(vendedor, clasificacion)
            return df, 0, "scikit-learn no instalado"

        df = self.get_resumen(vendedor, clasificacion)
        if len(df) < 5:
            return df, 0, "Pocos datos para clustering"

        features = ['regularidad', 'recencia', 'consistencia', 'meses_activos']
        df['log_ventas'] = np.log1p(df['ventas_promedio'])
        features.append('log_ventas')

        X = df[features].fillna(0).values
        X_scaled = StandardScaler().fit_transform(X)

        # eps estimado con heurística de k-distancia (k=3)
        from sklearn.neighbors import NearestNeighbors
        nbrs = NearestNeighbors(n_neighbors=3).fit(X_scaled)
        distances, _ = nbrs.kneighbors(X_scaled)
        eps = float(np.percentile(distances[:, -1], 75))
        eps = max(0.5, min(eps, 2.0))  # clamped

        db = DBSCAN(eps=eps, min_samples=3).fit(X_scaled)
        df['cluster'] = db.labels_

        n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
        df['cluster_label'] = df['cluster'].apply(
            lambda c: f'Grupo {c + 1}' if c >= 0 else 'Outlier'
        )
        msg = f"{n_clusters} grupos encontrados · eps={eps:.2f}"
        return df, n_clusters, msg

    def get_listas_filtros(self):
        raw = self.load_data()
        vendedores     = sorted({v.get('vendedor', '') for v in raw.values() if v.get('vendedor')})
        clasificaciones = sorted({v.get('clasificacion', '') for v in raw.values() if v.get('clasificacion')})
        return vendedores, clasificaciones
