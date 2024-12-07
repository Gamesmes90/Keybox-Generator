import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import os
import sys
from generate_cert_chains import delete_pattern

def main():
    # Make sure the script is running in the working directory
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    ECDSA_end_key = ""
    RSA_end_key = ""

    ECDSA_certificate_chain = ""
    RSA_certificate_chain = ""

    device_id = "device"

    parser = argparse.ArgumentParser(description="Script to generate a keybox.")
    parser.add_argument('-a', '--auto', action='store_true', help="Automatically look for the required files in the current directory")
    parser.add_argument('-d', '--device', type=str, required=False, help="The device ID to use in the keybox")
    parser.add_argument('-e', '--keyECDSA', type=str, required=False, help="ecdsa key")
    parser.add_argument('-r', '--keyRSA', type=str, required=False, help="rsa key")
    parser.add_argument('-ec', '--chainECDSA', type=str, required=False, help="ecdsa certificate chain")
    parser.add_argument('-rc', '--chainRSA', type=str, required=False, help="rsa certificate chain")
    parser.add_argument('-t', '--tab', action='store_true', help="Pretty print with tabs")
    parser.add_argument('-n', '--name', type=str, required=False, help="Name of the keybox (default: keybox)")
    parser.add_argument('-c', '--clean', action='store_true', help="Remove any generated keybox")

    args = parser.parse_args()

    if args.clean:
        keybox_pattern = os.path.join(os.getcwd(), "*.xml")
        delete_pattern(keybox_pattern)
        return

    if args.auto:
        ecdsa_filename = "ECDSA_end.key" if os.path.exists("ECDSA_end.key") else "ECDSA_model_CA.key"
        rsa_filename = "RSA_end.key" if os.path.exists("RSA_end.key") else "RSA_model_CA.key"
        ECDSA_end_key = read_ECDSA_key(ecdsa_filename)
        with open(rsa_filename, "r") as f:
            RSA_end_key = f.read()
        ECDSA_certificate_chain = split_certificates("ECDSA_certificate_chain.crt")
        RSA_certificate_chain = split_certificates("RSA_certificate_chain.crt")

    if args.device:
        device_id = args.device

    if args.keyECDSA:
        ECDSA_end_key = read_ECDSA_key(args.keyECDSA)

    if args.keyRSA:
        with open(args.keyRSA, "r") as f:
            RSA_end_key = f.read()

    if args.chainECDSA:
        ECDSA_certificate_chain = split_certificates(args.chainECDSA)

    if args.chainRSA:
        RSA_certificate_chain = split_certificates(args.chainRSA)

    if args.keyECDSA and args.chainECDSA and args.keyRSA and args.chainRSA or args.auto:
        generate_keybox(args.tab, device_id, ECDSA_end_key, RSA_end_key, ECDSA_certificate_chain, RSA_certificate_chain, len(ECDSA_certificate_chain), len(RSA_certificate_chain), args.name)
    else:
        generate_keybox(args.tab, device_id, name=args.name)


def read_ECDSA_key(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split the content by the end key delimiter
    contents = content.split("-----END EC PARAMETERS-----")
    return contents[1]


def split_certificates(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split the content by the end certificate delimiter
    certificates = content.split("-----END CERTIFICATE-----")
    
    # Add the delimiter back to each certificate and remove any empty strings
    certificates = [cert.strip() + "\n-----END CERTIFICATE-----" for cert in certificates if cert.strip()]
    
    return certificates

"""
Generates an XML keybox file with ECDSA and RSA keys and their respective certificate chains.
Args:
    tab (bool): If True, the XML will be pretty-printed with indentation.
    ecdsa_end_key (str, optional): The ECDSA private key in PEM format at the end of the chain. Defaults to an empty string.
    rsa_end_key (str, optional): The RSA private key in PEM format at the end of the chain. Defaults to an empty string.
    ecdsa_certs_chain (str, optional): The ECDSA certificate chain in PEM format. Defaults to an empty string.
    rsa_certs_chain (str, optional): The RSA certificate chain in PEM format. Defaults to an empty string.
    ecdsa_num (str, optional): The number of ECDSA certificates. Defaults to "1".
    rsa_num (str, optional): The number of RSA certificates. Defaults to "1".
    name (str, optional): The name of the keybox file. Defaults to "keybox".
Returns:
    None
Creates:
    A file named "keybox.xml" containing the generated keybox in XML format.
    Generates an empty keybox template if no arguments are provided.
Raises:
    None
Example:
    generate_keybox(
        tab=True,
        ecdsa_end_key="ecdsa_private_key",
        rsa_end_key="rsa_private_key",
        ecdsa_certs_chain="ecdsa_cert_chain",
        rsa_certs_chain="rsa_cert_chain",
        ecdsa_num="2",
        rsa_num="3"
    )
"""
def generate_keybox(tab, device_id="device", ecdsa_end_key="", rsa_end_key="", ecdsa_certs_chain=[""], rsa_certs_chain=[""], ecdsa_num=1, rsa_num=1, name="keybox"):

    if name == None:
        name = "keybox"

    # Keybox Root
    root = ET.Element("AndroidAttestation")

    # Keyboxes number
    keyboxes = ET.SubElement(root, "NumberOfKeyboxes")
    keyboxes.text = "1"

    # Keybox
    keybox = ET.SubElement(root, "Keybox")
    keybox.set("DeviceID", device_id)

    # Key ECDSA
    ecdsa = ET.SubElement(keybox, "Key")
    ecdsa.set("algorithm", "ecdsa")

    # Private Key
    ecdsa_key = ET.SubElement(ecdsa, "PrivateKey")
    ecdsa_key.set("format", "pem")
    ecdsa_key.text = ecdsa_end_key

    # Certificate Chain
    ecdsa_chain = ET.SubElement(ecdsa, "CertificateChain")
    
    # Number of certificates
    ecdsa_number_of_certificates = ET.SubElement(ecdsa_chain, "NumberOfCertificates")
    ecdsa_number_of_certificates.text = str(ecdsa_num)

    # Certificates
    for i in range(ecdsa_num):
        certificate = ET.SubElement(ecdsa_chain, "Certificate")
        certificate.set("format", "pem")
        certificate.text = ecdsa_certs_chain[i]

    # Key RSA
    rsa = ET.SubElement(keybox, "Key")
    rsa.set("algorithm", "rsa")

    # Private Key
    rsa_key = ET.SubElement(rsa, "PrivateKey")
    rsa_key.set("format", "pem")
    rsa_key.text = rsa_end_key

    # Certificate Chain
    rsa_chain = ET.SubElement(rsa, "CertificateChain")

    # Number of certificates
    rsa_number_of_certificates = ET.SubElement(rsa_chain, "NumberOfCertificates")
    rsa_number_of_certificates.text = str(rsa_num)

    # Certificates
    for i in range(rsa_num):
        certificate = ET.SubElement(rsa_chain, "Certificate")
        certificate.set("format", "pem")
        certificate.text = rsa_certs_chain[i]

    # Create a tree from the root element
    tree = ET.ElementTree(root)

    if tab:
        # Convert the tree to a string
        xml_str = ET.tostring(root, encoding="utf-8")

        # Parse the string using minidom for pretty printing
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent="    ")

        # Remove the XML declaration
        pretty_xml_str = '\n'.join(pretty_xml_str.split('\n')[1:])

        # Write the pretty-printed XML to a file
        with open(f"{name}.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml_str)
    else:
        # Write the tree to an XML file
        tree.write(f"{name}.xml", encoding="utf-8", xml_declaration=False)

    print("Keybox created successfully!")


if __name__ == "__main__":
    main()