import asyncio
import errno
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import unittest

from ofscraper.utils.context.eventloop import new_event_loop


@unittest.skipUnless(sys.platform == "linux", "Linux terminal regression")
class TerminalSummaryTest(unittest.TestCase):
    def test_network_loop_does_not_change_ui_loop_factory(self):
        import uvloop

        network = new_event_loop()
        ui = asyncio.new_event_loop()
        try:
            self.assertIsInstance(network, uvloop.Loop)
            self.assertIsInstance(ui, asyncio.SelectorEventLoop)
        finally:
            network.close()
            ui.close()

    def test_large_summary_returns_to_interactive_menu(self):
        import pty

        # stdin, stdout and stderr share a PTY, just as in an interactive shell.
        # Two real prompts surround output much larger than its kernel buffer.
        script = '''
import os
import asyncio
import uvloop
import ofscraper.__main__
from ofscraper.main.open.load import systemSet
from ofscraper.prompts.promptConvert import getChecklistSelection
from ofscraper.utils.console import get_shared_console
from ofscraper.utils.context.run_async import run
# Simulate terminal flags left behind by a previous version in the same shell.
os.set_blocking(0, False)
systemSet()
assert os.get_blocking(1), "Startup did not repair inherited terminal flags"
assert getChecklistSelection(message="FIRST_MENU", choices=["Continue"]) == "Continue"
assert os.get_blocking(1), "Menu left stdout nonblocking"
@run
async def network_work():
    assert isinstance(asyncio.get_running_loop(), uvloop.Loop)
    assert await asyncio.gather(asyncio.sleep(0, result=1), asyncio.sleep(0, result=2)) == [1, 2]
network_work()
asyncio.get_event_loop().close()
asyncio.set_event_loop(None)
console = get_shared_console()
console.print("SUMMARY_START")
console.print("\\n".join(f"SUMMARY_ROW_{i:05d}" for i in range(10000)), markup=False, highlight=False)
console.print("SUMMARY_END")
assert getChecklistSelection(message="SECOND_MENU", choices=["Quit"]) == "Quit"
assert os.get_blocking(1), "Second menu left stdout nonblocking"
print("CLEAN_EXIT")
'''
        master, slave = pty.openpty()
        proc = subprocess.Popen(
            [sys.executable, "-c", script],
            stdin=slave, stdout=slave, stderr=slave,
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "TERM": "xterm", "PROMPT_TOOLKIT_NO_CPR": "1"},
        )
        os.close(slave)
        output = bytearray()
        answered = set()
        paused = False
        deadline = time.monotonic() + 30
        try:
            while time.monotonic() < deadline:
                if not select.select([master], [], [], 0.1)[0]:
                    continue
                try:
                    chunk = os.read(master, 65536)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output.extend(chunk)
                for marker in (b"FIRST_MENU", b"SECOND_MENU"):
                    if marker in output and marker not in answered:
                        os.write(master, b"\r")
                        answered.add(marker)
                if b"SUMMARY_START" in output and not paused:
                    # Force backpressure while the child writes its summary.
                    time.sleep(0.25)
                    paused = True
            self.assertEqual(proc.wait(timeout=3), 0, output[-3000:].decode(errors="replace"))
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            os.close(master)
        self.assertIn(b"CLEAN_EXIT", output)
        self.assertNotIn(b"BlockingIOError", output)
        self.assertEqual(output.count(b"SUMMARY_START"), 1)
        self.assertEqual(output.count(b"SUMMARY_END"), 1)
        for i in range(10000):
            self.assertEqual(output.count(f"SUMMARY_ROW_{i:05d}".encode()), 1)


if __name__ == "__main__":
    unittest.main()
