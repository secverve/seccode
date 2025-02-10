#include <iostream>

void memory_leak() {
    int *ptr = new int[100];  // ❌ 메모리 할당 후 해제 없음
}

int main() {
    memory_leak();
    std::cout << "Memory leak example" << std::endl;
    return 0;
}
