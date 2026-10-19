# Hybrid Quantum Cryptographic Systems (QKD + PQC + AES)

[![ETSI Standard Compliance](https://img.shields.io/badge/ETSI-GS_QKD_004%2F014-blue.svg)](https://www.etsi.org/)
[![Post-Quantum Security](https://img.shields.io/badge/PQC-ML--DSA%20%28Dilithium2%29-emerald.svg)](https://openquantumsafe.org/)
[![License](https://img.shields.io/badge/License-MIT-slate.svg)](LICENSE)

An enterprise-grade, ETSI-compliant Security Operations Center (SOC) framework and simulation platform integrating **Decoy-State Quantum Key Distribution (BB84)**, **Post-Quantum Cryptography (ML-DSA / Dilithium2)**, and **Symmetric AES-128 Encryption**.

Developed for the Capstone Project at PES University by **Team 181**.

---

## 1. Project Overview & Scope

* **Project Title**: Hybrid Quantum Cryptographic Systems (QKD + PQC + AES)
* **Project ID**: [Insert Project ID]
* **Project Guide**: [Insert Guide Name]
* **Project Team**: Asmi (PES2UG23CS102) & Team 181
* **University**: PES University
* **Abstract & Scope**: Development of an enterprise-grade, ETSI-compliant Security Operations Center (SOC) framework integrating Decoy-State Quantum Key Distribution (BB84), Post-Quantum Cryptography (ML-DSA / Dilithium2), and symmetric AES encryption. The scope covers validating secure session establishment, active attack detection (Photon Number Splitting and Intercept-Resend), and physical attenuation boundaries up to 50 km SMF-28 optical fiber.

---

## 2. Review 1 & 2 Feedback and Feasibility

* **Review 1 Feedback**: Focused on clarifying the integration boundary between quantum key generation and classical AES symmetric rollover.
  * *Feasibility/Progress*: Implemented via the `ETSIQKDNodeAPI` abstraction layer, ensuring keys are only committed to active buffers upon passing dual-metric verification.
* **Review 2 Feedback**: Recommended strengthening the handling of physical channel limitations versus active eavesdropping to avoid false-positive attack classifications.
  * *Feasibility/Progress*: Successfully engineered a deterministic 30 km physical distance limit check (`EXCESSIVE_CHANNEL_LOSS_LIMIT`), separating natural fiber loss ($\alpha = 0.2\text{ dB/km}$) from malicious interference.

---

## 3. System Architecture & Modules

* **Layer 1: Optical Channel & Decoy Engine (`qkd_decoy.py`)**: Simulates pulsed coherent laser sources, decoy intensity states ($\mu, \nu$), and Bob's single-photon detector statistics.
* **Layer 2: PQC Authentication Gate (`oqs_auth.py`)**: Applies NIST-standard ML-DSA (Dilithium2) digital signatures via `liboqs` to authenticate sifting metadata across insecure classical TCP channels.
* **Layer 3: ETSI Hardware Abstraction Layer (`etsi_qkd_api.py`)**: Evaluates signal QBER ($E_\mu$) against the 11.0% GLLP threshold and decoy yield ($Y_\nu$) against the 0.002839 PNS safety bound. Enforces deterministic physical boundary checks at $>30.0\text{ km}$ and handles ETSI-compliant volatile memory zeroization (`0x00` overwrite).

```text
+-------------------+      ML-DSA Signed Sifting Frame      +-------------------+
|    Alice Node     | ====================================> |     Bob Node      |
|  (Decoy BB84 Tx)  | <==================================== |  (Decoy BB84 Rx)  |
+-------------------+       Public Classical Channel        +-------------------+
          |                                                           |
          +-------------------- Optical Fiber Link ------------------+
                                (SMF-28, 1-50 km)
                                        |
                                        v
                      +-----------------------------------+
                      |     ETSI Hardware Abstraction     |
                      |         (etsi_qkd_api.py)         |
                      +-----------------------------------+
                                        |
                  +---------------------+---------------------+
                  |                                           |
         [Passed Verification]                      [Threat / Loss Abort]
                  |                                           |
                  v                                           v
     +-------------------------+                 +-------------------------+
     |  AES-128 Key Generation |                 |  ETSI RAM Zeroization   |
     |  & Active Data Transfer |                 |  (Buffer Overwritten)   |
     +-------------------------+                 +-------------------------+
```

---

## 4. Implementation Details & Algorithms

* **Module 1 (Decoy-State QKD Engine)**: Utilizes Python and NumPy for stochastic modeling. Computes optical transmittance over SMF-28 fiber using exponential decay: $\eta = 10^{(-\alpha L / 10)}$ where $\alpha = 0.2\text{ dB/km}$ and $L$ is distance.
* **Module 2 (PQC Authentication)**: Utilizes `liboqs-python` to generate post-quantum public/private keypairs, signing sifting metadata packets before transmission to prevent Man-in-the-Middle (MitM) tampering.
* **Module 3 (ETSI Abstraction & Zeroization)**: Implements compliance with ETSI GS QKD 004/014 REST API logic, executing immediate RAM scrubbing (overwriting the key `bytearray` with `0x00`) upon breach or attenuation aborts.
* **Module 4 (SOC Visual Dashboard)**: Built with Streamlit (`dashboard_app.py`) and Tailwind CSS/Chart.js (`index.html`) to deliver real-time visual telemetry tracking, dedicated verification cards, and automated forensic report generation.

---

## 5. Project Structure

```text
├── etsi_qkd_api.py                # Hardware Abstraction Layer & zeroization engine
├── oqs_auth.py                    # ML-DSA (Dilithium2) PQC digital signature handler
├── qkd_decoy.py                   # Decoy-state BB84 pulse generator & detector physics
├── fingerprinting.py              # Statistical threat detection & metric classification
├── dashboard_app.py               # Python Streamlit SOC visual dashboard
├── index.html                     # Standalone HTML/Tailwind high-contrast SOC dashboard
├── alice_node.py                  # Quantum Tx node execution handler
├── bob_node.py                    # Quantum Rx node execution handler
└── Phase3_Verification_Report.md  # Experimental telemetry records & analysis
```

---

## 6. Quickstart & Installation

### Prerequisites

* Python 3.10+
* Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Asmitha1234/Hybrid_Quantum_Cryptography.git
   cd Hybrid_Quantum_Cryptography
   ```

2. Install dependencies:

   ```bash
   pip install numpy matplotlib streamlit oqs
   ```

### Running the SOC Dashboard

* **Option A (HTML / JS Dashboard)**:

  ```bash
  python -m http.server 8000
  ```

  Open `http://localhost:8000` in your browser.

* **Option B (Python Streamlit Dashboard)**:

  ```bash
  python -m streamlit run dashboard_app.py
  ```

---

## 7. Simulation & Test Scenarios

| Test Scenario | Distance | Network Vector | Expected Verdict | Action Taken |
| --- | --- | --- | --- | --- |
| **Nominal Link** | $10.0\text{ km}$ | Clean Link | `CLEAN_CHANNEL` | 128-bit AES Key Rollover Active |
| **PNS Attack** | $10.0\text{ km}$ | Zero-QBER PNS | `PNS_ATTACK_DETECTED` | Volatile RAM Scrubbed (`0x00`) |
| **Intercept-Resend** | $10.0\text{ km}$ | Active Intercept | `INTERCEPT_RESEND_ATTACK` | Volatile RAM Scrubbed (`0x00`) |
| **Distance Limit** | $35.0\text{ km}$ | Clean Link | `EXCESSIVE_CHANNEL_LOSS_LIMIT` | Session Aborted, Memory Zeroized |

---

## 8. Results and Discussion

* **Nominal Link ($10\text{ km}$)**: Verified nominal QBER ($\sim 1.05\%$) and Decoy Yield ($>0.002839$), yielding active 128-bit AES rollover keys (`SECURE_ACTIVE`).
* **Physical Attenuation Limit ($35\text{ km}$)**: Deterministic abort triggered correctly; natural fiber loss reduced decoy yield below operational bounds without false-positive attack alarms (`EXCESSIVE_CHANNEL_LOSS_LIMIT`).
* **Threat Scenarios**: Intercept-Resend attacks spiked QBER to $>16\%$, triggering immediate RAM zeroization (`INTERCEPT_RESEND_ATTACK`). PNS attacks were successfully flagged via decoy yield suppression (`PNS_ATTACK_DETECTED`).

---

## 9. Conclusion and Future Work

* **Conclusion**: Successfully designed, implemented, and validated an enterprise-grade ETSI-compliant QKD SOC dashboard integrating Post-Quantum Cryptography and autonomous memory zeroization, clearly separating eavesdropping vectors from physical attenuation limits.
* **Future Work**: Integration with physical continuous-variable QKD (CV-QKD) optical components and multi-node software-defined quantum network topologies incorporating quantum repeaters.

---

## 10. References

1. V. Scarani, H. Bechmann-Pasquinucci, N. J. Cerf, M. Dušek, N. Lütkenhaus, and M. Peev, "The security of practical quantum key distribution," *Rev. Mod. Phys.*, vol. 81, pp. 1301–1350, September 2009.
2. ETSI GS QKD 014, "Quantum Key Distribution (QKD); Protocol and data format of REST API," European Telecommunications Standards Institute, Specification, 2019.
3. D. Moody et al., "Status of the Post-Quantum Cryptography Standardization Process," *NIST Internal Report 8413*, National Institute of Standards and Technology, July 2022.
4. W. Y. Hwang, "Quantum key distribution with decoy states," *Phys. Rev. Lett.*, vol. 91, p. 057901, July 2003.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
