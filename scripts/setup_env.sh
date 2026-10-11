#!/bin/sh
# Создаёт изолированное Python-окружение для скилла: python-docx (отчёт), playwright (скриншоты), pymupdf (чтение PDF).
# Ничего не ставит в системный Python. Браузер Playwright НЕ скачивается: используется уже имеющийся (shots_lib.find_chrome).
set -e
VENV="${PRACTICE_VENV:-$HOME/.cache/practice-report-venv}"
if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
"$VENV/bin/pip" install -q python-docx playwright pymupdf
"$VENV/bin/python" -I -c "import docx, playwright, pymupdf; print('ok:', '$VENV')"
