"""Child killed by the Step 08 parent at a durable/ambiguous boundary."""
import json
import os
from pathlib import Path
import socket
import sys
from threading import Event

from preflight_support import AuditClock, Wire, operating_policy, request, iso
from trade_theorist.market_requests import Coordinator


def forbidden(*_): raise AssertionError("Account networking forbidden in preflight child")
socket.socket.connect = forbidden
root, mode = Path(sys.argv[1]), sys.argv[2]
clock = AuditClock()


def stop_here():
    with (root / "ready.json").open("w", encoding="utf-8") as out:
        out.write(json.dumps({"boundary": mode})); out.flush(); os.fsync(out.fileno())
    Event().wait(30)
    raise RuntimeError("Parent failed to terminate child")


wire = Wire(clock, log=root / "wire.jsonl")
def respond(params, count):
    if mode == "dispatch": stop_here()
    if mode == "wait": return wire.page(params, status=429, headers={"Retry-After": "120"})
    return wire.page(params, symbols=["AAA"], token="later-symbol")
wire.handler = respond
with Coordinator(root / "data", operating_policy(), wire, synthetic=True, registry_root=root / "registry", clock=clock, jitter=lambda: .5) as owner:
    work = owner.submit(request(), consumer="scheduled-child", max_attempts=10, deadline=iso(clock.wall() + 86400))
    if mode == "owner": stop_here()
    if mode == "wait": clock.on_sleep = lambda _: stop_here()
    owner.run(work, max_pages=1, before_commit=stop_here if mode == "commit" else None)
    stop_here()
