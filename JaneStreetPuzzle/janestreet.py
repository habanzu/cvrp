from pyscipopt import Model
import numpy as np

model = Model("JaneStreet")  # model name is optional
max_val = 102 #There is a known solution with value 480. Therefore with Gaußscher Summenformel it follows, that variables must be less thant 102
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
            model.addConsXor(square[i,j].flatten(), True)

    # Add constraints for each row
    magic_num = model.addVar(vtype="I", name=f"magic{square_number}")
    model.addCons(magic_num >= 0)
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

    # Add constraints for total square
    total_sum = 0
    for l in range(max_val):
        total_sum += (l+1)*square[:,:,l].sum()
    model.addCons(total_sum <= 3*magic_num)
    model.addCons(total_sum >= 3*magic_num - 3)


    diag1 = 0
    diag2 = 0
    for l in range(max_val):
        diag1 += (l+1)*(square[0,0,l] + square[1,1,l] + square[2,2,l])
        diag2 += (l+1)*(square[2,0,l] + square[1,1,l] + square[0,2,l])

    model.addCons(diag1 <= magic_num)
    model.addCons(diag1 >= magic_num - 1)
    model.addCons(diag2 <= magic_num)
    model.addCons(diag2 >= magic_num - 1)

    return magic_num

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
    model.addConsSOS1(vars.flatten())

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

magic1 = add_almost_magic_square_const(model, max_val, square1, 1)
magic2 = add_almost_magic_square_const(model, max_val, square2, 2)
magic3 = add_almost_magic_square_const(model, max_val, square3, 3)
magic4 = add_almost_magic_square_const(model, max_val, square4, 4)

# Add cuts due to known solution
left_over1, left_over2, left_over3, left_over4 = 0, 0, 0, 0
for l in range(max_val):
    left_over1 += (l+1)*(square1[2,1,l] + square2[1,2,l] + square3[1,0,l] + square4[0,1,l])
    left_over2 += (l+1)*(square2[1,1,l] + square2[2,1,l] + square3[0,1,l] + square3[1,1,l])
    left_over3 += (l+1)*(square1[1,:2,l].sum() + square4[1,1:,l].sum())
    left_over4 += (l+1)*(square1[0,2,l] + square2[0,0,l] + square3[2,2,l] + square4[2,0,l])
# rhs needs to be 8 higher, because magic can be 1 larger than the sum of the rows
model.addCons(2*magic1 + 2*magic2 + 2*magic3 + 2*magic4 + left_over1 <= 488)
model.addCons(2*magic1 + 2*magic2 + 2*magic3 + 2*magic4 + left_over4 <= 488)
model.addCons(3*magic1 + magic2 + magic3 + 3*magic4 + left_over2 <= 488)
model.addCons(magic1 + 3*magic2 + 3*magic3 + magic4 + left_over3 <= 488)

#Add symmetry breaking constraint for magic numbers
model.addCons(magic4 <= magic1)
model.addCons(magic4 <= magic2)
model.addCons(magic4 <= magic3)
model.addCons(magic2 <= magic3)

model.presolve()
# Model muss in gewisser Stage sein, damit trySol funktioniert
sol = model.readSolFile("puzzle.sol")

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
