# map_utils.py - Utilidades para crear mapas
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def get_map_styles():
    """
    Obtener todos los estilos de mapa disponibles.
    """
    return \
        {
            'carto-positron': 'Tema Claro',
            'open-street-map': 'Calles',
            'carto-darkmatter': 'Tema Oscuro'
        }


def get_region_centers():
    """
    Obtener centros y zoom para diferentes regiones.
    """
    return \
        {
            'Colombia': {
                'center': {'lat': 4.5709, 'lon': -74.2973},
                'zoom': 5
            },
            'Antioquia': {
                'center': {'lat': 6.8, 'lon': -75.3},
                'zoom': 8
            },
            'Medellín': {
                'center': {'lat': 6.2442, 'lon': -75.5812},
                'zoom': 11
            }
        }


def create_mapa_ventas(data, region_filter, map_style, theme='light'):
    """
    Crear mapa de ventas con diferentes tipos de visualización.

    Args:
        data: DataFrame con datos de ventas y coordenadas
        region_filter: 'Colombia', 'Antioquia', 'Medellín'
        map_style: Estilo del mapa
        theme: Tema del dashboard ('light' o 'dark')
    """
    if data.empty:
        # Crear mapa vacío
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de ventas con coordenadas disponibles",
            xref="paper",
            yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='#7f8c8d')
        )

        region_config = get_region_centers()[region_filter]
        fig.update_layout(
            height=500,
            mapbox=dict(
                style=map_style,
                center=region_config['center'],
                zoom=region_config['zoom']
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        return fig

    # Obtener configuración regional
    region_config = get_region_centers()[region_filter]

    if region_filter == 'Antioquia':
        data_filtered = data[data['departamento'].str.contains(
            'Antioquia', case=False, na=False)]
    elif region_filter == 'Medellín':
        data_filtered = data[data['ciudad'].str.contains(
            'Medellín|Medellin', case=False, na=False)]
    else:
        data_filtered = data

    # Si después del filtrado no hay datos, mostrar mapa vacío
    if data_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No hay datos disponibles para {region_filter}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='#7f8c8d')
        )

        fig.update_layout(
            height=500,
            mapbox=dict(
                style=map_style,
                center=region_config['center'],
                zoom=region_config['zoom']
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        return fig

    # Crear mapa según tipo de puntos
    fig = go.Figure()

    # Scatter plot con puntos circulares
    max_ventas = data['total_ventas'].max()
    min_ventas = data['total_ventas'].min()

    # Tamaños entre 8 y 50 píxeles
    if max_ventas > min_ventas:
        sizes = 8 + (data['total_ventas'] - min_ventas) / \
            (max_ventas - min_ventas) * 42
    else:
        sizes = [25] * len(data)  # Tamaño fijo si todos son iguales

    fig.add_trace(go.Scattermapbox(
        lat=data['lat'],
        lon=data['long'],
        mode='markers',
        marker=dict(
            size=sizes,
            color=data['total_ventas'],
            colorscale='Jet_r',
            opacity=0.6,
            sizemode='diameter'
        ),
        text=data['hover_text'],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False
    ))

    # Configurar layout del mapa
    fig.update_layout(
        mapbox=dict(
            style=map_style,
            center=region_config['center'],
            zoom=region_config['zoom']
        ),
        height=500,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )

    return fig


def create_map_controls_layout(page_name: str):
    """
    Crear layout de controles para el mapa.
    """
    from dash import dcc, html

    region_options = [
        {'label': 'Colombia', 'value': 'Colombia'},
        {'label': 'Antioquia', 'value': 'Antioquia'},
        {'label': 'Medellín', 'value': 'Medellín'}
    ]

    # Obtener estilos disponibles
    map_styles = get_map_styles()
    estilo_options = [
        {'label': label, 'value': value}
        for value, label in map_styles.items()
    ]

    return html.Div([
        # Controles en una fila
        html.Div([
            # Región
            html.Div([
                html.Label("📍 Región:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '8px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id=f'{page_name}-mapa-dropdown-region',
                    options=region_options,
                    value='Colombia',
                    style={'fontFamily': 'Inter', 'minWidth': '130px'},
                    className='modern-dropdown',
                    clearable=False
                )
            ], style={'flex': '0 0 130px', 'marginRight': '15px'}),

            # Estilo del mapa
            html.Div([
                html.Label("🗺️ Estilo del Mapa:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '8px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id=f'{page_name}-mapa-dropdown-estilo',
                    options=estilo_options,
                    value='carto-positron',
                    style={'fontFamily': 'Inter', 'minWidth': '200px'},
                    className='modern-dropdown',
                    clearable=False
                )
            ], style={'flex': '0 0 200px'})

        ], style={
            'display': 'flex',
            'alignItems': 'flex-end',
            'marginBottom': '20px',
            'flexWrap': 'wrap',
            'gap': '10px'
        })
    ])


def create_full_map_section(page_name: str):
    """
    Crear sección completa del mapa incluyendo controles y gráfico.
    """
    from dash import dcc, html

    return html.Div([
        html.H3("Geolocalización de Clientes", style={
            'textAlign': 'center',
            'marginBottom': '20px',
            'fontFamily': 'Inter'
        }),

        # Controles
        create_map_controls_layout(page_name),

        # Mapa
        dcc.Graph(
            id=f'mapa-{page_name}-clientes',
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                'scrollZoom': True
            }
        )

    ], style={
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'margin': '10px 0'
    }, id=f'{page_name}-mapa-row-container')
