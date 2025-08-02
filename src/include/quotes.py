import random

__all__ = ["get_quote"]

ALL_QUOTES = [
    "星垂平野阔，月涌大江流。",
    "自是人间英物，不须更试啼声。", # - 段成己《清平乐 子 祝福 薛子余弄璋》
    "醉里挑灯看剑，梦回吹角连营。", # - 辛弃疾
    "身无彩凤双飞翼，心有灵犀一点通。", # - 李商隐
    "相寻梦里路，飞雨落花中。", # - 晏几道《临江仙》
]

def get_quote():
    return random.choice(ALL_QUOTES)