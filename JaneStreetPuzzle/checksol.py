import numpy as np

with open("puzzleAltered.sol") as f:
    lines = f.readlines()

magic = [int(x.split()[1]) for x in lines[-4:]]
lines = [x.split(' ')[0] for x in lines if (not x.startswith("obj")) and (not x.startswith("\n")) and (not x.startswith("magic"))]
lines = [int(x.split("_")[-1]) for x in lines]

for i in range(4):
    sq = np.array(lines[9*i:9*(i+1)])
    sq = np.reshape(sq, (3,3))
    for j in range(3):
        # Check sum of row
        assert sum(sq[j]) <= magic[i]
        assert magic[i] - 1 <= sum(sq[j])
        print(f"Summe von Zeile {j} von Quadrat {i} ist korrekt.")

        # Check sum of column
        assert sum(sq[:,j]) <= magic[i]
        assert magic[i] - 1 <= sum(sq[:,j])
        print(f"Summe von Spalte {j} von Quadrat {i} ist korrekt.")

    assert sum(np.diag(np.fliplr(sq))) <= magic[i]
    assert magic[i] - 1 <= sum(np.diag(np.fliplr(sq)))
    print(f"Spur von Quadrat {i} ist korrekt")

    assert sum(np.diag(np.fliplr(sq))) <= magic[i]
    assert magic[i] - 1 <= sum(np.diag(np.fliplr(sq)))
    print(f"Zweite Diagonale von Quadrat {i} ist korrekt.")
