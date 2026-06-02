#!/usr/bin/env bash
# Configura branch protection rules no GitHub via gh CLI.
# Execute UMA VEZ após criar o repositório remoto:
#   bash scripts/setup-github-protection.sh <owner> <repo>
#
# Requer: gh CLI autenticado com permissão admin no repositório.

set -euo pipefail

OWNER="${1:-}"
REPO="${2:-}"

if [[ -z "$OWNER" || -z "$REPO" ]]; then
    echo "Uso: $0 <owner> <repo>"
    echo "Ex:  $0 vitormoreira fluxdrive"
    exit 1
fi

if ! command -v gh &>/dev/null; then
    echo "Erro: gh CLI não encontrado. Instale em https://cli.github.com/"
    exit 1
fi

echo "Configurando branch protection para ${OWNER}/${REPO}..."
echo ""

# ─── Proteção de 'master' ──────────────────────────────────────────────────
echo "→ Protegendo branch 'master'..."
gh api \
  --method PUT \
  "/repos/${OWNER}/${REPO}/branches/master/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Branch Protection Guard",
      "Code Formatting (black + isort)",
      "Static Type Analysis (mypy strict)",
      "Lint & SOLID Compliance (pylint)",
      "Docstring Coverage (interrogate 100%)",
      "Code Complexity (radon)",
      "Security Audit (bandit)",
      "Tests & Coverage (≥ 80%)",
      "SOLID + Design Patterns Compliance",
      "Quality Gate — Final Verdict"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
EOF

echo "✓ 'master' protegida"
echo ""

# ─── Proteção de 'development' ────────────────────────────────────────────
echo "→ Protegendo branch 'development'..."
gh api \
  --method PUT \
  "/repos/${OWNER}/${REPO}/branches/development/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Branch Protection Guard",
      "Code Formatting (black + isort)",
      "Static Type Analysis (mypy strict)",
      "Lint & SOLID Compliance (pylint)",
      "Docstring Coverage (interrogate 100%)",
      "Code Complexity (radon)",
      "Security Audit (bandit)",
      "Tests & Coverage (≥ 80%)",
      "SOLID + Design Patterns Compliance",
      "Quality Gate — Final Verdict"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
EOF

echo "✓ 'development' protegida"
echo ""

# ─── Desativa merge direto sem PR ─────────────────────────────────────────
echo "→ Configurando regras do repositório..."
gh api \
  --method PATCH \
  "/repos/${OWNER}/${REPO}" \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false \
  --field delete_branch_on_merge=true \
  --field allow_auto_merge=false \
  > /dev/null

echo "✓ Merge commits desabilitados (apenas squash)"
echo "✓ Delete automático de branches habilitado"
echo ""

# ─── Ruleset extra: bloqueia push direto ──────────────────────────────────
echo "→ Criando ruleset para bloqueio total de push direto..."
gh api \
  --method POST \
  "/repos/${OWNER}/${REPO}/rulesets" \
  --input - <<'EOF'
{
  "name": "Protect master and development — no direct push",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/master", "refs/heads/development"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "creation"},
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "Quality Gate — Final Verdict"}
        ]
      }
    }
  ],
  "bypass_actors": []
}
EOF

echo "✓ Ruleset de proteção ativa criado"
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Branch protection configurada com sucesso!"
echo "  Repositório: ${OWNER}/${REPO}"
echo ""
echo "  master     → só aceita PRs de 'development'"
echo "  development → só aceita PRs de branches filhas"
echo "  Ambas      → exigem todos os 10 quality checks"
echo "═══════════════════════════════════════════════════"
