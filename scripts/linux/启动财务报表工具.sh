#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/tools/report_downloader_app.py"
