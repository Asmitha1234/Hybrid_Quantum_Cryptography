"""
analyzer.py — Performance Analyzer & Visualization Module
Team 181 | Secure Communication over Public Networks Using Hybrid Cryptographic Systems

Generates the key performance graphs:
  • QBER vs Channel Noise Probability
  • QBER vs Eve Intercept Probability
  • Final Key Length vs Noise
  • Encryption Time comparison (Hybrid vs Classical AES)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Optional
import logging

from qkd_bb84 import BB84
from aes_encryption import AESModule

logger = logging.getLogger(__name__)

# ─── Styling ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":    "DejaVu Sans",
    "font.size":      10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.facecolor":   "#F8FAFC",
    "axes.facecolor":     "#F8FAFC",
    "axes.grid":          True,
    "grid.alpha":         0.35,
    "grid.linestyle":     "--",
})

NAVY  = "#1A2B5E"
TEAL  = "#028090"
AMBER = "#F59E0B"
RED   = "#DC2626"
GREEN = "#059669"


class Analyzer:
    """Runs sweep experiments and renders performance graphs."""

    QBER_THRESHOLD = BB84.QBER_THRESHOLD

    def __init__(self, num_qubits: int = 5000, n_trials: int = 10,
                 seed: int = 42):
        """
        Args:
            num_qubits : Qubits per simulation run.
            n_trials   : Number of Monte-Carlo trials to average per data point.
            seed       : Base RNG seed.
        """
        self.num_qubits = num_qubits
        self.n_trials   = n_trials
        self.seed       = seed

    # ------------------------------------------------------------------ #
    # Sweep helpers                                                        #
    # ------------------------------------------------------------------ #

    def _sweep_noise(self, noise_values: np.ndarray,
                     eve_prob: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """Sweep noise_prob; return mean QBER and mean key length arrays."""
        qbers, key_lens = [], []
        for noise in noise_values:
            trial_qbers, trial_lens = [], []
            for t in range(self.n_trials):
                bb = BB84(self.num_qubits, noise_prob=noise, eve_prob=eve_prob,
                          seed=self.seed + t)
                res = bb.run()
                trial_qbers.append(res["qber"])
                trial_lens.append(res["key_length"])
            qbers.append(np.mean(trial_qbers))
            key_lens.append(np.mean(trial_lens))
        return np.array(qbers), np.array(key_lens)

    def _sweep_eve(self, eve_values: np.ndarray,
                   noise_prob: float = 0.01) -> np.ndarray:
        """Sweep eve_prob; return mean QBER array."""
        qbers = []
        for eve in eve_values:
            trial_qbers = []
            for t in range(self.n_trials):
                bb = BB84(self.num_qubits, noise_prob=noise_prob,
                          eve_prob=eve, seed=self.seed + t)
                res = bb.run()
                trial_qbers.append(res["qber"])
            qbers.append(np.mean(trial_qbers))
        return np.array(qbers)

    # ------------------------------------------------------------------ #
    # Main plot                                                            #
    # ------------------------------------------------------------------ #

    def generate_report(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Generate a 2×2 grid of performance charts:
            [0,0] QBER vs Noise (no Eve)
            [0,1] QBER vs Eve Intercept Probability
            [1,0] Final Key Length vs Noise
            [1,1] Encryption + Decryption Time (Hybrid vs Classical AES only)

        Args:
            save_path : If given, saves figure to this file path (.png).

        Returns:
            matplotlib Figure object.
        """
        logger.info("Analyzer: Running sweep experiments …")

        noise_range = np.linspace(0.0, 0.15, 20)
        eve_range   = np.linspace(0.0, 1.0,  20)

        qber_no_eve, key_lens_no_eve = self._sweep_noise(noise_range, eve_prob=0.0)
        qber_with_eve, _             = self._sweep_noise(noise_range, eve_prob=0.5)
        qber_vs_eve                  = self._sweep_eve(eve_range, noise_prob=0.01)

        fig = plt.figure(figsize=(13, 8.5), constrained_layout=True)
        fig.suptitle(
            "Hybrid Cryptographic System — Performance Analysis\n"
            "Team 181 | Secure Communication over Public Networks",
            fontsize=13, fontweight="bold", color=NAVY, y=1.01
        )
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.3)

        # ── [0,0] QBER vs Channel Noise ────────────────────────────────
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.plot(noise_range * 100, qber_no_eve * 100, color=TEAL,
                 lw=2, marker="o", ms=4, label="No Eve")
        ax0.plot(noise_range * 100, qber_with_eve * 100, color=AMBER,
                 lw=2, marker="s", ms=4, linestyle="--", label="Eve (50% intercept)")
        ax0.axhline(self.QBER_THRESHOLD * 100, color=RED, lw=1.5,
                    linestyle=":", label=f"Threshold {self.QBER_THRESHOLD*100:.0f}%")
        ax0.fill_between(noise_range * 100, self.QBER_THRESHOLD * 100, 50,
                         alpha=0.08, color=RED)
        ax0.set_title("QBER vs Channel Noise Probability")
        ax0.set_xlabel("Channel Noise Probability (%)")
        ax0.set_ylabel("QBER (%)")
        ax0.set_xlim(0, 15)
        ax0.set_ylim(0, 50)
        ax0.legend(fontsize=9)
        ax0.text(10, self.QBER_THRESHOLD * 100 + 1.5, "ABORT zone",
                 color=RED, fontsize=8)

        # ── [0,1] QBER vs Eve Intercept Probability ────────────────────
        ax1 = fig.add_subplot(gs[0, 1])
        theoretical = eve_range * 0.25 * 100   # theoretical: QBER = P_eve/4
        ax1.plot(eve_range * 100, qber_vs_eve * 100, color=NAVY,
                 lw=2, marker="^", ms=4, label="Simulated QBER")
        ax1.plot(eve_range * 100, theoretical, color=AMBER,
                 lw=1.5, linestyle="--", label="Theoretical (P_eve/4)")
        ax1.axhline(self.QBER_THRESHOLD * 100, color=RED, lw=1.5,
                    linestyle=":", label=f"Threshold {self.QBER_THRESHOLD*100:.0f}%")
        ax1.fill_between(eve_range * 100, self.QBER_THRESHOLD * 100, 30,
                         alpha=0.08, color=RED)
        # Mark detection point
        detect_x = self.QBER_THRESHOLD / 0.25 * 100
        ax1.axvline(detect_x, color=GREEN, lw=1.3, linestyle="--")
        ax1.text(detect_x + 1, 2, f"Eve detected\nat {detect_x:.0f}% intercept",
                 color=GREEN, fontsize=8)
        ax1.set_title("QBER vs Eve Intercept Probability")
        ax1.set_xlabel("Eve Intercept Probability (%)")
        ax1.set_ylabel("QBER (%)")
        ax1.set_xlim(0, 100)
        ax1.set_ylim(0, 30)
        ax1.legend(fontsize=9)

        # ── [1,0] Key Length vs Noise ──────────────────────────────────
        ax2 = fig.add_subplot(gs[1, 0])
        # Expected sifted key ≈ num_qubits * 0.5 (matching bases) * (1 - noise_induced_abort)
        secure_mask = qber_no_eve <= self.QBER_THRESHOLD
        ax2.bar(noise_range[secure_mask] * 100, key_lens_no_eve[secure_mask],
                width=0.55, color=TEAL, alpha=0.8, label="Secure session")
        ax2.bar(noise_range[~secure_mask] * 100, key_lens_no_eve[~secure_mask],
                width=0.55, color=RED, alpha=0.4, label="Session aborted (QBER > threshold)")
        ax2.set_title("Final Secure Key Length vs Channel Noise")
        ax2.set_xlabel("Channel Noise Probability (%)")
        ax2.set_ylabel("Sifted Key Length (bits)")
        ax2.set_xlim(-0.5, 15.5)
        ax2.legend(fontsize=9)

        # ── [1,1] Encryption / Decryption Time ────────────────────────
        ax3 = fig.add_subplot(gs[1, 1])

        # Benchmark AES encryption time at varying message sizes
        message_sizes = [64, 256, 1024, 4096, 16384, 65536]  # bytes
        enc_times, dec_times = [], []

        # Use a dummy QKD key (128 random bits) for timing benchmark
        dummy_key = [int(b) for b in
                     np.random.default_rng(self.seed).integers(0, 2, 256)]
        aes = AESModule(dummy_key)

        for size in message_sizes:
            msg = "A" * size
            # Average over 20 repetitions
            e_timings, d_timings = [], []
            for _ in range(20):
                enc_res = aes.encrypt(msg)
                dec_res = aes.decrypt(enc_res["ciphertext"], enc_res["iv"])
                e_timings.append(enc_res["elapsed_ms"])
                d_timings.append(dec_res["elapsed_ms"])
            enc_times.append(np.mean(e_timings))
            dec_times.append(np.mean(d_timings))

        size_labels = ["64B", "256B", "1KB", "4KB", "16KB", "64KB"]
        x = np.arange(len(size_labels))
        w = 0.35
        ax3.bar(x - w / 2, enc_times, w, color=TEAL,   label="AES Encrypt (hybrid key)")
        ax3.bar(x + w / 2, dec_times, w, color=NAVY,   label="AES Decrypt (hybrid key)")
        ax3.set_title("AES-128 Enc/Dec Latency (Hybrid QKD Key)")
        ax3.set_xlabel("Plaintext Size")
        ax3.set_ylabel("Time (ms)")
        ax3.set_xticks(x)
        ax3.set_xticklabels(size_labels)
        ax3.legend(fontsize=9)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
            logger.info(f"Report saved to: {save_path}")

        return fig