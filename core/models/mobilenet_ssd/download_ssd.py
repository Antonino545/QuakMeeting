import os
import urllib.request
import tarfile

def download_models():
    base_dir = os.path.dirname(__file__)
    
    # URLs
    tar_url = "http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v1_coco_2017_11_17.tar.gz"
    pbtxt_url = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v1_coco_2017_11_17.pbtxt"
    
    tar_path = os.path.join(base_dir, "ssd_mobilenet_v1_coco_2017_11_17.tar.gz")
    pbtxt_path = os.path.join(base_dir, "ssd_mobilenet_v1_coco.pbtxt")
    
    print("Downloading MobileNet SSD Model...")
    if not os.path.exists(tar_path):
        urllib.request.urlretrieve(tar_url, tar_path)
    
    print("Extracting...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extract("ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb", path=base_dir)
        
    print("Downloading Configuration...")
    if not os.path.exists(pbtxt_path):
        urllib.request.urlretrieve(pbtxt_url, pbtxt_path)
        
    print("MobileNet SSD successfully configured for QuakMeeting.")

if __name__ == "__main__":
    download_models()
