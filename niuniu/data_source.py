import random

path = os.path.dirname(__file__)

def readInfo(file, info=None):
    with open(os.path.join(path, file), "r", encoding="utf-8") as f:
        context = f.read()
        if info != None:
            with open(os.path.join(path, file), "w", encoding="utf-8") as f:
                f.write(ujson.dumps(info, indent=4, ensure_ascii=False))
            with open(os.path.join(path, file), "r", encoding="utf-8") as f:
                data = f.read()
            return {"data": ujson.loads(context.strip())}
        else:
            return ujson.loads(context.strip())

def random_long():
    long = random.randint(1,9)
    long_ = random.choice([
        .00,.10,.20,.30,.40,.50,.60,.70,.80,.90,
        .10,.11,.12,.13,.14,.15,.16,.17,.18,.19,
        .20,.21,.22,.23,.24,.25,.26,.27,.28,.29,
        .30,.31,.32,.33,.34,.35,.36,.37,.38,.39,
        .40,.41,.42,.43,.44,.45,.46,.47,.48,.49,
        .50,.51,.52,.53,.54,.55,.56,.57,.58,.59,
        .60,.61,.62,.63,.64,.65,.66,.67,.68,.69,
        .70,.71,.72,.73,.74,.75,.76,.77,.78,.79,
        .80,.81,.82,.83,.84,.85,.86,.87,.88,.89,
        .90,.91,.92,.93,.94,.95,.96,.97,.98,.99
    ])
    return float(f"{long}{long_}")

def get_all_users(group):
    group = readInfo("data/long.json")[group]
    return group
    