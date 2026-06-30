CREATE TABLE IF NOT EXISTS tb_ordem_servico_ord (
    pk_id_ord                  INT AUTO_INCREMENT PRIMARY KEY,
    num_numero_os_ord          VARCHAR(50)  NOT NULL,
    num_numero_contrato_ord    VARCHAR(50)  NOT NULL,
    dat_emissao_os_ord         DATE,
    nom_cliente_os_ord         VARCHAR(255),
    nom_fornecedor_os_ord      VARCHAR(255),
    dat_inicio_vigencia_os_ord DATE,
    dat_fim_vigencia_os_ord    DATE,
    dsc_nome_arquivo_pdf_ord   VARCHAR(255),
    log_status_ord             VARCHAR(30)  DEFAULT 'ativo',
    dat_criado_em_ord          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    dat_atualizado_em_ord      DATETIME     DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP,
    dsc_usuario_ord             VARCHAR(100),
    pk_id_con                   INT NOT NULL,

    CONSTRAINT fk_osi_contrato
        FOREIGN KEY (pk_id_con) REFERENCES tb_contrato_con(pk_id_con)
        ON DELETE RESTRICT,

    INDEX idx_ord_contrato (pk_id_con),
    INDEX idx_ord_numero (num_numero_os_ord)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;