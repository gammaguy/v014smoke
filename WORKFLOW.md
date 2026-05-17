---
# Project identity
project:
  name: "<project-name>"               # e.g., "trading-system"
  github_repo: "<owner>/<repo>"        # GitHub repo this harness operates on

# Tracker settings
tracker:
  type: github
  poll_interval_seconds: 30

# Agent roles — map each pipeline role to a specific model + access method
# Each role requires either `cli` (subprocess) or `endpoint` (HTTP), not both.
# `session` distinguishes parallel sessions of the same CLI to reduce
# confirmation bias (e.g., decomposer and spec_refiner both use Claude
# but on different sessions).
agents:
  # v0.11 #3: haggle critics are configurable via agents.haggle_critics
  # below.  The default pair (qwen + deepseek-r1) shown is what fires
  # when haggle_critics is absent; declaring it explicitly lets you
  # disable critics ([]), swap models, or add a custom critic with its
  # own prompt template.  See the haggle_critics: block further down.
  #
  # Closing checkpoint roles (Gemini + Claude refiner + Claude critic)
  # remain constructed by pipeline_impl.build_concrete_impls; they are
  # not yet configurable.  Adding them follows the same pattern as
  # haggle_critics — captured for a future iteration.
  #
  # Fallback: if Gemini CLI is not installed or vLLM/DeepSeek are
  # not reachable, the orchestrator's adapters degrade gracefully:
  # ClaudeTestWriterAdapter takes over for test_writer, and the
  # closing checkpoint reports Gemini failure cleanly. Operating
  # without these is supported but loses model-diversity properties.

  spec_author:
    model: gemini-2.5-pro
    cli: gemini
    extra_config:
      gemini_bin: gemini

  spec_refiner:
    model: claude
    cli: claude_code
    session: spec_refiner

  spec_critic:
    model: claude
    cli: claude_code
    session: spec_critic

  decomposer:
    model: claude
    cli: claude_code
    session: decomposer

  contract_reviser:
    model: claude
    cli: claude_code
    session: decomposer

  # v0.11 #3: haggle critics (config-driven; the default pair below
  # matches pre-v0.11 #3 behavior).  Each entry needs name (operator-
  # visible identifier shown in critic verdicts) + prompt_template
  # (resolved against the default prompts dir, then paths.prompts_override).
  # The model field selects the LLM call factory by hint-based dispatch:
  # 'qwen' or a vLLM endpoint -> reuses vllm_client; 'deepseek' ->
  # reuses the deepseek API client; 'claude' or cli=claude_code ->
  # reuses claude_call.  Adding a fourth LLM family requires a
  # pipeline_impl.py change.
  #
  # To disable critics entirely (only schema_validator runs at haggle),
  # set `haggle_critics: []`.  If you delete this block, the default
  # pair fires.  If every configured entry has an unrecognized model,
  # the orchestrator logs a WARNING per skipped entry and falls
  # through to schema_validator-only haggle — check orch.log if you
  # expected critics to fire but don't see them.
  haggle_critics:
    - name: qwen
      prompt_template: contract_critic_qwen
      # v0.14 #1 part 1 / TOOL-WORKFLOW-TEMPLATE-MODEL-NAME-MISMATCH:
      # `qwen` is the short alias matching the conventional vLLM
      # launch flag `--served-model-name qwen`.  For a different
      # deployment, set this to the full HF model id (e.g.
      # `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ`) or whatever id your
      # vLLM endpoint reports at /v1/models.
      model: qwen
      endpoint: http://127.0.0.1:8000/v1
      extra_config:
        max_tokens: 4096
    - name: deepseek-r1
      prompt_template: contract_critic_deepseek_r1
      model: deepseek-reasoner
      endpoint: https://api.deepseek.com/v1
      extra_config:
        api_key_env: DEEPSEEK_API_KEY
        # max_tokens intentionally omitted: deepseek-reasoner falls
        # through to MODEL_MAX_TOKENS_DEFAULTS in
        # src/agent_orch/clients/deepseek.py (16384) — reasoning models
        # need headroom for chain-of-thought tokens, which count against
        # max_tokens alongside the answer. Only set max_tokens here to
        # override for a project-specific reason; this template carries
        # overrides, not defaults.

  codex_implementer:
    model: codex
    cli: codex
    extra_config:
      codex_bin: codex

  test_writer:
    # v0.14 #1 part 1 / TOOL-WORKFLOW-TEMPLATE-MODEL-NAME-MISMATCH:
    # see the haggle_critics/qwen entry above for the alias rationale.
    model: qwen
    endpoint: http://127.0.0.1:8000/v1
    extra_config:
      max_tokens: 8192
      temperature: 0.2

  reviewer_primary:
    model: claude
    cli: claude_code
    session: reviewer

  reviewer_panel:
    # v0.14 #1 part 1 / TOOL-WORKFLOW-TEMPLATE-MODEL-NAME-MISMATCH:
    # see the haggle_critics/qwen entry above for the alias rationale.
    - model: qwen
      endpoint: http://127.0.0.1:8000/v1
      extra_config:
        max_tokens: 4096
    - model: deepseek-reasoner
      endpoint: https://api.deepseek.com/v1
      extra_config:
        api_key_env: DEEPSEEK_API_KEY
        # max_tokens intentionally omitted — see the deepseek-r1 haggle
        # critic entry above. Falls through to MODEL_MAX_TOKENS_DEFAULTS
        # in src/agent_orch/clients/deepseek.py (16384).
    - model: gemini-2.5-pro
      cli: gemini
      extra_config:
        gemini_bin: gemini

# Project-wide defaults
defaults:
  tier: critical              # this project treats everything as mission-critical

# Per-issue git worktree settings
workspace:
  root: "./workspaces"
  cleanup_on_close: true
  cleanup_branches_after_days: 30
  # T8: pre-PR verify gate. When set, Codex runs this command inside its
  # implementation turn before producing the self-review JSON; the
  # orchestrator gates on tests_passing and retries via continuation
  # guidance up to pre_pr_verify_max_retries times before surfacing the
  # 3-way operator prompt (proceed-anyway / abandon-item / investigate).
  # Leave unset to skip the gate entirely; CI remains the only check.
  # pre_pr_verify_command: "pytest -q"
  # pre_pr_verify_max_retries: 1

# Per-agent concurrency caps (tuned to subscription rate limits)
concurrency:
  max_concurrent_codex: 4
  max_concurrent_claude: 3
  max_concurrent_gemini: 2
  max_concurrent_local_llm: 8
  max_concurrent_deepseek_api: 4

# Paths to project-local overrides
paths:
  prompts_override: ".cowork/prompts/"     # project-local prompt files
  critics: ".cowork/critics/"              # project-local domain critics
  invariants: ".invariants.yaml"

# Closing checkpoint behavior
closing_checkpoint:
  auto_trigger: true
  panel_verifiers:
    - claude
    # Add more verifiers as desired (e.g., a second Claude session, local qwen)

# Project-wide debt defenses
debt_defenses:
  accept_with_adjustments_followup_days: 7
  boy_scout_required: true
  weekly_debt_window_hours: 4

# Pattern-detector alert thresholds (replacing hard caps)
alerts:
  spec_issue_count_warning: 50
  rework_chain_similarity_threshold: 0.8
  duplicate_issue_similarity: 0.9

# Haggle settings
haggle:
  contract_haggle_max_cycles: 2
  contract_haggle_similarity_threshold: 0.85
  spec_haggle_cycle_limit: null           # unlimited; human decides
  spec_haggle_advisory_threshold: 5
  spec_haggle_concern_aging: 3

# Specialist reviewers (domain-specific). Empty by default; populate when needed.
# Example for a trading project:
#   specialist_reviewers:
#     - role: risk
#       prompt: ".cowork/critics/risk_reviewer.md"
#       model: claude
#       triggers_on: paths       # only on PRs touching strategy/execution paths
specialist_reviewers: []
---

# Project notes

This is a starter WORKFLOW.md for a new project. Customize the values above.

## Customizing for your project

The most likely changes:

1. **`project.name` and `project.github_repo`** — required, project-specific.
2. **Concurrency caps** — tune based on your observed subscription rate limits.
3. **`reviewer_panel`** — for early projects, you may want fewer panel members
   to reduce wall-clock latency. Add panel members as the project matures.
4. **`specialist_reviewers`** — start empty. Add when you have specific failure
   modes a domain-specific critic would catch.
5. **`paths.prompts_override`** — populate when you want project-specific
   prompt language (e.g., trading-specific examples in the decomposer prompt).

## How the harness uses this

The orchestrator reads this file at startup and on file change (the harness
watches for modifications). Most changes apply to future dispatches; in-flight
agent sessions complete with the prior config. Concurrency limit changes apply
to new dispatches immediately.

## Notes block (optional)

This markdown body is preserved as `notes` in the parsed Workflow but ignored
by the harness logic. Use it for human-readable project context that doesn't
fit in the structured frontmatter.
