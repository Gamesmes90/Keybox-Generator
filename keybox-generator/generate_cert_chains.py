import glob
import shutil
import subprocess
import argparse
import random
import string
import hashlib
import os
import sys

# Default subject details for the certificates. Customize as needed.
DETAILS = "/C=US/ST=Texas/L=Austin/O=Fuck Google Inc./OU=INT/CN=Fuck Google"

# Add subject details for each certificate in the chain. The end certificate subject is added automatically
# Example: ["/serialNumber=f92009e853b6b045","/title=TEE/serialNumber=5df398e7946db5ded47290cbb43c5028","/title=TEE/serialNumber=54d54a126a783bc9cba8c06137136943"]
SUBJECTS = []
SUBJECTS_POINTER = 0
# Default end subject for the end certificate. Customize as needed
END_SUBJECT = "/title=TEE/serialNumber=serial/O=org/street=str/UID=123"

DAYS = "1024"

ROOT_CA_KEY = "rootCA.key"
ROOT_CA_CERT = "rootCA.pem"

OEM=False

def run_command(command):
    """Run a shell command and print its output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
    else:
        print(stdout.decode('utf-8'))

def setup_subject():
    global SUBJECTS
    if SUBJECTS != []:
        SUBJECTS.append(END_SUBJECT)
        return
    for i in range(4):
        if i == 0:
            subject = f"/serialNumber={gen_hash(rand_str(15), True)}"
        elif i == 3:
            SUBJECTS.append(END_SUBJECT)
            break
        else:
            subject = f"/title=TEE/serialNumber={gen_hash(rand_str(15))}"
        SUBJECTS.append(subject)

def remove_file(file):
    if file == "":
        return
    try:
        os.remove(file)
    except:
        pass

def remove_files(files):
    for file in files:
        remove_file(file)

def delete_pattern(pattern):
    for file in glob.glob(pattern):
        remove_file(file)

def clean_workspace():
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    key_pattern = os.path.join(os.getcwd(), "*.key")
    crt_pattern = os.path.join(os.getcwd(), "*.crt")
    delete_pattern(key_pattern)
    delete_pattern(crt_pattern)
    os.chdir("certs")
    key_pattern = os.path.join(os.getcwd(), "*.key")
    csr_pattern = os.path.join(os.getcwd(), "*.csr")
    pem_pattern = os.path.join(os.getcwd(), "*.pem")
    crt_pattern = os.path.join(os.getcwd(), "*.crt")
    srl_pattern = os.path.join(os.getcwd(), "*.srl")
    delete_pattern(key_pattern)
    delete_pattern(csr_pattern)
    delete_pattern(pem_pattern)
    delete_pattern(crt_pattern)
    delete_pattern(srl_pattern)
    print("Workspace cleaned.")

def nextSubject():
    global DETAILS
    global SUBJECTS_POINTER
    if SUBJECTS != []:
        DETAILS = SUBJECTS[SUBJECTS_POINTER]
        SUBJECTS_POINTER += 1

def resetSubject():
    global SUBJECTS_POINTER
    if SUBJECTS != []:
        SUBJECTS_POINTER = 1

def gen_hash(input, short=False):
    md5 = hashlib.md5()

    md5.update(input.encode('utf-8'))

    full_hash = md5.digest()

    if(short): full_hash = full_hash[:8]

    return full_hash.hex()

def rand_str(len):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(len))

def file_exists(file):
    if os.path.exists(file):
        print(f"{file} already exists. Skipping generation.")
        nextSubject()
        return True
    return False

def generate_key(gen_key_cmd, key_file):
    if not os.path.exists(key_file):
        print(f"{key_file} not found. Generating a private key.")
        run_command(f"{gen_key_cmd} {key_file} {'4096' if 'rsa' in gen_key_cmd else ''}")
    nextSubject()

def generate_csr(key_file, csr_file):
    run_command(f"openssl req -new -key {key_file} -out {csr_file} -subj \"{DETAILS}\"")

def generate_cert(csr_file, ca_cert_file, ca_key_file, cert_file):
    run_command(f"openssl x509 -req -in {csr_file} -CA {ca_cert_file} -CAkey {ca_key_file} -CAcreateserial -out {cert_file} -days {DAYS} -sha256")

def generate_root_ca(force=False):
    # Generate Root CA
    if not os.path.exists(ROOT_CA_KEY):
        print("Root CA key not found. Generating a new one.")
        generate_key("openssl genrsa -out", ROOT_CA_KEY)
    else:
        print("Root CA key found.")
        nextSubject()
    if not os.path.exists(ROOT_CA_CERT) or force:
        print("Generating a new root certificate.")
        run_command(f"openssl req -x509 -new -key {ROOT_CA_KEY} -sha256 -days {DAYS} -out {ROOT_CA_CERT} -subj \"{DETAILS}\"")
    else:
        print("Root certificate found.")

def ecdsa_root(pair, force_cert):
    global ROOT_CA_KEY
    global ROOT_CA_CERT
    if pair:
        ROOT_CA_KEY = "rootCA_ecdsa.key"
        ROOT_CA_CERT = "rootCA_ecdsa.pem"
        generate_root_ca(force_cert)

def can_generate(file, force):
    if os.path.exists(file) and not force:
        print(f"{file} already exists. Skipping generation.")
        return False
    return True

def generate_cert_chain(cert_type, clean=False, keys=False, force=False):
    if cert_type == "ECDSA":
        gen_key_cmd = "openssl ecparam -genkey -name secp256r1 -out"
    elif cert_type == "RSA":
        gen_key_cmd = "openssl genrsa -out"
    else:
        print("Invalid type. Please choose either 'ecdsa' or 'rsa'.")
        return

    print(f"Generating {cert_type} certificate chain.")

    # Define file names
    oem_ca_key = f"{cert_type}_oem_CA.key"
    oem_ca_csr = f"{cert_type}_oem_CA.csr"
    oem_ca_cert = f"{cert_type}_oem_CA.pem"
    model_ca_key = f"{cert_type}_model_CA.key"
    model_ca_csr = f"{cert_type}_model_CA.csr"
    model_ca_cert = f"{cert_type}_model_CA.pem"
    end_key = f"{cert_type}_end.key"
    end_csr = f"{cert_type}_end.csr"
    end_cert = f"{cert_type}_end.crt"
    cert_chain = f"{cert_type}_certificate_chain.crt"

    if can_generate(oem_ca_cert, force):
        # Generate OEM CA A
        generate_key(gen_key_cmd, oem_ca_key)
        generate_csr(oem_ca_key, oem_ca_csr)
        generate_cert(oem_ca_csr, ROOT_CA_CERT, ROOT_CA_KEY, oem_ca_cert)


    if can_generate(model_ca_cert, force):
        # Generate Model CA B
        generate_key(gen_key_cmd, model_ca_key)
        generate_csr(model_ca_key, model_ca_csr)
        generate_cert(model_ca_csr, oem_ca_cert, oem_ca_key, model_ca_cert)


    if not OEM:
        if can_generate(end_cert, force):
            # Generate End Certificate
            generate_key(gen_key_cmd, end_key)
            generate_csr(end_key, end_csr)
            generate_cert(end_csr, model_ca_cert, model_ca_key, end_cert)

    cert_list = []
    if not OEM:
        cert_list.append(end_cert)
    cert_list.append(model_ca_cert)
    cert_list.append(oem_ca_cert)
    cert_list.append(ROOT_CA_CERT)

    # Combine certificates to create the certificate chain
    with open(cert_chain, "wb") as chain_file:
        for cert_file in cert_list:
            with open(cert_file, "rb") as f:
                chain_file.write(f.read())

    # Move the certificate chain to the parent directory
    shutil.move(cert_chain, f"../{cert_chain}")

    print(f"{cert_type} Certificate chain created and saved to {cert_chain}")

    if clean:
        remove_files([oem_ca_csr, oem_ca_cert, model_ca_csr, model_ca_cert, end_csr if not OEM else '', end_cert if not OEM else ''])

    if keys:
        remove_files([oem_ca_key, model_ca_key if not OEM else ''])

    # Move the end key to the parent directory
    if not OEM:
        shutil.copy(end_key, f"../{end_key}")
    else:
        shutil.copy(model_ca_key, f"../{model_ca_key}")

    # Reset the subject pointer
    resetSubject()

def main():
    global OEM
    parser = argparse.ArgumentParser(description="Script to generate certificate chains.")
    parser.add_argument('-d', '--days', type=str, required=False, help="Validity time frame in days. Default: 1024")
    parser.add_argument('-r', '--rsa', action='store_true', help="Generate RSA only")
    parser.add_argument('-e', '--ecdsa', action='store_true', help="Generate ECDSA only")
    parser.add_argument('-c', '--clean', action='store_true', help="Remove non-essential files made during the generation process")
    parser.add_argument('-k', '--keys', action='store_true', help="Remove non-essential private keys made during the generation process")
    parser.add_argument('-s', '--subject', action='store_true', help="Use auto generated subject details with config file")
    parser.add_argument('-f', '--force', action='store_true', help="Force the generation of a new certificate chain (overwrites existing certificates)")
    parser.add_argument('-o', '--oem', action='store_true', help="Skip the generation of the end certificate to make an OEM-like certificate chain")
    parser.add_argument('-p', '--pair', action='store_true', help="Use two different root certificates for rsa and ecdsa")
    parser.add_argument('-w', '--workspace', action='store_true', help="Cleans the workspace of all generated files")

    args = parser.parse_args()

    if args.workspace:
        clean_workspace()
        return

    if args.oem:
        OEM = True

    if args.days and args.days.isdigit():
        global DAYS
        DAYS = args.days

    if args.subject:
        setup_subject()

    # Change to the certs directory
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])) + "/certs")

    generate_root_ca(args.force)

    if args.rsa:
        generate_cert_chain("RSA", args.clean, args.keys, args.force)
    if args.ecdsa:
        ecdsa_root(args.pair, args.force)
        generate_cert_chain("ECDSA", args.clean, args.keys, args.force)
    if not args.rsa and not args.ecdsa:
        generate_cert_chain("RSA", args.clean, args.keys, args.force)
        ecdsa_root(args.pair, args.force)
        generate_cert_chain("ECDSA", args.clean, args.keys, args.force)

    if args.clean:
        remove_file(ROOT_CA_CERT)

    if args.keys:
        remove_file(ROOT_CA_KEY)

if __name__ == "__main__":
    main()