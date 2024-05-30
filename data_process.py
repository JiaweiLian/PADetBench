import os
import json
import numpy as np
import queue
import cv2
import carla
from pascal_voc_writer import Writer

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

def build_projection_matrix(w, h, fov):
    focal = w / (2.0 * np.tan(fov * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = w / 2.0
    K[1, 2] = h / 2.0
    return K

class DatasetGenerator:
    def __init__(self, world, spectator, save_path, dataset_name, sensor_blueprint_id='sensor.camera.rgb', image_width='800', image_height='600') -> None:
        self.world = world
        self.spectator = spectator
        
        # Create a blueprint for the camera
        camera_blueprint = world.get_blueprint_library().find(sensor_blueprint_id)
        camera_blueprint.set_attribute('image_size_x', image_width)
        camera_blueprint.set_attribute('image_size_y', image_height)

        # Get the camera attributes
        camera_initial_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=2.0))  
        self.camera = world.spawn_actor(camera_blueprint, camera_initial_transform, attach_to=spectator.base_spectator)
        
        # Create a queue to store and retrieve the sensor data
        self.image_queue = queue.Queue()
        self.camera.listen(self.image_queue.put)

        # Get the attributes from the camera
        self.image_w = camera_blueprint.get_attribute("image_size_x").as_int()
        self.image_h = camera_blueprint.get_attribute("image_size_y").as_int()
        fov = camera_blueprint.get_attribute("fov").as_float()

        # Calculate the camera projection matrix to project from 3D -> 2D
        self.K = build_projection_matrix(self.image_w, self.image_h, fov)

        # Remember the edge pairs
        self.edges = [[0,1], [1,3], [3,2], [2,0], [0,4], [4,5], [5,1], [5,7], [7,6], [6,4], [6,2], [7,3]]

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

        self.save_path = os.path.join(save_path, dataset_name.replace('.', '_'))
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.writer = Writer(self.save_path, self.image_w, self.image_h)

    def data_save(self, save_images = True, save_pascal_voc = False, save_images_with_2d_bb = False, save_images_with_3d_bb = False):

        image = self.image_queue.get()
        img = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

        # Get the camera matrix 
        world_2_camera = np.array(self.camera.get_transform().get_inverse_matrix())
        
        # weather_string = str(weather).replace(' ', '_').replace(':', '').replace(',', '').replace('(', '_').replace(')', '').replace('=', '').replace('%', '').replace('.', '_')
        # image_id = '%06d' % angle_degree + '_R%02d' % radius + '_H%02d_' % height + weather_string + '_' + map  # Detailed information of the image
        image_id = '%06d' % self.spectator.angle_degree
        image_name = image_id + '.png'

        image_json = {'file_name': image_name, 'height': image.height, 'width': image.width, 'id': int(image_id)}
        self.coco_label_json['images'].append(image_json)

        output_path = os.path.join(self.save_path, 'val2017', image_name)
        # Save the image
        if save_images:
            image.save_to_disk(output_path)

        # Initialize the exporter of pascal voc format
        for npc in self.world.get_actors().filter('*vehicle*'):
            bb = npc.bounding_box
            dist = npc.get_transform().location.distance(self.spectator.get_transform().location)
            if dist > 50:
                continue
            forward_vec = self.spectator.get_transform().get_forward_vector()
            ray = npc.get_transform().location - self.spectator.get_transform().location
            if forward_vec.dot(ray) > 1:
                p1 = get_image_point(bb.location, self.K, world_2_camera)
                verts = [v for v in bb.get_world_vertices(npc.get_transform())]
                if save_images_with_3d_bb:
                    for edge in self.edges:
                        p1 = get_image_point(verts[edge[0]], self.K, world_2_camera)
                        p2 = get_image_point(verts[edge[1]],  self.K, world_2_camera)
                        cv2.line(img, (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), (255,0,0, 255), 1)        

                x_max = -10000
                x_min = 10000
                y_max = -10000
                y_min = 10000
                for vert in verts:
                    p = get_image_point(vert, self.K, world_2_camera)
                    # Find the rightmost vertex
                    if p[0] > x_max:
                        x_max = p[0]
                    # Find the leftmost vertex
                    if p[0] < x_min:
                        x_min = p[0]
                    # Find the highest vertex
                    if p[1] > y_max:
                        y_max = p[1]
                    # Find the lowest  vertex
                    if p[1] < y_min:
                        y_min = p[1]
                if save_images_with_2d_bb:
                    cv2.line(img, (int(x_min),int(y_min)), (int(x_max),int(y_min)), (0,0,255, 255), 1)
                    cv2.line(img, (int(x_min),int(y_max)), (int(x_max),int(y_max)), (0,0,255, 255), 1)
                    cv2.line(img, (int(x_min),int(y_min)), (int(x_min),int(y_max)), (0,0,255, 255), 1)
                    cv2.line(img, (int(x_max),int(y_min)), (int(x_max),int(y_max)), (0,0,255, 255), 1)

                # Add the object to the frame (ensure it is inside the image)
                if x_min > 0 and x_max < self.image_w and y_min > 0 and y_max < self.image_h: 
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
                                'segmentation': []
                                }
                    self.coco_label_json['annotations'].append(annotation)
                    annotation_id += 1

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
        with open(os.path.join(self.save_path, 'annotations', 'captions_val2017.json'), 'w') as f:
            json.dump(self.coco_label_json, f)

    def __del__(self):
        self.annotation_save()
        self.camera.stop()
        self.camera.destroy()