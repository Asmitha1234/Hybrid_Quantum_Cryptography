"""
fingerprinting.py — Multi-Metric Attack Fingerprinting Engine
Team 181 | Hybrid Cryptographic Systems
"""

import numpy as np

class AttackSimulator:
    def __init__(self, seed: int = None):
        self.rng = np.random.default_rng(seed)

    def photon_number_splitting(self, photon_counts: np.ndarray) -> np.ndarray:
        """Eve suppresses single photons and splits multi-photon pulses."""
        modified = photon_counts.copy()
        # Suppress ~70% of single photons and keep multi-photons
        single_mask = (photon_counts == 1)
        suppress = self.rng.binomial(n=1, p=0.70, size=np.sum(single_mask))
        modified[single_mask] = 1 - suppress
        return modified

    def intercept_resend(self, bits: np.ndarray, bases: np.ndarray, eve_prob: float = 0.8) -> np.ndarray:
        """Eve measures in a random basis and resends, introducing ~25% QBER error."""
        modified = bits.copy()
        intercept_mask = self.rng.binomial(n=1, p=eve_prob, size=len(bits)).astype(bool)
        eve_bases = self.rng.integers(0, 2, size=len(bits))
        
        # Where Eve's basis doesn't match, bit gets randomized (50% error probability)
        mismatch = intercept_mask & (bases != eve_bases)
        flip = self.rng.binomial(n=1, p=0.5, size=np.sum(mismatch))
        modified[mismatch] = np.bitwise_xor(modified[mismatch], flip)
        return modified


class AttackFingerprinter:
    @staticmethod
    def analyze(metrics: dict, skr: float, distance_km: float = 10.0, mu: float = 0.5, nu: float = 0.1) -> tuple:
        """Analyzes live channel metrics against dynamic statistical bounds."""
        E_signal = metrics["E_signal"]
        Y_decoy = metrics["Y_decoy"]
        
        # Dynamic Expected Yield Threshold based on link attenuation
        transmittance = (10.0 ** (-(0.2 * distance_km) / 10.0)) * 0.1
        expected_Y_decoy = nu * transmittance
        
        # 1. Check for Intercept-Resend Attack (QBER > 11.0% GLLP Threshold)
        if E_signal >= 0.11:
            return "INTERCEPT_RESEND_ATTACK", f"Signal QBER ({E_signal:.2%}) exceeds GLLP security threshold (11.00%)."
        
        # 2. Check for PNS Attack (Decoy Yield significantly lower than expected bound)
        if Y_decoy < expected_Y_decoy * 0.45:
            return "PNS_ATTACK_DETECTED", f"Decoy Yield Y_nu ({Y_decoy:.6f}) below expected lower bound ({expected_Y_decoy*0.45:.6f}). Single-photon suppression detected."
        
        # 3. Clean Channel
        if skr > 0.0:
            return "CLEAN_CHANNEL", "Channel parameters within normal statistical variance bounds."
        
        return "HIGH_NOISE_ABORT", "Secret key rate collapsed due to channel degradation."