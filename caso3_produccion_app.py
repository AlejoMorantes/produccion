
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# ① Configuración
st.set_page_config(page_title='Produccion Fabrica Dashboard', 
                   layout='wide', initial_sidebar_state='expanded')

# ② Carga de datos con caché
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso3_produccion_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_produccion'] = pd.to_datetime(df['fecha_produccion'])
    return df

df = cargar_datos()

# ── Sidebar  filtros ───────────────────────────────────────
with st.sidebar:
    st.header("🔧 Filtros")

with st.sidebar: 
    st.header("🔧 Filtros")
    anio = st.multiselect("Año de Producción",
    sorted(df["fecha_produccion"].dt.year.unique()),
    list(df["fecha_produccion"].dt.year.unique())
    )

    maquina = st.multiselect("Máquina",
    sorted(df["maquina"].unique()),
    list(df["maquina"].unique())
    )
    linea_produccion =  st.multiselect("Línea",
    sorted(df["linea_produccion"].unique()),
    list(df["linea_produccion"].unique())
    )


# ── Aplicar filtros globales ──────────────────────
df_f = df.copy()

if anio:
    df_f = df_f[df_f['fecha_produccion'].dt.year.isin(anio)]
if maquina:
    df_f = df_f[df_f['maquina'].isin(maquina)]
if linea_produccion:
    df_f = df_f[df_f['linea_produccion'].isin(linea_produccion)] 
                                    

# ⑤ Título
st.title(" Dashboard de Producción")
st.markdown("**Panel de control de ventas**")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

total_produccion = df_f['unidades_producidas'].sum()
tasa_defectuosos = df["tasa_defectos_pct"].mean()
cumplimiento = ((df["unidades_producidas"] - df["unidades_defectuosas"]) / df["unidades_planificadas"] * 100).clip(upper=100)
pct_cumplimiento = cumplimiento.mean()
df["sobre_produccion"] = np.where(
    df["unidades_producidas"] > df["unidades_planificadas"],
    ((df["unidades_producidas"] - df["unidades_planificadas"]) / df["unidades_planificadas"]) * 100,
    np.nan
)
promedio_sobreproduccion = df["sobre_produccion"].mean()
tiempo_ciclo_promedio = df["tiempo_ciclo_min"].mean()
tiempo_paro_promedio = df["tiempo_paro_min"].mean()
costo_prodiccon_total = df["costo_produccion_cop"].sum()

with col1:
    st.metric("Total Producción", f"{total_produccion:,.0f}")
    st.metric("% Sobreproducción Promedio", f"{promedio_sobreproduccion:.2f}%")

with col2:
    st.metric("Promedio Tasa de Defectos", f"{tasa_defectuosos:.2f}%")
    st.metric("Tiempo de Ciclo Promedio", f"{tiempo_ciclo_promedio:.2f} min")

with col3:
    st.metric("% Cumplimiento Promedio", f"{pct_cumplimiento:.2f}%")
    st.metric("Tiempo de Paro Promedio", f"{tiempo_paro_promedio:.2f} min")

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Costo de Producción Total", f"${costo_prodiccon_total:,.0f}")

st.markdown("---")
st.markdown("---")



# FUnciones de gráficos
# grafico 1 col 1:
total_produccion = df_f['unidades_producidas'].sum()
produccion_por_producto = (
    df_f.groupby('producto')
        .agg(unidades_producidas=('unidades_producidas', 'sum'))  # suma por producto
        .sort_values('unidades_producidas', ascending=False)      # ordenar de mayor a menor
        .reset_index())
produccion_por_producto['porcentaje'] = (
    produccion_por_producto['unidades_producidas'] / total_produccion * 100)
produccion_por_producto = (
    df_f.groupby('producto')
        .agg(unidades_producidas=('unidades_producidas', 'sum'))  # suma por producto
        .sort_values('unidades_producidas', ascending=False)      # ordenar de mayor a menor
        .reset_index()
)
produccion_por_producto['porcentaje'] = (
    produccion_por_producto['unidades_producidas'] / total_produccion * 100
)

# grafico 2 col 2
total_defectuosas = df_f['unidades_defectuosas'].sum()
defectuosas_por_producto = (
    df_f.groupby('producto')
        .agg(unidades_defectuosas=('unidades_defectuosas', 'sum'))
        .sort_values('unidades_defectuosas', ascending=False)
        .reset_index()
)
defectuosas_por_producto['porcentaje'] = (
    defectuosas_por_producto['unidades_defectuosas'] / total_defectuosas * 100
)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# grafico 3 col 3
causas_paro = (
    df_f.groupby('causa_paro')
        .agg(frecuencia=('causa_paro', 'size'))
        .sort_values('frecuencia', ascending=False)
        .reset_index()
)

causas_paro['porcentaje_acumulado'] = (
    causas_paro['frecuencia'].cumsum() / causas_paro['frecuencia'].sum() * 100
)



#grafico 4 col 4
df_f['costo_unitario'] = df_f['costo_produccion_cop'] / df_f['unidades_producidas']



# grafico 5 col 5
df_mensual = (
    df_f.assign(mes=df_f['fecha_produccion'].dt.to_period('M').dt.to_timestamp())
        .groupby('mes')
        .agg(
            unidades_planificadas=('unidades_planificadas', 'sum'),
            unidades_producidas=('unidades_producidas', 'sum'),
            unidades_defectuosas=('unidades_defectuosas', 'sum')
        )
        .reset_index()
)


# ⑦ Fila 1: línea + pie (patrón Z)
col1, col2= st.columns([1.5, 1])
with col1:

    fig = px.pie(
        produccion_por_producto,
        names='producto',
        values='unidades_producidas',
        title='🥧 % de Unidades Producidas por Producto',
        labels={
            'producto': 'Producto',
            'unidades_producidas': 'Unidades Producidas'
        },
        color_discrete_sequence=px.colors.sequential.Teal,
        hole=0
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>'
                      'Unidades: %{value:,.0f}<br>'
                      'Porcentaje: %{percent}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)


with col2:

    fig = px.treemap(
        defectuosas_por_producto,
        path=[px.Constant('Unidades Defectuosas'), 'producto'],
        values='unidades_defectuosas',
        title='⚠️ Distribución de Unidades Defectuosas por Producto',
        color='unidades_defectuosas',
        color_continuous_scale='Reds',
        labels={
            'producto': 'Producto',
            'unidades_defectuosas': 'Unidades Defectuosas'
        }
    )

    fig.update_traces(
        textinfo='label+value+percent root',
        hovertemplate='<b>%{label}</b><br>'
                      'Defectuosas: %{value:,.0f}<br>'
                      'Porcentaje: %{percentRoot:.1%}<extra></extra>'
    )

    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10))

    st.plotly_chart(fig, use_container_width=True)




# ⑧ Fila 2: barras + scatter (patrón Z invertido)
col3, col4 = st.columns([1, 1.5])
with col3:

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=causas_paro['causa_paro'],
            y=causas_paro['frecuencia'],
            name='Frecuencia',
            marker=dict(
                color=causas_paro['frecuencia'],
                colorscale='Oranges',
                line=dict(color='white', width=1)
            ),
            text=causas_paro['frecuencia'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Frecuencia: %{y:,.0f}<extra></extra>'
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=causas_paro['causa_paro'],
            y=causas_paro['porcentaje_acumulado'],
            name='% Acumulado',
            mode='lines+markers+text',
            line=dict(color='firebrick', width=3),
            marker=dict(size=9),
            text=[f'{v:.1f}%' for v in causas_paro['porcentaje_acumulado']],
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>'
        ),
        secondary_y=True
    )

    fig.add_hline(
        y=80,
        line_dash='dash',
        line_color='gray',
        annotation_text='80%',
        annotation_position='top left',
        secondary_y=True
    )

    fig.update_layout(
        title='📊 Pareto de Causas de Paro',
        xaxis_title='Causa del Paro',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(t=80)
    )

    fig.update_yaxes(title_text='Frecuencia', secondary_y=False)
    fig.update_yaxes(
        title_text='% Acumulado',
        secondary_y=True,
        range=[0, 110],
        ticksuffix='%'
    )

    st.plotly_chart(fig, use_container_width=True)

    
with col4:

    fig = px.violin(
        df_f,
        x='producto',
        y='costo_unitario',
        color='producto',
        box=True,
        points='outliers',
        title='🎻 Distribución del Costo Unitario por Producto',
        labels={
            'producto': 'Producto',
            'costo_unitario': 'Costo Unitario (COP)'
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        spanmode='hard',
        hovertemplate='<b>%{x}</b><br>'
                      'Costo unitario: %{y:,.2f}<extra></extra>'
    )

    y_max = df_f['costo_unitario'].max() * 1.05

    fig.update_layout(
        showlegend=False,
        xaxis_title='Producto',
        yaxis_title='Costo Unitario (COP)',
        yaxis=dict(range=[0, y_max])
    )

    st.plotly_chart(fig, use_container_width=True)

# figura 5
fig5 = go.Figure()

fig5.add_trace(go.Scatter(
    x=df_mensual['mes'],
    y=df_mensual['unidades_planificadas'],
    name='Planificadas',
    mode='lines',
    fill='tozeroy',
    line=dict(color='#4C78A8', width=2),
    fillcolor='rgba(76, 120, 168, 0.35)',
    hovertemplate='%{y:,.0f}<extra>Planificadas</extra>'
))

fig5.add_trace(go.Scatter(
    x=df_mensual['mes'],
    y=df_mensual['unidades_producidas'],
    name='Producidas',
    mode='lines',
    fill='tozeroy',
    line=dict(color='#54A24B', width=2),
    fillcolor='rgba(84, 162, 75, 0.35)',
    hovertemplate='%{y:,.0f}<extra>Producidas</extra>'
))

fig5.add_trace(go.Scatter(
    x=df_mensual['mes'],
    y=df_mensual['unidades_defectuosas'],
    name='Defectuosas',
    mode='lines',
    fill='tozeroy',
    line=dict(color='#E45756', width=2),
    fillcolor='rgba(228, 87, 86, 0.35)',
    hovertemplate='%{y:,.0f}<extra>Defectuosas</extra>'
))

fig5.update_layout(
    title='📈 Distribución Mensual: Planificadas vs Producidas vs Defectuosas',
    xaxis_title='Mes',
    yaxis_title='Unidades',
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    xaxis=dict(tickformat='%b %Y')
)

st.plotly_chart(fig5, use_container_width=True)


# ⑩ Tabla colapsable
with st.expander("📋 Ver datos filtrados"):
    st.dataframe(df_f.sort_values('fecha_produccion', ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar CSV", df_f.to_csv(index=False), "produccion.csv")

st.caption("🔧 Streamlit + Plotly | Clase de Visualización de Datos")
