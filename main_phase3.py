"""
main_phase3.py — 70% Milestone Real-Time Execution Runner
Team 181 | Hybrid Cryptographic Systems
"""

import sys
import logging
from qkd_decoy import DecoyBB84
from fingerprinting import AttackSimulator, AttackFingerprinter
from aes_encryption import DynamicAESCipherController
from oqs_auth import PQCAuthenticator
from phase3_analyzer import generate_markdown_report, generate_performance_plot, run_parametric_distance_sweep

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s", stream=sys.stdout)
SEPARATOR = "═" * 70


def run_test_scenario(scenario_name: str, distance_km: float = 10.0, 
                      attack_type: str = None, plaintext: str = "Payload: Phase 3 Verification") -> dict:
    print(f"\n{SEPARATOR}", flush=True)
    print(f" SCENARIO: {scenario_name}", flush=True)
    print(f" Distance: {distance_km} km | Attack: {attack_type or 'None'}", flush=True)
    print(SEPARATOR, flush=True)

    # 0. Post-Quantum Classical Channel Authentication (ML-DSA / Dilithium)
    print("\n--- PQC CLASSICAL CHANNEL AUTHENTICATION ---", flush=True)
    pqc_alice = PQCAuthenticator(alg_name="Dilithium2")
    sifting_payload = f"Alice_Basis_Reconciliation_Vector_{distance_km}km".encode()
    signature = pqc_alice.sign_sifting_data(sifting_payload)
    
    if not pqc_alice.verify_sifting_data(sifting_payload, signature, pqc_alice.public_key):
        print("  Status  : AUTHENTICATION_FAILED (MITM Sifting Spoof Detected)", flush=True)
        return {"verdict": "AUTH_FAILURE", "aes_status": "ABORTED (PQC Signature Invalid)"}
    print("  Status  : AUTHENTICATED (ML-DSA Digital Signature Verified)", flush=True)

    # 1. Initialize Decoy BB84 Engine without fixed seed
    engine = DecoyBB84(num_pulses=20000, distance_km=distance_km, seed=None)
    alice = engine.generate_alice_pulses()

    # 2. Apply Optional Attack Models
    modified_bits = None
    modified_counts = None
    
    if attack_type == "pns":
        attacker = AttackSimulator()
        modified_counts = attacker.photon_number_splitting(alice["photon_counts"])
    elif attack_type == "intercept":
        attacker = AttackSimulator()
        modified_bits = attacker.intercept_resend(alice["bits"], alice["bases"], eve_prob=0.8)

    # 3. Simulate Bob's Reception & Extract Decoy Metrics
    bob = engine.simulate_bob_reception(alice, modified_bits=modified_bits, modified_counts=modified_counts)
    metrics = engine.process_decoy_statistics(alice, bob)
    skr = engine.calculate_skr(metrics)

    # 4. Run Fingerprinting Engine
    verdict, explanation = AttackFingerprinter.analyze(
        metrics, skr, distance_km=distance_km, mu=0.5, nu=0.1
    )

    print("\n--- METRICS & STATISTICAL ANALYSIS ---", flush=True)
    print(f"  Signal State QBER (E_mu) : {metrics['E_signal']:.4f} ({metrics['E_signal']:.2%})", flush=True)
    print(f"  Decoy State QBER (E_nu)   : {metrics['E_decoy']:.4f} ({metrics['E_decoy']:.2%})", flush=True)
    print(f"  Signal State Yield (Y_mu) : {metrics['Y_signal']:.6f}", flush=True)
    print(f"  Decoy State Yield (Y_nu)  : {metrics['Y_decoy']:.6f}", flush=True)
    print(f"  Single-Photon Yield (Y_1) : {metrics['Y_1']:.6f}", flush=True)
    print(f"  Secret Key Rate (SKR)     : {skr:.6f} bits/pulse", flush=True)
    print(f"  Sifted Key Output Length  : {len(metrics['sifted_key_bits'])} bits", flush=True)

    print("\n--- FINGERPRINTING ENGINE VERDICT ---", flush=True)
    print(f"  Status  : {verdict}", flush=True)
    print(f"  Details : {explanation}", flush=True)

    # 5. Dynamic Key Pool, Active Interlock, and AES Rotation
    print("\n--- DYNAMIC HYBRID AES INTEGRATION & RE-KEYING ---", flush=True)
    aes_controller = DynamicAESCipherController()
    hex_key = None
    
    if verdict in ["CLEAN_CHANNEL", "ENVIRONMENTAL_NOISE"] and skr > 0.0 and len(metrics["sifted_key_bits"]) >= 128:
        aes_controller.add_distilled_bits(metrics["sifted_key_bits"])
        if aes_controller.rotate_key_if_ready(min_bits=128):
            enc = aes_controller.encrypt_payload(plaintext.encode())
            dec = aes_controller.decrypt_payload(enc)
            
            hex_key = aes_controller.current_key.hex()
            session_status = f"SUCCESSFUL (AES Key Rollover #{aes_controller.key_id} Verified)"
            print(f"  AES Active Key (Hex)  : {hex_key}", flush=True)
            print(f"  Ciphertext            : {enc['ciphertext'].hex()[:32]}...", flush=True)
            print(f"  Decrypted Plaintext   : '{dec.decode()}'", flush=True)
            print(f"  Session Status        : {session_status}", flush=True)
    else:
        aes_controller.sanitize_memory()
        session_status = "ABORTED (Key Memory Zeroed & Blocked by Fingerprint Engine)"
        print(f"  Session Status        : {session_status}", flush=True)

    return {
        "qber": metrics["E_signal"],
        "y_nu": metrics["Y_decoy"],
        "skr": skr,
        "sifted_bits": len(metrics["sifted_key_bits"]),
        "verdict": verdict,
        "aes_status": session_status,
        "hex_key": hex_key,
    }


if __name__ == "__main__":
    results_data = {}

    results_data["clean"] = run_test_scenario("Clean Link over 10 km Fiber", distance_km=10.0, attack_type=None)
    results_data["pns"] = run_test_scenario("Zero-QBER PNS Attack Simulation", distance_km=10.0, attack_type="pns")
    results_data["intercept"] = run_test_scenario("Active Intercept-Resend Eavesdropping", distance_km=10.0, attack_type="intercept")

    print(f"\n{SEPARATOR}", flush=True)
    print(" GENERATING AUTOMATED VERIFICATION REPORT & PARAMETRIC SWEEPS", flush=True)
    print(SEPARATOR, flush=True)
    
    generate_markdown_report(results_data, report_filename="Phase3_Verification_Report.md")
    generate_performance_plot(results_data, output_filename="qkd_phase3_annotated_curves.png")
    
    # Run the 0-100km Parametric Fiber Sweep
    run_parametric_distance_sweep(output_filename="qkd_distance_sweep_70percent.png")