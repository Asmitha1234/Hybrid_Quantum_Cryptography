import numpy as np
import random
import hashlib
import matplotlib.pyplot as plt
import csv

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# -----------------------------
# PARAMETERS
# -----------------------------
N_BITS = 1000
QBER_THRESHOLD = 0.11

# -----------------------------
# QKD WITHOUT ATTACK
# -----------------------------
def run_qkd(noise_prob):
    alice_bits = np.random.randint(0, 2, N_BITS)
    alice_bases = np.random.choice(['+', 'x'], N_BITS)

    transmitted_bits = []
    for i in range(N_BITS):
        bit = alice_bits[i]
        if random.random() < noise_prob:
            bit = 1 - bit
        transmitted_bits.append(bit)

    bob_bases = np.random.choice(['+', 'x'], N_BITS)
    bob_bits = []

    for i in range(N_BITS):
        if bob_bases[i] == alice_bases[i]:
            bob_bits.append(transmitted_bits[i])
        else:
            bob_bits.append(random.randint(0, 1))

    alice_key, bob_key = [], []
    for i in range(N_BITS):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(bob_bits[i])

    errors = sum(a != b for a, b in zip(alice_key, bob_key))
    qber = errors / len(alice_key) if len(alice_key) > 0 else 1.0

    return qber, alice_key

# -----------------------------
# QKD WITH ATTACK
# -----------------------------
def run_qkd_with_attack(noise_prob, eve_prob):
    alice_bits = np.random.randint(0, 2, N_BITS)
    alice_bases = np.random.choice(['+', 'x'], N_BITS)

    transmitted_bits = []

    for i in range(N_BITS):
        bit = alice_bits[i]

        # Intercept-resend
        if random.random() < eve_prob:
            eve_basis = random.choice(['+', 'x'])
            if eve_basis != alice_bases[i]:
                bit = random.randint(0, 1)

        if random.random() < noise_prob:
            bit = 1 - bit

        transmitted_bits.append(bit)

    bob_bases = np.random.choice(['+', 'x'], N_BITS)
    bob_bits = []

    for i in range(N_BITS):
        if bob_bases[i] == alice_bases[i]:
            bob_bits.append(transmitted_bits[i])
        else:
            bob_bits.append(random.randint(0, 1))

    alice_key, bob_key = [], []
    for i in range(N_BITS):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(bob_bits[i])

    errors = sum(a != b for a, b in zip(alice_key, bob_key))
    qber = errors / len(alice_key) if len(alice_key) > 0 else 1.0

    return qber, alice_key

# -----------------------------
# AES
# -----------------------------
def qkd_to_aes_key(qkd_key):
    bit_string = ''.join(map(str, qkd_key))
    return hashlib.sha256(bit_string.encode()).digest()[:16]

def aes_encrypt_decrypt(message, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(message.encode(), AES.block_size))

    decrypted = unpad(
        AES.new(key, AES.MODE_CBC, cipher.iv).decrypt(ciphertext),
        AES.block_size
    ).decode()

    return ciphertext, decrypted

# -----------------------------
# FILE SETUP
# -----------------------------
csv_file = open("qkd_comparison_results.csv", "w", newline="")
csv_writer = csv.writer(csv_file)

csv_writer.writerow([
    "Noise", "Eve_Prob",
    "QBER_No_Attack", "QBER_With_Attack",
    "Status"
])

txt_file = open("qkd_results.txt", "w")
txt_file.write("QKD Simulation Results\n")
txt_file.write("="*50 + "\n\n")

# -----------------------------
# MAIN LOOP
# -----------------------------
noise_values = []
qber_no_attack = []
qber_with_attack = []

print("\n--- 20% IMPLEMENTATION ---\n")

for i in range(300):
    noise = round(i * 0.001, 3)
    eve_prob = round(i * 0.001, 3)

    qber1, _ = run_qkd(noise)
    qber2, key = run_qkd_with_attack(noise, eve_prob)

    status = "Secure" if qber2 <= QBER_THRESHOLD else "Rejected"

    noise_values.append(noise)
    qber_no_attack.append(qber1)
    qber_with_attack.append(qber2)

    # Console output
    print(f"Noise: {noise:.3f} | Eve: {eve_prob:.3f}")
    print(f"  No Attack QBER: {round(qber1,4)}")
    print(f"  With Attack QBER: {round(qber2,4)}")

    # Save to CSV
    csv_writer.writerow([
        noise, eve_prob,
        round(qber1, 5),
        round(qber2, 5),
        status
    ])

    # TXT OUTPUT
    txt_output = f"Noise: {noise:.3f}, Eve: {eve_prob:.3f}\n"
    txt_output += f"QBER (No Attack): {round(qber1,4)}\n"
    txt_output += f"QBER (With Attack): {round(qber2,4)}\n"
    txt_output += f"Status: {status}\n"

    if status == "Secure":
        aes_key = qkd_to_aes_key(key)
        msg = "Hello Quantum"

        ciphertext, decrypted = aes_encrypt_decrypt(msg, aes_key)

        txt_output += f"AES Key: {aes_key.hex()}\n"
        txt_output += f"Decrypted: {decrypted}\n"

        print("  AES Key:", aes_key.hex())
        print("  Decrypted:", decrypted)

    else:
        txt_output += "Key Rejected\n"
        print("\nKey Rejected at Noise =", noise)

    txt_output += "-"*40 + "\n"
    txt_file.write(txt_output)

    if status == "Rejected":
        break

# Close files
csv_file.close()
txt_file.close()

print("\nCSV saved as qkd_comparison_results.csv")
print("TXT saved as qkd_results.txt")

# -----------------------------
# GRAPH
# -----------------------------
plt.figure()
plt.plot(noise_values, qber_no_attack, label="No Attack")
plt.plot(noise_values, qber_with_attack, label="With Attack")
plt.axhline(y=QBER_THRESHOLD, linestyle='--')

plt.xlabel("Noise Probability")
plt.ylabel("QBER")
plt.title("QBER Comparison (Noise + Attack)")
plt.legend()
plt.grid()

plt.show()