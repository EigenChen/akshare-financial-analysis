#!/bin/bash
set -e

cd "$(dirname "$0")/../.."
streamlit run "apps/portal/unified_portal.py"
