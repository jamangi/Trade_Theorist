"""Build a wheel and exercise both command versions in a clean, offline installation.

Prepare a wheelhouse separately with: python -m pip download -r requirements.lock -d PATH
This check never downloads; supply wheels matching the current Python/platform.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    wheelhouse = Path(args.wheelhouse).resolve()
    logs = repo / ".local" / "installed-logs"
    logs.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="trade-theorist-installed-") as temp:
        root = Path(temp)
        guard = root / "guard"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(
            "import socket\ndef forbidden(*a, **kw): raise AssertionError('Network forbidden during installed check')\n"
            "socket.socket.connect = forbidden\nsocket.socket.connect_ex = forbidden\nsocket.create_connection = forbidden\n")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("TRADE_THEORIST_", "PYTHON", "PIP_"))}
        env.update(PYTHONPATH=str(guard), PYTHONNOUSERSITE="1", PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
        def run(name, command, expected=0, cwd=root):
            log = logs / (name + ".log")
            with log.open("w", encoding="utf-8") as output:
                result = subprocess.run([str(p) for p in command], cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=180)
            if result.returncode != expected:
                print(f"FAIL {name}: {log}")
                print(log.read_text(encoding="utf-8")[-2000:])
                raise RuntimeError(f"{name} exited {result.returncode}; expected {expected}")
            return log
        run("build", [sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "--wheel-dir", root / "wheel", repo])
        run("venv", [sys.executable, "-m", "venv", root / "env"])
        binary = root / "env" / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        cli = binary / ("trade-theorist.exe" if os.name == "nt" else "trade-theorist")
        run("install", [python, "-m", "pip", "install", "--no-index", "--find-links", wheelhouse,
                        "-r", repo / "requirements.lock", next((root / "wheel").glob("*.whl"))])
        run("package-origin", [python, "-c", "import sys,trade_theorist; from pathlib import Path; assert Path(trade_theorist.__file__).is_relative_to(sys.prefix); print('Installed package, no checkout imports')"])
        evidence = dict(installation="fresh venv and built wheel outside checkout", network="socket trap and pip --no-index", versions={})
        for version in (1, 2):
            common = ["--projection-version", str(version), "--fixture", "--data-root", str(root / f"data-v{version}")]
            output = ["--output-root", str(root / "bundle-v2")] if version == 2 else []
            first = run(f"v{version}-demo", [cli, "demo", *common, *output])
            demo = json.loads(first.read_text())
            run(f"v{version}-resume", [cli, "demo", *common, *output])
            evaluation = ["--portfolio", demo["portfolio"], "--as-of", "2099-01-11T21:00:00Z", "--receipt-cutoff", demo["as_of"]] if version == 2 else []
            run(f"v{version}-evaluate", [cli, "evaluate", *common, *evaluation])
            cutoff = ["--as-of", demo["as_of"]] if version == 2 else []
            run(f"v{version}-export", [cli, "export", *common, *output, *cutoff])
            run(f"v{version}-doctor", [cli, "doctor", *common, *output], expected=0 if version == 2 else 2)
            index = Path(demo["report"])
            reports = list(index.parent.rglob("report.json"))
            if not index.exists() or not reports:
                raise RuntimeError("Installed dashboard assets missing")
            report = reports[0]
            run(f"v{version}-validate", [cli, "validate", report])
            shutil.copyfile(report, logs / f"v{version}-report.json")
            evidence["versions"][str(version)] = dict(demo="passed", resume="passed", evaluate="passed", export="passed", doctor="passed", validate="passed", model_calls=demo["model_calls"])
        (logs / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS clean installed v1/v2 workflows, offline. Evidence and logs: {logs}")


if __name__ == "__main__":
    main()
