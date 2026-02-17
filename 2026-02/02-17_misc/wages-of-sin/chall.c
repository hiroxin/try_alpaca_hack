// gcc -o chall chall.c -O0 -lm

#include <math.h>
#include <stdio.h>

int main(void) {
  double x = 0.253936121155405;
  double sin_x = sin(x);
  if (sin_x == 0.2512157895691234) {
    printf("We got %.16f as expected.\n", sin_x);
    return 1;
  } else {
    printf("Wow, we got %.16f!\n", sin_x);
  }
}
