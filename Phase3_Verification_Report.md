# Phase 3 Verification Report: Real-Time QKD Fingerprinting Engine
**Team ID:** 181  
**Target Link Distance:** 10.0 km  
**Status:** Verification Complete (Real-Time Stochastic Simulation)

---

## 1. Experimental Summary

| Scenario | Signal QBER ($E_\mu$) | Decoy Yield ($Y_\nu$) | SKR (bits/pulse) | Sifted Key | Fingerprint Verdict | AES Session Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Clean Link** | `1.41%` | `0.007238` | `0.026082` | 213 bits | `CLEAN_CHANNEL` | **SUCCESSFUL (AES Key Rollover #1 Verified)** |
| **2. Zero-QBER PNS** | `0.00%` | `0.003797` | `0.000000` | 108 bits | `HIGH_NOISE_ABORT` | **ABORTED (Key Memory Zeroed & Blocked by Fingerprint Engine)** |
| **3. Intercept-Resend** | `27.60%` | `0.005323` | `0.000000` | 192 bits | `INTERCEPT_RESEND_ATTACK` | **ABORTED (Key Memory Zeroed & Blocked by Fingerprint Engine)** |

---

## 2. Real-Time Findings Analysis
* **Clean Link:** Achieved dynamic QBER of **1.41%** and derived AES key (`9e32f8be3cf51e0c23da00f6e3847ebd`).
* **PNS Attack:** Caught by decoy yield drop to **0.003797**. Session aborted.
* **Intercept-Resend:** Caught by elevated QBER of **27.60%**, exceeding 11% GLLP limit. Session aborted.
