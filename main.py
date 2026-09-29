"""
main.py — End-to-End Demo
Team 181 | Secure Communication over Public Networks Using Hybrid Cryptographic Systems

Runs a complete hybrid QKD + AES session and optionally generates
performance graphs. Run from the terminal:

    python main.py                      # default run
    python main.py --qubits 5000        # custom qubit count
    python main.py --noise 0.03 --eve 0.2
    python main.py --attack pns
    python main.py --graphs             # generate & save performance graphs
"""

import argparse
import logging
import sys

import numpy as np

from qkd_bb84 import BB84
from aes_encryption import AESModule
from attack_simulation import AttackSimulator

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SEPARATOR = "═" * 60


def run_session(num_qubits: int = 2000,
                noise_prob: float = 0.02,
                eve_prob: float = 0.0,
                attack: str | None = None,
                plaintext: str = "Secure project data: Team 181") -> None:
    """
    Execute a full hybrid cryptographic session.

    Pipeline:
        BB84 QKD → sifted key → AES key derivation → encrypt → decrypt → verify
    """
    print(f"\n{SEPARATOR}")
    print("  HYBRID CRYPTOGRAPHIC SYSTEM — Session Demo")
    print(f"  Team 181 | PES University | UE23CS320B")
    print(SEPARATOR)
    print(f"  Qubits      : {num_qubits}")
    print(f"  Noise prob  : {noise_prob:.1%}")
    print(f"  Eve prob    : {eve_prob:.1%}")
    print(f"  Attack mode : {attack or 'None'}")
    print(f"  Plaintext   : '{plaintext}'")
    print(SEPARATOR + "\n")

    # ── Phase 1: Optional pre-transmission attack simulation ──────────
    if attack == "pns":
        print("[ ATTACK ] Photon-Number Splitting attack engaged")
        sim = AttackSimulator(seed=99)
        dummy_bits  = np.ones(num_qubits, dtype=int)
        pns_result  = sim.photon_number_splitting(dummy_bits, multi_photon_prob=0.15)
        print(f"           Eve learned {len(pns_result['eve_learned_indices'])} bits "
              f"({pns_result['info_leakage_rate']:.1%} leakage)\n")

    elif attack == "intercept":
        print("[ ATTACK ] Intercept-Resend attack engaged")
        sim = AttackSimulator(seed=99)
        dummy_bits  = np.ones(num_qubits, dtype=int)
        dummy_bases = np.zeros(num_qubits, dtype=int)
        ir_result   = sim.intercept_resend(dummy_bits, dummy_bases,
                                           eve_intercept_prob=eve_prob or 1.0)
        print(f"           Eve intercepted {ir_result['num_intercepted']} qubits, "
              f"disturbed {ir_result['num_disturbed']} "
              f"(est. QBER ≈ {ir_result['estimated_qber']:.1%})\n")

    # ── Phase 2: BB84 QKD ──────────────────────────────────────────────
    print("[ QKD ] Running BB84 protocol …")
    bb84 = BB84(
        num_qubits=num_qubits,
        noise_prob=noise_prob,
        eve_prob=eve_prob,
        seed=42,
    )
    result = bb84.run()

    print(f"\n{'─'*40}")
    print(f"  Sifted key length : {result['key_length']} bits")
    print(f"  QBER              : {result['qber']:.4f} ({result['qber']:.1%})")
    print(f"  Sift ratio        : {result['sift_ratio']:.1%}")
    print(f"  Session secure    : {'✓ YES' if result['session_secure'] else '✗ NO  (ABORTED)'}")
    print(f"{'─'*40}\n")

    if not result["session_secure"]:
        print("  ⚠  Key exchange aborted — QBER exceeds security threshold.")
        print("  ⚠  No data encrypted. Start a new session.\n")
        return

    # ── Phase 3: AES Encryption ───────────────────────────────────────
    print("[ AES ] Deriving AES-128 key from QKD output via SHA-256 …")
    aes = AESModule(result["sifted_key"])
    print(f"  AES key (hex) : {aes.aes_key.hex()}\n")

    print(f"[ ENCRYPT ] Encrypting: '{plaintext}'")
    enc = aes.encrypt(plaintext)
    print(f"  IV          : {enc['iv'].hex()}")
    print(f"  Ciphertext  : {enc['ciphertext'].hex()}")
    print(f"  Time        : {enc['elapsed_ms']:.4f} ms\n")

    print("[ DECRYPT ] Decrypting ciphertext …")
    dec = aes.decrypt(enc["ciphertext"], enc["iv"])
    print(f"  Recovered   : '{dec['plaintext']}'")
    print(f"  Time        : {dec['elapsed_ms']:.4f} ms\n")

    # ── Phase 4: Verification ──────────────────────────────────────────
    match = dec["plaintext"] == plaintext
    print(f"{'─'*40}")
    if match:
        print("  ✓  ROUND-TRIP VERIFICATION PASSED")
        print("  ✓  Secure end-to-end communication demonstrated.")
    else:
        print("  ✗  VERIFICATION FAILED — decryption error.")
    print(f"{'─'*40}\n")

    print(SEPARATOR)
    print("  SESSION SUMMARY")
    print(SEPARATOR)
    print(f"  Protocol    : BB84 QKD + AES-128 (CBC)")
    print(f"  Key source  : Quantum (simulation, no hardware needed)")
    print(f"  Key length  : {result['key_length']} bits (raw sifted)")
    print(f"  AES key     : 128-bit (via SHA-256 truncation)")
    print(f"  QBER        : {result['qber']:.4f} ({result['qber']:.1%})")
    print(f"  Enc time    : {enc['elapsed_ms']:.4f} ms")
    print(f"  Dec time    : {dec['elapsed_ms']:.4f} ms")
    print(f"  Status      : {'SECURE ✓' if match else 'FAILED ✗'}")
    print(SEPARATOR + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Team 181 — Hybrid QKD+AES Cryptographic System Demo"
    )
    parser.add_argument("--qubits",    type=int,   default=2000,
                        help="Number of qubits (default: 2000)")
    parser.add_argument("--noise",     type=float, default=0.02,
                        help="Channel noise probability 0.0-0.15 (default: 0.02)")
    parser.add_argument("--eve",       type=float, default=0.0,
                        help="Eve intercept probability 0.0-1.0 (default: 0)")
    parser.add_argument("--attack",    type=str,   default=None,
                        choices=["intercept", "pns"],
                        help="Attack simulation: 'intercept' or 'pns'")
    parser.add_argument("--msg",       type=str,
                        default="Secure project data: Team 181",
                        help="Plaintext message to encrypt")
    parser.add_argument("--graphs",    action="store_true",
                        help="Generate and save performance graphs")
    args = parser.parse_args()

    run_session(
        num_qubits=args.qubits,
        noise_prob=args.noise,
        eve_prob=args.eve,
        attack=args.attack,
        plaintext=args.msg,
    )

    if args.graphs:
        print("[ GRAPHS ] Generating performance report (this may take ~30s) …")
        from analyzer import Analyzer
        import matplotlib.pyplot as plt
        az = Analyzer(num_qubits=3000, n_trials=8)
        az.generate_report(save_path="performance_report.png")
        print("  Saved → performance_report.png\n")


if __name__ == "__main__":
    main()