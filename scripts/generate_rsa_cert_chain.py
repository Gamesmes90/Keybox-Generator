import subprocess

def run_command(command):
    """Run a shell command and print its output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout.decode('utf-8'))

# Variables
ROOT_CA_KEY = "RSA_rootCA.key" # Given
ROOT_CA_CERT = "RSA_rootCA.pem"

# Intermediate CA A
INTERMEDIATE_CA_KEY_A = "RSA_intermediateCA_A.key"
INTERMEDIATE_CA_CSR_A = "RSA_intermediateCA_A.csr"
INTERMEDIATE_CA_CERT_A = "RSA_intermediateCA_A.pem"

# Intermediate CA B
INTERMEDIATE_CA_KEY_B = "RSA_intermediateCA_B.key"
INTERMEDIATE_CA_CSR_B = "RSA_intermediateCA_B.csr"
INTERMEDIATE_CA_CERT_B = "RSA_intermediateCA_B.pem"

# Server Certificate
SERVER_KEY = "RSA_server.key"
SERVER_CSR = "RSA_server.csr"
SERVER_CERT = "RSA_server.crt"

CERT_CHAIN = "RSA_certificate_chain.crt"

DETAILS = "/C=US/ST=Texas/L=Austin/O=Fuck Google INC/OU=INT/CN=FG"

DAYS = "1024"

# Generate Root CA
run_command(f"openssl req -x509 -new -nodes -key {ROOT_CA_KEY} -sha256 -days {DAYS} -out {ROOT_CA_CERT} -subj \"{DETAILS}\"")

# Generate Intermediate CA A
run_command(f"openssl genrsa -out {INTERMEDIATE_CA_KEY_A} 4096")
run_command(f"openssl req -new -key {INTERMEDIATE_CA_KEY_A} -out {INTERMEDIATE_CA_CSR_A} -subj \"{DETAILS}\"")
run_command(f"openssl x509 -req -in {INTERMEDIATE_CA_CSR_A} -CA {ROOT_CA_CERT} -CAkey {ROOT_CA_KEY} -CAcreateserial -out {INTERMEDIATE_CA_CERT_A} -days {DAYS} -sha256")

# Generate Intermediate CA B

run_command(f"openssl genrsa -out {INTERMEDIATE_CA_KEY_B} 4096")
run_command(f"openssl req -new -key {INTERMEDIATE_CA_KEY_B} -out {INTERMEDIATE_CA_CSR_B} -subj \"{DETAILS}\"")
run_command(f"openssl x509 -req -in {INTERMEDIATE_CA_CSR_B} -CA {INTERMEDIATE_CA_CERT_A} -CAkey {INTERMEDIATE_CA_KEY_A} -CAcreateserial -out {INTERMEDIATE_CA_CERT_B} -days {DAYS} -sha256")

# Generate Server Certificate
run_command(f"openssl genrsa -out {SERVER_KEY} 4096")
run_command(f"openssl req -new -key {SERVER_KEY} -out {SERVER_CSR} -subj \"{DETAILS}\"")
run_command(f"openssl x509 -req -in {SERVER_CSR} -CA {INTERMEDIATE_CA_CERT_B} -CAkey {INTERMEDIATE_CA_KEY_B} -CAcreateserial -out {SERVER_CERT} -days {DAYS} -sha256")

# Combine certificates to create the certificate chain
with open(CERT_CHAIN, "wb") as chain_file:
    for cert_file in [SERVER_CERT, INTERMEDIATE_CA_CERT_B, INTERMEDIATE_CA_CERT_A, ROOT_CA_CERT]:
        with open(cert_file, "rb") as f:
            chain_file.write(f.read())

print(f"Certificate chain created and saved to {CERT_CHAIN}")
