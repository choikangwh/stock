#!/bin/bash
echo "=================================================="
echo "  Stock Analyst Dashboard 를 실행하는 중입니다..."
echo "=================================================="

# 1. Python 설치 확인
if ! command -v python3 &> /dev/null
then
    echo "[오류] 시스템에 Python3가 설치되어 있지 않습니다."
    echo "Python3를 설치한 후에 다시 실행해주세요."
    exit 1
fi

# 2. 가상환경 설정 및 활성화
if [ ! -d ".venv" ]; then
    echo "가상환경(.venv)을 생성하고 있습니다..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 3. 패키지 설치
echo "필요한 패키지 라이브러리를 설치/업데이트하고 있습니다..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# 4. 대시보드 실행
echo "=================================================="
echo "  대시보드가 웹 브라우저에서 실행됩니다."
echo "  Gemini API Key는 브라우저 화면에서 직접 입력하세요."
echo "=================================================="
streamlit run app.py
