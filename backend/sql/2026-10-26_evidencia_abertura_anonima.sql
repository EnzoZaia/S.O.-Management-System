-- Evidências anexadas na abertura anônima de OS (aluno/funcionário sem login) não têm usuário.
-- O autor passa a ser opcional; as evidências de usuários logados continuam com usuario_id preenchido.
ALTER TABLE evidencia_ordem ALTER COLUMN usuario_id DROP NOT NULL;
