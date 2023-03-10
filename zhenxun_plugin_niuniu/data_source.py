import random
from decimal import Decimal as de

def random_long():
    return de(str(f"{random.randint(1,9)}.{random.randint(00,99)}"))
    