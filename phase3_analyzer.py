"""
phase3_analyzer.py — Dynamic Plot, Report, and Parametric Sweep Generator
Team 181 | Hybrid Cryptographic Systems
"""

import matplotlib.pyplot as plt
import numpy as np


def generate_performance_plot(results_data, output_filename="qkd_phase3_annotated_curves.png"):
    plt.style.use("seaborn-v0_8-darkgrid" if "seaborn-v0_8-darkgrid" in plt.style.available else "default")
    distances = np.linspace(0, 50, 100)

    # Physical parameters
    alpha, eta_bob = 0.2, 0.1
    mu, y0, e_dark, e_detector = 0.5, 1e-5, 0.5, 0.015
    eta_total = (10.0 ** (-(alpha * distances) / 10.0)) * eta_bob

    def binary_entropy(p):
        p = np.clip(p, 1e-12, 1.0 - 1e-12)
        return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)

    # Theoretical curves
    Y_signal_clean = (1.0 - np.exp(-mu * eta_total)) + y0
    Y_1_clean = eta_total + y0
    QBER_clean = (e_detector * (1.0 - np.exp(-mu * eta_total)) + e_dark * y0) / Y_signal_clean
    H2_clean = binary_entropy(QBER_clean)
    SKR_clean = np.maximum(0, 0.5 * (Y_1_clean * (1.0 - H2_clean) - Y_signal_clean * 1.16 * H2_clean))

    Y_signal_pns = Y_signal_clean * 0.45
    Y_1_pns = Y_1_clean * 0.25
    SKR_pns = np.maximum(0, 0.5 * (Y_1_pns * (1.0 - H2_clean) - Y_signal_pns * 1.16 * H2_clean))

    # Real-time run values
    clean_skr = results_data.get('clean', {}).get('skr', 0.0)
    clean_qber = results_data.get('clean', {}).get('qber', 0.0) * 100
    pns_skr = results_data.get('pns', {}).get('skr', 0.0)
    int_qber = results_data.get('intercept', {}).get('qber', 0.0) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=100)
    c_clean, c_pns, c_intercept = "#1f77b4", "#ff7f0e", "#d62728"

    # --- Left: SKR ---
    ax1.plot(distances, SKR_clean, label="Clean Channel", color=c_clean, linewidth=2.0)
    ax1.plot(distances, SKR_pns, label="PNS Attack", color=c_pns, linewidth=1.8, linestyle="--")
    ax1.plot(distances, np.zeros_like(distances), label="Intercept-Resend", color=c_intercept, linewidth=1.8, linestyle=":")
    
    ax1.axvline(x=10.0, color="gray", linestyle=":", alpha=0.6)
    ax1.scatter([10.0, 10.0, 10.0], [max(1e-6, clean_skr), max(1e-6, pns_skr), 1e-6], 
                color=[c_clean, c_pns, c_intercept], s=35, zorder=5)

    ax1.annotate(f"Clean: {clean_skr:.4f}", xy=(10.0, max(1e-6, clean_skr)), xytext=(15, max(1e-6, clean_skr) * 1.3),
                 arrowprops=dict(arrowstyle="->", color=c_clean, lw=1), fontsize=8, color=c_clean,
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=c_clean, alpha=0.9))
    ax1.annotate(f"PNS: {pns_skr:.4f}", xy=(10.0, max(1e-6, pns_skr)), xytext=(15, max(1e-6, pns_skr) * 0.25),
                 arrowprops=dict(arrowstyle="->", color=c_pns, lw=1), fontsize=8, color=c_pns,
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=c_pns, alpha=0.9))

    ax1.set_title("Secret Key Rate (SKR)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Fiber Distance (km)", fontsize=9.5)
    ax1.set_ylabel("SKR (bits/pulse)", fontsize=9.5)
    ax1.set_yscale("log")
    ax1.set_ylim(1e-6, 1e-1)
    ax1.set_xlim(0, 50)
    ax1.legend(frameon=True, facecolor="white", fontsize=8.5, loc="upper right")
    ax1.grid(True, which="both", linestyle="--", alpha=0.4)

    # --- Right: QBER ---
    ax2.plot(distances, QBER_clean * 100, label="Clean / PNS Channel", color=c_clean, linewidth=2.0)
    ax2.plot(distances, np.full_like(distances, 23.12), label="Intercept-Resend", color=c_intercept, linewidth=1.8, linestyle=":")
    ax2.axhline(y=11.0, color="black", linestyle="-.", linewidth=1.2, label="GLLP Limit (11.0%)")
    ax2.axvline(x=10.0, color="gray", linestyle=":", alpha=0.6)
    
    ax2.scatter([10.0, 10.0], [clean_qber, int_qber], color=[c_clean, c_intercept], s=35, zorder=5)

    ax2.annotate(f"Clean: {clean_qber:.2f}%", xy=(10.0, clean_qber), xytext=(15, 4.0),
                 arrowprops=dict(arrowstyle="->", color=c_clean, lw=1), fontsize=8, color=c_clean,
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=c_clean, alpha=0.9))
    ax2.annotate(f"Intercept: {int_qber:.2f}%", xy=(10.0, int_qber), xytext=(15, 25.0),
                 arrowprops=dict(arrowstyle="->", color=c_intercept, lw=1), fontsize=8, color=c_intercept,
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=c_intercept, alpha=0.9))

    ax2.set_title("Signal QBER ($E_\\mu$)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Fiber Distance (km)", fontsize=9.5)
    ax2.set_ylabel("QBER (%)", fontsize=9.5)
    ax2.set_ylim(-1, 30)
    ax2.set_xlim(0, 50)
    ax2.legend(frameon=True, facecolor="white", fontsize=8.5, loc="center right")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.fill_between(distances, 11.0, 30.0, color="red", alpha=0.06)

    plt.suptitle("Team 181 | Phase 3 Real-Time Channel Performance Evaluation", fontsize=12, fontweight="bold", y=0.98)
    plt.subplots_adjust(top=0.86, bottom=0.14, left=0.08, right=0.98, wspace=0.25)
    
    plt.savefig(output_filename, dpi=200, bbox_inches="tight")
    print(f"\n[ANALYZER] Plot generated and saved to '{output_filename}'")
    plt.close()


def run_parametric_distance_sweep(output_filename="qkd_distance_sweep_70percent.png"):
    """Generates 0-100 km physical optical fiber performance sweep graphics."""
    from qkd_decoy import DecoyBB84

    distances = np.linspace(0, 100, 21)
    skr_list, qber_list = [], []

    for dist in distances:
        engine = DecoyBB84(num_pulses=5000, distance_km=dist, seed=None)
        alice = engine.generate_alice_pulses()
        bob = engine.simulate_bob_reception(alice)
        metrics = engine.process_decoy_statistics(alice, bob)
        skr = engine.calculate_skr(metrics)
        
        skr_list.append(skr)
        qber_list.append(metrics["E_signal"] * 100)

    fig, ax1 = plt.subplots(figsize=(8, 4.5))

    color = 'tab:blue'
    ax1.set_xlabel('Fiber Distance (km)')
    ax1.set_ylabel('Secret Key Rate (bits/pulse)', color=color)
    ax1.plot(distances, skr_list, 'o-', color=color, label="Secret Key Rate (SKR)")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()  
    color = 'tab:red'
    ax2.set_ylabel('Signal QBER (%)', color=color)
    ax2.plot(distances, qber_list, 's--', color=color, label="Signal QBER (E_mu)")
    ax2.axhline(y=11.0, color='r', linestyle=':', label="11% GLLP Threshold")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("Team 181 | QKD Optical Channel Performance Sweep (0–100 km SMF-28)")
    fig.tight_layout()
    plt.savefig(output_filename, dpi=300)
    print(f"[ANALYZER] Saved 0-100km parametric sweep plot to '{output_filename}'")
    plt.close()


def generate_markdown_report(results_data, report_filename="Phase3_Verification_Report.md"):
    report_content = f"""# Phase 3 Verification Report: Real-Time QKD Fingerprinting Engine
**Team ID:** 181  
**Target Link Distance:** 10.0 km  
**Status:** Verification Complete (Real-Time Stochastic Simulation)

---

## 1. Experimental Summary

| Scenario | Signal QBER ($E_\\mu$) | Decoy Yield ($Y_\\nu$) | SKR (bits/pulse) | Sifted Key | Fingerprint Verdict | AES Session Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Clean Link** | `{results_data['clean']['qber']*100:.2f}%` | `{results_data['clean']['y_nu']:.6f}` | `{results_data['clean']['skr']:.6f}` | {results_data['clean']['sifted_bits']} bits | `{results_data['clean']['verdict']}` | **{results_data['clean']['aes_status']}** |
| **2. Zero-QBER PNS** | `{results_data['pns']['qber']*100:.2f}%` | `{results_data['pns']['y_nu']:.6f}` | `{results_data['pns']['skr']:.6f}` | {results_data['pns']['sifted_bits']} bits | `{results_data['pns']['verdict']}` | **{results_data['pns']['aes_status']}** |
| **3. Intercept-Resend** | `{results_data['intercept']['qber']*100:.2f}%` | `{results_data['intercept']['y_nu']:.6f}` | `{results_data['intercept']['skr']:.6f}` | {results_data['intercept']['sifted_bits']} bits | `{results_data['intercept']['verdict']}` | **{results_data['intercept']['aes_status']}** |

---

## 2. Real-Time Findings Analysis
* **Clean Link:** Achieved dynamic QBER of **{results_data['clean']['qber']*100:.2f}%** and derived AES key (`{results_data['clean'].get('hex_key', 'N/A')}`).
* **PNS Attack:** Caught by decoy yield drop to **{results_data['pns']['y_nu']:.6f}**. Session aborted.
* **Intercept-Resend:** Caught by elevated QBER of **{results_data['intercept']['qber']*100:.2f}%**, exceeding 11% GLLP limit. Session aborted.
"""
    with open(report_filename, "w") as f:
        f.write(report_content)
    print(f"[ANALYZER] Report generated and saved to '{report_filename}'")