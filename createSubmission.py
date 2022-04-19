import numpy as np

with open("puzzleAltered.sol") as f:
    lines = f.readlines()

lines = [x.split()[0] for x in lines if (not x.startswith("obj")) and (not x.startswith("\n")) and (not x.startswith("magic"))]
lines = [int(x.split("_")[-1]) for x in lines]


sq = np.empty((4,3,3),dtype=int)
for i in range(4):
    sq[i] = np.array(lines[9*i:9*(i+1)]).reshape((3,3))

sq1 = sq[0].flatten()[:5]
result = sq1
for i in range(3):
    result = np.hstack((result,sq[2][i],sq[1][i]))
result = np.hstack((result, sq[3].flatten()[4:]))

# Überprüfe, dass es keine Duplikate gibt
assert len(result) == len(set(result))

print(list(result))
print(f"Summe aller Einträge ist {sum(result)}")
