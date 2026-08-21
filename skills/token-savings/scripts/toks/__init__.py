"""toks - portable token-saving toolkit.

Synthesized from three open-source approaches and adapted for a skill-driven
assistant (no custom runtime, must preserve input/output quality):

- ojuschugh1/sqz         -> content-hash dedup + lossless JSON pipeline + safe mode
- alexgreensh/token-optimizer -> multi-surface compression + checkpoint + quality gate
- vaibkumr/prompt-optimizer  -> protected zones ([[KEEP]]) + entropy as a diagnostic

All modules are pure stdlib so they run under any Python 3.9+.
"""
__version__ = "1.0.0"
