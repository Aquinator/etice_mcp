-- db/migrations/005_create_contrato_recurso.sql
-- Cria a tabela tb_contrato_recurso_cre conforme modelo de dados (PNG)
-- FK para tb_contrato_con (ON DELETE RESTRICT — não apaga contrato com recursos cadastrados)

CREATE TABLE IF NOT EXISTS tb_contrato_recurso_cre (
    pk_id_cre                      INT             NOT NULL AUTO_INCREMENT,
    num_numero_contrato_cre        VARCHAR(50)     NOT NULL COMMENT 'Número do contrato (exibição)',
    num_seq_recurso_cre            INT             NOT NULL COMMENT 'Sequência do item na tabela de preços',
    dsc_especificacao_recurso_cre  TEXT            NULL     COMMENT 'Descrição completa do item contratado',
    dsc_unidade_medida_recurso_cre VARCHAR(30)     NOT NULL COMMENT 'Ex: UST, UST-A, UST-B, LICENÇA, Usuário, Turmas',
    qtd_quantidade_recurso_cre     DECIMAL(14,4)   NOT NULL DEFAULT 0 COMMENT 'Quantidade total contratada',
    vlr_valor_unitario_recurso_cre DECIMAL(14,2)   NOT NULL DEFAULT 0 COMMENT 'Valor unitário (R$) conforme tabela de preços',
    vlr_valor_total_recurso_cre    DECIMAL(16,2)   NOT NULL DEFAULT 0 COMMENT 'Valor total do item (R$)',
    log_status_cre                 VARCHAR(30)     NOT NULL DEFAULT 'ativo',
    dat_criado_em_cre              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dat_atualizado_em_cre          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    dsc_usuario_cre                VARCHAR(100)    NOT NULL,
    pk_id_con                      INT             NOT NULL COMMENT 'FK para tb_contrato_con',

    PRIMARY KEY (pk_id_cre),
    UNIQUE KEY uq_recurso_seq (pk_id_con, num_seq_recurso_cre),
    CONSTRAINT fk_recurso_contrato
        FOREIGN KEY (pk_id_con)
        REFERENCES tb_contrato_con (pk_id_con)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Itens da tabela de preços de cada contrato (recursos contratados)';