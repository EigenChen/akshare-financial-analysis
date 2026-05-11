#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/tools/excel_viewer_app.py"
