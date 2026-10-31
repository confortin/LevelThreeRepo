-- Executar no terminal: sqlite3 Manufacturing_Defects.db < import_data_sqlite_final.sql
-- O arquivo CSV deve estar na mesma pasta do terminal.
.bail on
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS importacao_temp;
CREATE TABLE importacao_temp (
 ProductionVolume INTEGER,
 ProductionCost REAL,
 SupplierQuality REAL,
 DeliveryDelay INTEGER,
 DefectRate REAL,
 QualityScore REAL,
 MaintenanceHours INTEGER,
 DowntimePercentage REAL,
 InventoryTurnover REAL,
 StockoutRate REAL,
 WorkerProductivity REAL,
 SafetyIncidents INTEGER,
 EnergyConsumption REAL,
 EnergyEfficiency REAL,
 AdditiveProcessTime REAL,
 AdditiveMaterialCost REAL,
 DefectStatus INTEGER
);
.mode csv
.import --skip 1 manufacturing_defect_dataset.csv importacao_temp
.mode list
BEGIN TRANSACTION;
-- Interromper sem inserir se alguma tabela já tiver linhas ou se CSV não tiver 3240 linhas.
CREATE TEMP TABLE verificacao (ok INTEGER NOT NULL CHECK (ok = 1));
INSERT INTO verificacao
SELECT CASE WHEN
 (SELECT COUNT(*) FROM importacao_temp) = 3240
 AND (SELECT COUNT(*) FROM Production) = 0
 AND (SELECT COUNT(*) FROM Supplier) = 0
 AND (SELECT COUNT(*) FROM Performance) = 0
 AND (SELECT COUNT(*) FROM Quality) = 0
 THEN 1 ELSE 0 END;
DROP TABLE verificacao;

INSERT INTO Production (ProductionID, ProductionVolume, ProductionCost, WorkerProductivity, SafetyIncidents)
SELECT rowid, ProductionVolume, ProductionCost, WorkerProductivity, SafetyIncidents
FROM importacao_temp ORDER BY rowid;

INSERT INTO Supplier (ProductionID, SupplierQuality, DeliveryDelay, InventoryTurnover, StockoutRate)
SELECT rowid, SupplierQuality, DeliveryDelay, InventoryTurnover, StockoutRate
FROM importacao_temp ORDER BY rowid;

INSERT INTO Performance (ProductionID, MaintenanceHours, DowntimePercentage, EnergyConsumption,
 EnergyEfficiency, AdditiveProcessTime, AdditiveMaterialCost)
SELECT rowid, MaintenanceHours, DowntimePercentage, EnergyConsumption,
 EnergyEfficiency, AdditiveProcessTime, AdditiveMaterialCost
FROM importacao_temp ORDER BY rowid;

INSERT INTO Quality (ProductionID, DefectRate, QualityScore, DefectStatus)
SELECT rowid, DefectRate, QualityScore, DefectStatus
FROM importacao_temp ORDER BY rowid;

COMMIT;
DROP TABLE importacao_temp;
SELECT 'Production' AS tabela, COUNT(*) AS registros FROM Production
UNION ALL SELECT 'Supplier', COUNT(*) FROM Supplier
UNION ALL SELECT 'Performance', COUNT(*) FROM Performance
UNION ALL SELECT 'Quality', COUNT(*) FROM Quality;
PRAGMA foreign_key_check;
