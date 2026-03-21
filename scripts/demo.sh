#!/bin/bash
# HireKit Demo Script — for asciinema recording
# Usage: asciinema rec demo.cast -c "bash scripts/demo.sh"

set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

DELAY=1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  HireKit — AI-powered company analysis CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep $DELAY

echo "$ hirekit --version"
hirekit --version
echo ""
sleep $DELAY

echo "$ hirekit sources"
hirekit sources
echo ""
sleep $DELAY

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. Company Analysis — 카카오"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "$ hirekit analyze 카카오 --no-llm -o terminal"
hirekit analyze 카카오 --no-llm -o terminal
echo ""
sleep $DELAY

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  2. Interview Prep — 카카오 PM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "$ hirekit interview 카카오 --position PM -o terminal"
hirekit interview 카카오 --position PM -o terminal
echo ""
sleep $DELAY

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done! Visit: https://github.com/zihoshin-dev/hirekit"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
