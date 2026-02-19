from passlib.context import CryptContext
import os

print("Testing password hashing...")

try:
    pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
    print("CryptContext created successfully.")
    
    hash = pwd_context.hash("testpassword")
    print(f"Hash generated: {hash}")
    
    verify = pwd_context.verify("testpassword", hash)
    print(f"Verification result: {verify}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
