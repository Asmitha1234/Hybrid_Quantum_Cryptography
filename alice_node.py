"""
alice_node.py — Alice (Sender) Client Script with Live Attack Injection Option
Team 181 | Hybrid Quantum Cryptographic Systems
"""

import socket
import pickle
from etsi_qkd_api import ETSIQKDNodeAPI

def run_alice_client(attack_type=None, host='127.0.0.1', port=65432):
    print(f"\n[ALICE CLIENT] Initializing transmission packet...")
    
    qkd_api = ETSIQKDNodeAPI(distance_km=10.0)
    
    # 1. Prepare PQC Signature
    sifting_msg = b"ALICE_BASIS_EXCHANGE_DIST_10KM"
    signature = qkd_api.authenticator.sign_sifting_data(sifting_msg)
    
    packet = {
        "attack_type": attack_type,
        "sifting_msg": sifting_msg,
        "signature": signature,
        "public_key": qkd_api.authenticator.public_key
    }

    # 2. Connect to Bob over TCP Socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"[ALICE CLIENT] Connected to Bob at {host}:{port}")
        
        client_socket.sendall(pickle.dumps(packet))
        
        # 3. Receive response from Bob
        response_data = client_socket.recv(4096)
        response = pickle.loads(response_data)
        
        print("\n" + "="*60)
        print(" [ALICE CLIENT] REMOTE SESSION RESPONSE RECEIVED")
        print("="*60)
        print(f" Status   : {response.get('status', 'UNKNOWN')}")
        print(f" Verdict  : {response.get('verdict', 'N/A')}")
        print(f" QBER     : {response.get('qber', 0.0):.2f}%")
        print(f" Yield    : {response.get('yield', 0.0):.6f}")
        
        if response.get('status') == "SUCCESS":
            print(f" AES Key  : {response.get('aes_key')}")
            print(" Result   : Secure Link Established & Payload Encrypted!")
        else:
            print(f" Result   : Session Aborted & Memory Zeroized! Reason: {response.get('reason', 'Security Breach Detected')}")
        print("="*60 + "\n")
        
    except ConnectionRefusedError:
        print("[ALICE CLIENT] Error: Could not connect to Bob. Make sure bob_node.py is running!")
    finally:
        client_socket.close()

if __name__ == "__main__":
    print("Select Attack Vector to Send to Bob:")
    print("1. Clean Link (Normal)")
    print("2. Zero-QBER PNS Attack (Stealth)")
    print("3. Active Intercept-Resend Attack (QBER Spike)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    attack_map = {"1": None, "2": "pns", "3": "intercept"}
    selected_attack = attack_map.get(choice, None)
    
    run_alice_client(attack_type=selected_attack)