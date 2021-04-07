#!/usr/bin/env python3
import os

from loguru import logger

logger.add('events.log', retention='5 days', backtrace=True, diagnose=True)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
