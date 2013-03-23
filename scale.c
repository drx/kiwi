#include <string.h>
#include <stdlib.h>
#include <hqx/hqx.h>

extern unsigned int *screen, *scaled_screen;

const int width = 320, height = 240;
int hqx_init = 0;

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
    (((x)+(dx) < 0 || (x)+(dx) >= w || (y)+(dy) < 0 || (y)+(dy) >= h) ? 0 : \
        src[(y+dy)*w+x+dx])

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

struct point epx_table_3x[4][2] = {
    {{1, -1}, {-1, -1}}, 
    {{-1, -1}, {-1, 1}}, 
    {{1, 1}, {1, -1}}, 
    {{-1, 1}, {1, 1}}
};

int epx_rotation[4] = {1, 3, 0, 2};
int epx_corners_3x[9] = {0, -1, 1, -1, -1, -1, 2, -1, 3};

void scale_epx_hw(unsigned int *dest, unsigned int *src, int scale, int h, int w)
{
    if (scale == 3)
    {
        for (int y=0; y<h; y++)
        {
            for (int x=0; x<w; x++)
            {
                for (int i=0; i<scale; i++)
                {
                    for (int j=0; j<scale; j++)
                    {
                        unsigned int pixel;
                        pixel = get_pixel(0, 0);
                        int k = i*3+j;
                        if (!(k & 1) && k != 4)
                        {
                            struct point *row = epx_table_2x[epx_corners_3x[k]];
                            if (epx_pixel(1) == epx_pixel(0) && 
                                    epx_pixel(1) != epx_pixel(2) &&
                                    epx_pixel(0) != epx_pixel(3))
                            {
                                pixel = epx_pixel(0);
                            }
                        }
                        else if (k & 1)
                        {
                            struct point *row_3x = epx_table_3x[k>>1];
                            struct point *row;
                            row = epx_table_2x[k>>1];
                            if (epx_pixel(1) == epx_pixel(0) && 
                                    epx_pixel(1) != epx_pixel(2) &&
                                    epx_pixel(0) != epx_pixel(3) &&
                                    get_pixel(0, 0) != get_pixel(row_3x[0].x, row_3x[0].y))
                            {
                                pixel = epx_pixel(1);
                            }

                            row = epx_table_2x[epx_rotation[k]];
                            if (epx_pixel(1) == epx_pixel(0) && 
                                    epx_pixel(1) != epx_pixel(2) &&
                                    epx_pixel(0) != epx_pixel(3) &&
                                    get_pixel(0, 0) != get_pixel(row_3x[1].x, row_3x[1].y))
                            {
                                pixel = epx_pixel(0);
                            }
                        }
                        dest[(y*scale+i)*w*scale+x*scale+j] = pixel;
                    }
                }
            }
        }
    }
    else if (scale == 2)
    {
        for (int y=0; y<h; y++)
        {
            for (int x=0; x<w; x++)
            {
                for (int i=0; i<scale; i++)
                {
                    for (int j=0; j<scale; j++)
                    {
                        unsigned int pixel;
                        struct point *row = epx_table_2x[i*2+j];
                        if (epx_pixel(1) == epx_pixel(0) && 
                                epx_pixel(1) != epx_pixel(2) &&
                                epx_pixel(0) != epx_pixel(3))
                        {
                            pixel = epx_pixel(0);
                        }
                        else
                        {
                            pixel = get_pixel(0, 0);
                        }

                        dest[(y*scale+i)*w*scale+x*scale+j] = pixel;
                    }
                }
            }
        }
    }
    else if (scale == 4)
    {
        unsigned int *temp_buf = malloc(sizeof(unsigned int)*width*height*4);
        scale_epx_hw(temp_buf, src, 2, h, w);
        scale_epx_hw(dest, temp_buf, 2, h*2, w*2);
        free(temp_buf);
    }
}

void scale_epx(unsigned int *dest, unsigned int *src, int scale)
{
    scale_epx_hw(dest, src, scale, height, width);
}

void scale_hqx(unsigned int *dest, unsigned int *src, int scale)
{
    if (!hqx_init)
    {
        hqxInit();
        hqx_init = 1;
    }

    if (scale == 2)
    {
        hq2x_32(src, dest, width, height);
    }
    else if (scale == 3)
    {
        hq3x_32(src, dest, width, height);
    }
    else if (scale == 4)
    {
        hq4x_32(src, dest, width, height);
    }
}

struct s_filters
{
    char name[16];
    void (*fn)(unsigned int *, unsigned int *, int);
} filters[] = {
    {"None", scale_nearest},
    {"EPX", scale_epx},
    {"hqx", scale_hqx}
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

