# Commented out IPython magic to ensure Python compatibility.
#downloading test images from Roboflow
#export dataset above with format COCO JSON
#or import your test images via other means. 
import os
import glob
# os.system('mkdir test')

# %cd /content/test/
# os.system('cd test && curl -L "https://app.roboflow.com/ds/1hpgGsgjQX?key=CEPLsAtHHw" > roboflow.zip; unzip roboflow.zip; rm roboflow.zip')

# Commented out IPython magic to ensure Python compatibility.
import matplotlib
import matplotlib.pyplot as plt


import io
import scipy.misc
import numpy as np
from six import BytesIO
from PIL import Image, ImageDraw, ImageFont
import cv2
import tensorflow as tf

from object_detection.utils import label_map_util
from object_detection.utils import config_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

# %matplotlib inline
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def load_image_into_numpy_array(path):
  """Load an image from file into a numpy array.

  Puts image into numpy array to feed into tensorflow graph.
  Note that by convention we put it into a numpy array with shape
  (height, width, channels), where channels=3 for RGB.

  Args:
    path: the file path to the image

  Returns:
    uint8 numpy array with shape (img_height, img_width, 3)
  """
  img_data = tf.io.gfile.GFile(path, 'rb').read()
  image = Image.open(BytesIO(img_data))
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

# Commented out IPython magic to ensure Python compatibility.
# %ls '/content/training/'

import pathlib

filenames = list(pathlib.Path('./training/').glob('*.index'))

filenames.sort()
print(filenames)

#recover our saved model
pipeline_config = './pipeline_file.config'
#generally you want to put the last ckpt from training in here
model_dir = str(filenames[-1]).replace('.index','')
configs = config_util.get_configs_from_pipeline_file(pipeline_config)
model_config = configs['model']
detection_model = model_builder.build(
      model_config=model_config, is_training=False)

# Restore checkpoint
ckpt = tf.compat.v2.train.Checkpoint(
      model=detection_model)
# ckpt.restore(os.path.join(str(filenames[-1]).replace('.index',''))).expect_partial()
ckpt.restore(os.path.join('saved_ckpt', 'ckpt-3')).expect_partial()



def get_model_detection_function(model):
  """Get a tf.function for detection."""

  @tf.function
  def detect_fn(image):
    """Detect objects in image."""

    image, shapes = model.preprocess(image)
    prediction_dict = model.predict(image, shapes)
    detections = model.postprocess(prediction_dict, shapes)

    return detections, prediction_dict, tf.reshape(shapes, [-1])

  return detect_fn

detect_fn = get_model_detection_function(detection_model)

#map labels for inference decoding
label_map_path = configs['eval_input_config'].label_map_path
label_map = label_map_util.load_labelmap(label_map_path)
categories = label_map_util.convert_label_map_to_categories(
    label_map,
    max_num_classes=label_map_util.get_max_label_map_index(label_map),
    use_display_name=True)
category_index = label_map_util.create_category_index(categories)
label_map_dict = label_map_util.get_label_map_dict(label_map, use_display_name=True)

#run detector on test image
#it takes a little longer on the first run and then runs at normal speed. 
import random
for i in range(50):
  # TEST_IMAGE_PATHS = glob.glob('./test/test/*.jpg')
  TEST_IMAGE_PATHS = glob.glob('./test_set/*.jpg')
  image_path = random.choice(TEST_IMAGE_PATHS)
  image_np = load_image_into_numpy_array(image_path)

  # Things to try:
  # Flip horizontally
  # image_np = np.fliplr(image_np).copy()

  # Convert image to grayscale
  # image_np = np.tile(
  #     np.mean(image_np, 2, keepdims=True), (1, 1, 3)).astype(np.uint8)

  input_tensor = tf.convert_to_tensor(
      np.expand_dims(image_np, 0), dtype=tf.float32)
  detections, predictions_dict, shapes = detect_fn(input_tensor)

  label_id_offset = 1
  image_np_with_detections = image_np.copy()
  import time
  viz_utils.visualize_boxes_and_labels_on_image_array(
        image_np_with_detections,
        detections['detection_boxes'][0].numpy(),
        (detections['detection_classes'][0].numpy() + label_id_offset).astype(int),
        detections['detection_scores'][0].numpy(),
        category_index,
        use_normalized_coordinates=True,
        max_boxes_to_draw=200,
        min_score_thresh=.65,
        agnostic_mode=False,
        
  )

  plt.figure(figsize=(12,16))
  plt.imshow(image_np_with_detections)

  plt.savefig("prediction.png")
  time.sleep(0.5)

  """## Congrats!

  Hope you enjoyed this!

  --Team [Roboflow](https://roboflow.ai)
 CUDA_VISIBLE_DEVICES="-1" python3 models/research/object_detection/model_main_tf2.py     --pipeline_config_path='pipeline_file.config'     --model_dir='training/'  --checkpoint_dir=training/ eval_dir=eval/

python3 models/research/object_detection/exporter_main_v2.py  --input_type=image_tensor --pipeline_config_path='pipeline_file.config'  --trained_checkpoint_dir=training/ --output_directory=export/


python3 models/research/object_detection/export_tflite_graph_tf2.py  --pipeline_config_path='pipeline_file.config'  --trained_checkpoint_dir=export_ckpt/ --output_directory=tflite/

tflite_convert --saved_model_dir=tflite/saved_model --output_file=tflite/saved_model/detect.tflite --input_shapes=1,300,300,3 --input_arrays=normalized_input_image_tensor --output_arrays='TFLite_Detection_PostProcess','TFLite_Detection_PostProcess:1','TFLite_Detection_PostProcess:2','TFLite_Detection_PostProcess:3' --inference_type=QUANTIZED_UINT8 --allow_custom_ops



"""