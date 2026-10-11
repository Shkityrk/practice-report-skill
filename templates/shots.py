"""Съёмка скриншотов ПР{N}. Запуск:  <venv>/bin/python -I report/shots.py > notes/shots-run.log 2>&1

Принципы: (1) начать с чистого состояния, (2) снимать этапы в порядке методички, (3) команды – настоящие,
(4) всё, что может раскрыть секрет, подменять через (команда, "как показать"), (5) в конце – освободить ресурсы.
"""
import os, subprocess, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude/skills/practice-report/scripts"))
from playwright.sync_api import sync_playwright
from shots_lib import Shooter, find_chrome

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SECRETS = []   # строки, которые нельзя показывать (токены, имя рабочего контекста, адреса): маскируются везде
S = Shooter(ROOT, os.path.join(HERE, "screenshots"), os.path.join(ROOT, "notes"), prompt="user@host pr-N %",
            redact=SECRETS)


def main():
    procs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=find_chrome())   # None -> Playwright выберет свой билд
        page = b.new_page()

        # 0. чистое состояние (удалить пробные запуски, тома, дополнения – всё, что мешает повторяемости)
        S.sh("true")

        # 1. этап методички -> кадр (имя файла = порядок в отчёте)
        S.shot(page, "01-example.png", "Заголовок окна", [
            "echo пример команды",
            ("echo токен=$(cat .secret)", "echo токен=<из файла>"),   # подмена подписи; вывод команды секрета не печатает
        ])

        # 2. браузер (если нужен): S.browser_shot(page, "02-browser.png", url, width=900, height=620)
        # 3. фоновые процессы: p = S.bg("..."); url = S.wait_url(p, r"http://127\.0\.0\.1:\d+"); procs.append(p)

        for p in procs:
            p.terminate()
        b.close()
    subprocess.run("true", shell=True)   # добить фоновые процессы: pkill -f '<шаблон>'


if __name__ == "__main__":
    main()
