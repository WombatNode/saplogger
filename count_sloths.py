import json
from collections import Counter

sloths_by_pack = Counter()

with open("saplogger/stats.json") as fp:
    stats = json.load(fp)
    pets = stats["Pet"]
    for mode, packs in pets.items():
        for pack, data in packs.items():
            for petno, turn, count in data:
                if petno == 71:
                    print(mode, pack, turn, count)
                    sloths_by_pack[pack] += count

                    # exit()
    # print(list(["Arena"].keys()))
print(sloths_by_pack)