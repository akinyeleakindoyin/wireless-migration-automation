"""Concurrent integrity output capture with 10-second buffer wait per worker.
Ten seconds is NOT a fleet-wide completion-time claim.
"""
from verification_common import run_variant

if __name__ == "__main__":
    run_variant("buffer")
