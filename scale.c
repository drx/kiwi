extern unsigned int *screen, *scaled_screen;

void scale_nearest(unsigned int *dest, unsigned int *src, int scale)
{
    int width = 320, height = 240;
    int scaled_size = 1<<(scale-1);
    for (int y=0; y<height; y++)
    {
        for (int x=0; x<width; x++)
        {
            for (int i=0; i<scaled_size; i++)
            {
                for (int j=0; j<scaled_size; j++)
                {
                    dest[(y*scale+i)*320*scale+x*scale+j] = src[y*320+x];
                }
            }
        }
    }
}

void scale_filter(const char *filter, int scale)
{
    scale_nearest(scaled_screen, screen, scale);
}

