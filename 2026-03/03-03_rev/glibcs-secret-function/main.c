// gcc -o chal main.c

#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>

const unsigned char expected[97] = {107, 70, 90, 75, 73, 75, 81, 126, 66, 67, 89, 117, 67, 89, 117, 94, 66, 79, 117, 0, 103, 115, 121, 126, 111, 120, 99, 101, 127, 121, 117, 75, 68, 78, 117, 125, 101, 100, 110, 111, 120, 108, 127, 102, 0, 117, 76, 95, 68, 73, 94, 67, 69, 68, 117, 67, 68, 117, 77, 70, 67, 72, 73, 11, 117, 107, 70, 89, 69, 117, 66, 69, 93, 117, 75, 72, 69, 95, 94, 117, 89, 94, 88, 76, 88, 83, 117, 76, 95, 68, 73, 94, 67, 69, 68, 21, 87};

int main()
{
    char input[112], work[112];
    printf("Input > ");
    scanf("%111s", input);

    size_t len = strlen(input);
    if (len == sizeof(expected))
    {
        strcpy(work, input);
        memfrob(work, len);
        if(!memcmp(work, expected, sizeof(expected)))
        {
            printf("Correct! The flag is %s\n", input);
            return 0;
        }
    }
    printf("Incorrect...\n");
    return 1;
}
