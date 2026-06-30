-- db/migrations/006_seed_recursos_contrato.sql
-- Dados reais da tabela de preços dos contratos 03/2024 e 29/2024
-- Fonte: PDFs assinados (Cláusula Terceira – Do Valor)
-- Pré-requisito: migration 005 já aplicada.
--
-- Contrato 03/2024 | GOLDEN | pk_id_con=13 | R$ 46.795.360,40 (10 itens)
--   Itens 1-6 (SaaS): vlr_total = 12 × qtd × vlr_unitario_mensal
--   Itens 7-10 (Serviços): vlr_total = qtd × vlr_unitario (sem fator 12)
--
-- Contrato 29/2024 | PORTFOLIO | pk_id_con=28 | R$ 23.324.551,95 (2 itens)
--
-- Contrato 21/2021 | ELOGROUP | pk_id_con=2
--   ⚠ PDF com tabela de preços não disponível. Inserir manualmente.

START TRANSACTION;

INSERT INTO tb_contrato_recurso_cre (
    num_numero_contrato_cre, num_seq_recurso_cre,
    dsc_especificacao_recurso_cre, dsc_unidade_medida_recurso_cre,
    qtd_quantidade_recurso_cre, vlr_valor_unitario_recurso_cre, vlr_valor_total_recurso_cre,
    log_status_cre, dsc_usuario_cre, pk_id_con
) VALUES

-- ── CONTRATO 03/2024 — GOLDEN TECHNOLOGIA LTDA. (pk_id_con = 13) ─────────────
-- Tabela 1 – SaaS  |  vlr_total_anual = 12 × qtd × vlr_unit_mensal

('03/2024', 1,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Frontline Worker Starter',
 'LICENÇA', 50000, 19.00, 11400000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 50.000 × R$19,00 = R$11.400.000,00 ✓

('03/2024', 2,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Frontline Worker Standard',
 'LICENÇA', 15000, 44.30, 7974000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 15.000 × R$44,30 = R$7.974.000,00 ✓

('03/2024', 3,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Starter',
 'LICENÇA', 20000, 33.80, 8112000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 20.000 × R$33,80 = R$8.112.000,00 ✓

('03/2024', 4,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Standard',
 'LICENÇA', 3484, 93.80, 3921590.40, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 3.484 × R$93,80 = R$3.921.590,40 ✓

('03/2024', 5,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Workspace Enterprise Plus',
 'LICENÇA', 1000, 108.00, 1296000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 1.000 × R$108,00 = R$1.296.000,00 ✓

('03/2024', 6,
 'Cessão de direito de uso de Software em Nuvem Pública como SaaS, Google Vault',
 'LICENÇA', 200, 21.00, 50400.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 12 × 200 × R$21,00 = R$50.400,00 ✓

-- Tabela 2 – Serviços  |  vlr_total = qtd × vlr_unit (sem fator 12)

('03/2024', 7,
 'Serviço de implantação e Migração Solução de produtividade e colaboração',
 'Usuário', 85997, 10.00, 859970.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 85.997 × R$10,00 = R$859.970,00 ✓

('03/2024', 8,
 'Treinamento para ADMINISTRADOR da solução de produtividade e colaboração Google Workspace',
 'Turmas', 20, 9000.00, 180000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 20 × R$9.000,00 = R$180.000,00 ✓

('03/2024', 9,
 'Treinamento para Usuário Solução de produtividade e colaboração Google Workspace',
 'Usuário', 86000, 9.90, 851400.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 86.000 × R$9,90 = R$851.400,00 ✓

('03/2024', 10,
 'Serviços de gerenciamento, orquestração da nuvem, sustentação emergencial, administração dos projetos',
 'UST', 90000, 135.00, 12150000.00, 'ativo', 'seed_pdf_03_2024', 13),
-- 90.000 × R$135,00 = R$12.150.000,00 ✓

-- ── CONTRATO 29/2024 — PORTFOLIO CONSULTORIA EMPRESARIAL LTDA. (pk_id_con = 28) ──

('29/2024', 1,
 'UNIDADE DE SERVIÇO TÉCNICO A: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – LEVANTAMENTO DOS SERVIÇOS E GESTÃO DO PROCESSO DE TRANSFORMAÇÃO DE SERVIÇOS.',
 'UST-A', 22443, 79.80, 1790951.40, 'ativo', 'seed_pdf_29_2024', 28),
-- 22.443 × R$79,80 = R$1.790.951,40 ✓

('29/2024', 2,
 'UNIDADE DE SERVIÇO TÉCNICO B: TRANSFORMAÇÃO E IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS – IMPLEMENTAÇÃO DOS SERVIÇOS DIGITAIS.',
 'UST-B', 246239, 87.45, 21533600.55, 'ativo', 'seed_pdf_29_2024', 28);
-- 246.239 × R$87,45 = R$21.533.600,55 ✓

COMMIT;

-- ── Verificação pós-seed ──────────────────────────────────────────────────────

SELECT
    cre.num_numero_contrato_cre          AS contrato,
    COUNT(*)                              AS qtd_itens,
    SUM(cre.vlr_valor_total_recurso_cre) AS total_R$,
    con.vlr_valor_total_contrato_con      AS total_contrato_R$
FROM tb_contrato_recurso_cre cre
JOIN tb_contrato_con con ON con.pk_id_con = cre.pk_id_con
WHERE cre.pk_id_con IN (13, 28)
GROUP BY cre.num_numero_contrato_cre, con.vlr_valor_total_contrato_con;

-- Resultado esperado (totais devem ser iguais):
-- 03/2024 | 10 | 46.795.360,40 | 46.795.360,40
-- 29/2024 |  2 | 23.324.551,95 | 23.324.551,95