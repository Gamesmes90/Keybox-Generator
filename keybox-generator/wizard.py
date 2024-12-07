import subprocess
import os
import sys
import glob

def get_python_executable():
    for executable in ["python3", "python"]: 
        try: 
            subprocess.check_output([executable, "--version"]) 
            return executable 
        except (subprocess.CalledProcessError, FileNotFoundError): 
            continue 
    raise RuntimeError("No suitable Python executable found.")

def remove_files(pattern):
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)
            print(f"Removed {file}")
        except OSError as e:
            print(f"Error: {e.strerror} - {file}")

def main():
    # Change to the working directory
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    print("Welcome to the keybox generator wizard!")
    print("This wizard will guide you through the process of generating a keybox.")
    print("For a more detailed generation, check out the scripts individually.")
    print("If you have your own private keys, put them in the certs folder.")
    print("Read the README.md for more information.")

    print("Specify the duration of the certificate validity.")
    print("The default value is 1024 days.")
    print("Would you like to change it? (y/n)")
    days = input()
    if days == "y":
        print("Enter the number of days:")
        days = input()

    print("Starting the generation process.")    
    print("Step 1: Generate the certificate chains.")

    python_executable = get_python_executable()

    if days == "n" or days == "":
        subprocess.run([python_executable, 'generate_cert_chains.py', '-s'])
    else:
        subprocess.run([python_executable, 'generate_cert_chains.py', '-s', '-d', days])
        
    print("Step 2: Generate the keybox.")
    subprocess.run([python_executable, 'generate_keybox.py', '-a', '-t'])
    print("Step 3: Done!")

    print("Would you like to clean the certs folder? (y/n)")
    clean = input()
    if clean == "y":
        remove_files('certs/*')
        print("Certs folder cleaned.")
    
    print("Would you like to clean the working folder from the certificate chain files? (y/n)")
    clean = input()
    if clean == "y":
        remove_files('ECDSA_certificate_chain.crt')
        remove_files('RSA_certificate_chain.crt')
        remove_files('ECDSA_end.key')
        remove_files('RSA_end.key')
        print("Working folder cleaned.")

if __name__ == "__main__":
    main()