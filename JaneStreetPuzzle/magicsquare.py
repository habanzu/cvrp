from pyscipopt import Model
import numpy as np

model = Model("JaneStreet")  # model name is optional

max_val = 25
square = np.empty((3,3,max_val),dtype=object)

for i in range(3):
    for j in range(3):
        for l in range(max_val):
            square[i,j,l] = model.addVar(f"{i}_{j}_{l+1}", vtype="BINARY",obj=l+1)

for i in range(3):
    for j in range(3):
        # Wieso kommt hier kein echtes XOR raus?
        model.addConsXor(square[i,j],True)
        model.addConsCardinality(square[i,j],1)

for l in range(max_val):
    model.addConsCardinality(square[:,:,l].flatten(), 1)

magic_num = model.addVar(vtype="I")
for i in range(3):
    row = 0
    col = 0
    for l in range(max_val):
        row += (l+1)*sum(square[i,:,l])
        col += (l+1)*sum(square[:,i,l])
    model.addCons(row == magic_num)
    model.addCons(col == magic_num)

diag1 = 0
diag2 = 0
for l in range(max_val):
    diag1 += (l+1)*(square[0,0,l] + square[1,1,l] + square[2,2,l])
    diag2 += (l+1)*(square[2,0,l] + square[1,1,l] + square[0,2,l])

model.addCons(diag1 == magic_num)
model.addCons(diag2 == magic_num)


# model.setObjective(x + y)
model.optimize()
sol = model.getBestSol()
print("Optimal value:", model.getObjVal())
for i in range(3):
    for j in range(3):
        for l in range(max_val):
            if model.getVal(square[i,j,l]) > 0.1:
                print(square[i,j,l])
