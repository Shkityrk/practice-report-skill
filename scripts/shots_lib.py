"""Съёмка скриншотов для отчёта: «терминальные кадры» из реального вывода команд + кадры браузера (Playwright).

Идея: команды выполняются НАСТОЯЩИЕ, вывод сохраняется в notes/*.log, а затем рисуется как окно терминала.
Так снимки воспроизводимы, а в кадр можно подставить «безопасную» подпись команды (shown), не раскрывая
секреты/адреса. Для окружения с изолированной конфигурацией (kubeconfig и т.п.) команды запускаются через
`source env.sh` – см. references/safety.md.
"""
import glob, html, os, re, subprocess, time

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CSS = """
body{margin:0;background:#fff;font-family:Menlo,'DejaVu Sans Mono',monospace}
.win{width:1180px;background:#1e1f22;border-radius:8px;overflow:hidden;box-shadow:0 0 0 1px #444}
.bar{background:#2b2d30;height:28px;display:flex;align-items:center;padding:0 12px;color:#aaa;font:12px -apple-system,Helvetica,Arial}
.dot{width:12px;height:12px;border-radius:50%;margin-right:7px}
pre{margin:0;padding:14px 18px;color:#d4d4d4;font-size:13.5px;line-height:1.38;white-space:pre-wrap;word-break:break-all}
.p{color:#6a9955}.c{color:#9cdcfe}
"""


def find_chrome():
    """Ищет уже скачанный headless-chromium Playwright (версия Playwright может хотеть другой билд – берём то, что есть)."""
    pats = ["~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell",   # macOS
            "~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"]            # Linux
    found = sorted(p for pat in pats for p in glob.glob(os.path.expanduser(pat)))
    return found[-1] if found else None


class Shooter:
    def __init__(self, root, out_dir, notes_dir, prompt="user@host %", env_file="env.sh", shell="/bin/zsh",
                 redact=None):
        """redact – список строк (токены, имена рабочих контекстов, адреса), которые маскируются как «<скрыто>»
        и в подписи команды, и в её выводе, и в notes/*.log. Подмена `(команда, "как показать")` скрывает только
        подпись, поэтому сама команда не должна печатать секрет, либо он обязан быть в redact."""
        self.root, self.out, self.notes = root, out_dir, notes_dir
        self.prompt, self.env_file, self.shell = prompt, env_file, shell
        self.redact = [s for s in (redact or []) if s]
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(notes_dir, exist_ok=True)

    def _prefix(self):
        has_env = os.path.exists(os.path.join(self.root, self.env_file))
        return f"source ./{self.env_file} >/dev/null && " if has_env else ""

    def sh(self, cmd, timeout=600):
        """Выполняет команду в корне работы, предварительно подключив изолированное окружение (env.sh)."""
        r = subprocess.run(f'cd "{self.root}" && {self._prefix()}{cmd}', shell=True, capture_output=True,
                           text=True, timeout=timeout, executable=self.shell)
        return self._mask(ANSI.sub("", r.stdout + r.stderr).rstrip("\n"))

    def _mask(self, text):
        for s in self.redact:
            text = text.replace(s, "<скрыто>")
        return text

    def bg(self, cmd):
        """Фоновый процесс (проброс порта, веб-интерфейс --url ...). Не забудьте .terminate()."""
        return subprocess.Popen(f'cd "{self.root}" && {self._prefix()}{cmd}', shell=True, executable=self.shell,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    @staticmethod
    def wait_url(proc, pattern, timeout=120):
        """Ждёт в stdout фонового процесса строку по регулярке (например, URL веб-интерфейса)."""
        os.set_blocking(proc.stdout.fileno(), False)
        t0, buf = time.time(), ""
        while time.time() - t0 < timeout:
            try:
                chunk = proc.stdout.read()
            except Exception:
                chunk = None
            if chunk:
                buf += chunk
                m = re.search(pattern, buf)
                if m:
                    return m.group(0)
            time.sleep(1)
        raise RuntimeError("не дождались: " + buf[-300:])

    def term_html(self, title, blocks):
        body = "".join(f'<span class="p">{html.escape(self.prompt)}</span> <span class="c">{html.escape(c)}</span>\n'
                       f'{html.escape(o)}\n' for c, o in blocks)
        return (f"<html><head><meta charset=utf-8><style>{CSS}</style></head><body><div class=win id=w><div class=bar>"
                "<span class=dot style=background:#ff5f57></span><span class=dot style=background:#febc2e></span>"
                f"<span class=dot style=background:#28c840></span>{html.escape(title)}</div><pre>{body}</pre></div></body></html>")

    def render(self, page, name, title, blocks):
        """blocks: [(показанная_команда, вывод)] -> PNG окна терминала + лог в notes/."""
        blocks = [(self._mask(c), self._mask(o)) for c, o in blocks]
        with open(os.path.join(self.notes, name.replace(".png", ".log")), "w", encoding="utf-8") as f:
            for c, o in blocks:
                f.write(f"$ {c}\n{o}\n\n")
        page.set_viewport_size({"width": 1220, "height": 600})
        page.set_content(self.term_html(title, blocks))
        page.locator("#w").screenshot(path=os.path.join(self.out, name))
        print("shot", name, flush=True)

    def shot(self, page, name, title, steps):
        """steps: строки-команды или кортежи (команда, показать_как). Команды выполняются реально.
        `показать_как` нужен, если реальная команда содержит секрет/локальный адрес, а в отчёте нужна «чистая» запись."""
        blocks = []
        for s in steps:
            cmd, shown = (s, s) if isinstance(s, str) else s
            blocks.append((shown or cmd, self.sh(cmd)))
        self.render(page, name, title, blocks)

    def browser_shot(self, page, name, url, width=900, height=620, full_page=False, wait_ms=1000):
        """Кадр страницы в браузере. Для длинных страниц (веб-интерфейсы) задайте большую height вместо full_page."""
        page.set_viewport_size({"width": width, "height": height})
        page.goto(url)
        time.sleep(wait_ms / 1000)
        page.screenshot(path=os.path.join(self.out, name), full_page=full_page)
        print("shot", name, flush=True)
