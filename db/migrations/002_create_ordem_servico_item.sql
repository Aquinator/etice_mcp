CREATE TABLE IF NOT EXISTS tb_ordem_servico_item_osi (
    pk_id_osi                       INT AUTO_INCREMENT PRIMARY KEY,
    num_numero_os_osi                VARCHAR(50),
    num_seq_item_os_osi               INT NOT NULL,
    dsc_especificacao_item_os_osi     TEXT,
    dsc_unidade_medida_item_os_osi    VARCHAR(30),
    qtd_quantidade_item_os_osi        DECIMAL(15,4) DEFAULT 1,
    qtd_frequencia_item_os_osi        VARCHAR(50),
    vlr_valor_unitario_item_os_osi    DECIMAL(15,2) NOT NULL,
    vlr_valor_total_item_os_osi       DECIMAL(15,2) NOT NULL,
    log_status_osi                    VARCHAR(30) DEFAULT 'ativo',
    dat_criado_em_osi                 DATETIME DEFAULT CURRENT_TIMESTAMP,
    dat_atualizado_em_osi             DATETIME DEFAULT CURRENT_TIMESTAMP
                                                ON UPDATE CURRENT_TIMESTAMP,
    dsc_usuario_osi                    VARCHAR(100),
    pk_id_ord                          INT NOT NULL,

    CONSTRAINT fk_item_ordem_servico
        FOREIGN KEY (pk_id_ord) REFERENCES tb_ordem_servico_ord(pk_id_ord)
        ON DELETE CASCADE,

    INDEX idx_osi_ordem (pk_id_ord)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;