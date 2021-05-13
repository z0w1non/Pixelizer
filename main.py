import sys
import copy
import math
from PIL import Image, ImageFilter, ImageEnhance
import cv2

# returns (rsize, gsize, bsize)
def get_cube_size(cube):
    return (cube[1][0] - cube[0][0], cube[1][1] - cube[0][1], cube[1][2] - cube[0][2])

def contains_color(cube, color):
    return cube[0][0] <= color[0] and cube[0][1] <= color[1] and cube[0][2] <= color[2] \
        and cube[1][0] >= color[0] and cube[1][1] >= color[1] and cube[1][2] >= color[2]

def get_cube_count(cube, image):
    count = 0
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if contains_color(cube, image.getpixel((x, y))):
                count += 1
    return count

def get_color_distance(color1, color2):
    return math.sqrt((color1[0] - color2[0]) ** 2 + (color1[1] - color2[1]) ** 2 + (color1[2] - color2[2]) ** 2)
    
def get_nearest_color(color, colors):
    nearest = sys.float_info.max
    nearest_color = None
    for c in colors:
        d = get_color_distance(c, color)
        if d < nearest:
            nearest = d
            nearest_color = c
    return nearest_color

def get_nearest_colors(target_colors, pallet_colors):
    result = []
    for c in target_colors:
        result.append(get_nearest_color(c, pallet_colors))
    return result

def get_nearest_tiles(color, tiles):
    nearest = sys.float_info.max
    nearest_tile = None
    for tile in tiles:
        d = get_color_distance(tile.get_average_color(), color)
        if d < nearest:
            nearest = d
            nearest_tile = tile
    return nearest_tile

def get_largest_cube(cubes, image):
    max_count = 0
    largest_index = -1

    for i in range(len(cubes)):
        cube = cubes[i]
        count = get_cube_count(cube, image)
        if max_count < count:
            largest_index = i
            max_count = count

    return cubes[largest_index]

# returns (cube1, cube2)
def split_cube(cube):
    cube_size = get_cube_size(cube)
    max_size = max(cube_size)
    
    largest_dimension = -1
    for i in range(len(cube_size)):
        if cube_size[i] == max_size:
            largest_dimension = i
    
    if largest_dimension == 0:
        return (((cube[0][0]                    , cube[0][1], cube[0][2]), (cube[0][0] + max_size // 2, cube[1][1], cube[1][2])), \
                ((cube[0][0] + max_size // 2 + 1, cube[0][1], cube[0][2]), (cube[1][0]                , cube[1][1], cube[1][2])))
    
    if largest_dimension == 1:
        return (((cube[0][0], cube[0][1]                    , cube[0][2]), (cube[1][0], cube[0][1] + max_size // 2, cube[1][2])), \
                ((cube[0][0], cube[0][1] + max_size // 2 + 1, cube[0][2]), (cube[1][0], cube[1][1]                , cube[1][2])))

    if largest_dimension == 2:
        return (((cube[0][0], cube[0][1], cube[0][2]                    ), (cube[1][0], cube[1][1], cube[0][2] + max_size // 2)), \
                ((cube[0][0], cube[0][1], cube[0][2] + max_size // 2 + 1), (cube[1][0], cube[1][1], cube[1][2]                )))

def get_cube_color(cube, image):
    r = 0
    g = 0
    b = 0
    count = 0

    for y in range(image.size[1]):
        for x in range(image.size[0]):
            temp = image.getpixel((x, y))
            tempr, tempg, tempb = temp
            if contains_color(cube, temp):
                r += tempr
                g += tempg
                b += tempb
                count += 1
                
    if count == 0:
        return

    return (r // count, g // count, b // count)

# returns [color1, color2, color3, ...]
def median_cut(image, color_number):
    minr = 255
    ming = 255
    minb = 255
    maxr = 0
    maxg = 0
    maxb = 0
    
    # get color range
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            r, g, b = image.getpixel((x, y))
            minr = min(minr, r)
            ming = min(ming, g)
            minb = min(minb, b)
            maxr = max(maxr, r)
            maxg = max(maxg, g)
            maxb = max(maxb, b)
    cubes = [((minr, ming, minb), (maxr, maxg, maxb))]
    
    while (len(cubes) < color_number):
        largest_cube = get_largest_cube(cubes, image)
        cubes.remove(largest_cube)
        cube1, cube2 = split_cube(largest_cube)
        if get_cube_count(cube1, image) > 0:
            cubes.append(cube1)
        if get_cube_count(cube2, image) > 0:
            cubes.append(cube2)
        
    colors = []
    for cube in cubes:
        colors.append(get_cube_color(cube, image))
    return colors
    
def map_color(image, colors):
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            color = image.getpixel((x, y))
            # print(color)
            image.putpixel((x, y), get_nearest_color(color, colors))

def map_tile(image, tiles):
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            color = image.getpixel((x, y))
            image.putpixel((x, y), get_nearest_tiles(color, tiles).get_color(x, y))

class Tile:
    def __init__(self, color1, color2):
        self.color1 = color1
        self.color2 = color2
        
    def get_average_color(self):
        return ((self.color1[0] + self.color2[0]) // 2, (self.color1[1] + self.color2[1]) // 2, (self.color1[2] + self.color2[2]) // 2)

    def get_color(self, x, y):
        if ((x + y) % 2) == 0:
            return self.color1
        else:
            return self.color2

def create_dither_tiles(colors):
    tiles = [];
    for i in range(len(colors)):
        for j in range(i, len(colors)):
            tiles.append(Tile(colors[i], colors[j]))
    return tiles

def create_tone_colors(tone_number):
    result = []
    for rtone in range(tone_number):
        for gtone in range(tone_number):
            for btone in range(tone_number):
                result.append(((255 * rtone // tone_number), (255 * gtone // tone_number), (255 * btone // tone_number)))
    return result

def video_to_images(video_path, fps):
    images = []
    
    temp_path = "temp.png"

    video = cv2.VideoCapture(video_path)
    
    if not video.isOpened():
        return
    
    count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    total_time = count / video.get(cv2.CAP_PROP_FPS)
    capture_frame_number = int(total_time * fps)
    print("capture_frame_number: ", capture_frame_number)

    for i in range(capture_frame_number):
        print(i)
        video.set(cv2.CAP_PROP_POS_FRAMES, int(count * i / capture_frame_number) )
        ret, frame = video.read()
        if ret:
            cv2.imwrite(temp_path, frame)
            image = Image.open(temp_path).convert("RGB")
            images.append(pixelize(image))
        else:
            return
    
    return images
    
def pixelize(image):
    # parameters
    pixel_size = 20
    color_number = 16
    tone_number = 8

    image = image.filter(ImageFilter.MedianFilter())
    size = (image.size[0] // pixel_size, image.size[1] // pixel_size)
    image = image.resize(size)
    
    output_image = Image.new("RGB", size)
    output_image.paste(image)
    
    output_image = ImageEnhance.Color(output_image).enhance(2)
    output_image = ImageEnhance.Contrast(output_image).enhance(2)

    colors = median_cut(image, color_number)
    colors = get_nearest_colors(colors, create_tone_colors(tone_number))
    tiles = create_dither_tiles(colors)
    map_tile(output_image, tiles)

    #output_image = output_image.resize((size[0] * pixel_size, size[1] * pixel_size), Image.NEAREST)
    output_image = output_image.resize((size[0] * 5, size[1] * 5), Image.NEAREST)
    return output_image

def main():
    if len(sys.argv) < 3:
        print("pixelizer <input-video-path> <output-gif-path>", file=sys.stderr)

    input_video_path = sys.argv[1]
    output_gif_path = sys.argv[2]

    # parameters
    fps = 4

    images = video_to_images(input_video_path, fps)
    images[0].save(output_gif_path, save_all=True, append_images=images[1:], optimize=False, duration=1000//fps, loop=0, include_color_table=True)

if __name__ == "__main__":
    main()
