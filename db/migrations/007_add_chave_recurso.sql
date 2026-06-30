-- db/migrations/007_add_chave_recurso.sql
-- Adiciona coluna dsc_chave_recurso_cre para cruzamento preciso com itens de OS
-- quando múltiplos recursos têm a mesma unidade de medida (ex: 6 tipos de LICENÇA).
--
-- A chave é um substring identificador único dentro de dsc_especificacao_item_os_osi.
-- Quando NULL, o cruzamento cai na unidade de medida (comportamento anterior).

ALTER TABLE tb_contrato_recurso_cre
    ADD COLUMN dsc_chave_recurso_cre VARCHAR(100) NULL
        COMMENT 'Substring identificador para cruzar com dsc_especificacao_item_os_osi. NULL = cruzar só pela unidade.'
        AFTER dsc_especificacao_recurso_cre;

-- Preencher as chaves para o contrato 03/2024 (itens com LICENÇA precisam de chave)
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Frontline Worker Starter'  WHERE pk_id_con = 13 AND num_seq_recurso_cre = 1;
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Frontline Worker Standard' WHERE pk_id_con = 13 AND num_seq_recurso_cre = 2;
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Enterprise Starter'        WHERE pk_id_con = 13 AND num_seq_recurso_cre = 3;
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Enterprise Standard'       WHERE pk_id_con = 13 AND num_seq_recurso_cre = 4;
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Enterprise Plus'           WHERE pk_id_con = 13 AND num_seq_recurso_cre = 5;
UPDATE tb_contrato_recurso_cre SET dsc_chave_recurso_cre = 'Google Vault'              WHERE pk_id_con = 13 AND num_seq_recurso_cre = 6;
-- Itens 7-10: unidades únicas (Usuário/Turmas/UST), dsc_chave_recurso_cre permanece NULL

-- Contrato 29/2024: UST-A e UST-B são unidades distintas, NULL é suficiente

-- Verificação
SELECT pk_id_con, num_seq_recurso_cre, dsc_unidade_medida_recurso_cre, dsc_chave_recurso_cre
FROM tb_contrato_recurso_cre
WHERE pk_id_con = 13
ORDER BY num_seq_recurso_cre;