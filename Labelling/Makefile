labelling_lib: labelling_lib.cpp labelling_lib.h
	clang++ -c -Wpedantic -Wall -Wextra -O3 -std=c++17 -o labelling_lib.o labelling_lib.cpp -fPIC
	clang++ -shared -o labelling_lib.so labelling_lib.o

linux: labelling_lib.cpp labelling_lib.h
	g++ -c -Wpedantic -Wall -Wextra -O3 -std=c++17 -o labelling_lib.o labelling_lib.cpp -fPIC
	g++ -shared -o labelling_lib.so labelling_lib.o
