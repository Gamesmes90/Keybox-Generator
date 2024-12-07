import xml.etree.ElementTree as ET
import argparse

def extract_keys_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    ecdsa_key = None
    rsa_key = None
    
    
    for key in root.findall('./Keybox/Key'):
        key_type = key.get('algorithm')

        if key_type == 'ecdsa':
            for priv_key in key.findall('PrivateKey'):
                    ecdsa_key = priv_key.text
        elif key_type == 'rsa':
            for priv_key in key.findall('PrivateKey'):
                    rsa_key = priv_key.text

    return ecdsa_key, rsa_key

def save_key_to_file(key, filename):
    with open(filename, 'w') as file:
        file.write(key)

def main():

    parser = argparse.ArgumentParser(description="Script to extract private keys from a keybox.")
    parser.add_argument('-f', '--file', type=str, required=False, help="XML file containing the keys. Default: keybox.xml")

    args = parser.parse_args()

    xml_file = 'keybox.xml'

    if args.file:
        xml_file = args.file

    ecdsa_key, rsa_key = extract_keys_from_xml(xml_file)

    if ecdsa_key:
        save_key_to_file(ecdsa_key, 'ECDSA_rootCA.key')
    else:
        print("ECDSA key not found in the XML file.")

    if rsa_key:
        save_key_to_file(rsa_key, 'RSA_rootCA.key')
    else:
        print("RSA key not found in the XML file.")

if __name__ == "__main__":
    main()