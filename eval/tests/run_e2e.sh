#!/usr/bin/env bash
set -e

# Flags fixas
export E2E_USE_REAL_GOOGLE=1
export E2E_USE_REAL_LLM=1
export E2E_SNIPPET_LIMIT=0
export PYTHONPATH=$(pwd)

echo "🚀 Rodando testes E2E no modo REAL (Google + LLM) sem truncamento..."
python3 eval/tests/e2e_mvp_runner.py
