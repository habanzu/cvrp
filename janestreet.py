from pyscipopt import Model
import numpy as np

model = Model("JaneStreet")  # model name is optional
max_val = 137 #The solution on the website has value 137
filename = "test"

def create_magic_square_vars(model, max_val, square_number):
    square = np.empty((3,3,max_val),dtype=object)

    for i in range(3):
        for j in range(3):
            for l in range(max_val):
                square[i,j,l] = model.addVar(f"sq{square_number}_{i}_{j}_{l+1}", vtype="BINARY",obj=l+1)
    return square

def add_almost_magic_square_const(model, max_val, square, square_number):
    for i in range(3):
        for j in range(3):
            # Wieso kommt hier kein echtes XOR raus?
            model.addConsXor(square[i,j],True)
            model.addConsCardinality(square[i,j],1)

    magic_num = model.addVar(vtype="I", name=f"magic{square_number}")
    for i in range(3):
        row = 0
        col = 0
        for l in range(max_val):
            row += (l+1)*sum(square[i,:,l])
            col += (l+1)*sum(square[:,i,l])
        model.addCons(row <= magic_num)
        model.addCons(row >= magic_num - 1)
        model.addCons(col <= magic_num)
        model.addCons(col >= magic_num - 1)


    diag1 = 0
    diag2 = 0
    for l in range(max_val):
        diag1 += (l+1)*(square[0,0,l] + square[1,1,l] + square[2,2,l])
        diag2 += (l+1)*(square[2,0,l] + square[1,1,l] + square[0,2,l])

    model.addCons(diag1 <= magic_num)
    model.addCons(diag1 >= magic_num - 1)
    model.addCons(diag2 <= magic_num)
    model.addCons(diag2 >= magic_num - 1)

# Upper square
square1 = create_magic_square_vars(model, max_val, 1)
# left square
square2 = create_magic_square_vars(model, max_val, 2)
# right square
square3 = create_magic_square_vars(model, max_val, 3)
# bottom square
square4 = create_magic_square_vars(model, max_val, 4)

# Add uniqueness constraints
for l in range(max_val):
    vars = np.vstack((square1[:,:,l],square2[:,:,l],square3[:,:,l],square4[:,:,l]))
    model.addConsCardinality(vars.flatten(), 1)

# Set current limit, as the website states that there exists a solution with value 1111
# model.setObjlimit(1111)

# Link the squares
for l in range(max_val):
    square1[1,2,l] = square3[0,0,l]
    square1[2,0,l] = square2[0,1,l]
    square1[2,1,l] = square2[0,2,l]
    square1[2,2,l] = square3[1,0,l]
    square2[1,2,l] = square4[0,0,l]
    square3[2,0,l] = square4[0,1,l]
    square3[2,1,l] = square4[0,2,l]
    square2[2,2,l] = square4[1,0,l]

add_almost_magic_square_const(model, max_val, square1, 1)
add_almost_magic_square_const(model, max_val, square2, 2)
add_almost_magic_square_const(model, max_val, square3, 3)
add_almost_magic_square_const(model, max_val, square4, 4)

model.presolve()
# Model muss in gewisser Stage sein, damit trySol funktioniert
sol = model.readSolFile("KnownSol.sol")
print(model.getStage())
input()

model.trySol(sol, completely=True)

maxthr = model.getParam("parallel/maxnthreads")
model.setParam("parallel/minnthreads", 3)
minthr = model.getParam("parallel/minnthreads")
print(f"Minimum/Maxium number of threads:{minthr}/{maxthr}")
model.solveConcurrent()
# model.optimize()
sol = model.getBestSol()
print("Optimal value:", model.getObjVal())
model.writeBestSol(filename=f"{filename}.sol")


print("Square 1")
for i in range(3):
    for j in range(3):
        for l in range(max_val):
            if model.getVal(square1[i,j,l]) > 0.1:
                print(square1[i,j,l])

print("Square 2")
for i in range(3):
    for j in range(3):
        for l in range(max_val):
            if model.getVal(square2[i,j,l]) > 0.1:
                print(square2[i,j,l])

print("Square 3")
for i in range(3):
    for j in range(3):
        for l in range(max_val):
            if model.getVal(square3[i,j,l]) > 0.1:
                print(square3[i,j,l])

print("Square 4")
for i in range(3):
    for j in range(3):
        for l in range(max_val):
            if model.getVal(square3[i,j,l]) > 0.1:
                print(square3[i,j,l])
