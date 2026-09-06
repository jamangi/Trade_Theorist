from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import http.client
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from trade_theorist.cli import main
from trade_theorist.contracts import ContractError, digest
from trade_theorist.export_v2 import build_private, export_private
from trade_theorist.local_server import create_server, serve
from trade_theorist.operations_v2 import ReadOnlyV2, run_demo, DEMO_CUTOFF
from trade_theorist.private_bundle import ASSETS, load_bundle, load_version, publish, writer
from trade_theorist.storage_v2 import V2Store


class PrivateServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = TemporaryDirectory()
        cls.source = Path(cls.base.name) / "data"
        cls.bundle = Path(cls.base.name) / "bundle"
        with patch("socket.socket.connect", side_effect=AssertionError("No provider calls")):
            run_demo(cls.source, cls.bundle)
        cls.report, _ = load_bundle(cls.bundle)

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data, self.output = self.root / "data", self.root / "bundle"
        self.data.mkdir()
        shutil.copy2(self.source / "research.sqlite3", self.data / "research.sqlite3")
        shutil.copytree(self.bundle, self.output)
        self.folder = next((self.output / "versions").iterdir())
        self.external_calls = []
        original = socket.socket.connect
        def local_only(sock, address):
            if address[0] != "127.0.0.1":
                self.external_calls.append(address)
                raise AssertionError("Provider/network call forbidden")
            return original(sock, address)
        guard = patch("socket.socket.connect", local_only)
        guard.start()
        self.addCleanup(guard.stop)
        for target in ("trade_theorist.learn.model.BoundedModel.complete", "trade_theorist.adapters.alpaca_market_data.AlpacaBarsAdapter._request"):
            provider_guard = patch(target, side_effect=AssertionError("Provider/model call forbidden"))
            provider_guard.start()
            self.addCleanup(provider_guard.stop)

    def start(self):
        server = create_server(self.data, self.output, fixture=True, port=0)
        thread = Thread(target=server.serve_forever, kwargs=dict(poll_interval=0.01), daemon=True)
        thread.start()
        def stop():
            server.shutdown()
            server.server_close()
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.addCleanup(stop)
        return server

    def request(self, server, path="/", method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_exact_assets_headers_offline_refresh_and_fixed_snapshot(self):
        before = (self.data / "research.sqlite3").read_bytes()
        server = self.start()
        for path, (name, expected) in server.routes.items():
            status, headers, body = self.request(server, path)
            self.assertEqual((status, body), (200, expected))
            self.assertEqual(headers["Cache-Control"], "no-store")
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
            self.assertNotIn("Access-Control-Allow-Origin", headers)
            self.assertNotIn("Set-Cookie", headers)
            self.assertNotIn("unsafe-inline", headers["Content-Security-Policy"])
        status, headers, body = self.request(server, method="HEAD")
        self.assertEqual((status, body), (200, b""))
        self.assertGreater(int(headers["Content-Length"]), 0)
        # Tampering with disk after admission cannot change any running response.
        expected = self.request(server)[2]
        (self.output / "index.html").write_text("SECRET-DISK-CONTENT")
        with patch("trade_theorist.local_server.load_bundle", side_effect=AssertionError("No disk reload")):
            self.assertEqual(self.request(server)[2], expected)
        self.assertEqual(before, (self.data / "research.sqlite3").read_bytes())
        self.assertEqual(self.external_calls, [])

    def test_binding_refused_before_validation_or_socket_creation(self):
        with patch("trade_theorist.local_server.load_bundle", side_effect=AssertionError("Must validate bind first")):
            for host in ("0.0.0.0", "localhost", "::", "::1", "192.168.1.2", "127.0.0.2"):
                with self.subTest(host=host), self.assertRaises(ContractError):
                    create_server(self.data, self.output, fixture=True, host=host)
            for port in (-1, 65536, True):
                with self.assertRaises(ContractError):
                    create_server(self.data, self.output, fixture=True, port=port)

    def test_foreign_missing_duplicate_host_origin_and_cross_site_are_refused(self):
        server = self.start()
        for headers in ({"Host": "evil.example"}, {"Host": "localhost:" + str(server.server_port)},
                        {"Origin": "null"}, {"Origin": "https://evil.example"},
                        {"Origin": server.origin + "/"}, {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"}):
            self.assertEqual(self.request(server, headers=headers)[0], 403)
        self.assertEqual(self.request(server, headers={"Origin": server.origin, "Sec-Fetch-Site": "same-origin"})[0], 200)
        for headers in ([], [("Host", server.authority), ("Host", server.authority)],
                        [("Host", server.authority), ("Origin", server.origin), ("Origin", server.origin)]):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                connection.putrequest("GET", "/", skip_host=True)
                for k, v in headers:
                    connection.putheader(k, v)
                connection.endheaders()
                self.assertEqual(connection.getresponse().status, 403)
            finally:
                connection.close()

    def test_methods_traversal_encoded_paths_siblings_and_unlisted_files(self):
        server = self.start()
        (self.output / ".env").write_text("SECRET-NOT-FOR-BROWSER")
        (self.output / "research.sqlite3").write_text("SECRET-DATABASE")
        for path in ("/.env", "/research.sqlite3", "/manifest.json", "/versions/", "/../data/research.sqlite3",
                     "/%2e%2e/data/research.sqlite3", "/%252e%252e%252f.env", "/..\\data\\research.sqlite3",
                     "/%2fetc/passwd", "/index.html?secret=value", "/index.html%00", "/bundle-sibling/index.html",
                     "/versions/" + self.folder.name + "/manifest.json", "http://evil.example/index.html"):
            status, _, body = self.request(server, path, headers={"Host": server.authority})
            self.assertEqual(status, 404, path)
            self.assertNotIn(b"SECRET", body)
            self.assertNotIn(path.encode(), body)
        for method in ("POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE", "CONNECT"):
            status, headers, _ = self.request(server, method=method)
            self.assertEqual(status, 405)
            self.assertEqual(headers["Allow"], "GET, HEAD")
        self.assertEqual(self.request(server, "//index.html")[0], 400)

    def test_manifest_unknown_keys_version_and_byte_hash_fail_closed(self):
        path = self.folder / "manifest.json"
        original = json.loads(path.read_text())
        for mutate in (lambda m: m.update(secret="private"), lambda m: m.update(bundle_format=True),
                       lambda m: m.update(bundle_format=99), lambda m: m["assets"]["report.json"].update(sha256="0" * 64)):
            value = deepcopy(original)
            mutate(value)
            path.write_text(json.dumps(value))
            with self.assertRaises(ContractError):
                load_bundle(self.output)
        path.write_text(json.dumps(original))
        (self.folder / "unknown.txt").write_text("private")
        with self.assertRaises(ContractError):
            load_bundle(self.output)

    def test_untrusted_executable_rehashed_manifest_and_entry_are_rejected(self):
        script = self.folder / "private.js"
        script.write_text("fetch('https://evil.example')")
        path = self.folder / "manifest.json"
        value = json.loads(path.read_text())
        value["assets"]["private.js"] = dict(sha256=sha256(script.read_bytes()).hexdigest(), bytes=script.stat().st_size)
        path.write_text(json.dumps(value))
        with self.assertRaises(ContractError):
            load_bundle(self.output)
        (self.output / "index.html").write_text("<script>bad()</script>")
        with self.assertRaises(ContractError):
            load_bundle(self.output)

    def test_unknown_report_fields_missing_evidence_and_secrets_never_publish(self):
        cases = [lambda r: r.update(credential="private"), lambda r: r["evidence"].clear()]
        for secret in ("api_key=never-publish", "Bearer token-value", "sk-abcdefghijklmnopqrstuvwx",
                       "C:\\Users\\owner\\private.txt", "/home/owner/books/source.pdf", "file:///private/book"):
            cases.append(lambda r, text=secret: r.update(notice=text))
        for mutate in cases:
            value = deepcopy(self.report)
            mutate(value)
            value["content_hash"] = digest({k: v for k, v in value.items() if k != "content_hash"})
            target = self.root / "must-not-exist"
            with self.assertRaises(ContractError):
                publish(value, target)
            self.assertFalse(target.exists())

    def test_typed_text_secret_is_rejected_from_database_lineage(self):
        with V2Store(self.data, synthetic=True) as store:
            context = deepcopy(next(store.iter_v2(kind="inspection_context")))
            context.update(id="context:secret", created_at="2099-01-11T21:01:00Z", rationale="password=must-not-appear")
            store.put_v2([context])
            with self.assertRaises(ContractError):
                export_private(store, self.root / "secret-output", as_of=DEMO_CUTOFF)
        self.assertFalse((self.root / "secret-output").exists())

    def test_stale_but_self_consistent_bundle_requires_lineage_revalidation(self):
        value = deepcopy(self.report)
        value["notice"] = "Different authored notice"
        value["content_hash"] = digest({k: v for k, v in value.items() if k != "content_hash"})
        publish(value, self.output)
        with patch("trade_theorist.local_server.PrivateServer", side_effect=AssertionError("Cannot bind invalid lineage")):
            with self.assertRaises(ContractError):
                create_server(self.data, self.output, fixture=True, port=0)

    def test_outside_git_and_separate_data_root_required_even_for_fixtures(self):
        (self.root / ".git").write_text("gitdir: elsewhere")
        with self.assertRaises(ContractError):
            create_server(self.data, self.output, fixture=True, port=0)
        (self.root / ".git").unlink()
        with self.assertRaises(ContractError):
            create_server(self.output / "database", self.output, fixture=True, port=0)

    def test_hardlinked_asset_is_never_admitted(self):
        target = self.root / "private-copy"
        os.link(self.folder / "report.json", target)
        with self.assertRaises(ContractError):
            load_bundle(self.output)

    def test_directory_junction_or_symlink_cannot_redirect_bundle(self):
        link = self.root / "linked-bundle"
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.output)], capture_output=True)
            self.assertEqual(result.returncode, 0, "Cannot construct required junction test")
            self.addCleanup(link.rmdir)
        else:
            link.symlink_to(self.output, target_is_directory=True)
            self.addCleanup(link.unlink)
        with self.assertRaises(ContractError):
            load_bundle(link)
        with self.assertRaises(ContractError):
            publish(self.report, link)
        with self.assertRaises(ContractError):
            create_server(self.data, link, fixture=True, port=0)
        moved = self.root / "moved-bundle"
        self.output.rename(moved)  # The now-dangling junction must still be refused.
        with self.assertRaises(ContractError):
            publish(self.report, link)
        self.assertFalse(self.output.exists())

    def test_retention_keeps_current_previous_and_unrelated_changed_files(self):
        unrelated = self.output / "versions" / "notes"
        unrelated.mkdir()
        (unrelated / "book.txt").write_text("private original")
        altered = self.folder
        (altered / "owner-note.txt").write_text("do not prune")
        legitimate = []
        for i in range(3):
            value = deepcopy(self.report)
            value["notice"] = f"Original fixture publication {i}"
            value["content_hash"] = digest({k: v for k, v in value.items() if k != "content_hash"})
            publish(value, self.output, keep=2)
            legitimate.append(next(p for p in (self.output / "versions").iterdir() if p not in legitimate and p not in (altered, unrelated)))
        self.assertFalse(legitimate[0].exists())
        self.assertTrue(legitimate[1].exists())
        self.assertTrue(legitimate[2].exists())
        self.assertTrue((altered / "owner-note.txt").exists())
        self.assertTrue((unrelated / "book.txt").exists())
        self.assertEqual(load_bundle(self.output)[0]["notice"], "Original fixture publication 2")

    def test_atomic_handoff_failure_and_asset_interruption_reuse_old_entry(self):
        old = (self.output / "index.html").read_bytes()
        value = deepcopy(self.report)
        value["notice"] = "Another original fixture publication"
        value["content_hash"] = digest({k: v for k, v in value.items() if k != "content_hash"})
        replace = os.replace
        def fail_asset(source, target):
            if Path(target).name == "report.json":
                raise OSError("interrupted asset")
            return replace(source, target)
        with patch("trade_theorist.private_bundle.os.replace", fail_asset):
            with self.assertRaises(OSError):
                publish(value, self.output)
        self.assertEqual((self.output / "index.html").read_bytes(), old)
        def fail():
            raise OSError("interrupted before entry")
        with self.assertRaises(OSError):
            publish(value, self.output, before_publish=fail)
        self.assertEqual((self.output / "index.html").read_bytes(), old)
        publish(value, self.output)
        self.assertEqual(load_bundle(self.output)[0], value)

    def test_os_writer_lock_refuses_overlap_and_releases_after_error(self):
        with writer(self.output):
            with self.assertRaises(OSError):
                publish(self.report, self.output)
        publish(self.report, self.output)
        self.assertEqual(load_bundle(self.output)[0], self.report)

    def test_ctrl_c_closes_listener_and_cli_requires_explicit_v2_roots(self):
        captured = []
        original = create_server
        def capture(*args, **kwargs):
            server = original(*args, **kwargs)
            captured.append(server)
            return server
        output = io.StringIO()
        with patch("trade_theorist.local_server.create_server", capture), patch("trade_theorist.local_server.PrivateServer.serve_forever", side_effect=KeyboardInterrupt), redirect_stdout(output):
            serve(self.data, self.output, fixture=True, port=0)
        self.assertEqual(captured[0].socket.fileno(), -1)
        self.assertIn("Private observatory stopped", output.getvalue())
        self.assertIn("http://127.0.0.1:", output.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["serve"]), 2)
            self.assertEqual(main(["serve", "--projection-version", "2"]), 2)
        with patch("trade_theorist.local_server.serve") as launch, redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--projection-version", "2", "--data-root", str(self.data), "--output-root", str(self.output), "--serve", "--port", "0"]), 0)
            launch.assert_called_once_with(str(self.data), str(self.output), fixture=True, port=0)


if __name__ == "__main__":
    unittest.main()
