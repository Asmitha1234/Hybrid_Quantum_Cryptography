# Phase 3 Verification Report: Real-Time QKD Fingerprinting Engine
**Team ID:** 181  
**Target Link Distance:** 10.0 km  
**Status:** Verification Complete (Real-Time Stochastic Simulation)

---

## 1. Experimental Summary

| Scenario | Signal QBER ($E_\mu$) | Decoy Yield ($Y_\nu$) | SKR (bits/pulse) | Sifted Key | Fingerprint Verdict | AES Session Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Clean Link** | `1.55%` | `0.006323` | `0.025739` | 193 bits | `CLEAN_CHANNEL` | **SUCCESSFUL (AES Key Rollover #1 Verified)** |
| **2. Zero-QBER PNS** | `0.00%` | `0.002011` | `0.000000` | 101 bits | `PNS_ATTACK_DETECTED` | **ABORTED (Key Memory Zeroed & Blocked by Fingerprint Engine)** |
| **3. Intercept-Resend** | `15.76%` | `0.005309` | `0.000000` | 203 bits | `INTERCEPT_RESEND_ATTACK` | **ABORTED (Key Memory Zeroed & Blocked by Fingerprint Engine)** |

---

## 2. Real-Time Findings Analysis
* **Clean Link:** Achieved dynamic QBER of **1.55%** and derived AES key (`fa75f333470d7d583306a5ff2b1532b4`).
* **PNS Attack:** Caught by decoy yield drop to **0.002011**. Session aborted.
* **Intercept-Resend:** Caught by elevated QBER of **15.76%**, exceeding 11% GLLP limit. Session aborted.
