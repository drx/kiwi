#include <string.h>

extern unsigned int *screen, *scaled_screen;

const int width = 320, height = 240;

/* 
 * The nearest-neightbor naive scaling algorithm.
 * Pixels are magnified without any additional filtering.
 */
void scale_nearest(unsigned int *dest, unsigned int *src, int scale)
{
    for (int y=0; y<height; y++)
    {
        for (int x=0; x<width; x++)
        {
            for (int i=0; i<scale; i++)
            {
                for (int j=0; j<scale; j++)
                {
                    dest[(y*scale+i)*width*scale+x*scale+j] = src[y*width+x];
                }
            }
        }
    }
}

/*
 * The EPX algorithm (from http://en.wikipedia.org/wiki/Image_scaling)
 *
 * 2x:
 * 
 *   A      1 2
 * C P B -> 3 4
 *   D 
 *
 * 1=P; 2=P; 3=P; 4=P;
 * if C==A and C!=D and A!=B => 1=A
 * if A==B and A!=C and B!=D => 2=B
 * if D==C and D!=B and C!=A => 3=C
 * if B==D and B!=A and D!=C => 4=D
 *
 * 3x:
 * 
 * A B C    1 2 3
 * D E F -> 4 5 6
 * G H I    7 8 9
 *
 * 1=E; 2=E; 3=E; 4=E; 5=E; 6=E; 7=E; 8=E; 9=E;
 * if D==B and D!=H and B!=F => 1=D
 * if (D==B and D!=H and B!=F and E!=C) or (B==F and B!=D and F!=H and E!=A) => 2=B
 * if B==F and B!=D and F!=H => 3=F
 * if (H==D and H!=F and D!=B and E!=A) or (D==B and D!=H and B!=F and E!=G) => 4=D
 * 5=E
 * if (B==F and B!=D and F!=H and E!=I) or (F==H and F!=B and H!=D and E!=C) => 6=F
 * if H==D and H!=F and D!=B => 7=D
 * if (F==H and F!=B and H!=D and E!=G) or (H==D and H!=F and D!=B and E!=I) => 8=H
 * if F==H and F!=B and H!=D => 9=F
 * 
 * 4x is 2x applied twice
 */
#define get_pixel(dx, dy) \
    (((x)+(dx) < 0 || (x)+(dx) >= width || (y)+(dy) < 0 || (y)+(dy) >= height) ? 0 : \
        src[(y+dy)*width+x+dx])

#define epx_pixel(i) get_pixel(row[i].x, row[i].y)


struct point {
    int x;
    int y;
} epx_table_2x[4][4] = {
    {{0, -1}, {-1, 0}, {0, 1}, {1, 0}},
    {{1, 0}, {0, -1}, {-1, 0}, {0, 1}},
    {{-1, 0}, {0, 1}, {1, 0}, {0, -1}},
    {{0, 1}, {1, 0}, {0, -1}, {-1, 0}},
};

void scale_epx(unsigned int *dest, unsigned int *src, int scale)
{
    for (int y=0; y<height; y++)
    {
        for (int x=0; x<width; x++)
        {
            for (int i=0; i<scale; i++)
            {
                for (int j=0; j<scale; j++)
                {
                    unsigned int pixel = get_pixel(0, 0);
                    struct point *row = epx_table_2x[i*2+j];
                    if (epx_pixel(1) == epx_pixel(0) && 
                            epx_pixel(1) != epx_pixel(2) &&
                            epx_pixel(0) != epx_pixel(3))
                    {
                        pixel = epx_pixel(0);
                    }

                    dest[(y*scale+i)*width*scale+x*scale+j] = pixel;
                }
            }
        }
    }
}

struct s_filters
{
    char name[16];
    void (*fn)(unsigned int *, unsigned int *, int);
} filters[] = {
    {"None", scale_nearest},
    {"EPX", scale_epx}
};

void scale_filter(const char *filter, int scale)
{
    for (int i=0; i<sizeof(filters)/sizeof(struct s_filters); i++)
    {
        if (!strcmp(filter, filters[i].name))
        {
            (filters[i].fn)(scaled_screen, screen, scale);
            break;
        }

    }
}

