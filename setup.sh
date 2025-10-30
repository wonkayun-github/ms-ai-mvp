#!/bin/bash
# ----------------------------------------
# Project setup script
# Description: Installs Python dependencies for PostgreSQL project
# ----------------------------------------

echo "🚀 Starting setup..."

# 1️⃣ Python 가상환경 생성 (선택사항)
# uv venv
# source .venv/bin/activate

# 2️⃣ pip 최신화
echo "🔧 Upgrading pip..."
uv pip install --upgrade pip

# 3️⃣ 필수 패키지 설치
echo "📦 Installing dependencies..."
uv pip install openai streamlit dotenv psycopg2-binary azure-storage-blob azure-search-documents azure-core

# 5️⃣ 완료 메시지
echo "✅ Setup complete! Virtual environment activated."
