# Projeto Data Analytics

Validação e análise exploratória de qualidade de dados do dataset de defeitos de manufatura.

## Estrutura

```
LevelThreeRepo/
├── .gitignore
├── README.md
├── docker-compose.yml
└── projeto-tema2/
    ├── data/
    │   └── defects_data.csv        # dataset de defeitos
    ├── figs/
    │   └── falhas_por_categoria_mes.png
    ├── src/
    │   ├── __init__.py
    │   ├── validate_data.py        # validação de qualidade dos dados
    │   ├── falhas_mensais.py       # gráfico de falhas por categoria, mês a mês
    │   └── pipeline.py             # pipeline (executado pelo Docker)
    ├── tests/
    │   └── test_validate_data.py
    ├── Dockerfile
    ├── .dockerignore
    └── requirements.txt
```

## Dataset

`data/defects_data.csv`: 1.000 registros de defeitos e 8 colunas, sem valores nulos e sem linhas duplicadas. Período: 01/01/2024 a 30/06/2024.

| Coluna | Tipo | Descrição |
|---|---|---|
| `defect_id` | int | Identificador do defeito |
| `product_id` | int | Identificador do produto (1 a 100) |
| `defect_type` | texto | `Structural` (352), `Functional` (339), `Cosmetic` (309) |
| `defect_date` | data (M/D/AAAA) | Data do registro |
| `defect_location` | texto | `Surface` (353), `Component` (326), `Internal` (321) |
| `severity` | texto | `Minor` (358), `Critical` (333), `Moderate` (309) |
| `inspection_method` | texto | `Manual Testing` (352), `Visual Inspection` (351), `Automated Testing` (297) |
| `repair_cost` | float | Custo do reparo (10,22 a 999,64) |

## Scripts

- `src/validate_data.py`: lê o CSV e imprime no terminal o resumo por coluna (tipo, nulos, % de nulos, únicos e duplicados), estatísticas das colunas numéricas (mínimo, máximo, média, desvio padrão, negativos, zeros e outliers pela regra do IQR) e as colunas constantes. Não altera o dataset.
- `src/falhas_mensais.py`: conta as falhas por `defect_type` em cada mês e salva o gráfico em `figs/falhas_por_categoria_mes.png`.
- `src/pipeline.py`: lê e limpa o dataset, gera a tabela-resumo e dois gráficos em `output/`:
  - `tabela_resumo.csv`: por `defect_type`, registros, % do total, custo médio, custo total e % de defeitos críticos.
  - `grafico_1.png`: custo médio de reparo por severidade.
  - `grafico_2.png`: % de defeitos críticos por método de inspeção.

### Decisões de limpeza (pipeline)

1. **Outliers:** checados pelo IQR só em `repair_cost` (ids não são medidas). Nenhuma linha é removida, pois custos altos são reparos reais.
2. **Datas:** `defect_date` é convertida de texto `M/D/AAAA` para data; datas inválidas são descartadas e é criada a coluna `mes`.
3. **Categorias:** textos sem espaços nas pontas, `severity` ordenada (`Minor` < `Moderate` < `Critical`) e coluna `is_critical` (1 = crítico).

Os scripts usam caminhos relativos ao próprio arquivo, então funcionam a partir de qualquer pasta.

## Instalação

Requisito: Python 3.10 ou superior.

Windows:

```
python -m venv venv
venv\Scripts\activate
pip install -r projeto-tema2/requirements.txt
```

macOS/Linux:

```
python3 -m venv venv
source venv/bin/activate
pip install -r projeto-tema2/requirements.txt
```

## Uso

A partir da pasta `projeto-tema2`:

```
python src/validate_data.py
python src/falhas_mensais.py
python src/pipeline.py
```

## Testes

A partir da pasta `projeto-tema2`:

```
python -m pytest
```

## Docker

Com Docker Compose, a partir da raiz do repositório:

```
docker compose up --build
```

As saídas aparecem em `projeto-tema2/output/`.

Ou manualmente:

```
docker build -t levelthree-pipeline projeto-tema2
docker run --rm -v "$(pwd)/projeto-tema2/data:/app/data" levelthree-pipeline
```

Os dados não entram na imagem; são montados por volume em `/app/data`.
