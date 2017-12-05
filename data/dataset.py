import torch as t
from .voc_dataset import VOCBboxDataset
from skimage import transform as sktsf
from torchvision import transforms as tvtsf
from . import util

def preprocess(img,min_size = 600, max_size = 1000):
    """Preprocess an image for feature extraction.

    The length of the shorter edge is scaled to :obj:`self.min_size`.
    After the scaling, if the length of the longer edge is longer than
    :obj:`self.max_size`, the image is scaled to fit the longer edge
    to :obj:`self.max_size`.

    After resizing the image, the image is subtracted by a mean image value
    :obj:`self.mean`.

    Args:
        img (~numpy.ndarray): An image. This is in CHW and RGB format.
            The range of its value is :math:`[0, 255]`.

    Returns:
        ~numpy.ndarray:
        A preprocessed image.

    """
    C, H, W = img.shape
    scale1 = min_size / min(H, W)
    scale2 = max_size / max(H, W)
    scale = min(scale1, scale2)
    # 总之较长的一边和较短的一边都要小于（max_size和min_size）
    #img = resize(img, (int(H * scale), int(W * scale)))
    img = img / 256
    img = sktsf.resize(img, (C,H*scale,W*scale),mode='reflect')
    
    normalize = tvtsf.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[0.229, 0.224, 0.225])

    img = normalize(t.from_numpy(img))
    return img.numpy()
    #NOTE: 原始的normalize 为什么只减均值，不除以标准差？？
    # mean=np.array([122.7717, 115.9465, 102.9801],
    # img = (img - self.mean).astype(np.float32, copy=False)


class Transform(object):

    def __init__(self, min_size=600,max_size=1000):
        self.min_size = min_size
        self.max_size = max_size

    def __call__(self, in_data):
        img, bbox, label = in_data
        _, H, W = img.shape
        img = preprocess(img, self.min_size, self.max_size)
        _, o_H, o_W = img.shape
        scale = o_H / H
        bbox = util.resize_bbox(bbox, (H, W), (o_H, o_W))

        # horizontally flip
        img, params = util.random_flip(
            img, x_random=True, return_param=True)
        bbox = util.flip_bbox(
            bbox, (o_H, o_W), x_flip=params['x_flip'])

        return img, bbox, label, scale

class Dataset():
    def __init__(self, opt):
        self.opt = opt
        self.db = VOCBboxDataset(opt.voc_data_dir)
        self.tsf = Transform(opt.min_size,opt.max_size)

    def __getitem__(self, idx):
        img, bbox, label, difficult = self.db.get_example(idx)

        img, bbox, label, scale = self.tsf((img, bbox, label))
        return img, bbox, label, scale
