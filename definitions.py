#!/usr/bin/env python3
from loguru import logger

logger.add('events.log', retention='5 days', backtrace=True, diagnose=True)
