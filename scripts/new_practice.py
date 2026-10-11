#!/usr/bin/env python3
"""Создаёт каркас практической работы: PLAN.md, env.sh, notes/, report/{config.json,shots.py,build_report.py}.

    python3 new_practice.py <каталог pr-N> --no N --student-surname <Фамилия> --student-short "<Фамилия И.О.>" \
        --group <группа> --discipline "<дисциплина>" --supervisor "<должность Фамилия И.О.>" \
        [--institute "..."] [--department "..."] [--logo путь_к_картинке] [--title "тема"]

Значений по умолчанию для студента, группы, дисциплины и руководителя нет – их сообщает пользователь.
Логотип необязателен: если указан --logo, файл копируется в report/. Существующие файлы не перезаписываются.
"""
import argparse, json, os, shutil

SK = os.path.join(os.path.expanduser("~"), ".claude/skills/practice-report")


def put(src, dst, repl=None):
    if os.path.exists(dst):
        print("пропуск (уже есть):", dst)
        return
    s = open(src, encoding="utf-8").read()
    for k, v in (repl or {}).items():
        s = s.replace(k, v)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(s)
    print("создан:", dst)


ap = argparse.ArgumentParser()
ap.add_argument("target")
ap.add_argument("--no", required=True)
ap.add_argument("--student-surname", required=True)
ap.add_argument("--student-short", required=True)
ap.add_argument("--group", required=True)
ap.add_argument("--discipline", required=True)
ap.add_argument("--supervisor", required=True)
ap.add_argument("--institute", default="")
ap.add_argument("--department", default="")
ap.add_argument("--logo", default="")
ap.add_argument("--title", default="{тема}")
a = ap.parse_args()

t = os.path.abspath(a.target)
rep = {"{N}": a.no, "{тема}": a.title, "prN": f"pr{a.no}", "ПР{N}": f"ПР{a.no}", "pr-N": f"pr-{a.no}"}
put(os.path.join(SK, "templates/PLAN.md"), os.path.join(t, "PLAN.md"), rep)
put(os.path.join(SK, "templates/env.sh"), os.path.join(t, "env.sh"), rep)
put(os.path.join(SK, "templates/shots.py"), os.path.join(t, "report/shots.py"), rep)
put(os.path.join(SK, "templates/build_report.py"), os.path.join(t, "report/build_report.py"), rep)
os.makedirs(os.path.join(t, "notes"), exist_ok=True)
os.makedirs(os.path.join(t, "report/screenshots"), exist_ok=True)

logo = ""
if a.logo:
    if os.path.exists(a.logo):
        logo = os.path.join(t, "report", os.path.basename(a.logo))
        if not os.path.exists(logo):
            shutil.copy(a.logo, logo)
    else:
        print("логотип не найден, пропуск:", a.logo)

cfgp = os.path.join(t, "report/config.json")
if not os.path.exists(cfgp):
    cfg = json.load(open(os.path.join(SK, "templates/config.example.json"), encoding="utf-8"))
    cfg.update(practice_no=a.no, group=a.group, discipline=a.discipline, supervisor=a.supervisor,
               student_surname=a.student_surname, student_short=a.student_short, logo=logo)
    for k in ("institute", "department"):
        if getattr(a, k):
            cfg[k] = getattr(a, k)
        else:
            cfg.pop(k, None)
    json.dump(cfg, open(cfgp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("создан:", cfgp)
