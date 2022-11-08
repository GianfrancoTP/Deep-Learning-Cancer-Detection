import os
import pyvips
import argparse
import openslide
from os import listdir
from itertools import product
from PIL import Image, ImageOps
from os.path import isfile, join
import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon

Image.MAX_IMAGE_PIXELS = 1149657159

def analize_tile(x_start, y_start, file_info, image, percentage, background_cut):
    gray_image = ImageOps.grayscale(image)
    pix = gray_image.load()
    w, h = gray_image.size
    total_pixels = w*h
    max_background_pixels = total_pixels*(1-percentage)

    positive_pixels = 0
    polygon_list = []
    background_pixels_count = 0
    useful_image = True
    
    for annotation in file_info:
        for region in file_info[annotation]:
            poly_coords = []
            for j in range(len(file_info[annotation][region]['x'])):
                x = file_info[annotation][region]['x'][j]
                y = file_info[annotation][region]['y'][j]
                poly_coords.append((x, y))
    
            polygon = Polygon(poly_coords)
            polygon_list.append(polygon)
    
    for i in range(w):
        for j in range(h):
            # Count background pixels.
            if pix[i,j] >= background_cut:
                background_pixels_count += 1
                if background_pixels_count >= max_background_pixels:
                    useful_image = False
                    return positive_pixels/total_pixels, useful_image

            # Detecting pixels inside marked regions.
            point = Point(i+x_start, j+y_start)
            for polygon in polygon_list:
                if point.within(polygon):
                    positive_pixels += 1
                    break
            
    return positive_pixels/total_pixels, useful_image

def read_xml_file(path):
    tree = ET.parse(path)
    Annotations = tree.getroot()

    annotations = {}

    for Annotation in Annotations:
        if Annotation.attrib['Visible'] == '1':
            annotation_id = Annotation.attrib['Id']
            annotations[annotation_id] = {}
            for Regions in Annotation.iter('Regions'):
                for Region in Regions.iter('Region'):
                    region_id = Region.attrib['Id']
                    annotations[annotation_id][region_id] = {'x':[], 'y':[]}
                    annotations[annotation_id][region_id]['AreaMicrons'] = Region.attrib['AreaMicrons']
                    for Vertices in Region.iter('Vertices'):
                        for Vertex in Vertices:
                            annotations[annotation_id][region_id]['x'].append(int(Vertex.attrib['X']))
                            annotations[annotation_id][region_id]['y'].append(int(Vertex.attrib['Y']))
                
    return annotations

def show_positive_tiles(case_path, min_x, max_x, crop_start, tile_size):
    img_jpeg = Image.open(f'{case_path}/image crop.jpeg')
    for file in listdir(f'{case_path}/positive'):
        file = file.replace('.jpeg','').split('_')
        j = int(file[1])-crop_start
        i = int(file[0])
        pix = img_jpeg.load()
        for x in range(tile_size):
            for y in range(tile_size):
                #print(pix[x,y])  # Get the RGBA Value of the a pixel of an image
                pix[j+x, i+y] = (pix[j+x, i+y][0], 255, pix[j+x, i+y][2])

    for file in listdir(f'{case_path}/negative'):
        file = file.replace('.jpeg','').split('_')
        j = int(file[1])-crop_start
        i = int(file[0])
        pix = img_jpeg.load()
        for x in range(tile_size):
            for y in range(tile_size):
                #print(pix[x,y])  # Get the RGBA Value of the a pixel of an image
                pix[j+x, i+y] = (pix[j+x, i+y][0], pix[j+x, i+y][1], 255)            

    out = os.path.join(f'{case_path}/image crop positive zones.jpeg')
    img_jpeg.save(out)

def create_data(base_path, file_name, setup):    
    # Creating output file folde
    print(f'Processing {file_name} file...')

    case_path = f'{setup["output_path"]}/{file_name}'
    case_path_positive =f'{case_path}/positive'
    case_path_negative = f'{case_path}/negative'
    positive_path = f'{setup["output_path"]}/positive'
    negative_path = f'{setup["output_path"]}/negative'
    os.mkdir(case_path)
    os.mkdir(case_path_positive)
    os.mkdir(case_path_negative)
    if not os.path.isdir(positive_path):
        os.mkdir(positive_path)
    if not os.path.isdir(negative_path):
        os.mkdir(negative_path)
    
    # Read .xml file
    xml_path = f'{base_path}/{file_name}.xml'
    file_info = read_xml_file(xml_path)
    
    # Read .svs file
    svs_path = f'{base_path}/{file_name}.svs'
    img = openslide.OpenSlide(svs_path)
    w, h = img.dimensions
    img = pyvips.Image.new_from_file(svs_path)
    
    # Here we get de min and max values of x between all the polygons to make the cut of the .svs image 
    min_x = w
    max_x = 0
    for annotation in file_info:
        for region in file_info[annotation]:
            region_x_min = min(file_info[annotation][region]['x'])
            region_x_max = max(file_info[annotation][region]['x'])
            if region_x_min < min_x or min_x == None:
                min_x = region_x_min
            if region_x_max > max_x or max_x == None:
                max_x = region_x_max
                
    max_pixel = 25500
    max_crop_lenght = max_pixel - (max_x - min_x)
    if max_crop_lenght > 0:
        crop_start = max(int(min_x - (max_crop_lenght/2)), 0)
        if int(max_x + (max_crop_lenght/2)) > w:
            crop_lenght = w-crop_start
        else:
            crop_lenght = int(max_x + (max_crop_lenght/2))-crop_start
    else:
        crop_start = min_x
        crop_lenght = max_pixel
    image_part = img.crop(crop_start, 0, crop_lenght, h)
    del img
    image_crop_path = f'{case_path}/image crop.jpeg'
    image_part.jpegsave(image_crop_path)

    #Create '.jpeg' tiles from every part of the image crop file.
    grid = product(range(0, h-h%setup['tile_size'], setup['tile_size']), range(0, crop_lenght-crop_lenght%setup['tile_size'], setup['tile_size']))
    total_tiles = len(list(grid))
    tile_count = 0
    grid = product(range(0, h-h%setup['tile_size'], setup['tile_size']), range(0, crop_lenght-crop_lenght%setup['tile_size'], setup['tile_size']))
    for i, j in grid:
        tile_count += 1
        print(f'   - Creating Tile {tile_count}/{total_tiles}', end="\r")
        
        image_tile = image_part.crop(j, i, setup['tile_size'], setup['tile_size'])
        img_jpeg_path = f'{case_path}/file in process.jpeg'
        image_tile.jpegsave(img_jpeg_path)
        img_jpeg = Image.open(img_jpeg_path)

        positive_percentage, useful_tile = analize_tile(j+crop_start, i, file_info, img_jpeg, setup['tissue_percentage'], setup['background_cut'])

        if useful_tile and positive_percentage >= setup['min_positive_percentage']:
            out_1 = f'{case_path_positive}/{i}_{j+crop_start}.jpeg'
            out_2 = f'{positive_path}/{file_name}_{i}_{j+crop_start}.jpeg'
            img_jpeg.save(out_1)
            img_jpeg.save(out_2)
        elif useful_tile and positive_percentage <= setup['max_positive_percentage']:
            out_1 = f'{case_path_negative}/{i}_{j+crop_start}.jpeg'
            out_2 = f'{negative_path}/{file_name}_{i}_{j+crop_start}.jpeg'
            img_jpeg.save(out_1)
            img_jpeg.save(out_2)
                       
        img_jpeg.close()
        
    os.remove(img_jpeg_path)
    show_positive_tiles(case_path, min_x, max_x, crop_start, setup['tile_size'])

if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description = "Automatic data generator from Aperio ImageScope files.")
    parser.add_argument("-i", type=str,  help="Input file path", required = False, default = './data/input')
    parser.add_argument("-o", type=str,  help="Output file path", required = False, )
    parser.add_argument("-s", type=int, help = "Size of tiles.", required = False, default = 100)
    parser.add_argument("-min", type=float, help = "Minimum percentage of positive pixels in tile to be considered as positive.", required = False, default = 0.8)
    parser.add_argument("-max", type=float, help="Maximum percentage of positive pixels in tile to be considered as negative.", required = False, default = 0.1)
    parser.add_argument("-t", type=float, help="Minimum percentage of tissue pixels to be considered a useful tile.", required = False, default = 0.85)
    parser.add_argument("-b", type=int, choices=range(256), help="Minimum tiled pixel brightness to be considered as background.", required = False, default = 215)
    pargs = parser.parse_args()

    setup = {}
    
    setup['input_path'] = pargs.i
    setup['output_path'] = pargs.o
    setup['tile_size'] = pargs.s
    setup['min_positive_percentage'] = pargs.min
    setup['max_positive_percentage'] = pargs.max
    setup['tissue_percentage'] = pargs.t
    setup['background_cut'] = pargs.b

    if setup['output_path'] == None:
        setup['output_path'] = f"./data/dataset ({setup['tile_size']}x{setup['tile_size']})"

    if not os.path.isdir(setup['output_path']):
        os.mkdir(setup['output_path'])

    with open(f"{setup['output_path']}/Data setup.txt", 'w') as f:
        f.write(f"These are the initial setup variables for this data generator:\n")
        f.write(f"Tile size (pixels): {setup['tile_size']}\n")
        f.write(f"Min positive percentage: {setup['min_positive_percentage']}\n")
        f.write(f"Max positive percentage: {setup['max_positive_percentage']}\n")
        f.write(f"Tissue percentage: {setup['tissue_percentage']}\n")
        f.write(f"background cut: {setup['background_cut']}")

    for case in listdir(setup['input_path']):
        for file_name in listdir(f"{setup['input_path']}/{case}"):
            name, ext = os.path.splitext(file_name)
            if ext == '.svs':
                case_path = f"{setup['input_path']}/{case}"
                create_data(case_path, name, setup)
