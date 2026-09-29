"""
qkd_bb84.py — BB84 Quantum Key Distribution Simulation
Team 181 | Secure Communication over Public Networks Using Hybrid Cryptographic Systems
"""

import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class BB84:
    """
    Simulates the BB84 Quantum Key Distribution protocol.

    Alice generates random bits and bases, transmits qubits, Bob measures
    with random bases. After basis reconciliation, a shared sifted key is
    extracted and the Quantum Bit Error Rate (QBER) is computed.

    Optionally, an eavesdropper (Eve) can intercept-and-resend, introducing
    detectable errors.
    """

    QBER_THRESHOLD = 0.11   # > 11% QBER → abort session (BB84 security limit)

    def __init__(self, num_qubits: int = 1000, noise_prob: float = 0.0,
                 eve_prob: float = 0.0, seed: int | None = None):
        """
        Args:
            num_qubits  : Number of qubits Alice transmits.
            noise_prob  : Probability of a random bit-flip on the quantum channel
                          (models thermal noise / fiber loss).  Range [0.0, 0.15].
            eve_prob    : Probability that Eve intercepts any given qubit and
                          re-sends it (intercept-resend attack).  Range [0.0, 1.0].
            seed        : Optional RNG seed for reproducibility.
        """
        if not (0.0 <= noise_prob <= 0.15):
            raise ValueError("noise_prob must be in [0.0, 0.15]")
        if not (0.0 <= eve_prob <= 1.0):
            raise ValueError("eve_prob must be in [0.0, 1.0]")

        self.num_qubits = num_qubits
        self.noise_prob = noise_prob
        self.eve_prob = eve_prob
        self.rng = np.random.default_rng(seed)

        # Results populated after run()
        self.alice_bits: np.ndarray | None = None
        self.alice_bases: np.ndarray | None = None
        self.bob_bases: np.ndarray | None = None
        self.bob_bits: np.ndarray | None = None
        self.sifted_key: list[int] = []
        self.qber: float = 0.0
        self.session_secure: bool = False

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run(self) -> dict:
        """
        Execute the full BB84 protocol and return a result dictionary.

        Returns:
            {
                "sifted_key"      : list[int],
                "key_length"      : int,
                "qber"            : float,
                "session_secure"  : bool,
                "num_qubits"      : int,
                "sift_ratio"      : float,
            }
        """
        logger.info("─── BB84 Protocol Start ───────────────────────────────")
        logger.info(f"  Qubits: {self.num_qubits} | Noise: {self.noise_prob:.1%} "
                    f"| Eve intercept prob: {self.eve_prob:.1%}")

        # Step 1 — Alice prepares random bits & random bases (0=rectilinear, 1=diagonal)
        self.alice_bits  = self.rng.integers(0, 2, self.num_qubits)
        self.alice_bases = self.rng.integers(0, 2, self.num_qubits)

        # Step 2 — Transmit through quantum channel (with optional Eve + noise)
        transmitted = self._quantum_channel(self.alice_bits, self.alice_bases)

        # Step 3 — Bob chooses random measurement bases and measures
        self.bob_bases = self.rng.integers(0, 2, self.num_qubits)
        self.bob_bits  = self._bob_measure(transmitted, self.bob_bases)

        # Step 4 — Basis reconciliation (sifting): keep only matching bases
        matching = np.where(self.alice_bases == self.bob_bases)[0]
        alice_sifted = self.alice_bits[matching]
        bob_sifted   = self.bob_bits[matching]

        sift_ratio = len(matching) / self.num_qubits
        logger.info(f"  Sifted key indices: {len(matching)} / {self.num_qubits} "
                    f"({sift_ratio:.1%} kept)")

        # Step 5 — QBER estimation (sample a subset of sifted bits)
        self.qber = self._compute_qber(alice_sifted, bob_sifted)
        logger.info(f"  QBER = {self.qber:.4f} ({self.qber:.1%})")

        # Step 6 — Security decision
        if self.qber > self.QBER_THRESHOLD:
            logger.warning(f"  QBER {self.qber:.1%} exceeds threshold "
                           f"{self.QBER_THRESHOLD:.0%} — session ABORTED.")
            self.session_secure = False
            self.sifted_key = []
        else:
            logger.info(f"  QBER within threshold — session SECURE.")
            self.session_secure = True
            # Use remaining bits (not used in QBER sampling) as the raw key
            self.sifted_key = alice_sifted.tolist()

        logger.info(f"  Final key length: {len(self.sifted_key)} bits")
        logger.info("─── BB84 Protocol End ─────────────────────────────────\n")

        return {
            "sifted_key":     self.sifted_key,
            "key_length":     len(self.sifted_key),
            "qber":           round(self.qber, 6),
            "session_secure": self.session_secure,
            "num_qubits":     self.num_qubits,
            "sift_ratio":     round(sift_ratio, 4),
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _quantum_channel(self, bits: np.ndarray, bases: np.ndarray) -> np.ndarray:
        """
        Simulate qubit transmission.
        1. Optionally apply Eve's intercept-resend attack.
        2. Apply random channel noise (bit-flips).
        Returns the bits received at Bob's end before his measurement.
        """
        received = bits.copy()

        # Eve's intercept-resend attack
        if self.eve_prob > 0:
            eve_mask = self.rng.random(self.num_qubits) < self.eve_prob
            eve_bases = self.rng.integers(0, 2, self.num_qubits)
            # Where Eve chose the wrong basis she has a 50% chance of disturbing the qubit
            wrong_basis = eve_mask & (eve_bases != bases)
            flip_mask = wrong_basis & (self.rng.random(self.num_qubits) < 0.5)
            received = np.where(flip_mask, 1 - received, received)
            eve_intercepts = int(eve_mask.sum())
            disturbances   = int(flip_mask.sum())
            logger.info(f"  Eve intercepted {eve_intercepts} qubits, "
                        f"disturbed {disturbances}")

        # Channel noise (thermal noise / fiber loss model)
        if self.noise_prob > 0:
            noise_mask = self.rng.random(self.num_qubits) < self.noise_prob
            received = np.where(noise_mask, 1 - received, received)
            logger.info(f"  Channel noise flipped {int(noise_mask.sum())} qubits")

        return received

    def _bob_measure(self, transmitted: np.ndarray,
                     bob_bases: np.ndarray) -> np.ndarray:
        """
        Bob measures each qubit.
        • Matching basis  → deterministic result (same as transmitted).
        • Mismatched basis → random result (50/50).
        """
        mismatched = self.alice_bases != bob_bases
        random_results = self.rng.integers(0, 2, self.num_qubits)
        return np.where(mismatched, random_results, transmitted)

    def _compute_qber(self, alice_sifted: np.ndarray,
                      bob_sifted: np.ndarray) -> float:
        """
        Compute QBER using the full sifted key.
        QBER = (number of mismatched bits) / (total sifted bits)
        """
        if len(alice_sifted) == 0:
            return 0.0
        errors = int(np.sum(alice_sifted != bob_sifted))
        return errors / len(alice_sifted)