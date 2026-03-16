import os
import base64
import hashlib
import argparse
import json
import jsonlines

def derive_key(password: str, length: int) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(password.encode())
    key = hasher.digest()
    return key * (length // len(key)) + key[: length % len(key)]

def decrypt(ciphertext_b64: str, password: str) -> str:
    encrypted = base64.b64decode(ciphertext_b64)
    key = derive_key(password, len(encrypted))
    decrypted = bytes(a ^ b for a, b in zip(encrypted, key))
    return decrypted.decode()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decrypt a JSONL file.')
    parser.add_argument('input_path', help='The input path of jsonl file to decrypt.')
    parser.add_argument('output_path', help='The output path of jsonl file to write decrypted data to.')
    
    args = parser.parse_args()

    decrypt_data = []

    encrypt_data = []
    with jsonlines.open(args.input_path) as reader:
        for item in reader:
            encrypt_data.append(item)

    for item in encrypt_data:
        password = item['canary']
        question = item['question']
        answer = item['answer']

        item['question'] = decrypt(question, password)
        for i, ans in enumerate(answer):
            item['answer'][i] = decrypt(ans, password)

        decrypt_data.append(item)

    with open(args.output_path, 'w', encoding='utf-8') as f:   
        for sample in decrypt_data:
            json_line = json.dumps(sample, ensure_ascii=False)
            f.write(json_line + '\n')
