#include <iostream>\nvoid memory_leak() { int *ptr = new int[100]; }\nint main() { memory_leak(); return 0; }
