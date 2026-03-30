import streamlit as st
import pandas as pd
import pyodbc

# -------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------
st.set_page_config(layout="wide")
st.title("💊 Dashboard Farmácia - Gestão de Saúde")

# -------------------------------
# CONEXÃO COM BANCO (SQL SERVER)
# -------------------------------


# -------------------------------
# CARREGAR DADOS
# -------------------------------
@st.cache_data
def carregar_dados():
    query = """
SELECT 
    d.data_hora_dispensacao,
    d.quantidade,
    d.preco_medio AS preco_dispensacao,
    (d.quantidade * d.preco_medio) AS custo_total,
    d.nome_medicamento AS produto,
    u.nome_unidade AS unidade,
    m.nome_municipio AS municipio,
    e.estoque_atual,
    e.preco_medio AS preco_estoque
FROM dispensacoes_analitica d
LEFT JOIN dim_unidade u 
    ON d.codigo_unidade_fornec = u.codigo_unidade
LEFT JOIN dim_municipio m 
    ON d.codigo_municipio = m.codigo_municipio
LEFT JOIN dados_estoque e 
    ON d.codigo_produto = e.codigo_produto limit 10
    """
    df = pd.read_sql(query, conn)
    df["data_hora_dispensacao"] = pd.to_datetime(df["data_hora_dispensacao"])
    return df

df = carregar_dados()

# -------------------------------
# SIDEBAR - FILTROS
# -------------------------------
st.sidebar.header("🎛️ Filtros")

# filtro unidade
lista_unidades = ["Todas"] + sorted(df["unidade"].dropna().unique())
unidade = st.sidebar.selectbox("Unidade", lista_unidades)

# filtro município
lista_municipios = ["Todos"] + sorted(df["municipio"].dropna().unique())
municipio = st.sidebar.selectbox("Município", lista_municipios)

# filtro data
data_inicio = st.sidebar.date_input("Data início", df["data_hora_dispensacao"].min())
data_fim = st.sidebar.date_input("Data fim", df["data_hora_dispensacao"].max())

# -------------------------------
# APLICAR FILTROS
# -------------------------------
df_filtrado = df.copy()

if unidade != "Todas":
    df_filtrado = df_filtrado[df_filtrado["unidade"] == unidade]

if municipio != "Todos":
    df_filtrado = df_filtrado[df_filtrado["municipio"] == municipio]

df_filtrado = df_filtrado[
    (df_filtrado["data_hora_dispensacao"] >= pd.to_datetime(data_inicio)) &
    (df_filtrado["data_hora_dispensacao"] <= pd.to_datetime(data_fim))
]

# -------------------------------
# KPIs
# -------------------------------
total_dispensado = df_filtrado["quantidade"].sum()
total_custo = df_filtrado["custo_total"].sum()
total_atendimentos = df_filtrado.shape[0]
media = df_filtrado["quantidade"].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("💊 Total dispensado", f"{total_dispensado:,.0f}")
col2.metric("💰 Custo total", f"R$ {total_custo:,.2f}")
col3.metric("👥 Atendimentos", f"{total_atendimentos}")
col4.metric("📊 Média por atendimento", f"{media:,.2f}")

# -------------------------------
# GRÁFICOS
# -------------------------------

# TOP UNIDADES
st.subheader("🏆 Total dispensado por unidade")

df_unidade = (
    df_filtrado.groupby("unidade")["quantidade"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(df_unidade)

# CUSTO POR UNIDADE
st.subheader("💰 Custo por unidade")

df_custo = (
    df_filtrado.groupby("unidade")["custo_total"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(df_custo)

# -------------------------------
# MUNICÍPIOS
# -------------------------------
st.subheader("🌍 Dispensação por município")

df_municipio = (
    df_filtrado.groupby("municipio")
    .agg({"quantidade": "sum", "custo_total": "sum"})
    .sort_values(by="quantidade", ascending=False)
)

st.dataframe(df_municipio)

# -------------------------------
# ESTOQUE / PRODUTOS
# -------------------------------
st.subheader("📦 Produtos mais dispensados")

df_produtos = (
    df_filtrado.groupby("produto")["quantidade"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.dataframe(df_produtos)

# -------------------------------
# INSIGHT AUTOMÁTICO
# -------------------------------
if not df_filtrado.empty:
    top_produto = df_produtos.index[0]
    st.success(f"🔝 Produto mais dispensado: {top_produto}")
