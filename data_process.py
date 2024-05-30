import os
import json
import numpy as np
import queue
import cv2
import carla
from pascal_voc_writer import Writer
from tick import Camera

def get_image_point(loc, K, w2c):
    # Calculate 2D projection of 3D coordinate

    # Format the input coordinate (loc is a carla.Position object)
    point = np.array([loc.x, loc.y, loc.z, 1])
    # transform to camera coordinates
    point_camera = np.dot(w2c, point)

    # New we must change from UE4's coordinate system to an "standard"
    # (x, y ,z) -> (y, -z, x)
    # and we remove the fourth componebonent also
    point_camera = [point_camera[1], -point_camera[2], point_camera[0]]

    # now project 3D->2D using the camera matrix
    point_img = np.dot(K, point_camera)
    # normalize
    point_img[0] /= point_img[2]
    point_img[1] /= point_img[2]

    return point_img[0:2]

def get_2d_bb(verts, K, world_2_camera):
    point_pairs = []
    for vert in verts:
        point_pairs.append(get_image_point(vert, K, world_2_camera))
    
    x_list, y_list = zip(*point_pairs)
    # Find the rightmost vertex
    x_max = max(x_list)
    # Find the leftmost vertex
    x_min = min(x_list)
    # Find the highest vertex
    y_max = max(y_list)
    # Find the lowest  vertex
    y_min = min(y_list)

    return x_max, x_min, y_max, y_min

class DatasetGenerator:
    def __init__(self, world, camera: Camera, save_path: str, dataset_name: str) -> None:
        self.world = world
        self.camera = camera

        self.annotation_id = 1
        self.coco_label_json = {
        "info": ['none'], 
        "license": ['none'], 
        "images": [], 
        "categories": [], 
        "annotations": []
        }
        self.coco_categories = {'person': 0, 'bicycle': 1, 'car': 2, 'motorcycle': 3, 'airplane': 4, 'bus': 5, 'train': 6, 'truck': 7, 'boat': 8, 'traffic light': 9, 'fire hydrant': 10, 'stop sign': 11, 'parking meter': 12, 'bench': 13, 'bird': 14, 'cat': 15, 'dog': 16, 'horse': 17, 'sheep': 18, 'cow': 19, 'elephant': 20, 'bear': 21, 'zebra': 22, 'giraffe': 23, 'backpack': 24, 'umbrella': 25, 'handbag': 26, 'tie': 27, 'suitcase': 28, 'frisbee': 29, 'skis': 30, 'snowboard': 31, 'sports ball': 32, 'kite': 33, 'baseball bat': 34, 'baseball glove': 35, 'skateboard': 36, 'surfboard': 37, 'tennis racket': 38, 'bottle': 39, 'wine glass': 40, 'cup': 41, 'fork': 42, 'knife': 43, 'spoon': 44, 'bowl': 45, 'banana': 46, 'apple': 47, 'sandwich': 48, 'orange': 49, 'broccoli': 50, 'carrot': 51, 'hot dog': 52, 'pizza': 53, 'donut': 54, 'cake': 55, 'chair': 56, 'couch': 57, 'potted plant': 58, 'bed': 59, 'dining table': 60, 'toilet': 61, 'tv': 62, 'laptop': 63, 'mouse': 64, 'remote': 65, 'keyboard': 66, 'cell phone': 67, 'microwave': 68, 'oven': 69, 'toaster': 70, 'sink': 71, 'refrigerator': 72, 'book': 73, 'clock': 74, 'vase': 75, 'scissors': 76, 'teddy bear': 77, 'hair drier': 78, 'toothbrush': 79}
        for caftegory, category_id in self.coco_categories.items():
            self.coco_label_json['categories'].append({'supercategory': 'none', 'id': category_id, 'name': caftegory})

        # saving parameters
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        self.save_path = os.path.join(save_path, dataset_name)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.writer = Writer(self.save_path, camera.image_w, camera.image_h)

    def add_3dbb_to_img(self, img, verts, K, world_2_camera):
        edges = [[0,1], [1,3], [3,2], [2,0], [0,4], [4,5], [5,1], [5,7], [7,6], [6,4], [6,2], [7,3]]
        for edge in edges:
            p1x, p1y = get_image_point(verts[edge[0]], K, world_2_camera)
            p2x, p2y = get_image_point(verts[edge[1]],  K, world_2_camera)
            cv2.line(img, (int(p1x),int(p1y)), (int(p2x),int(p2y)), (255,0,0, 255), 1)

    def add_2dbb_to_img(self, img, verts, K, world_2_camera):
        x_max, x_min, y_max, y_min = get_2d_bb(verts, K, world_2_camera)
        cv2.line(img, (int(x_min),int(y_min)), (int(x_max),int(y_min)), (0,0,255, 255), 1)
        cv2.line(img, (int(x_min),int(y_max)), (int(x_max),int(y_max)), (0,0,255, 255), 1)
        cv2.line(img, (int(x_min),int(y_min)), (int(x_min),int(y_max)), (0,0,255, 255), 1)
        cv2.line(img, (int(x_max),int(y_min)), (int(x_max),int(y_max)), (0,0,255, 255), 1)

    def save_data(self, save_images = True, save_pascal_voc = False, save_images_with_2d_bb = False, save_images_with_3d_bb = False):
        # Get the camera matrix 
        world_2_camera = self.camera.get_matrix()

        # Initialize the exporter of pascal voc format
        verts = self.camera.get_vertices()
        x_max, x_min, y_max, y_min = get_2d_bb(verts, self.camera.K, world_2_camera)

        # Ensure the bounding box is inside the image
        x_min = max(0, x_min)
        x_max = min(self.camera.image_w, x_max)
        y_min = max(0, y_min)
        y_max = min(self.camera.image_h, y_max)

        # image processing
        image = self.camera.get_image()
        img = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

        # Add the object to the frame (ensure it is inside the image)
        # weather_string = str(weather).replace(' ', '_').replace(':', '').replace(',', '').replace('(', '_').replace(')', '').replace('=', '').replace('%', '').replace('.', '_')
        # image_id = '%06d' % angle_degree + '_R%02d' % radius + '_H%02d_' % height + weather_string + '_' + map  # Detailed information of the image
        image_id = f'{self.annotation_id:06d}'
        image_name = image_id + '.png'

        image_json = {'file_name': image_name, 'height': image.height, 'width': image.width, 'id': int(image_id)}
        self.coco_label_json['images'].append(image_json)

        self.writer.addObject('car', x_min, y_min, x_max, y_max)

        npc_width = abs(x_max - x_min)
        npc_height = abs(y_max - y_min)
        annotation = {'area': npc_width * npc_height, 
                    'iscrowd': 0, 
                    'image_id': int(image_id), 
                    'bbox': [x_min, y_min, npc_width, npc_height], 
                    'category_id': self.coco_categories['car'], 
                    'id': self.annotation_id, 
                    'ignore': 0, 
                    'segmentation': {'counts': [1,2,3], 'size': [600,800]}
                    }
        self.coco_label_json['annotations'].append(annotation)
        self.annotation_id += 1

        # Save the image
        if save_images:
            output_path = os.path.join(self.save_path, 'val2017', image_name)
            image.save_to_disk(output_path)

        if save_images_with_3d_bb:
            self.add_3dbb_to_img(img, verts, self.camera.K, world_2_camera)

        if save_images_with_2d_bb:
            self.add_2dbb_to_img(img, verts, self.camera.K, world_2_camera)

        if save_pascal_voc:
            # Save the bounding boxes in the scene
            self.writer.save(os.path.join(self.save_path, image_id + '.xml'))

        if save_images_with_2d_bb or save_images_with_3d_bb:
            cv2.imwrite(os.path.join(self.save_path, image_id + '_bb.png'), img)

    def annotation_save(self):
        # Create the folder to store the annotations
        if not os.path.exists(os.path.join(self.save_path, 'annotations')):
            os.makedirs(os.path.join(self.save_path, 'annotations'))

        # Save the json file with the annotations
        with open(os.path.join(self.save_path, 'annotations', 'instances_val2017.json'), 'w') as f:
            json.dump(self.coco_label_json, f)