#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/tools/company_compare_app.py"
