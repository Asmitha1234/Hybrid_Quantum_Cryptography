"""
attack_simulation.py — Attack Simulation Module
Team 181 | Secure Communication over Public Networks Using Hybrid Cryptographic Systems

Models three real-world attack vectors against QKD:
  1. Intercept-Resend (Eve)
  2. Photon-Number Splitting (PNS)
  3. General channel noise injection

All attacks operate on the bit stream level (simulation) and return the
disturbed bit array along with attack statistics.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class AttackSimulator:
    """
    Injects attack-specific disturbances into a qubit stream.

    All attack methods accept the original Alice bits/bases and return a
    modified received array representing what Bob actually gets.
    """

    def __init__(self, seed: int | None = None):
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------ #
    # Attack 1 — Intercept-Resend (Eve)                                   #
    # ------------------------------------------------------------------ #

    def intercept_resend(self, alice_bits: np.ndarray, alice_bases: np.ndarray,
                         eve_intercept_prob: float = 1.0) -> dict:
        """
        Eve intercepts each qubit with probability `eve_intercept_prob`,
        measures it in a random basis, and re-sends her result.

        When Eve picks the wrong basis (50% of the time), she has a 50%
        chance of sending the wrong bit → expected QBER contribution ≈ 25%.

        Args:
            alice_bits          : Alice's original bit array.
            alice_bases         : Alice's basis choices (0=rectilinear, 1=diagonal).
            eve_intercept_prob  : Probability Eve intercepts any given qubit.

        Returns:
            {
                "received_bits"     : np.ndarray,   # what Bob receives
                "num_intercepted"   : int,
                "num_disturbed"     : int,
                "estimated_qber"    : float,        # theoretical estimate
            }
        """
        n = len(alice_bits)
        received = alice_bits.copy()

        # Eve's random basis choices
        eve_bases = self.rng.integers(0, 2, n)
        intercept_mask = self.rng.random(n) < eve_intercept_prob

        # Wrong basis → 50% chance of bit flip
        wrong_basis = intercept_mask & (eve_bases != alice_bases)
        flip = wrong_basis & (self.rng.random(n) < 0.5)
        received = np.where(flip, 1 - received, received)

        num_intercepted = int(intercept_mask.sum())
        num_disturbed   = int(flip.sum())

        # Theoretical QBER from intercept-resend = P_eve * 0.5 * 0.5 = P_eve/4
        estimated_qber  = eve_intercept_prob * 0.25

        logger.info(
            f"[Intercept-Resend] intercepted={num_intercepted}, "
            f"disturbed={num_disturbed}, est_QBER≈{estimated_qber:.2%}"
        )
        return {
            "received_bits":   received,
            "num_intercepted": num_intercepted,
            "num_disturbed":   num_disturbed,
            "estimated_qber":  round(estimated_qber, 4),
        }

    # ------------------------------------------------------------------ #
    # Attack 2 — Photon-Number Splitting (PNS)                            #
    # ------------------------------------------------------------------ #

    def photon_number_splitting(self, alice_bits: np.ndarray,
                                multi_photon_prob: float = 0.1) -> dict:
        """
        Simulates a PNS attack on weak coherent pulse (WCP) sources.

        In real QKD hardware, a laser sometimes emits 2+ photons per pulse.
        Eve blocks single-photon pulses (causing loss), keeps one photon
        from multi-photon pulses (gaining full information), and forwards
        the rest to Bob — remaining completely undetected in the QBER.

        In our simulation we model this as:
            - Multi-photon pulses (prob = multi_photon_prob): Eve learns the
              bit without disturbing it → she gains info, QBER stays 0 for
              these bits.
            - Single-photon pulses: Eve blocks them (channel loss increase).

        Args:
            alice_bits        : Alice's bit array.
            multi_photon_prob : Fraction of pulses that are multi-photon.

        Returns:
            {
                "received_bits"        : np.ndarray,
                "eve_learned_indices"  : np.ndarray,   # bit indices Eve knows
                "blocked_indices"      : np.ndarray,   # bits lost (channel loss)
                "info_leakage_rate"    : float,
            }
        """
        n = len(alice_bits)
        pulse_is_multi = self.rng.random(n) < multi_photon_prob

        # Eve learns bits from multi-photon pulses without disturbing them
        eve_learned_indices = np.where(pulse_is_multi)[0]

        # Single-photon pulses: Eve blocks a fraction (simulate channel loss
        # by replacing with random bit — in practice Bob discards these via
        # detection efficiency, here we just mark them)
        single_photon = ~pulse_is_multi
        blocked_mask = single_photon & (self.rng.random(n) < 0.3)  # 30% loss
        blocked_indices = np.where(blocked_mask)[0]

        # Bob still receives multi-photon bits correctly (Eve forwards them)
        received = alice_bits.copy()

        info_leakage_rate = len(eve_learned_indices) / n

        logger.info(
            f"[PNS Attack] multi-photon pulses={len(eve_learned_indices)}, "
            f"blocked={len(blocked_indices)}, "
            f"info leakage={info_leakage_rate:.2%}"
        )
        return {
            "received_bits":       received,
            "eve_learned_indices": eve_learned_indices,
            "blocked_indices":     blocked_indices,
            "info_leakage_rate":   round(info_leakage_rate, 4),
        }

    # ------------------------------------------------------------------ #
    # Attack 3 — General Channel Noise Injection                          #
    # ------------------------------------------------------------------ #

    def inject_noise(self, bits: np.ndarray, noise_prob: float) -> dict:
        """
        Injects random bit-flip noise (models thermal noise, fiber loss,
        or general environmental interference).

        Args:
            bits       : Input bit array.
            noise_prob : Probability of each bit being flipped.  [0.0, 1.0]

        Returns:
            {
                "received_bits" : np.ndarray,
                "num_flipped"   : int,
                "actual_ber"    : float,    # actual bit error rate introduced
            }
        """
        flip_mask = self.rng.random(len(bits)) < noise_prob
        received  = np.where(flip_mask, 1 - bits, bits)
        num_flipped = int(flip_mask.sum())

        logger.info(
            f"[Channel Noise] flipped={num_flipped}/{len(bits)} bits "
            f"({num_flipped/len(bits):.2%} BER)"
        )
        return {
            "received_bits": received,
            "num_flipped":   num_flipped,
            "actual_ber":    round(num_flipped / len(bits), 4),
        }