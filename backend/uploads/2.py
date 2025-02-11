import random

# ❌ 보안 취약점: 취약한 난수 발생기 사용 (B311)
random_value = random.randint(1, 100)
print(f"Generated value: {random_value}")