#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selective Hawajees remix tool. Use only with audio you own or have permission to edit."""
import argparse, shutil, subprocess
from pathlib import Path


def need(cmd):
    if shutil.which(cmd) is None:
        raise SystemExit(f"Missing command: {cmd}")


def run(cmd):
    print("\n>>>", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def sec(x):
    p = [float(i