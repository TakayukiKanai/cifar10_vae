# VAE & CNN example of CIFAR10(Tensorflow)
CIFAR10でVAによるreconstructEやCNNによるclassificationをやる．  
Windows10 + Pycharm なら，tensorboardはwsl上で起動しましょう．  
windowsがpermission周りにうるさかったりフォルダを手放さなかったりするので．
batch-normのコーディングなんか参考になると思います.  
~~就活でtensorflow書けるって言って歩ているのに，何も見せられるコードが無かったので作りました．~~

## Enviroment
* OS
  * windows10 (+ wsl for tensorboard)
  * Ubuntu 16.04
  
* Python packages and version
  * Python 3.6.xxx
  * tensorflow(tensorflow-gpu) 1.1xxx
  * numpy 1.14.xxx
  * numpy 1.14.xxx
  * opencv-python 1.14.xxx
  * Pillow 5.xxx

## Contents
It contains the following codes.

| Python code| Explanation |
| ------ | ------ |
| [main.py](./main.py)   | Train the model of VAE (by train_vae()) and CNN-classification (by train_classification())|
| [network.py](./network.py)  | The model of VAE(3-layer-encoder +3-layer-decoder) & CNN(5layer+batch_norm) |
| [cifar10_loader.py](./cifar10_loader.py)  | Download CIFAR10-binary-data automatically and |

## For Quick Start
Run VAE model (Default)
```bash
$ python main.py
```
If you want to run CNN classification model, comment out train_vae() in [main.py](./main.py) , and comment in train_classification().  
By the tensorboard, you can see the loss (or generated images) transition.  
```bash
$ cd <saved_dir>/VAEsample/<log_dir_name>
$ tensorboard --logdir=./ --port 6006
```