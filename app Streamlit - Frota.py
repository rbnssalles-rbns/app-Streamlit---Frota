#!/usr/bin/env python
# coding: utf-8

# In[2]:


# ================================
# app Streamlit - Frota
# ================================
import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# -------------------------------
# 1. Geração de dados simulados
# -------------------------------
@st.cache_data
def gerar_dados(num_registros=1500, num_veiculos=20):
    inicio = datetime(2025, 7, 1)
    fim = datetime(2025, 12, 31)
    tipos_evento = ["Operação", "Manutenção Preventiva", "Manutenção Corretiva", "Sinistro"]

    def random_date(start, end):
        return start + timedelta(days=random.randint(0, (end-start).days))

    dados = []
    for i in range(num_registros):
        veiculo = f"V{str(random.randint(1, num_veiculos)).zfill(3)}"
        data = random_date(inicio, fim)
        km = round(np.random.normal(120, 30), 1)
        consumo = round(km / np.random.uniform(8, 12), 2)
        evento = np.random.choice(tipos_evento, p=[0.75, 0.1, 0.1, 0.05])
        custo, descricao = 0, ""

        if evento == "Operação":
            custo = round(consumo * 6.5, 2)
            descricao = "Rodagem diária"
        elif evento == "Manutenção Preventiva":
            custo = random.randint(300, 800)
            descricao = "Troca de óleo / revisão"
        elif evento == "Manutenção Corretiva":
            custo = random.randint(500, 3000)
            descricao = "Reparo mecânico inesperado"
        elif evento == "Sinistro":
            custo = random.randint(1000, 10000)
            descricao = "Colisão / avaria"

        dados.append([data, veiculo, km, consumo, evento, custo, descricao])

    df = pd.DataFrame(dados, columns=[
        "Data", "Veiculo_ID", "Km_rodado", "Consumo_combustivel",
        "Tipo_evento", "Custo_evento", "Descricao_evento"
    ]).sort_values("Data").reset_index(drop=True)
    return df

df_frota = gerar_dados()

# -------------------------------
# 2. Sidebar - filtros
# -------------------------------
st.sidebar.header("Filtros")
veiculo_sel = st.sidebar.selectbox("Selecione o veículo", ["Todos"] + list(df_frota["Veiculo_ID"].unique()))
periodo = st.sidebar.date_input("Período", [df_frota["Data"].min(), df_frota["Data"].max()])

df_filtrado = df_frota.copy()
if veiculo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Veiculo_ID"] == veiculo_sel]
if isinstance(periodo, list) and len(periodo) == 2:
    df_filtrado = df_filtrado[(df_filtrado["Data"] >= periodo[0]) & (df_filtrado["Data"] <= periodo[1])]

# -------------------------------
# 3. Módulo de Eficiência
# -------------------------------
st.header("📊 Eficiência da Frota")
df_operacao = df_filtrado[df_filtrado["Tipo_evento"] == "Operação"]
if not df_operacao.empty:
    df_operacao["Custo_km"] = df_operacao["Custo_evento"] / df_operacao["Km_rodado"]

    eficiencia = df_operacao.groupby("Veiculo_ID").agg({
        "Km_rodado":"sum",
        "Consumo_combustivel":"sum",
        "Custo_evento":"sum"
    })
    eficiencia["Km_por_litro"] = eficiencia["Km_rodado"] / eficiencia["Consumo_combustivel"]
    eficiencia["Custo_por_km"] = eficiencia["Custo_evento"] / eficiencia["Km_rodado"]

    # Formatar custo/km como moeda
    eficiencia["Custo_por_km"] = eficiencia["Custo_por_km"].apply(lambda x: f"R${x:,.2f}")
    eficiencia["Custo_evento"] = eficiencia["Custo_evento"].apply(lambda x: f"R${x:,.2f}")

    st.dataframe(eficiencia)
else:
    st.info("Nenhum dado de operação disponível para os filtros selecionados.")

# -------------------------------
# 4. Módulo de Manutenção
# -------------------------------
st.header("🔧 Manutenções")
df_manutencao = df_filtrado[df_filtrado["Tipo_evento"].str.contains("Manutenção")]
if not df_manutencao.empty:
    manutencao_stats = df_manutencao.groupby("Tipo_evento").agg({
        "Custo_evento":"mean",
        "Veiculo_ID":"count"
    }).rename(columns={"Veiculo_ID":"Qtd_eventos"})
    manutencao_stats["Custo_evento"] = manutencao_stats["Custo_evento"].apply(lambda x: f"R${x:,.2f}")
    st.dataframe(manutencao_stats)
else:
    st.info("Nenhum dado de manutenção disponível para os filtros selecionados.")

# -------------------------------
# 5. Módulo de Sinistros
# -------------------------------
st.header("🚨 Sinistros")
df_sinistros = df_filtrado[df_filtrado["Tipo_evento"] == "Sinistro"]
if not df_sinistros.empty:
    sinistros_stats = df_sinistros.groupby("Veiculo_ID").agg({
        "Custo_evento":"sum",
        "Data":"count"
    }).rename(columns={"Data":"Qtd_sinistros"})
    sinistros_stats["Custo_evento"] = sinistros_stats["Custo_evento"].apply(lambda x: f"R${x:,.2f}")
    st.dataframe(sinistros_stats)
else:
    st.info("Nenhum dado de sinistro disponível para os filtros selecionados.")

# -------------------------------
# 6. Painel de Indicadores
# -------------------------------
st.header("📌 Painel de Indicadores")

df_operacao_f = df_filtrado[df_filtrado["Tipo_evento"] == "Operação"]
df_manutencao_f = df_filtrado[df_filtrado["Tipo_evento"].str.contains("Manutenção")]
df_sinistros_f = df_filtrado[df_filtrado["Tipo_evento"] == "Sinistro"]

kpi = {
    "Custo total combustível": f"R${df_operacao_f['Custo_evento'].sum():,.2f}",
    "Custo total manutenções": f"R${df_manutencao_f['Custo_evento'].sum():,.2f}",
    "Custo total sinistros": f"R${df_sinistros_f['Custo_evento'].sum():,.2f}",
    "Km total rodado": round(df_operacao_f["Km_rodado"].sum(),2),
    "Média km/l": round(df_operacao_f["Km_rodado"].sum() / df_operacao_f["Consumo_combustivel"].sum(),2) if len(df_operacao_f)>0 else 0,
    "Qtd manutenções preventivas": len(df_filtrado[df_filtrado["Tipo_evento"]=="Manutenção Preventiva"]),
    "Qtd manutenções corretivas": len(df_filtrado[df_filtrado["Tipo_evento"]=="Manutenção Corretiva"]),
    "Qtd sinistros": len(df_sinistros_f)
}

cols = st.columns(4)
for i, (k,v) in enumerate(kpi.items()):
    cols[i % 4].metric(label=k, value=v)


# In[ ]:




