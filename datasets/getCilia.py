'''
Preprocessing helper for creating a PyTorch Dataset class Cilia.
Official Document can be found at:
http://pytorch.org/docs/master/data.html#torch.utils.data.Dataset

Inspired from:
https://github.com/bfortuner/pytorch_tiramisu/blob/master/datasets/camvid.py
https://github.com/ZijunDeng/pytorch-semantic-segmentation/blob/master/datasets/cityscapes.py

'''

import json
from numpy import array, zeros
from scipy.misc import imread
from glob import glob
import os
import numpy as np
import torch
import torchvision
from torchvision import transforms
from torch.utils import data


def load_input(base, split):
    '''
    Helper function to get the foler path.
    'base' is the parameter for the path of the data
    'split' could be 'train', 'validate', or 'test'.
    Return lists of training imgs and masks.
    '''
    input_imgs = []
    masks_imgs = []
    all_hash = sorted(os.listdir(base + split + '/data/'))

    # read in the data using scipy.misc.imread
    # (alternatively, one can also only load the paths here and use torch loader later.)
    for imgHash in all_hash:
        inputs = glob(base + split + '/data/' + imgHash + '/*.png')
        input_imgs.append(array([imread(f, mode='L') for f in inputs]).sum(axis=0))

        if split != 'test':
            masks = glob(base + split + '/masks/' + imgHash + '.png')
            masks_imgs.append(array([imread(f, mode='L') for f in masks]))

    # check whether if inputs and masks have the desired length
    if len(input_imgs) == 0 or len(masks_imgs) == 0:
        raise RuntimeError('Found 0 images, please check the data set')
    if len(input_imgs) != len(masks_imgs):
        raise RuntimeError('Must be the same amount of the input and mask images!')

    # reshape the input and its type
    for i in range(len(input_imgs)):
        input_imgs[i] = input_imgs[i].reshape(input_imgs[i].shape + (1,))
        input_imgs[i] = input_imgs[i].astype(np.uint8)

    # reshape the mask and its type
    for i in range(len(masks_imgs)):
        masks_imgs[i] = masks_imgs[i].reshape(masks_imgs[i][0].shape + (1,))
        masks_imgs[i] = masks_imgs[i].astype(np.uint8)
    return input_imgs, masks_imgs


class CiliaData(data.Dataset):
    '''
    PyTorch class of dataset for loading input and target data.

    __init__ starts a class.
    'root' is the root path of the dataset.
    'joint_transform' is used for transforming inputs and masks together.
    'input_transform' is used for transforming inputs.
    'target_transform' is used for transforming masks.

    __getitem__ builds iterator of pairs of input and target images.
    __len__ returns the length of the dataset
    '''
    def __init__(self, root, split='train', joint_transform=None,
                 input_transform=None, target_transform=None):
        self.root = root
        assert split in ('train', 'validate', 'test')
        self.split = split
        self.input_transform = input_transform
        self.target_transform = target_transform
        self.joint_transform = joint_transform
        self.imgs, self.masks = load_input(self.root, split)

    def __getitem__(self, index):
        img, target = self.imgs[index], self.masks[index]
        # we need joint transform because we need to crop the same area
        if self.joint_transform is not None:
            img, target = self.joint_transform(img, target)
        if self.input_transform is not None:
            img = self.input_transform(img)
        if self.target_transform is not None:
            target = self.target_transform(target)
        return img, target

    def __len__(self):
        return len(self.imgs)