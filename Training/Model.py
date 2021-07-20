import os
import pathlib
import matplotlib
import matplotlib.pyplot as plt
import re
import tarfile
import os
import random
import io
import imageio
import glob
import scipy.misc
import numpy as np
from six import BytesIO
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display, Javascript
from IPython.display import Image as IPyImage

import tensorflow as tf

from object_detection.utils import label_map_util
from object_detection.utils import config_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# Clone the tensorflow models repository if it doesn't already exist
if "models" in pathlib.Path.cwd().parts:
  while "models" in pathlib.Path.cwd().parts:
    os.chdir('..')
elif not pathlib.Path('models').exists():
  os.system('git clone --depth 1 https://github.com/tensorflow/models')


# ## Test
# os.system('python3 models/research/object_detection/builders/model_builder_tf2_test.py')

if not pathlib.Path('data').exists():
    os.system('mkdir data')
    os.system('cd data && curl -L "<link>" > roboflow.zip; unzip roboflow.zip; rm roboflow.zip')

test_record_fname = 'data/test/Lights.tfrecord'
train_record_fname = 'data/train/Lights.tfrecord'
label_map_pbtxt_fname = 'data/train/Lights_label_map.pbtxt'

# http://download.tensorflow.org/models/object_detection/tf2/20210210/centernet_mobilenetv2fpn_512x512_coco17_od.tar.gz
##change chosen model to deploy different models available in the TF2 object detection zoo
MODELS_CONFIG = {
    'ssdV2': {
        'model_name': 'ssd_mobilenet_v2_320x320_coco17_tpu-8',
        'base_pipeline_file': 'pipeline.config',
        'pretrained_checkpoint': 'ssd_mobilenet_v2_320x320_coco17_tpu-8.tar.gz',
        'batch_size': 16
    },
    'efficientdet-d0': {
        'model_name': 'centernet_mobilenetv2fpn_512x512_coco17_od',
        'base_pipeline_file': 'ssd_efficientdet_d0_512x512_coco17_tpu-8.config',
        'pretrained_checkpoint': 'efficientdet_d0_coco17_tpu-32.tar.gz',
        'batch_size': 3
    },
    'efficientdet-d1': {
        'model_name': 'efficientdet_d1_coco17_tpu-32',
        'base_pipeline_file': 'ssd_efficientdet_d1_640x640_coco17_tpu-8.config',
        'pretrained_checkpoint': 'efficientdet_d1_coco17_tpu-32.tar.gz',
        'batch_size': 1
    },
    'efficientdet-d2': {
        'model_name': 'efficientdet_d2_coco17_tpu-32',
        'base_pipeline_file': 'ssd_efficientdet_d2_768x768_coco17_tpu-8.config',
        'pretrained_checkpoint': 'efficientdet_d2_coco17_tpu-32.tar.gz',
        'batch_size': 1
    },
        'efficientdet-d3': {
        'model_name': 'efficientdet_d3_coco17_tpu-32',
        'base_pipeline_file': 'ssd_efficientdet_d3_896x896_coco17_tpu-32.config',
        'pretrained_checkpoint': 'efficientdet_d3_coco17_tpu-32.tar.gz',
        'batch_size': 1
    }
}

#in this tutorial we implement the lightweight, smallest state of the art efficientdet model
#if you want to scale up tot larger efficientdet models you will likely need more compute!
chosen_model = 'ssdV2'

num_steps = 300000 #The more steps, the longer the training. Increase if your loss function is still decreasing and validation metrics are increasing. 
num_eval_steps = 100 #Perform evaluation after so many steps

model_name = MODELS_CONFIG[chosen_model]['model_name']
pretrained_checkpoint = MODELS_CONFIG[chosen_model]['pretrained_checkpoint']
base_pipeline_file = MODELS_CONFIG[chosen_model]['base_pipeline_file']
batch_size = MODELS_CONFIG[chosen_model]['batch_size'] #if you can fit a large batch in memory, it may speed up your training


download_tar = 'http://download.tensorflow.org/models/object_detection/tf2/20200711/' + pretrained_checkpoint
# download_config = 'https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/configs/tf2/' + base_pipeline_file

if not pathlib.Path('deploy').exists():
    os.system('mkdir deploy')
    os.chdir('deploy')
    os.system('wget {}'.format(download_tar))
    tar = tarfile.open(pretrained_checkpoint)
    tar.extractall()
    tar.close()
    os.system('rm -rf *.tar.gz')
    os.chdir('..')


# #download base training configuration file

#prepare
pipeline_fname = 'deploy/' + model_name + '/' + base_pipeline_file
fine_tune_checkpoint = 'deploy/' + model_name + '/checkpoint/ckpt-0'

def get_num_classes(pbtxt_fname):
    from object_detection.utils import label_map_util
    label_map = label_map_util.load_labelmap(pbtxt_fname)
    categories = label_map_util.convert_label_map_to_categories(
        label_map, max_num_classes=90, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)
    return len(category_index.keys())
num_classes = get_num_classes(label_map_pbtxt_fname)


print('writing custom configuration file')

with open(pipeline_fname) as f:
    s = f.read()
with open('pipeline_file.config', 'w') as f:
    
    # fine_tune_checkpoint
    s = re.sub('fine_tune_checkpoint: ".*?"',
               'fine_tune_checkpoint: "{}"'.format(fine_tune_checkpoint), s)
    
    # tfrecord files train and test.
    s = re.sub(
        '(input_path: ".*?)(PATH_TO_BE_CONFIGURED/train)(.*?")', 'input_path: "{}"'.format(train_record_fname), s)
    s = re.sub(
    '(input_path: ".*?)(PATH_TO_BE_CONFIGURED/test)(.*?")', 'input_path: "{}"'.format(test_record_fname), s)

    # label_map_path
    s = re.sub(
        'label_map_path: ".*?"', 'label_map_path: "{}"'.format(label_map_pbtxt_fname), s)

    # Set training batch_size.
    s = re.sub('batch_size: [0-9]+',
               'batch_size: {}'.format(batch_size), s)

    # Set training steps, num_steps
    s = re.sub('num_steps: [0-9]+',
               'num_steps: {}'.format(num_steps), s)
    
    # Set number of classes num_classes.
    s = re.sub('num_classes: [0-9]+',
               'num_classes: {}'.format(num_classes), s)
    
    #fine-tune checkpoint type
    s = re.sub(
        'fine_tune_checkpoint_type: "classification"', 'fine_tune_checkpoint_type: "{}"'.format('detection'), s)
        
    f.write(s)

# os.system('cat pipeline_file.config')

pipeline_file = 'pipeline_file.config'

if not pathlib.Path('training').exists():
    os.system('mkdir training')

model_dir = 'training/'


"""# Train Custom TF2 Object Detector

# * pipeline_file: defined above in writing custom training configuration
# * model_dir: the location tensorboard logs and saved model checkpoints will save to
# * num_train_steps: how long to train for
# * num_eval_steps: perform eval on validation set after this many steps



CUDA_VISIBLE_DEVICES="0" python3 models/research/object_detection/model_main_tf2.py \
    --pipeline_config_path='pipeline_file.config' \
    --model_dir='training/' \
    --alsologtostderr \
    --num_train_steps=20000 \
    --sample_1_of_n_eval_examples=1 \
    --num_eval_steps=100



# """