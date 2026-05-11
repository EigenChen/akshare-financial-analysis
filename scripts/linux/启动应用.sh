#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/a_share/a_share_streamlit_app.py"
