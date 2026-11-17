"""Send a task to Fo by iMessage/SMS from this Mac (Messages app).

Fo reads texts sent to its number and acts on them, so BearDen can hand off
tasks with no extra API. Set FO_NUMBER in .env (the number shown during
Wajo signup). The first send triggers a macOS prompt asking to let Terminal
control Messages: click OK.
"""
import os
import subprocess

APPLESCRIPT = '''
on run argv
    set theNumber to item 1 of argv
    set theText to item 2 of argv
    tell application "Messages"
        try
            set svc to 1st account whose service type = iMessage
            send theText to participant theNumber of svc
        on error
            set svc to 1st account whose service type = SMS
            send theText to participant theNumber of svc
        end try
    end tell
end run
'''


def send_to_fo(task: str) -> tuple[bool, str]:
    number = os.environ.get("FO_NUMBER", "").strip()
    if not number:
        return False, "Add FO_NUMBER to your .env file first."
    try:
        r = subprocess.run(
            ["osascript", "-e", APPLESCRIPT, number, task],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        return False, "This only works on a Mac (needs the Messages app)."
    except subprocess.TimeoutExpired:
        return False, "Messages didn't respond. Is it open and signed in?"
    if r.returncode != 0:
        return False, f"Messages error: {r.stderr.strip() or 'unknown'}"
    return True, f"Sent to Fo ({number}). Watch your phone for Fo's report."
