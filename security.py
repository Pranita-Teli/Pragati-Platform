import hashlib

def hash_ekyc_token(raw_token: str) -> str:
    """
    Simulate secure cryptographic hashing of e-KYC token for verification.
    In production, this could interface with UIDAI Aadhaar/e-Sign APIs.
    """
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

def verify_ekyc_token(raw_token: str, stored_hash: str) -> bool:
    """
    Verifies a raw e-KYC token against a stored SHA-256 hash.
    """
    return hash_ekyc_token(raw_token) == stored_hash
