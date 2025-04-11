from pathlib import Path

FENCE_COOLDOWN = 180
"""发起者冷却"""
FENCED_PROTECTION = 300
""" 被击剑者冷却保护 """
UNSUBSCRIBE_GOLD = 500
""" 注销牛牛所需金币 """
QUICK_GLUE_COOLDOWN = 240
""" 连续打胶冷却判定， 要比打胶冷却大，不然会出问题 """
GLUE_COOLDOWN = 180
""" 打胶冷却时间 """
ICON_PATH = Path(__file__).parent
"""商店目录"""
