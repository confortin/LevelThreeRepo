
-- 1. O adminstrador do banco gostaria de entender se a entrega rápida de um equipamento pode ter maiores taxas de defeito.
--     Para isso ele decide buscar as 10 maiores taxas de defeito e ver se existe um padrão no atraso da entrega.
--      Com a consulta abaixo é possivel ver que a produção pode ter uma alta taxa de defeito independente do atraso na entrega. 

SELECT
    p.ProductionID,
    p.ProductionVolume,
    q.DefectRate,
    s.DeliveryDelay
FROM Production p
INNER JOIN Quality q
    ON p.ProductionID = q.ProductionID
INNER JOIN Supplier s
    ON p.ProductionID = s.ProductionID
WHERE s.DeliveryDelay IN (0, 5)
ORDER BY q.DefectRate DESC
LIMIT 10;

-- 2. O adminstrador do banco gostaria de saber quais fornecedores apresentam os maiores atrasos nas entregas. 
--      Ele quer definir se esse atraso tem relação com a nota de qualidade destes fornecedores. 
--      Olhando para o resultado já é possivel ver diversos fornecedores com notas acima de 99 atrasam mais de 2 dias. 
--      Podemos concluir que não há relação entre a nota e os dias de atraso.
        
SELECT
    s.SupplierID,
    SUM(s.DeliveryDelay) AS TotalDeliveryDelay,
    ROUND(AVG(s.SupplierQuality), 2) AS SupplierQuality
FROM Supplier s
GROUP BY s.SupplierID
ORDER BY SupplierQuality DESC;

-- 3. Após alguns meses de operação a gestão pensou em consultar como o consumo de energia varia de acordo com o volume de produção.
--      Para isso ela olhou para os registros de produção com os maiores volumes produzidos e buscou comparar como mostrado abaixo. 
--      Olhando para os resultados os 4 maiores índices de consumo de energia tem altos volumes de produção.
--      No entanto essa tendência começa a dminuir e perder força logo abaixo então mais análises precisam ser feitas.  

SELECT
    P.ProductionID,
    P.ProductionVolume,
    F.EnergyConsumption
FROM Production P
INNER JOIN Performance F
    ON P.ProductionID = F.ProductionID
ORDER BY F.EnergyConsumption DESC;

-- 4. Cada produção tem um valor de tempo de manutenção e os gestores da área querem ver as pruções com tempo maior que a média.
--      Além disso é importante verificar se o número de registros acima da média é proporcional à quantidade de dados ou temos outliers. 
--      Os dados de execução mostram um retorno de 1601 registros de 3240, ou seja, 49,41% tem uma média de tempo de manutenção maior que a média. 
--      Esse resultado demonstra que os tempos de manutenção estão equilibrados entre as produções pois é esperado que um número perto da metade seja acima da média. 

SELECT
    ProductionID,
    ROUND(AVG(DowntimePercentage), 2) AS AvgDowntime,
    ROUND(
        AVG(DowntimePercentage) -
        (SELECT AVG(DowntimePercentage) FROM Performance),
        2
    ) AS DifferenceFromAverage
FROM Performance
GROUP BY ProductionID
HAVING AVG(DowntimePercentage) > (
    SELECT AVG(DowntimePercentage)
    FROM Performance
)
ORDER BY AvgDowntime DESC;

-- 5. O gestor gostaria de saber, dos fornecedores que apresentam índice de qualidade superior a 95, quais são suas médias de horas de manutenção e taxas de defeitos.
--      Ele gostaria de vizualizar estes dados classificados da maior para a menor qualidade do fonecedor. 
--      Como já tinhamos concluido a média de defeitos e a qualidade do fornecedor não tem relação
--      No entanto aqui podemos ver que fornecedores com altas notas possuem média no tempo de manutenção maior que 10h, regularmente. 

SELECT
    s.SupplierID AS Supplier,
    ROUND(AVG(s.SupplierQuality), 2) AS SupplierQuality,
    ROUND(AVG(p.MaintenanceHours), 2) AS AvgMaintenanceHours,
    ROUND(AVG(q.DefectRate), 2) AS AvgDefectRate
FROM Supplier s
INNER JOIN Performance p
    ON s.ProductionID = p.ProductionID
INNER JOIN Quality q
    ON s.ProductionID = q.ProductionID
WHERE s.SupplierQuality > 95
GROUP BY s.SupplierID
ORDER BY SupplierQuality DESC;