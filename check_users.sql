-- Verificar se sac_reader e sac_writer já existem no MariaDB
-- Rodar como root: mysql -u root -p -P 3307 < check_users.sql

SELECT User, Host FROM mysql.user WHERE User IN ('sac_reader', 'sac_writer');

-- Se a query acima retornar 0 linhas, nenhum dos dois foi criado ainda.
-- Se retornar 1 linha, só um foi criado — confira qual.
-- Se retornar 2 linhas, ambos existem — falta só conferir os grants:

SHOW GRANTS FOR 'sac_reader'@'%';
SHOW GRANTS FOR 'sac_writer'@'%';