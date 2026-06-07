#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hawajees Remix Tool

Use only with audio you own or have permission to edit.
The tool processes only the poet time ranges you provide.
Anything outside those ranges is preserved, so song parts after the poet are not touched.
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def need(cmd: str) -> None:
   