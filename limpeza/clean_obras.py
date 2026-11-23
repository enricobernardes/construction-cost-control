"""Gera as tabelas finais do projeto construction-cost-control.

Uso: python3 -I clean_obras.py <pasta_raw> <pasta_dados_saida>
Saídas: obras.csv, itens.csv, evolucao_mensal.csv
"""
import os
import sys

import numpy as np
import pandas as pd

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

DESC_PT = {
    11: "Topografia de obra", 12: "Topografia as-built", 13: "Ensaios de qualidade",
    15: "Localização de interferências", 16: "Aluguel de GPS", 21: "Limpeza do terreno (estoque)",
    22: "Bota-fora de limpeza", 23: "Trituração de vegetação", 31: "Raspagem de solo vegetal",
    32: "Bota-fora de solo vegetal", 33: "Reespalhamento de solo vegetal", 41: "Demolições",
    51: "Corte e aterro", 52: "Aterro com material estocado", 53: "Corte com bota-fora",
    54: "Corte para estoque", 55: "Aterro geral", 57: "Troca de solo inadequado",
    59: "Acabamento de áreas não pavimentadas", 61: "Preparo do subleito",
    62: "Base de brita compactada", 63: "Regularização das camadas", 64: "Imprimação / tratamento superficial",
    65: "Asfalto (CBUQ)", 66: "Sinalização horizontal", 67: "Sinalização e mobiliário viário",
    68: "Estabilização de solo in situ", 71: "Meio-fio e sarjeta", 72: "Cabeceiras de concreto",
    73: "Calçadas", 75: "Corte e selagem de juntas", 81: "Tubos de drenagem > 450 mm",
    82: "Tubos de drenagem 525–750 mm", 85: "Bocas de lobo e poços de visita",
    86: "Drenagem subempreitada", 87: "Drenagem subterrânea", 88: "Limpeza de valetas",
    91: "Tubos de chorume", 95: "Esgoto (subempreitada)", 103: "Rede de água (subempreitada)",
    110: "Elétrica e telecom", 111: "Eletrodutos e caixas", 112: "Eletrodutos (subempreitada)",
    113: "Elétrica (subempreitada)", 120: "Paisagismo (subempreitada)", 121: "Paisagismo (subempreitada)",
    123: "Mobiliário urbano", 131: "Cercas (subempreitada)", 132: "Muros de arrimo (subempreitada)",
    134: "Aluguel de tapume", 135: "Fundação de muro de arrimo", 141: "Controladores de tráfego",
    142: "Aluguel de dispositivos de tráfego", 151: "Barreiras de sedimento", 152: "Dispositivos de segurança",
    161: "Geotêxtil de proteção", 162: "Geotêxtil de separação", 181: "Galerias celulares",
    182: "Lajes de base", 191: "Serviços por administração", 201: "Não conformidade (retrabalho)",
    220: "Serviços de proteção", 221: "Serviços por administração", 222: "Manta de PEAD",
    223: "Manta GCL", 224: "Brita de drenagem", 510: "Compactação de alta energia",
    613: "Entrega de brita para base", 901: "Gerenciamento do projeto", 902: "Supervisão da obra",
    903: "Instalações do canteiro", 904: "Seguros, taxas e licenças", 905: "Ferramentas pequenas",
    906: "Contingência", 907: "Mobilização do canteiro", 908: "EPI", 910: "Desmobilização e limpeza",
    911: "Alojamento", 913: "Paralisação por chuva", 914: "Treinamento", 915: "Manutenção",
    916: "Administração do canteiro",
}


def grupo(w):
    if w in (91, 222, 223, 224):
        return "Impermeabilização (aterro)"
    if w >= 900:
        return "Custos indiretos"
    if 10 <= w < 20:
        return "Topografia e qualidade"
    if 20 <= w < 40:
        return "Limpeza e solo vegetal"
    if 40 <= w < 50:
        return "Demolição"
    if 50 <= w < 60 or w == 510:
        return "Terraplenagem"
    if 60 <= w < 70 or w in (613, 161, 162):
        return "Pavimentação"
    if 70 <= w < 80:
        return "Concreto, meio-fio e calçadas"
    if 80 <= w < 90 or w in (181, 182):
        return "Drenagem"
    if w in (95, 103) or 110 <= w < 120:
        return "Redes (água, esgoto, elétrica)"
    if 120 <= w < 140:
        return "Paisagismo, cercas e muros"
    if 140 <= w < 160:
        return "Tráfego, segurança e meio ambiente"
    if w in (191, 201, 220, 221):
        return "Serviços extras e retrabalho"
    return "Outros"


obras = pd.read_csv(os.path.join(RAW, "obras_raw.csv"))
itens = pd.read_csv(os.path.join(RAW, "itens_raw.csv"))
mensal = pd.read_csv(os.path.join(RAW, "mensal_raw.csv"), parse_dates=["mes"])

# ---------- itens ----------
itens = itens[(itens["orcado"] != 0) | (itens["custo_real"] != 0)].copy()
itens["descricao_pt"] = itens["wbs"].map(DESC_PT).fillna(itens["descricao"])
itens["grupo"] = itens["wbs"].map(grupo)
# saldo = orçado − real (como extrato de banco: positivo = sobrou verba, negativo = estourou)
itens["saldo"] = itens["orcado"] - itens["custo_real"]
itens["saldo_pct"] = np.where(itens["orcado"] > 0, itens["saldo"] / itens["orcado"], np.nan)


def situacao(r):
    if r.orcado == 0 and r.custo_real > 0:
        return "Não orçado"
    if r.orcado > 0 and r.custo_real == 0:
        return "Não executado"
    # tolerância zero: qualquer real acima do orçado é estouro
    if r.custo_real > r.orcado:
        return "Estourou"
    return "Abaixo do orçado"


itens["situacao"] = itens.apply(situacao, axis=1)

# saldo separado em quantidade e preço (só onde há quantidade orçada e real); positivo = economia
ok = (itens["qtd_orcada"] > 0) & (itens["qtd_real"] > 0) & (itens["orcado"] > 0)
taxa_orc = itens["orcado"] / itens["qtd_orcada"]
taxa_real = itens["custo_real"] / itens["qtd_real"]
itens["efeito_quantidade"] = np.where(ok, (itens["qtd_orcada"] - itens["qtd_real"]) * taxa_orc, np.nan)
itens["efeito_preco"] = np.where(ok, (taxa_orc - taxa_real) * itens["qtd_real"], np.nan)

cols = ["obra", "wbs", "descricao_pt", "descricao", "grupo", "unidade", "qtd_orcada", "qtd_real",
        "orcado", "custo_real", "saldo", "saldo_pct", "situacao", "efeito_quantidade", "efeito_preco"]
itens = itens[cols].rename(columns={"descricao": "descricao_original"}).sort_values(["obra", "wbs"])

# ---------- evolução mensal (carteira por obra) ----------
ev = mensal.groupby(["obra", "mes"], as_index=False)[["pv_acum", "ev_acum", "ac_acum"]].sum()
ev["cpi"] = np.where(ev["ac_acum"] > 0, ev["ev_acum"] / ev["ac_acum"], np.nan)
ev["spi"] = np.where(ev["pv_acum"] > 0, ev["ev_acum"] / ev["pv_acum"], np.nan)
ev["mes_n"] = ev.groupby("obra").cumcount() + 1
bac = itens.groupby("obra")["orcado"].sum()
ev["pct_executado"] = ev["ev_acum"] / ev["obra"].map(bac)

# ---------- obras ----------
tot = itens.groupby("obra").agg(orcado=("orcado", "sum"), custo_real=("custo_real", "sum"),
                                n_itens=("wbs", "size"))
tot["saldo"] = tot["orcado"] - tot["custo_real"]
tot["saldo_pct"] = tot["saldo"] / tot["orcado"]
per = ev.groupby("obra")["mes"].agg(inicio="min", fim="max")
per["meses"] = ev.groupby("obra")["mes"].nunique()
obras = obras[["obra", "nome", "nome_en", "codigo_original"]].set_index("obra").join(tot).join(per).reset_index()
obras["cpi_final"] = obras["orcado"] / obras["custo_real"]

obras.to_csv(os.path.join(OUT, "obras.csv"), index=False, date_format="%Y-%m-%d")
itens.to_csv(os.path.join(OUT, "itens.csv"), index=False)
ev.to_csv(os.path.join(OUT, "evolucao_mensal.csv"), index=False, date_format="%Y-%m-%d")

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 20)
print(obras.round(3))
print(itens["situacao"].value_counts())
print("carteira:", round(obras.orcado.sum()), round(obras.custo_real.sum()),
      round(obras.custo_real.sum() / obras.orcado.sum() - 1, 4))
print(itens.groupby("grupo")[["orcado", "custo_real", "saldo"]].sum().sort_values("saldo").round(0))
