"""Strict, locally owned bundles. No request-time filesystem access or trust in JS input."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import files
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from types import MappingProxyType

from .contracts import ContractError, digest

FORMAT = 1
RETAIN = 20
MAX_FILE = 32 * 1024 * 1024
APP_ASSETS = ("app.js", "private.js", "style.css", "favicon.svg")
ASSETS = frozenset({"index.html", "schema.json", "report.json", *APP_ASSETS})
VERSION = re.compile(r"[0-9a-f]{64}")


def checked_path(value, *, outside_git=False):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ContractError("Bundle path must be absolute")
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            info = None
        if info and (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ContractError("Bundle paths cannot use symlinks or junctions")
        if outside_git and (part / ".git").exists():
            raise ContractError("Serving requires a bundle root outside every Git checkout")
    return path.resolve()


def read_bytes(path):
    checked_path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE or info.st_nlink != 1:
        raise ContractError("Bundle asset must be a bounded ordinary file")
    with path.open("rb") as handle:
        value = handle.read(MAX_FILE + 1)
    if len(value) > MAX_FILE:
        raise ContractError("Bundle asset is too large")
    return value


def reject_private_text(value):
    """Reject recognizable secrets/absolute locators, including in allowed prose.

    This is a conservative guard, not a universal secret detector. Upstream typed
    selection remains required and the owner must not author secrets into prose.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            reject_private_text(key)
            reject_private_text(item)
    elif isinstance(value, list):
        for item in value:
            reject_private_text(item)
    elif isinstance(value, str) and re.search(
        r"(?i)(?:-----BEGIN[ -].*PRIVATE KEY|\b(?:sk|pk)[-_][a-z0-9_-]{16,}|\bAKIA[A-Z0-9]{16}\b|"
        r"\b(?:api[_ -]?key|secret|password|access[_ -]?token|authorization)\s*[:=]\s*\S+|"
        r"\bBearer\s+\S+|\b[a-z]:[\\/]|\\\\[^\s\\]+\\|file://|(?:^|[\s\"'])/(?:home|Users|tmp|var|etc|mnt|private)/)", value):
        raise ContractError("Private text contains a credential or filesystem locator")


def template():
    return files("trade_theorist").joinpath("dashboard", "private.html").read_text(encoding="utf-8")


def manifest(version, report, assets):
    return dict(bundle_format=FORMAT, publication_class="private-owner-v2", version_id=version,
                generated_at=report["generated_at"], report_hash=report["content_hash"],
                assets={name: dict(sha256=sha256(body).hexdigest(), bytes=len(body)) for name, body in sorted(assets.items())})


def load_version(folder):
    """Only the shipped application and strict report/schema can be admitted."""
    from .export_v2 import PRIVATE_SCHEMA, validate_private
    checked_path(folder)
    if not VERSION.fullmatch(folder.name):
        raise ContractError("Unknown bundle version")
    if {p.name for p in folder.iterdir()} != ASSETS | {"manifest.json"}:
        raise ContractError("Unknown or missing bundle assets")
    assets = {name: read_bytes(folder / name) for name in ASSETS}
    meta = json.loads(read_bytes(folder / "manifest.json"))
    if not isinstance(meta, dict) or type(meta.get("bundle_format")) is not int:
        raise ContractError("Unsupported bundle manifest")
    report = validate_private(json.loads(assets["report.json"]))
    reject_private_text(report)
    if json.loads(assets["schema.json"]) != PRIVATE_SCHEMA:
        raise ContractError("Private schema differs from installed package")
    source = files("trade_theorist").joinpath("dashboard")
    for name in APP_ASSETS:
        if assets[name] != source.joinpath(name).read_text(encoding="utf-8").encode():
            raise ContractError("Bundle executable assets differ from installed package")
    html = template()
    original = {name: body.decode("utf-8") for name, body in assets.items() if name != "index.html"}
    version = digest(["private-bundle-v1", html, original])
    expected_index = html.replace("<!--BASE-->", f'<base href="versions/{version}/">').encode()
    if folder.name != version or assets["index.html"] != expected_index or meta != manifest(version, report, assets):
        raise ContractError("Bundle manifest or content identity differs")
    return report, MappingProxyType(assets)


def load_bundle(root, *, outside_git=True):
    root = checked_path(root, outside_git=outside_git)
    entry = read_bytes(root / "index.html")
    match = re.search(rb'<base href="versions/([0-9a-f]{64})/">', entry)
    if match is None:
        raise ContractError("Re-export this bundle with the current package")
    version = match[1].decode()
    report, assets = load_version(root / "versions" / version)
    if entry != assets["index.html"]:
        raise ContractError("Bundle entry differs from manifest")
    routes = {"/": ("index.html", entry), "/index.html": ("index.html", entry)}
    routes.update({f"/versions/{version}/{name}": (name, body) for name, body in assets.items() if name != "index.html"})
    return report, MappingProxyType(routes)


@contextmanager
def writer(root):
    """OS-released single-writer lock, so a killed publisher leaves no stale lock."""
    path = checked_path(root / ".publish.lock")
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise ContractError("Invalid bundle lock")
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def remove_owned(folder, root):
    """No recursive deletion: exact known ordinary files in a verified child only."""
    if checked_path(folder).parent != checked_path(root / "versions"):
        raise ContractError("Retention path escapes bundle versions")
    if {p.name for p in folder.iterdir()} != ASSETS | {"manifest.json"}:
        return
    for name in ASSETS | {"manifest.json"}:
        read_bytes(folder / name)
    for name in ASSETS | {"manifest.json"}:
        (folder / name).unlink()
    folder.rmdir()


def retain_owned(root, current, *, keep):
    candidates = []
    for folder in (root / "versions").iterdir():
        try:
            load_version(folder)
            candidates.append(folder)
        except (ContractError, OSError, ValueError, TypeError, KeyError):
            continue  # Never delete unrecognized, changed, linked or unrelated data.
    others = sorted((p for p in candidates if p.name != current), key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    for folder in others[max(0, keep - 1):]:
        try:
            remove_owned(folder, root)
        except (ContractError, OSError):
            pass  # Retention failure cannot invalidate a successfully published entry.


def publish(report, root, *, before_publish=None, keep=RETAIN):
    from .export_v2 import PRIVATE_SCHEMA, validate_private
    validate_private(report)
    reject_private_text(report)
    if type(keep) is not int or keep < 1:
        raise ContractError("Retain at least one bundle version")
    root = checked_path(root)
    source = files("trade_theorist").joinpath("dashboard")
    texts = {name: source.joinpath(name).read_text(encoding="utf-8") for name in APP_ASSETS}
    texts.update({"schema.json": json.dumps(PRIVATE_SCHEMA), "report.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n"})
    html = template()
    version = digest(["private-bundle-v1", html, texts])
    texts["index.html"] = html.replace("<!--BASE-->", f'<base href="versions/{version}/">')
    assets = {name: value.encode("utf-8") for name, value in texts.items()}
    if any(len(body) > MAX_FILE for body in assets.values()):
        raise ContractError("Bundle exceeds the per-asset size limit")
    folder = checked_path(root / "versions" / version)
    root.mkdir(parents=True, exist_ok=True)
    with writer(root):
        folder.mkdir(parents=True, exist_ok=True)
        contents = assets | {"manifest.json": (json.dumps(manifest(version, report, assets), sort_keys=True, indent=2) + "\n").encode()}
        # Files are exclusive and immutable. Partial versions can be safely resumed;
        # the entry is replaced only after the entire version passes admission.
        for name, body in contents.items():
            path = checked_path(folder / name)
            if path.exists():
                if read_bytes(path) != body:
                    raise ContractError("Immutable bundle asset changed")
            else:
                with tempfile.NamedTemporaryFile("wb", dir=root, delete=False, prefix=".asset-") as handle:
                    temporary = Path(handle.name)
                    handle.write(body)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
        load_version(folder)
        if before_publish:
            before_publish()
        checked_path(root / "index.html")
        with tempfile.NamedTemporaryFile("wb", dir=root, delete=False, prefix=".entry-") as handle:
            temporary = Path(handle.name)
            handle.write(assets["index.html"])
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, root / "index.html")
        finally:
            temporary.unlink(missing_ok=True)
        retain_owned(root, version, keep=keep)
    return root / "index.html"
