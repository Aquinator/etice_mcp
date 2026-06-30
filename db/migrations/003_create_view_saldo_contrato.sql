CREATE OR REPLACE VIEW vw_saldo_contrato AS
SELECT
    con.pk_id_con,
    con.num_numero_contrato_con,
    con.dsc_empresa_contratada_con,
    con.vlr_valor_total_contrato_con                          AS valor_total_contrato,
    COALESCE(SUM(osi.vlr_valor_total_item_os_osi), 0)         AS valor_total_consumido,
    con.vlr_valor_total_contrato_con
        - COALESCE(SUM(osi.vlr_valor_total_item_os_osi), 0)  AS saldo_disponivel,
    COUNT(DISTINCT ord.pk_id_ord)                              AS qtd_ordens_servico
FROM tb_contrato_con con
LEFT JOIN tb_ordem_servico_ord      ord ON ord.pk_id_con = con.pk_id_con
LEFT JOIN tb_ordem_servico_item_osi osi ON osi.pk_id_ord = ord.pk_id_ord
GROUP BY con.pk_id_con, con.num_numero_contrato_con,
         con.dsc_empresa_contratada_con, con.vlr_valor_total_contrato_con;