"""
bob_node.py — Bob (Receiver) TCP Socket Server with Robust Error Handling
Team 181 | Hybrid Quantum Cryptographic Systems
"""

import socket
import pickle
from etsi_qkd_api import ETSIQKDNodeAPI

def start_bob_server(host='127.0.0.1', port=65432):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print(f"\n[BOB NODE] Listening for quantum/classical connection on {host}:{port}...")
    
    qkd_api = ETSIQKDNodeAPI(distance_km=10.0)

    while True:
        conn, addr = server_socket.accept()
        print(f"\n[BOB NODE] Connection established with Alice at {addr}")
        
        try:
            data = conn.recv(4096)
            if not data:
                conn.close()
                continue
                
            packet = pickle.loads(data)
            attack_type = packet.get("attack_type", None)
            sifting_msg = packet.get("sifting_msg")
            signature = packet.get("signature")
            alice_pubkey = packet.get("public_key")

            print(f"[BOB NODE] Received PQC Sifting Metadata & Attack Mode: [{attack_type or 'None'}]")

            # 1. Verify PQC Signature
            is_valid = qkd_api.authenticator.verify_sifting_data(sifting_msg, signature, alice_pubkey)
            if not is_valid:
                print("[BOB NODE] PQC Authentication FAILED! Terminating session.")
                conn.sendall(pickle.dumps({
                    "status": "ABORT", 
                    "verdict": "PQC_AUTH_FAILED", 
                    "qber": 0.0, 
                    "yield": 0.0,
                    "reason": "PQC Auth Failed"
                }))
                conn.close()
                continue
                
            print("[BOB NODE] PQC Signature VERIFIED successfully via ML-DSA (Dilithium2).")

            # 2. Execute QKD & Fingerprint Evaluation via ETSI API
            result = qkd_api.execute_quantum_exchange(attack_type=attack_type)
            print(f"[BOB NODE] Fingerprint Engine Verdict: {result['verdict']}")

            response = {
                "status": "SUCCESS" if result["verdict"] == "CLEAN_CHANNEL" else "ABORT",
                "verdict": result["verdict"],
                "qber": result["qber"],
                "yield": result["yield"],
                "reason": "Security Breach Detected - Memory Zeroized" if result["verdict"] != "CLEAN_CHANNEL" else "None"
            }

            if result["verdict"] == "CLEAN_CHANNEL":
                response["aes_key"] = qkd_api.get_key().hex()
                print(f"[BOB NODE] AES Session Key Rollover #1 Success: {response['aes_key']}")
            else:
                print(f"[BOB NODE] Security violation caught! Session aborted and key memory zeroized.")

            conn.sendall(pickle.dumps(response))
            
        except Exception as e:
            print(f"[BOB NODE ERROR] Exception encountered during session: {e}")
            try:
                error_response = {
                    "status": "ABORT",
                    "verdict": "SERVER_ERROR",
                    "qber": 0.0,
                    "yield": 0.0,
                    "reason": str(e)
                }
                conn.sendall(pickle.dumps(error_response))
            except:
                pass
        finally:
            conn.close()

if __name__ == "__main__":
    start_bob_server()