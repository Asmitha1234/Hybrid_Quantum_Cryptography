"""
qkd_decoy.py — Decoy-State BB84 QKD Engine with Real-Time Stochastic Noise
Team 181 | Hybrid Cryptographic Systems
"""

import numpy as np

class DecoyBB84:
    def __init__(self, num_pulses: int = 20000, distance_km: float = 10.0, seed: int = None):
        # Uses system entropy when seed=None for real-time variance
        self.rng = np.random.default_rng(seed)
        self.num_pulses = num_pulses
        self.distance_km = distance_km
        
        # Fiber & Hardware Specifications
        self.alpha = 0.2           # Fiber attenuation (dB/km)
        self.eta_bob = 0.1         # Bob's optical efficiency
        self.mu = 0.5              # Signal state mean photon intensity
        self.nu = 0.1              # Decoy state mean photon intensity
        self.y0 = 1e-5             # Dark count probability
        self.e_optical = 0.015     # Baseline optical alignment error (1.5%)

    def generate_alice_pulses(self) -> dict:
        """Generates random bits, bases, and Poisson-distributed photon intensities."""
        bits = self.rng.integers(0, 2, size=self.num_pulses)
        bases = self.rng.integers(0, 2, size=self.num_pulses)
        
        # Intensity allocation: 60% Signal (mu), 30% Decoy (nu), 10% Vacuum (0.0)
        intensities = self.rng.choice([self.mu, self.nu, 0.0], size=self.num_pulses, p=[0.6, 0.3, 0.1])
        
        # Real-world coherent state emission follows Poisson photon distribution
        photon_counts = self.rng.poisson(lam=intensities)

        return {
            "bits": bits,
            "bases": bases,
            "intensities": intensities,
            "photon_counts": photon_counts
        }

    def simulate_bob_reception(self, alice: dict, modified_bits=None, modified_counts=None) -> dict:
        """Simulates photon channel propagation using Binomial loss sampling."""
        bits = modified_bits if modified_bits is not None else alice["bits"]
        counts = modified_counts if modified_counts is not None else alice["photon_counts"]
        
        # Calculate channel transmittance
        transmittance = (10.0 ** (-(self.alpha * self.distance_km) / 10.0)) * self.eta_bob
        
        # Probability of detection per pulse: P = 1 - (1 - eta)^n + y0
        p_click = 1.0 - (1.0 - transmittance) ** counts + self.y0
        p_click = np.clip(p_click, 0.0, 1.0)
        
        # Stochastic Binomial trial for detection events
        detections = self.rng.binomial(n=1, p=p_click)
        bob_bases = self.rng.integers(0, 2, size=self.num_pulses)
        
        # Bit error generation on matching bases
        matching_bases = (alice["bases"] == bob_bases)
        errors = self.rng.binomial(n=1, p=self.e_optical, size=self.num_pulses)
        
        bob_bits = np.where(
            matching_bases,
            np.bitwise_xor(bits, errors),
            self.rng.integers(0, 2, size=self.num_pulses)
        )

        return {
            "detections": detections,
            "bob_bases": bob_bases,
            "bob_bits": bob_bits
        }

    def process_decoy_statistics(self, alice: dict, bob: dict) -> dict:
        """Sifts keys and extracts observed Yields and QBER values."""
        det = bob["detections"] == 1
        sift_mask = det & (alice["bases"] == bob["bob_bases"])
        
        # Filter intensities
        signal_mask = alice["intensities"] == self.mu
        decoy_mask = alice["intensities"] == self.nu
        
        # Compute dynamic yields
        Y_signal = np.sum(det & signal_mask) / max(1, np.sum(signal_mask))
        Y_decoy = np.sum(det & decoy_mask) / max(1, np.sum(decoy_mask))
        
        # Compute QBER
        signal_sift = sift_mask & signal_mask
        decoy_sift = sift_mask & decoy_mask
        
        E_signal = np.mean(alice["bits"][signal_sift] != bob["bob_bits"][signal_sift]) if np.sum(signal_sift) > 0 else 0.0
        E_decoy = np.mean(alice["bits"][decoy_sift] != bob["bob_bits"][decoy_sift]) if np.sum(decoy_sift) > 0 else 0.0

        # Estimate single-photon yields (Decoy State lower bounds)
        transmittance = (10.0 ** (-(self.alpha * self.distance_km) / 10.0)) * self.eta_bob
        Y_1 = max(1e-6, transmittance + self.y0)
        e_1 = max(0.0, E_signal)

        return {
            "E_signal": E_signal,
            "E_decoy": E_decoy,
            "Y_signal": Y_signal,
            "Y_decoy": Y_decoy,
            "Y_1": Y_1,
            "e_1": e_1,
            "sifted_key_bits": alice["bits"][signal_sift]
        }

    def calculate_skr(self, metrics: dict) -> float:
        """Computes Secret Key Rate (SKR) per pulse using GLLP formula."""
        e = metrics["E_signal"]
        if e >= 0.11 or len(metrics["sifted_key_bits"]) < 128:
            return 0.0
        
        def H2(p):
            if p <= 0 or p >= 1: return 0.0
            return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)
        
        skr = 0.5 * (metrics["Y_1"] * (1.0 - H2(metrics["e_1"])) - metrics["Y_signal"] * 1.16 * H2(e))
        return max(0.0, float(skr))