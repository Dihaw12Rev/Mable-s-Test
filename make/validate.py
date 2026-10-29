#!/usr/bin/env python3
"""Static checks for the built blueprints: unique module IDs, every {{N.x}} reference
points to a module that runs earlier on the same path, and every Code module parses."""
import json, pathlib, re, subprocess, sys, tempfile

DIST = pathlib.Path(__file__).resolve().parent / "dist"
REF = re.compile(r"(?<![\w.`])(\d+)\.")
errors = []

def refs(obj):
    s = json.dumps({k: v for k, v in obj.items() if k in ("mapper", "filter", "outputs")})
    out = set()
    for expr in re.findall(r"\{\{(.*?)\}\}", s):
        expr = re.sub(r'\\?"[^"]*\\?"', "", expr)          # drop string literals
        out |= {int(n) for n in REF.findall(expr)}
    return out

def walk(flow, seen, ids, fname):
    seen = list(seen)
    for m in flow:
        if m["id"] in ids:
            errors.append(f"{fname}: duplicate id {m['id']}")
        ids.add(m["id"])
        for r in sorted(refs(m)):
            if r not in seen:
                errors.append(f"{fname}: module {m['id']} ({m['module']}) references {r}, which hasn't run yet")
        for e in m.get("onerror") or []:
            ids.add(e["id"])
            if e["module"] == "builtin:Break" and not all(isinstance(e["mapper"].get(k), int) for k in ("count", "interval")):
                errors.append(f"{fname}: retry handler {e['id']} needs numeric count/interval (Make rejects text)")
        lim = (m.get("mapper") or {}).get("limit")
        if lim is not None and not isinstance(lim, int) and not str(lim).startswith("{{"):
            errors.append(f"{fname}: module {m['id']} limit must be a number, got {lim!r}")
        seen.append(m["id"])
        for route in m.get("routes", []):
            walk(route["flow"], seen, ids, fname)
        if m["module"] == "code:ExecuteCode":
            js = "(function(input){\n" + m["mapper"]["codeEditorJavascript"] + "\n})"
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(js)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            if r.returncode:
                errors.append(f"{fname}: code module {m['id']} does not parse: {r.stderr.strip()[:300]}")

for p in sorted(DIST.rglob("*.json")):
    bp = json.loads(p.read_text())
    walk(bp["flow"], [], set(), p.name)
    print(f"checked {p.name}")
print("\n".join(errors) if errors else "OK: no problems found")
sys.exit(1 if errors else 0)
