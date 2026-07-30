import subprocess
import os

print("Launching new console window...")
subprocess.Popen(
    ["python", "-u", "backend/run_live.py", "--target", "5000"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)
print("Done.")
