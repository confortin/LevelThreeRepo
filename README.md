# Projeto Data Analytics

Validação e análise exploratória de qualidade de dados do dataset de defeitos de manufatura.

## Estrutura

```
LevelThreeRepo/
├── .gitignore
└── projeto-tema2/
    ├── data/
    │   └── manufacturing_defect_dataset.csv
    ├── src/
    │   └── validate_data.py
    ├── requirements.txt
    └── README.md
```

## Dataset

`data/manufacturing_defect_dataset.csv`: 3.240 linhas e 17 colunas (12 `float64`, 5 `int64`), sem valores nulos e sem linhas duplicadas.

Variável alvo: `DefectStatus` (1 = defeito, 0 = sem defeito). Distribuição: 2.723 registros com `1` e 517 com `0`.

| Grupo | Colunas |
|---|---|
| Produção | `ProductionVolume`, `ProductionCost` |
| Fornecimento | `SupplierQuality`, `DeliveryDelay` |
| Qualidade | `DefectRate`, `QualityScore` |
| Manutenção e paradas | `MaintenanceHours`, `DowntimePercentage` |
| Estoque | `InventoryTurnover`, `StockoutRate` |
| Trabalho e segurança | `WorkerProductivity`, `SafetyIncidents` |
| Energia | `EnergyConsumption`, `EnergyEfficiency` |
| Manufatura aditiva | `AdditiveProcessTime`, `AdditiveMaterialCost` |
| Alvo | `DefectStatus` |

## Script

`src/validate_data.py` lê o CSV e imprime no terminal:

1. Resumo por coluna: tipo, nulos, % de nulos, valores únicos e valores repetidos.
2. Estatísticas das colunas numéricas: mínimo, máximo, média, desvio padrão, negativos, zeros e outliers pela regra do IQR (1,5 × IQR).
3. Colunas de texto: valores mais frequentes, espaços nas pontas, variações de maiúsculas/minúsculas e placeholders (`NA`, `null`, `?`, `-` etc.).
4. Colunas que deveriam ser numéricas mas contêm texto.
5. Colunas constantes.

O script não altera o dataset nem gera arquivos.

## Requisitos

- Python 3.10 ou superior
- pandas

## Instalação

Windows:

```
python -m venv venv
venv\Scripts\activate
pip install pandas
```

macOS/Linux:

```
python3 -m venv venv
source venv/bin/activate
pip install pandas
```

## Uso

A partir da pasta `projeto-tema2`:

```
python src/validate_data.py
```

O script usa caminhos relativos ao próprio arquivo, então também funciona se executado de outra pasta.