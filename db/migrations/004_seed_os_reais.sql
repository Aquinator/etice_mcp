-- db/migrations/004_seed_os_reais.sql
-- Gerado a partir de Tabela_OS_normalizada.xlsx + tb_contrato_con_202605172145.csv
-- Dados reais de OS para prova de conceito SAC Fase 2
--
-- Contratos cobertos (os únicos 3 com OS na planilha):
--   pk_id_con=2  | 21/2021 | ELOGROUP  (11 OS, 1 item cada)
--   pk_id_con=13 | 03/2024 | GOLDEN    ( 8 OS, 1 item cada)
--   pk_id_con=28 | 29/2024 | PORTFOLIO ( 3 OS, multi-item)
--
-- Pré-requisito: migrations 001, 002 e 003 já aplicadas.
-- Os pk_id_ord e pk_id_osi usam os valores originais da planilha
-- para facilitar rastreabilidade. Se as tabelas já tiverem dados,
-- ajuste ou limpe antes de rodar.

START TRANSACTION;

INSERT INTO tb_ordem_servico_ord
    (pk_id_ord, num_numero_os_ord, num_numero_contrato_ord, dat_emissao_os_ord,
     nom_cliente_os_ord, nom_fornecedor_os_ord, pk_id_con, log_status_ord, dsc_usuario_ord)
VALUES
    -- Contrato 21/2021 — ELOGROUP (pk_id_con = 2)
    (1,  '51/2025', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (2,  '01/2025', '21/2021', NULL, 'EMPRESA DE TECNOLOGIA DA INFORMAÇÃO DO CEARÁ',        'ELOGROUP',                                     2, 'ativo', 'seed_poc'),
    (3,  '42/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (4,  '43/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (5,  '41/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (6,  '44/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (7,  '36/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (8,  '37/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (9,  '40/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (10, '39/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    (11, '38/2026', '21/2021', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'ELOGROUP DESENVOLVIMENTO E CONSULTORIA LTDA', 2, 'ativo', 'seed_poc'),
    -- Contrato 29/2024 — PORTFOLIO (pk_id_con = 28)
    (12, '12/2026', '29/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'PORTFOLIO CONSULTORIA EMPRESARIAL LTDA',       28, 'ativo', 'seed_poc'),
    (13, '07/2026', '29/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'PORTFOLIO CONSULTORIA EMPRESARIAL LTDA',       28, 'ativo', 'seed_poc'),
    (14, '01/2026', '29/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'PORTFOLIO CONSULTORIA EMPRESARIAL LTDA',       28, 'ativo', 'seed_poc'),
    -- Contrato 03/2024 — GOLDEN (pk_id_con = 13)
    (15, '19/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (16, '18/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (17, '14/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (18, '13/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (19, '11/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (20, '08/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (21, '09/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc'),
    (22, '06/2026', '03/2024', NULL, 'Empresa de Tecnologia da Informação do Ceará - ETICE', 'GOLDEN TECHNOLOGIA LTDA',                     13, 'ativo', 'seed_poc');

INSERT INTO tb_ordem_servico_item_osi
    (pk_id_osi, num_numero_os_osi, num_seq_item_os_osi, dsc_especificacao_item_os_osi,
     dsc_unidade_medida_item_os_osi, qtd_quantidade_item_os_osi,
     vlr_valor_unitario_item_os_osi, vlr_valor_total_item_os_osi,
     pk_id_ord, log_status_osi, dsc_usuario_osi)
VALUES
    -- OS 51/2025 (pk_id_ord=1) — ELOGROUP
    (1,  '51/2025', 4, 'Suporte técnico para desenvolvimento e implantação de camada de interoperabilidade, incluindo serviços de integração de sistemas',
         'UST', 600.0, 70.00, 42000.00, 1, 'ativo', 'seed_poc'),
    -- OS 01/2025 (pk_id_ord=2) — ELOGROUP
    (2,  '01/2025', 1, 'Disponibilização de solução tecnológica (SaaS) multicanal para atendimento e gerenciamento do relacionamento com o usuário, disponibilização de informações, digitalização e automação de serviços',
         'Licença/Mês', 19.0, 5.27, 100.13, 2, 'ativo', 'seed_poc'),
    -- OS 42/2026 (pk_id_ord=3) — ELOGROUP
    (3,  '42/2026', 3, 'Adequação e automação de serviços públicos com o uso da solução tecnológica',
         'USTA', 587.5, 110.00, 64625.00, 3, 'ativo', 'seed_poc'),
    -- OS 43/2026 (pk_id_ord=4) — ELOGROUP
    (4,  '43/2026', 3, 'Adequação e automação de serviços públicos com o uso da solução tecnológica',
         'USTA', 225.0, 110.00, 24750.00, 4, 'ativo', 'seed_poc'),
    -- OS 41/2026 (pk_id_ord=5) — ELOGROUP
    (5,  '41/2026', 4, 'Suporte técnico para desenvolvimento e implantação de camada de interoperabilidade, incluindo serviços de integração de sistemas',
         'UST', 290.4, 70.00, 20328.00, 5, 'ativo', 'seed_poc'),
    -- OS 44/2026 (pk_id_ord=6) — ELOGROUP
    (6,  '44/2026', 4, 'Suporte técnico para desenvolvimento e implantação de camada de interoperabilidade, incluindo serviços de integração de sistemas',
         'UST', 290.4, 70.00, 20328.00, 6, 'ativo', 'seed_poc'),
    -- OS 36/2026 (pk_id_ord=7) — ELOGROUP
    (7,  '36/2026', 3, 'Adequação e automação de serviços públicos com o uso da solução tecnológica',
         'USTA', 450.0, 110.00, 49500.00, 7, 'ativo', 'seed_poc'),
    -- OS 37/2026 (pk_id_ord=8) — ELOGROUP
    (8,  '37/2026', 3, 'Adequação e automação de serviços públicos com o uso da solução tecnológica',
         'USTA', 525.0, 110.00, 57750.00, 8, 'ativo', 'seed_poc'),
    -- OS 40/2026 (pk_id_ord=9) — ELOGROUP
    (9,  '40/2026', 4, 'Suporte técnico para desenvolvimento e implantação de camada de interoperabilidade, incluindo serviços de integração de sistemas',
         'UST', 931.7, 70.00, 65219.00, 9, 'ativo', 'seed_poc'),
    -- OS 39/2026 (pk_id_ord=10) — ELOGROUP
    (10, '39/2026', 4, 'Suporte técnico para desenvolvimento e implantação de camada de interoperabilidade, incluindo serviços de integração de sistemas',
         'UST', 112.2, 70.00, 7854.00, 10, 'ativo', 'seed_poc'),
    -- OS 38/2026 (pk_id_ord=11) — ELOGROUP
    (11, '38/2026', 3, 'Adequação e automação de serviços públicos com o uso da solução tecnológica',
         'USTA', 5600.0, 110.00, 616000.00, 11, 'ativo', 'seed_poc'),
    -- OS 12/2026 (pk_id_ord=12) — PORTFOLIO — 4 itens UST-B
    (12, '12/2026', 1, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 1232.0, 87.45, 107738.40, 12, 'ativo', 'seed_poc'),
    (13, '12/2026', 2, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 1936.0, 87.45, 169303.20, 12, 'ativo', 'seed_poc'),
    (14, '12/2026', 3, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 1232.0, 87.45, 107738.40, 12, 'ativo', 'seed_poc'),
    (15, '12/2026', 4, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 1936.0, 87.45, 169303.20, 12, 'ativo', 'seed_poc'),
    -- OS 07/2026 (pk_id_ord=13) — PORTFOLIO — UST-B + licença Google
    (16, '07/2026', 2, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 1853.71, 87.45, 162106.94, 13, 'ativo', 'seed_poc'),
    (25, '07/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 2.0, 35.34, 70.68, 13, 'ativo', 'seed_poc'),
    -- OS 01/2026 (pk_id_ord=14) — PORTFOLIO — UST-A + UST-B
    (17, '01/2026', 1, 'UNIDADE DE SERVIÇO TÉCNICO A: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – LEVANTAMENTO DOS SERVIÇOS E GESTÃO DO PROCESSO DE TRANSFORMAÇÃO DE SERVIÇOS.',
         'UST-A', 1838.55815, 79.80, 146716.94, 14, 'ativo', 'seed_poc'),
    (18, '01/2026', 2, 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
         'UST-B', 16963.6505, 87.45, 1483471.24, 14, 'ativo', 'seed_poc'),
    -- OS 19/2026 (pk_id_ord=15) — GOLDEN — licença Google Enterprise Standard
    (19, '19/2026', 4, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Standard',
         'LICENÇA', 2.0, 91.64, 183.28, 15, 'ativo', 'seed_poc'),
    -- OS 18/2026 (pk_id_ord=16) — GOLDEN
    (20, '18/2026', 4, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Standard',
         'LICENÇA', 2.0, 91.64, 183.28, 16, 'ativo', 'seed_poc'),
    -- OS 14/2026 (pk_id_ord=17) — GOLDEN
    (21, '14/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 33.0, 35.34, 1166.22, 17, 'ativo', 'seed_poc'),
    -- OS 13/2026 (pk_id_ord=18) — GOLDEN
    (22, '13/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 30.0, 35.34, 1060.20, 18, 'ativo', 'seed_poc'),
    -- OS 11/2026 (pk_id_ord=19) — GOLDEN — Frontline Worker
    (23, '11/2026', 1, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Frontline Worker Starter',
         'LICENÇA', 5.0, 19.76, 98.80, 19, 'ativo', 'seed_poc'),
    -- OS 08/2026 (pk_id_ord=20) — GOLDEN
    (24, '08/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 1.0, 35.34, 35.34, 20, 'ativo', 'seed_poc'),
    -- OS 09/2026 (pk_id_ord=21) — GOLDEN
    (26, '09/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 25.0, 35.34, 883.50, 21, 'ativo', 'seed_poc'),
    -- OS 06/2026 (pk_id_ord=22) — GOLDEN
    (27, '06/2026', 3, 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
         'LICENÇA', 45.0, 35.34, 1590.30, 22, 'ativo', 'seed_poc');

COMMIT;

-- =============================================================================
-- VERIFICAÇÃO PÓS-SEED (executar manualmente e comparar com tabela abaixo)
-- =============================================================================

SELECT
    con.num_numero_contrato_con,
    con.dsc_empresa_contratada_con,
    v.valor_total_contrato,
    v.valor_total_consumido,
    v.saldo_disponivel,
    v.qtd_ordens_servico,
    ROUND(v.valor_total_consumido / v.valor_total_contrato * 100, 2) AS pct_consumido
FROM vw_saldo_contrato v
JOIN tb_contrato_con con ON con.pk_id_con = v.pk_id_con
WHERE v.pk_id_con IN (2, 13, 28)
ORDER BY v.pk_id_con;

-- RESULTADO ESPERADO:
-- ┌─────────────┬──────────────────────────┬───────────────┬──────────────┬───────────────┬─────┬──────────┐
-- │ contrato    │ empresa                  │ valor_total   │ consumido    │ saldo         │ OS  │ %consumo │
-- ├─────────────┼──────────────────────────┼───────────────┼──────────────┼───────────────┼─────┼──────────┤
-- │ 21/2021     │ ELOGROUP                 │ 12.639.597,60 │   968.454,13 │ 11.671.143,47 │  11 │   7,66%  │
-- │ 03/2024     │ GOLDEN TECHNOLOGIA LTDA. │ 46.795.360,40 │     5.200,92 │ 46.790.159,48 │   8 │   0,01%  │
-- │ 29/2024     │ PORTFOLIO CONSULTORIA    │ 23.324.551,95 │ 2.346.449,00 │ 20.978.102,95 │   3 │  10,06%  │
-- └─────────────┴──────────────────────────┴───────────────┴──────────────┴───────────────┴─────┴──────────┘
--
-- Total geral consumido (soma de todos os itens): R$ 3.320.104,05