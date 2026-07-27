#!/usr/bin/env python3
import os
import subprocess
import sys

root = os.path.dirname(os.path.abspath(__file__))
cmd = [sys.executable, os.path.join(root, "anime_expedition_macro.py"), "--gui"]
subprocess.Popen(cmd, cwd=root)
