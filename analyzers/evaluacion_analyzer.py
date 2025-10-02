import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from analyzers import VentasAnalyzer


class EvaluacionAnalyzer:

    def __init__(self):
        """
        Initialize the EvaluacionAnalyzer.
        """
        from . import get_unified_analyzer
        self._unified_analyzer = get_unified_analyzer()

        self._analisis_data = {}
        self._maestro_labs = {}
        self._last_analisis_update = None

        self.__ventas_analyzer = VentasAnalyzer()

    def _get_db(self):
        """
        Get database instance.
        """
        return self._unified_analyzer._get_db()

    def load_analisis_vendedores(self, force_reload=False):
        """
        Load analisis_vendedores data from Firebase
        """
        try:
            if not force_reload and self._analisis_data and self._last_analisis_update:
                # Check if cache is less than 5 minutes old
                if (datetime.now() - self._last_analisis_update).seconds < 300:
                    return self._analisis_data

            db = self._get_db()

            if not db:
                print("❌ No se pudo obtener conexión para análisis vendedores")
                return {}

            # Load analisis_vendedores
            data = db.get("analisis_vendedores")

            if data:
                self._analisis_data = data
                self._last_analisis_update = datetime.now()

            # Load maestros/codigos_labs
            labs_data = db.get_by_path("maestros/codigos_labs")

            if labs_data:
                self._maestro_labs = labs_data

            return self._analisis_data

        except Exception as e:
            print(f"❌ Error cargando análisis vendedores: {e}")
            return {}

    def _calculate_average_growth_rate(self, vendor_data):
        """
        Calculates average growth rate for each vendor.
        """
        try:
            current_date = datetime.now()
            monthly_sales = {}

            # Calcular ventas de los últimos 6 meses
            for i in range(6):
                month_date = current_date - timedelta(days=30*i)
                month_key = month_date.strftime("%Y%m")
                monthly_sales[month_key] = 0

                for date_key, date_data in vendor_data.items():
                    if date_key.startswith(month_key):
                        if 'proveedores' in date_data:
                            for value in date_data['proveedores'].values():
                                monthly_sales[month_key] += value

            # Calcular tasas de crecimiento mes a mes
            sorted_months = sorted(monthly_sales.keys())
            growth_rates = []

            for i in range(1, len(sorted_months)):
                prev_month = sorted_months[i-1]
                curr_month = sorted_months[i]

                if monthly_sales[prev_month] > 0:
                    growth = ((monthly_sales[curr_month] - monthly_sales[prev_month]) /
                              monthly_sales[prev_month]) * 100
                    growth_rates.append(growth)

            # Retornar promedio
            return sum(growth_rates) / len(growth_rates) if growth_rates else 0

        except Exception as e:
            print(f"Error calculando crecimiento: {e}")
            return 0

    def _get_assigned_clients_count(self, vendor_name):
        """
        Contar clientes activos asignados
        """
        try:
            data = \
                self.__ventas_analyzer._count_active_clients_by_vendor()

            return \
                data.get(vendor_name, 0)

        except Exception as e:
            print(f"Error obteniendo clientes asignados: {e}")
            return 0

    def get_evolution_data_for_vendors(self, months=6):
        """
        Get evolution data for all vendors with both efficiency and quality metrics
        """
        try:
            analisis_data = self.load_analisis_vendedores()

            if not analisis_data:
                return pd.DataFrame()

            db = self._get_db()
            vendor_codes = db.get_by_path("maestros/codigos_vendedores") or {}
            active_vendors = \
                db.get_by_path("maestros/vendedores_activos") or []

            # Filter active vendors
            active_vendor_codes = []
            for code, name in vendor_codes.items():
                if name in active_vendors:
                    active_vendor_codes.append(code)

            # Get current date and previous months
            current_date = datetime.now()
            results = []

            for month_offset in range(months):
                month_date = current_date - timedelta(days=30*month_offset)
                month_str = month_date.strftime("%Y%m")

                for vendor_code in active_vendor_codes:
                    if vendor_code not in analisis_data:
                        continue

                    vendor_name = vendor_codes.get(vendor_code, vendor_code)
                    vendor_data = analisis_data[vendor_code]

                    # Calculate metrics for this specific month
                    metrics = self._calculate_metrics_for_month(
                        vendor_data, vendor_name, month_str
                    )

                    if metrics:
                        metrics['fecha'] = month_date.strftime("%Y-%m-01")
                        results.append(metrics)

            if not results:
                return pd.DataFrame()

            df = pd.DataFrame(results)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values(['vendedor', 'fecha'])

            return df

        except Exception as e:
            print(f"Error getting evolution data: {e}")
            return pd.DataFrame()

    def _calculate_metrics_for_month(self, vendor_data, vendor_name, month_str):
        """
        Calculate metrics for a specific historical month.
        """
        try:
            unique_products = set()
            unique_providers = set()
            unique_clients = set()
            total_sales = 0

            for date_key, date_data in vendor_data.items():
                if not date_key.startswith(month_str):
                    continue

                if 'proveedores' in date_data and date_data['proveedores']:
                    for prov_code, prov_data in date_data['proveedores'].items():
                        unique_providers.add(prov_code)
                        if isinstance(prov_data, dict):
                            total_sales += prov_data.get('v', 0)

                if 'clientes' in date_data and date_data['clientes']:
                    for client_id in date_data['clientes'].keys():
                        unique_clients.add(client_id)

                if 'producto' in date_data and date_data['producto']:
                    if isinstance(date_data['producto'], dict):
                        for prod_code in date_data['producto'].keys():
                            unique_products.add(prod_code)

            if total_sales == 0:
                return None

            # Simplified scoring for historical data
            TOTAL_PRODUCTOS = 9018
            TOTAL_PROVEEDORES = 232

            # Get assigned clients for this vendor
            total_assigned = self._get_assigned_clients_count(vendor_name)

            # Calculate normalized scores
            client_score = (len(unique_clients) / max(total_assigned, 1)
                            ) * 100 if total_assigned > 0 else 0
            portfolio_score = min(
                ((len(unique_products) / TOTAL_PRODUCTOS) * 100 / 10) * 100, 100)
            provider_score = min(
                ((len(unique_providers) / TOTAL_PROVEEDORES) * 100 / 30) * 100, 100)

            # Simplified efficiency and quality
            eficiencia = min(client_score * 0.5 + 50, 100)  # Simplified
            calidad = (portfolio_score * 0.5 + provider_score * 0.5)

            return {
                'vendedor': vendor_name,
                'eficiencia': round(eficiencia, 2),
                'calidad': round(calidad, 2),
                'score_total': round((eficiencia + calidad) / 2, 2)
            }

        except:
            return None

    def _get_quota_compliance(self, vendor_name):
        """
        Get quota compliance from existing VentasAnalyzer.
        """
        try:
            from analyzers import VentasAnalyzer
            analyzer = VentasAnalyzer()
            data = analyzer.get_cumplimiento_cuotas(vendor_name, 'Todos')
            if not data.empty:
                return data['cumplimiento_pct'].iloc[0]
            return 0
        except:
            return 0

    def _calculate_growth_rate(self, vendor_data):
        """
        Calculate growth rate comparing current vs previous month.
        """
        try:
            current_date = datetime.now()
            current_month = current_date.strftime("%Y%m")
            prev_month = (current_date.replace(day=1) -
                          timedelta(days=1)).strftime("%Y%m")

            current_sales = 0
            prev_sales = 0

            for date_key, date_data in vendor_data.items():
                if date_key.startswith(current_month):
                    if 'proveedores' in date_data:
                        for prov_data in date_data['proveedores'].values():
                            current_sales += prov_data.get('v', 0)
                elif date_key.startswith(prev_month):
                    if 'proveedores' in date_data:
                        for prov_data in date_data['proveedores'].values():
                            prev_sales += prov_data.get('v', 0)

            if prev_sales > 0:
                return ((current_sales - prev_sales) / prev_sales) * 100
            return 0
        except:
            return 0

    def _get_return_rate(self, vendor_name):
        """
        Get return rate from existing data.
        """
        try:
            from analyzers import VentasAnalyzer
            analyzer = VentasAnalyzer()
            resumen = analyzer.get_resumen_ventas(vendor_name, 'Todos')
            if resumen['total_ventas'] > 0:
                return (resumen['total_devoluciones'] / resumen['total_ventas']) * 100
            return 0
        except:
            return 0

    def _get_convenios_progress_compliance(self, vendor_name):
        """
        Obtain compliance with agreements based on expected progress.
        """
        try:
            data = \
                self.__ventas_analyzer.get_analisis_convenios(vendor_name)

            if data.empty:
                return 100  # Sin convenios = 100%

            # Comparar progreso actual vs esperado
            cumpliendo = data[data['progreso_meta_pct']
                              >= data['progreso_esperado_pct']]

            if len(data) > 0:
                return (len(cumpliendo) / len(data)) * 100
            return 100

        except Exception as e:
            print(f"Error en convenios: {e}")
            return 100

    def _get_collection_rate(self, vendor_name):
        """
        Get collection rate vs sales.
        """
        try:
            from analyzers import VentasAnalyzer
            analyzer = VentasAnalyzer()

            # Get sales
            resumen = analyzer.get_resumen_ventas(vendor_name, 'Todos')
            total_sales = resumen.get('ventas_netas', 0)

            # Get collections
            total_recaudo = analyzer.get_resumen_recaudo(vendor_name, 'Todos')

            if total_sales > 0:
                return min((total_recaudo / total_sales) * 100, 100)
            return 0
        except:
            return 0

    def get_historical_trends(self, vendedor='Todos', months=6):
        """
        Get historical trends for efficiency and quality metrics
        """
        try:
            # Load data
            analisis_data = self.load_analisis_vendedores()
            if not analisis_data:
                return pd.DataFrame()

            db = self._get_db()
            vendor_codes = db.get_by_path("maestros/codigos_vendedores") or {}
            active_vendors = db.get_by_path(
                "maestros/vendedores_activos") or []

            # Filter to active vendors
            active_vendor_codes = []
            for code, name in vendor_codes.items():
                if name in active_vendors:
                    active_vendor_codes.append(code)

            # Determine vendor to analyze
            if vendedor != 'Todos':
                vendor_name_to_code = {v: k for k, v in vendor_codes.items()}
                vendor_code = vendor_name_to_code.get(vendedor)
                if not vendor_code or vendor_code not in active_vendor_codes:
                    return pd.DataFrame()
                vendors_to_analyze = [(vendor_code, vendedor)]
            else:
                vendors_to_analyze = [(code, vendor_codes.get(code, code))
                                      for code in active_vendor_codes
                                      if code in analisis_data]

            # Get last N months
            current_date = datetime.now()
            months_to_analyze = []
            for i in range(months):
                month_date = current_date - timedelta(days=30*i)
                months_to_analyze.append(month_date.strftime("%Y%m"))

            results = []

            for vendor_code, vendor_name in vendors_to_analyze:
                vendor_data = analisis_data.get(vendor_code, {})

                for month in months_to_analyze:
                    month_metrics = self._calculate_month_metrics(
                        vendor_data, vendor_name, month
                    )
                    if month_metrics:
                        month_metrics['mes'] = month
                        results.append(month_metrics)

            if not results:
                return pd.DataFrame()

            df_results = pd.DataFrame(results)
            df_results['fecha'] = pd.to_datetime(df_results['mes'] + '01')
            df_results = df_results.sort_values(['vendedor', 'fecha'])

            return df_results

        except Exception as e:
            print(f"❌ Error getting historical trends: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _calculate_month_metrics(self, vendor_data, vendor_name, month):
        """
        Calculate metrics for a specific month
        """
        try:
            # Initialize aggregators
            total_sales = 0
            unique_products = set()
            unique_providers = set()
            unique_clients = set()

            # Process daily data for the month
            for date_key, date_data in vendor_data.items():
                if not date_key.startswith(month):
                    continue

                # Process providers
                if 'proveedores' in date_data and date_data['proveedores']:
                    for prov_code, prov_data in date_data['proveedores'].items():
                        unique_providers.add(prov_code)
                        if isinstance(prov_data, dict):
                            total_sales += prov_data.get('v', 0)

                # Process clients
                if 'clientes' in date_data and date_data['clientes']:
                    for client_id in date_data['clientes'].keys():
                        unique_clients.add(client_id)

                # Process products
                if 'producto' in date_data and date_data['producto']:
                    if isinstance(date_data['producto'], dict):
                        for prod_code in date_data['producto'].keys():
                            unique_products.add(prod_code)

            if total_sales == 0:
                return None

            # Calculate simple metrics for historical view
            num_products = len(unique_products)
            num_providers = len(unique_providers)
            num_clients = max(len(unique_clients), 1)

            # Simplified scoring for historical view
            portfolio_score = min((num_products / 100) * 100, 100)
            provider_score = min((num_providers / 20) * 100, 100)
            client_score = min((num_clients / 50) * 100, 100)

            # Simple efficiency and quality scores
            eficiencia = (client_score * 0.5 + 50)  # Simplified
            calidad = (portfolio_score * 0.5 + provider_score * 0.5)

            return {
                'vendedor': vendor_name,
                'eficiencia': round(eficiencia, 2),
                'calidad': round(calidad, 2),
                'score_total': round((eficiencia + calidad) / 2, 2),
                'num_productos': num_products,
                'num_proveedores': num_providers,
                'num_clientes': num_clients,
                'ventas_totales': total_sales
            }

        except Exception as e:
            print(f"❌ Error calculating month metrics: {e}")
            return None

    def get_vendor_ranking(self, metric='score_total', mes="Todos"):
        """
        Get vendor ranking for podium display

        Args:
            metric: 'score_total', 'eficiencia', or 'calidad'

        Returns:
            DataFrame sorted by metric
        """
        try:
            df_metrics = self.calculate_vendor_metrics('Todos', mes)

            if df_metrics.empty:
                return pd.DataFrame()

            # Sort by selected metric
            df_sorted = df_metrics.sort_values(metric, ascending=False)

            # Add ranking
            df_sorted['ranking'] = range(1, len(df_sorted) + 1)

            # Add performance category
            df_sorted['categoria_desempeno'] = df_sorted.apply(
                lambda row: self._categorize_performance(row[metric]), axis=1
            )

            # Add brief analysis for each vendor
            df_sorted['analisis_breve'] = df_sorted.apply(
                lambda row: self._generate_vendor_analysis(row), axis=1
            )

            return df_sorted

        except Exception as e:
            print(f"❌ Error getting vendor ranking: {e}")
            return pd.DataFrame()

    def _categorize_performance(self, score):
        """
        Categorize performance based on score.
        """
        if score >= 85:
            return "🌟 Excelente"
        elif score >= 70:
            return "✅ Bueno"
        elif score >= 50:
            return "⚠️ Regular"
        else:
            return "🔴 Necesita Mejora"

    def _generate_vendor_analysis(self, row):
        """
        Generate brief analysis for vendor.
        """
        analysis_parts = []

        # Analyze efficiency
        if row['eficiencia'] >= 80:
            analysis_parts.append("Alta eficiencia operativa")
        elif row['eficiencia'] >= 60:
            analysis_parts.append("Eficiencia moderada")
        else:
            analysis_parts.append("Baja eficiencia, requiere atención")

        # Analyze quality
        if row['calidad'] >= 80:
            analysis_parts.append("excelente calidad de gestión")
        elif row['calidad'] >= 60:
            analysis_parts.append("calidad aceptable")
        else:
            analysis_parts.append("calidad por mejorar")

        # Identify main strengths
        metrics = {
            'Cuota': row['cumplimiento_cuota'],
            'Portafolio': row['profundidad_portafolio'],
            'Proveedores': row['diversificacion_proveedores'],
            'Recaudo': row['tasa_recaudo']
        }

        best_metric = max(metrics.items(), key=lambda x: x[1])
        worst_metric = min(metrics.items(), key=lambda x: x[1])

        if best_metric[1] >= 80:
            analysis_parts.append(f"Destaca en {best_metric[0].lower()}")

        if worst_metric[1] < 50:
            analysis_parts.append(f"Mejorar {worst_metric[0].lower()}")

        return ". ".join(analysis_parts) + "."

    def get_metric_breakdown(self, vendedor, periodo="Todos", metric_type='eficiencia'):
        """
        Get detailed breakdown of a specific metric

        Args:
            vendedor: Vendor name
            metric_type: 'eficiencia' or 'calidad'

        Returns:
            Dict with breakdown details
        """
        try:
            df_metrics = self.calculate_vendor_metrics(vendedor, periodo)

            if df_metrics.empty:
                return {}

            row = df_metrics.iloc[0]

            if metric_type == 'eficiencia':
                return {
                    'total': row['eficiencia'],
                    'components': [
                        {
                            'name': 'Cumplimiento de Cuota',
                            'value': row['cumplimiento_cuota'],
                            'weight': 50,
                            'contribution': row['cumplimiento_cuota'] * 0.5
                        },
                        {
                            'name': 'Crecimiento en Ventas',
                            'value': row['crecimiento_ventas'],
                            'weight': 30,
                            'contribution': row['crecimiento_ventas'] * 0.3
                        },
                        {
                            'name': 'Cumplimiento de Convenios',
                            'value': row['cumplimiento_convenios'],
                            'weight': 20,
                            'contribution': row['cumplimiento_convenios'] * 0.2
                        }
                    ]
                }
            else:  # calidad
                return {
                    'total': row['calidad'],
                    'components': [
                        {
                            'name': 'Profundidad del Portafolio',
                            'value': row['profundidad_portafolio'],
                            'weight': 35,
                            'contribution': row['profundidad_portafolio'] * 0.35
                        },
                        {
                            'name': 'Diversificación de Proveedores',
                            'value': row['diversificacion_proveedores'],
                            'weight': 20,
                            'contribution': row['diversificacion_proveedores'] * 0.2
                        },
                        {
                            'name': 'Sensibilidad de Clientes',
                            'value': row['sensibilidad_clientes'],
                            'weight': 25,
                            'contribution': row['sensibilidad_clientes'] * 0.25
                        },
                        {
                            'name': 'Control de Devoluciones',
                            'value': row['tasa_devoluciones_inv'],
                            'weight': 5,
                            'contribution': row['tasa_devoluciones_inv'] * 0.05
                        },
                        {
                            'name': 'Tasa de Recaudo',
                            'value': row['tasa_recaudo'],
                            'weight': 15,
                            'contribution': row['tasa_recaudo'] * 0.15
                        }
                    ]
                }

        except Exception as e:
            print(f"❌ Error getting metric breakdown: {e}")
            return {}

    def calculate_vendor_metrics(self, vendedor='Todos', periodo='Todos'):
        """
        Calculate metrics for vendors that appear in cuotas_vendedores
        Using last closed month, not current.
        """
        try:
            analisis_data = self.load_analisis_vendedores()

            if not analisis_data:
                return pd.DataFrame()

            db = self._get_db()

            # Get vendor codes mapping
            vendor_codes = db.get_by_path("maestros/codigos_vendedores") or {}

            # Get vendors from cuotas_vendedores (last month with quotas)
            cuotas_data = db.get("cuotas_vendedores") or {}

            if not cuotas_data:
                return pd.DataFrame()

            # Find the last month in cuotas
            months_in_cuotas = list(cuotas_data.keys())

            if not months_in_cuotas:
                return pd.DataFrame()

            # Sort to get the most recent month
            months_in_cuotas.sort(reverse=True)
            last_quota_month = months_in_cuotas[0]

            # Get vendors from that month
            active_vendors = []

            if last_quota_month in cuotas_data and \
                    isinstance(cuotas_data[last_quota_month], dict):
                active_vendors = list(cuotas_data[last_quota_month].keys())

            # Get vendor codes for active vendors
            active_vendor_codes = []
            vendor_name_to_code = {v: k for k, v in vendor_codes.items()}

            for vendor_name in active_vendors:
                if vendor_name in vendor_name_to_code:
                    active_vendor_codes.append(
                        vendor_name_to_code[vendor_name])

            # Determine vendors to analyze
            if vendedor == 'Todos':
                vendors_to_analyze = active_vendor_codes
            else:
                vendor_code = vendor_name_to_code.get(vendedor)

                if not vendor_code or vendor_code not in active_vendor_codes:
                    return pd.DataFrame()

                vendors_to_analyze = [vendor_code]

            results = []

            for vendor_code in vendors_to_analyze:
                vendor_name = vendor_codes.get(vendor_code, vendor_code)

                if vendor_name not in active_vendors:
                    continue

                vendor_data = analisis_data.get(vendor_code, {})

                metrics = \
                    self._calculate_current_metrics(
                        vendor_data,
                        vendor_name,
                        periodo
                    )

                # if periodo == 'Todos':
                #     metrics = \
                #         self._calculate_current_metrics(
                #             vendor_data,
                #             vendor_name,
                #             periodo
                #         )
                # else:
                #     metrics = \
                #         self._calculate_historical_metrics(
                #             vendor_data,
                #             vendor_name
                #         )

                if metrics:
                    results.append(metrics)

            if not results:
                return pd.DataFrame()

            df = pd.DataFrame(results)

            # AÑADIR SCORE DE VOLUMEN
            if 'ventas_totales' in df.columns:
                # Calcular percentiles de ventas
                df['volume_percentile'] = df['ventas_totales'].rank(
                    pct=True) * 100

                # Actualizar score con volumen (20%)
                df['score'] = (
                    df['score'] * 0.8 +  # 80% del score original
                    df['volume_percentile'] * 0.2  # 20% volumen
                )

                # SCORE TOTAL FINAL: 40% eficiencia, 10% calidad, 50% score
                df['score_total'] = (
                    df['eficiencia'] * 0.40 +
                    df['calidad'] * 0.10 +
                    df['score'] * 0.50
                )

            return df

        except Exception as e:
            print(f"❌ Error calculando métricas: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _calculate_current_metrics(self, vendor_data, vendor_name, periodo):
        """
        Metrics with new weights and corrections.
        """
        try:
            if periodo == "Todos":
                last_month_date = datetime.now()
                last_month = last_month_date.strftime("%Y%m")
            else:
                last_month = periodo.replace("-", "")

            # Aggregators
            monthly_providers = {}
            monthly_clients = {}
            monthly_products = {}
            total_sales = 0
            unique_clients = set()

            # Procesar datos del mes
            for date_key, date_data in vendor_data.items():
                if periodo != "Todos" and not date_key.startswith(last_month):
                    continue

                if 'proveedores' in date_data:
                    for prov_code, value in date_data['proveedores'].items():
                        monthly_providers[prov_code] = monthly_providers.get(
                            prov_code, 0) + value
                        total_sales += value

                if 'clientes' in date_data:
                    for client_id, value in date_data['clientes'].items():
                        monthly_clients[client_id] = monthly_clients.get(
                            client_id, 0) + value
                        unique_clients.add(client_id)

                if 'productos' in date_data:
                    for prod_code, value in date_data['productos'].items():
                        monthly_products[prod_code] = monthly_products.get(
                            prod_code, 0) + value

            # SCORE DE CONCENTRACIÓN/DISPERSIÓN
            score_proveedores = self.calculate_concentration_score(
                monthly_providers)
            score_clientes = self.calculate_concentration_score(
                monthly_clients)
            score_productos = self.calculate_concentration_score(
                monthly_products)

            # VOLUMEN DE VENTAS (nuevo componente del score)

            # INDICADORES BASE
            num_products = len(monthly_products)
            num_providers = len(monthly_providers)
            num_clients = len(unique_clients)

            # 1. CUMPLIMIENTO DE CUOTA (promedio histórico)
            quota_compliance = self._get_average_quota_compliance(vendor_name)

            # 2. CRECIMIENTO PROMEDIO
            avg_growth = self._calculate_average_growth_rate(vendor_data)
            # Normalizar: -20% a +20% → 0 a 100
            growth_score = max(0, min(100, 50 + (avg_growth * 2.5)))

            # 3. CUMPLIMIENTO DE CONVENIOS (progreso actual vs esperado)
            convenios_score = self._get_convenios_progress_compliance(
                vendor_name)

            # 4. TASA DE RECAUDO
            collection_score = self._get_collection_rate(vendor_name)

            # 5. SENSIBILIDAD DE CLIENTES (% de clientes impactados)
            total_assigned = self._get_assigned_clients_count(vendor_name)
            if total_assigned > 0:
                client_coverage = (num_clients / total_assigned) * 100
            else:
                client_coverage = 0

            # 6. PROFUNDIDAD PORTAFOLIO Y PROVEEDORES
            TOTAL_PRODUCTOS = 9018
            TOTAL_PROVEEDORES = 232

            portfolio_percentage = (num_products / TOTAL_PRODUCTOS) * 100
            provider_percentage = (num_providers / TOTAL_PROVEEDORES) * 100

            # 7. TASA DE DEVOLUCIONES
            return_rate = self._get_return_rate(vendor_name)
            return_score = max(0, 100 - (return_rate * 10))  # Penalización 10x

            # CÁLCULO DE INDICADORES COMPUESTOS

            # EFICIENCIA (normalizada)
            eficiencia = (
                quota_compliance * 0.35 +
                growth_score * 0.25 +
                convenios_score * 0.20 +
                collection_score * 0.20
            )

            portfolio_score = min(portfolio_percentage * 100, 100)
            provider_score = min(provider_percentage * 100, 100)
            client_score = min(client_coverage, 100)  # Ya está en porcentaje
            # Penalización por devoluciones
            return_score = max(0, 100 - (return_rate * 10))

            # CALIDAD (ajustada)
            calidad = (
                portfolio_score * 0.35 +      # 35% del peso
                provider_score * 0.20 +        # 20% del peso
                client_score * 0.25 +          # 25% del peso
                return_score * 0.20            # 20% del peso
            )

            # SCORE (sin volumen aún - se añadirá después)
            quality_score = (
                score_productos * 0.35 +   # Reducido de 40%
                score_clientes * 0.30 +    # Reducido de 35%
                score_proveedores * 0.15   # Reducido de 25%
            )

            return {
                'vendedor': vendor_name,
                'eficiencia': round(eficiencia, 2),
                'calidad': round(calidad, 2),
                'score': round(quality_score, 2),
                'score_total': 0,
                'cumplimiento_cuota': round(quota_compliance, 1),
                'crecimiento_ventas': round(avg_growth, 1),
                'cumplimiento_convenios': round(convenios_score, 1),
                'tasa_recaudo': round(collection_score, 1),
                'profundidad_portafolio': round(portfolio_percentage, 1),
                'diversificacion_proveedores': round(provider_percentage, 1),
                'sensibilidad_clientes': round(client_coverage, 1),
                'tasa_devoluciones_inv': round(return_score, 1),
                'score_productos': round(score_productos, 1),
                'score_clientes': round(score_clientes, 1),
                'score_proveedores': round(score_proveedores, 1),
                'num_productos': num_products,
                'num_proveedores': num_providers,
                'num_clientes': num_clients,
                'ventas_totales': total_sales
            }

        except Exception as e:
            print(f"Error en métricas: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_quota_compliance_for_month(self, vendor_name, month):
        """
        Get quota compliance for a specific month
        """
        try:
            from analyzers import VentasAnalyzer
            analyzer = VentasAnalyzer()
            data = analyzer.get_cumplimiento_cuotas(vendor_name, month)
            if not data.empty:
                return data['cumplimiento_pct'].iloc[0]
            return 0
        except:
            return 0

    def get_evolution_data_for_all_vendors(self, months=6):
        """
        Get evolution data showing ALL vendors with consistent calculations
        """
        try:
            analisis_data = self.load_analisis_vendedores()

            if not analisis_data:
                return pd.DataFrame()

            db = self._get_db()
            vendor_codes = db.get_by_path("maestros/codigos_vendedores") or {}

            # Get vendors from cuotas
            cuotas_data = db.get("cuotas_vendedores") or {}

            if not cuotas_data:
                return pd.DataFrame()

            # Get latest month vendors
            months_in_cuotas = sorted(cuotas_data.keys(), reverse=True)

            if not months_in_cuotas:
                return pd.DataFrame()

            last_quota_month = months_in_cuotas[0]
            active_vendors = list(cuotas_data[last_quota_month].keys(
            )) if last_quota_month in cuotas_data else []

            # Map vendor names to codes
            vendor_name_to_code = {v: k for k, v in vendor_codes.items()}

            results = []
            current_date = datetime.now()

            # Process each month
            # Start from 1 to skip current month
            for month_offset in range(0, months):
                month_date = current_date.replace(
                    day=1) - timedelta(days=month_offset * 30)
                month_str = month_date.strftime("%Y%m")

                for vendor_name in active_vendors:
                    vendor_code = vendor_name_to_code.get(vendor_name)
                    if not vendor_code or vendor_code not in analisis_data:
                        continue

                    vendor_data = analisis_data[vendor_code]

                    # Calculate metrics for this month (using same logic as current metrics)
                    metrics = self._calculate_metrics_for_specific_month(
                        vendor_data, vendor_name, month_str
                    )

                    if metrics:
                        metrics['fecha'] = month_date.strftime("%Y-%m-01")
                        results.append(metrics)

            if not results:
                return pd.DataFrame()

            df = pd.DataFrame(results)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values(['vendedor', 'fecha'])

            return df

        except Exception as e:
            print(f"Error getting evolution data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _calculate_metrics_for_specific_month(self, vendor_data, vendor_name, month_str):
        """
        Calculare efficiency, quality and total score metrics for fiven month.
        """
        try:
            monthly_providers = {}
            monthly_clients = {}
            monthly_products = {}
            total_sales = 0

            for date_key, date_data in vendor_data.items():
                if not date_key.startswith(month_str):
                    continue

                if 'proveedores' in date_data:
                    for prov_code, value in date_data['proveedores'].items():
                        monthly_providers[prov_code] = monthly_providers.get(
                            prov_code, 0) + value
                        total_sales += value

                if 'clientes' in date_data:
                    for client_id, value in date_data['clientes'].items():
                        monthly_clients[client_id] = monthly_clients.get(
                            client_id, 0) + value

                if 'productos' in date_data:
                    for prod_code, value in date_data['productos'].items():
                        monthly_products[prod_code] = monthly_products.get(
                            prod_code, 0) + value

            if total_sales == 0:
                return None

            # Calcular scores de concentración
            score_proveedores = self.calculate_concentration_score(
                monthly_providers)
            score_clientes = self.calculate_concentration_score(
                monthly_clients)
            score_productos = self.calculate_concentration_score(
                monthly_products)

            quality_score = (
                score_productos * 0.40 +
                score_clientes * 0.35 +
                score_proveedores * 0.25
            )

            # Simplificado para histórico
            num_products = len(monthly_products)
            num_providers = len(monthly_providers)
            num_clients = len(monthly_clients)

            # Scores simplificados
            TOTAL_PRODUCTOS = 9018
            TOTAL_PROVEEDORES = 232

            portfolio_score = min(
                ((num_products / TOTAL_PRODUCTOS) * 100 / 5) * 100, 100)
            provider_score = min(
                ((num_providers / TOTAL_PROVEEDORES) * 100 / 15) * 100, 100)

            total_assigned = self._get_assigned_clients_count(vendor_name)
            client_score = (num_clients / max(total_assigned, 1)
                            ) * 100 if total_assigned > 0 else 0

            # Simplificado
            eficiencia = 50 + (client_score * 0.2)
            calidad = (portfolio_score * 0.3 + provider_score *
                       0.25 + client_score * 0.25 + 20)

            return {
                'vendedor': vendor_name,
                'eficiencia': round(eficiencia, 2),
                'calidad': round(calidad, 2),
                'score': round(quality_score, 2),
                'score_total': round((eficiencia * 0.3 + calidad * 0.3 + quality_score * 0.4), 2)
            }

        except Exception as e:
            print(f"Error in month metrics: {e}")
            return None

    def calculate_concentration_score(self, sales_dict):
        """
        Score de concentración más realista
        """
        if not sales_dict or len(sales_dict) == 0:
            return 0

        total = sum(sales_dict.values())

        if total == 0:
            return 0

        n = len(sales_dict)

        # Para pocos elementos, penalizar más
        if n <= 3:
            return n * 10  # Máximo 30 puntos para 3 o menos

        # Calcular entropía normalizada (mejor que HHI para este caso)
        shares = [val/total for val in sales_dict.values()]
        entropy = -sum([s * np.log(s) for s in shares if s > 0])
        max_entropy = np.log(n)

        # Normalizar entropía a escala 0-100
        if max_entropy > 0:
            normalized_entropy = (entropy / max_entropy) * 100
        else:
            normalized_entropy = 0

        # Ajustar por número de elementos (premiar diversidad)
        # Hasta 20 puntos extra por tener 20+ elementos
        diversity_bonus = min(n / 20, 1) * 20

        score = normalized_entropy * 0.8 + diversity_bonus

        return min(100, score)

    def calculate_quality_score(self, vendor_data, date_key):
        """
        Calculate the quality score based on sales distribution
        """
        try:
            if date_key not in vendor_data:
                return 0

            day_data = vendor_data[date_key]

            # Calcular scores de concentración para cada dimensión
            proveedor_score = self.calculate_concentration_score(
                day_data.get('proveedores', {})
            )
            cliente_score = self.calculate_concentration_score(
                day_data.get('clientes', {})
            )
            producto_score = self.calculate_concentration_score(
                day_data.get('productos', {})
            )

            # Quality score weighting
            quality_score = (
                producto_score * 0.40 +  # 40% - Diversidad de productos
                cliente_score * 0.35 +   # 35% - Diversidad de clientes
                proveedor_score * 0.25   # 25% - Diversidad de proveedores
            )

            return round(quality_score, 2)

        except Exception as e:
            print(f"Error calculando quality score: {e}")
            return 0

    def _get_average_quota_compliance(self, vendor_name):
        """
        Obtain historical average compliance with fee
        """
        try:
            from analyzers import VentasAnalyzer
            analyzer = VentasAnalyzer()

            # Obtener últimos 6 meses
            total_compliance = 0
            months_count = 0

            for i in range(6):
                month_date = datetime.now() - timedelta(days=30*i)
                month_str = month_date.strftime("%Y-%m")

                data = analyzer.get_cumplimiento_cuotas(vendor_name, month_str)

                if not data.empty:
                    total_compliance += data['cumplimiento_pct'].iloc[0]
                    months_count += 1

            if months_count > 0:
                return total_compliance / months_count

            return 0

        except Exception as e:
            print(f"Error getting average quota compliance: {e}")
            return 0
