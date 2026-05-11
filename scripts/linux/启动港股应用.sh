#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/hk/hk_pipeline_app.py"
