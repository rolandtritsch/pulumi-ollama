#!/usr/bin/env python3

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


def pulumi(*args: str) -> str:
    return subprocess.check_output(["pulumi", *args], text=True).strip()


def pulumi_optional(*args: str) -> str | None:
    try:
        return pulumi(*args)
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    public_ip = pulumi("stack", "output", "eipPublicIp")
    models_raw = pulumi_optional("config", "get", "models") or "llama3.2:latest"
    expected = {model.strip() for model in models_raw.split(",")}
    endpoint = f"http://{public_ip}:11434/api/tags"
    deadline = time.monotonic() + 900

    print(f"Waiting for {endpoint} and models: {', '.join(sorted(expected))}")
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(endpoint, timeout=10) as response:
                payload = json.load(response)
            available = {
                model.get("name") or model.get("model")
                for model in payload.get("models", [])
            }
            available.discard(None)
            missing = expected - available
            if not missing:
                print(f"Ollama is ready at {endpoint}")
                return 0
            print(f"Ollama is responding; waiting for models: {', '.join(sorted(missing))}")
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            print(f"Not ready: {error}")
        time.sleep(10)

    print("Timed out after 15 minutes", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
