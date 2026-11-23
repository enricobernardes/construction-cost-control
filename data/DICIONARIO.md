# Dicionário de dados

As planilhas originais (uma por obra, com formatos diferentes) foram convertidas em 3 tabelas limpas, salvas como **CSV** (planilha em texto puro, sem formatação, que qualquer programa abre). Valores em dólar australiano (A\$).

**Termo:** *EAP (estrutura analítica do projeto)* é a lista de serviços da obra, como os itens de uma nota fiscal de supermercado: cada linha é um serviço com quantidade e preço.

**`obras.csv`** (8 linhas)
| Coluna | Significado |
|---|---|
| obra | Código da obra (P01 a P18) |
| nome | Nome traduzido |
| orcado | Orçamento aprovado (soma dos itens) |
| custo_real | Custo final (soma dos itens) |
| saldo / saldo_pct | Orçado − custo real, em A\$ e em % (positivo = sobrou, negativo = estourou) |
| inicio / fim / meses | Período com acompanhamento mensal |
| cpi_final | Orçado ÷ custo real (não usado nesta análise) |

**`itens.csv`** (265 linhas: cada serviço de cada obra)
| Coluna | Significado |
|---|---|
| wbs | Código do serviço na EAP (padronizado entre as obras) |
| descricao_pt / descricao_original | Nome do serviço em português e no original |
| grupo | Agrupamento que criei (terraplenagem, pavimentação, drenagem...) |
| qtd_orcada / qtd_real | Quantidades previstas e executadas |
| orcado / custo_real / saldo / saldo_pct | Valores do item (saldo = orçado − real) |
| situacao | Estourou (acima do orçado), abaixo do orçado, não orçado ou não executado |
| efeito_quantidade / efeito_preco | Parte do saldo que veio da quantidade e parte que veio do preço unitário (positivo = economia) |

**`evolucao_mensal.csv`** (76 linhas): acompanhamento mensal de cada obra, com valores acumulados de planejado, executado e gasto. Fica para a próxima etapa (projetar o custo final durante a obra) e não entra nesta análise.
