import random
from decimal import Decimal as de

def random_long():
    #创建一个1-9.99的随机浮点数
    long = random.randint(100,999)/100
    return de(str(long))
    