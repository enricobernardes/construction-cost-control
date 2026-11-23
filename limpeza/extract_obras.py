"""Extrai as 8 obras do Project Portfolio Dataset para tabelas limpas.

Uso: python3 -I extract_obras.py <pasta_xlsx> <pasta_saida>
"""
import datetime as dt
import glob
import os
import re
import sys

import openpyxl
import pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

NOMES_PT = {
    "P01": "Estacionamento de aeroporto",
    "P02": "Célula de aterro sanitário",
    "P03": "Rodovia de contorno regional",
    "P04": "Recuperação de pavimento arterial",
    "P05": "Reconstrução de via semiurbana",
    "P06": "Reconstrução de via urbana",
    "P17": "Loteamento de marina",
    "P18": "Recuperação de estrada rural",
}


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


obras, itens, mensal, lancamentos, receita = [], [], [], [], []

for path in sorted(glob.glob(os.path.join(SRC, "P0*.xlsx"))):
    fn = os.path.basename(path)
    m = re.match(r"(P\d{3}) - (P\d{2}) (.+)\.xlsx", fn)
    cod_orig, obra, nome_en = m.group(1), m.group(2), m.group(3)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

    # ---------- Portfolio WBS: orçamento x final + série mensal acumulada ----------
    rows = list(wb["Portfolio WBS"].iter_rows(values_only=True))
    ih = next(k for k, r in enumerate(rows[:6]) if "Final Cost" in r)
    isub = next(k for k, r in enumerate(rows[:6]) if "PV" in r and "EV" in r)
    head, sub = rows[ih], rows[isub]
    c_bac = head.index("BAC") if "BAC" in head else sub.index("BAC")
    c_fc = head.index("Final Cost")
    c_fq = head.index("Final Qty")
    c_unit = 3
    blocos = []
    for j, v in enumerate(sub):
        if v == "PQ" and tuple(sub[j:j + 5]) == ("PQ", "PV", "AQ", "AC", "EV"):
            d = None
            for c in range(j, j + 5):
                hv = head[c] if c < len(head) else None
                if isinstance(hv, dt.datetime):
                    d = hv.date()
                elif isinstance(hv, (int, float)) and 30000 < hv < 60000:
                    d = (dt.datetime(1899, 12, 30) + dt.timedelta(days=int(hv))).date()
            if d is not None:
                blocos.append((j, d))
    for r in rows[max(ih, isub) + 1:]:
        code = num(r[0])
        if code is None or r[1] is None:
            continue
        itens.append({
            "obra": obra, "wbs": int(code), "descricao": str(r[1]).strip(),
            "unidade": (str(r[c_unit]).strip() if r[c_unit] else None) or None,
            "qtd_orcada": num(r[2]), "orcado": num(r[c_bac]) or 0.0,
            "qtd_real": num(r[c_fq]), "custo_real": num(r[c_fc]) or 0.0,
        })
        for j, d in blocos:
            mensal.append({"obra": obra, "wbs": int(code), "mes": d,
                           "pv_acum": num(r[j + 1]) or 0.0, "ac_acum": num(r[j + 3]) or 0.0,
                           "ev_acum": num(r[j + 4]) or 0.0})

    # ---------- Actual Costs: lançamentos ----------
    rows = list(wb["Actual Costs"].iter_rows(values_only=True))
    for r in rows[1:]:
        d, tot, wbs = r[0], num(r[7]), num(r[8])
        if not isinstance(d, dt.datetime) or tot is None:
            continue
        lancamentos.append({
            "obra": obra, "data": d.date(), "descricao": str(r[1] or "").strip(),
            "recurso": str(r[2] or "").strip(), "unidade": str(r[3] or "").strip() or None,
            "quantidade": num(r[4]), "preco_unitario": num(r[5]),
            "valor": tot, "wbs": int(wbs) if wbs is not None else None,
        })

    # ---------- Budget & Revenue: valor do contrato (receita) ----------
    rows = list(wb["Budget & Revenue"].iter_rows(values_only=True))
    h = rows[0]
    i_ct = next(h.index(c) for c in ("Contract Total", "Final Contract Total", "Contract Sell Total") if c in h)
    contrato = sum(num(r[i_ct]) or 0 for r in rows[1:])
    obras.append({"obra": obra, "codigo_original": cod_orig, "nome_en": nome_en,
                  "nome": NOMES_PT.get(obra, nome_en), "valor_contrato": contrato,
                  "coluna_contrato": h[i_ct]})

obras = pd.DataFrame(obras)
itens = pd.DataFrame(itens)
mensal = pd.DataFrame(mensal)
lanc = pd.DataFrame(lancamentos)

# conferências
chk = itens.groupby("obra")[["orcado", "custo_real"]].sum().join(
    lanc.groupby("obra")["valor"].sum().rename("soma_lancamentos")).join(
    mensal.groupby(["obra", "mes"])[["ac_acum", "pv_acum", "ev_acum"]].sum()
    .groupby("obra").last().rename(columns=lambda c: c + "_ultimo_mes")).join(
    obras.set_index("obra")[["valor_contrato"]])
pd.set_option("display.width", 250)
print(chk.round(0))
print(itens.shape, mensal.shape, lanc.shape)
print(mensal.groupby("obra")["mes"].agg(["min", "max", "nunique"]))

obras.to_csv(os.path.join(OUT, "obras_raw.csv"), index=False)
itens.to_csv(os.path.join(OUT, "itens_raw.csv"), index=False)
mensal.to_csv(os.path.join(OUT, "mensal_raw.csv"), index=False)
lanc.to_csv(os.path.join(OUT, "lancamentos_raw.csv"), index=False)
