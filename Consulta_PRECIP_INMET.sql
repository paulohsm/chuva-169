SELECT dse_estacao, 
       ST_AsEWKT(est_geom::geometry), 
       dse_valor 
  FROM pcd.dado_sensor, 
       pcd.estacao 
 WHERE dse_sensor = 22
   AND dse_data = '2014-03-31 00:00'
   AND dse_estacao BETWEEN 394 AND 909 
   AND est_codigo = dse_estacao
 ORDER BY dse_estacao;
