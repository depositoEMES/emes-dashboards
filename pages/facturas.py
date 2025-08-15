from dash import dcc, html

layout = html.Div([
    html.Div([
        # Header con navegación
        html.Div([
            html.Div([
                dcc.Link("← Volver al Dashboard", href="/dashboard",
                         className="back-link"),
                html.H1("Gestión de Facturas", className="page-title"),
                html.P("Análisis y seguimiento de facturas",
                       className="page-subtitle")
            ], className="page-header"),
        ], className="header-container"),

        # Contenido principal - Cards de selección
        html.Div([
            # Card Proveedores
            html.Div([
                html.Div([
                    html.Div("📦", className="card-icon"),
                    html.H3("Facturas de Proveedores",
                            className="selection-card-title"),
                    html.P("Análisis de facturas vs órdenes de compra, liquidación y seguimiento de pagos.",
                           className="selection-card-description")
                ], className="selection-card-content"),
                html.Div([
                    dcc.Link("Acceder", href="/facturas/proveedores",
                             className="selection-card-button")
                ], className="selection-card-actions")
            ], className="selection-card proveedores-selection"),

            # Card Clientes
            html.Div([
                html.Div([
                    html.Div("🏥", className="card-icon"),
                    html.H3("Facturas de Clientes",
                            className="selection-card-title"),
                    html.P("Gestión de facturación a clientes, seguimiento de pagos y cartera.",
                           className="selection-card-description")
                ], className="selection-card-content"),
                html.Div([
                    dcc.Link("Próximamente", href="#",
                             className="selection-card-button disabled")
                ], className="selection-card-actions")
            ], className="selection-card clientes-selection"),
        ], className="selection-grid"),

        # Información adicional
        html.Div([
            html.H4("📋 Funcionalidades Disponibles", className="info-title"),
            html.Div([
                html.Div([
                    html.H5("🔍 Análisis Detallado"),
                    html.P(
                        "Comparación automática entre facturas recibidas y órdenes de compra generadas.")
                ], className="feature-item"),
                html.Div([
                    html.H5("💰 Cálculo de Diferencias"),
                    html.P(
                        "Identificación automática de diferencias de precios y generación de notas.")
                ], className="feature-item"),
                html.Div([
                    html.H5("📊 Reportes en Tiempo Real"),
                    html.P(
                        "Información actualizada directamente desde la base de datos Firebase.")
                ], className="feature-item"),
                html.Div([
                    html.H5("📅 Filtros Avanzados"),
                    html.P(
                        "Filtrado por fechas, proveedores y estados de facturación.")
                ], className="feature-item")
            ], className="features-grid")
        ], className="info-section")
    ], className="facturas-container")
])
