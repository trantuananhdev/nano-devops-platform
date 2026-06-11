#!/bin/bash
# Test .env variable interpolation
cd "$(dirname "$0")"
source .env
echo "ACER_HOST: ${ACER_HOST}"
echo "LLM_BASE_URL: ${LLM_BASE_URL}"
