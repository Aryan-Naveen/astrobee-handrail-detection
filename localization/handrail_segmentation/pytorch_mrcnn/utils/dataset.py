import os
import numpy as np
import torch
from PIL import Image, ImageOps
import cv2
import random

from .visualize import convert_mask_to_image
from torchvision.transforms import functional as F

class AstrobeeHandrailDataset(torch.utils.data.Dataset):
    def __init__(self, root, transforms):
        self.root = root
        self.transforms = transforms
        # load all image files, sorting them to
        # ensure that they are aligned
        self.imgs = list(sorted(os.listdir(os.path.join(root, "images"))))
        self.masks = list(sorted(os.listdir(os.path.join(root, "colored_maps"))))
        self.label_dict = {39: 1, 137: 2, 102: 3, 85: 4, 255: 1, 101: 1}

    def __getitem__(self, idx):
        # load images and masks
        img_path = os.path.join(self.root, "images", self.imgs[idx])
        mask_path = os.path.join(self.root, "colored_maps", self.masks[idx])
        img = Image.open(img_path).convert("RGB")
        # note that we haven't converted the mask to RGB,
        # because each color corresponds to a different instance
        # with 0 being background

        mask = ImageOps.grayscale(Image.open(mask_path))
        # convert the PIL Image into a numpy array
        mask = np.array(mask)
        # instances are encoded as different colors
        obj_ids = np.unique(mask)
        # first id is the background, so remove it
        obj_ids = obj_ids[1:]

        # split the color-encoded mask into a set
        # of binary masks
        masks = mask == obj_ids[:, None, None]

        # get bounding box coordinates for each mask
        num_objs = len(obj_ids)
        boxes = []
        labels = []
        for i in range(num_objs):
            pos =  np.where(masks[i])
            xmin = np.min(pos[1])
            xmax = np.max(pos[1])
            ymin = np.min(pos[0])
            ymax = np.max(pos[0])
            if (ymax - ymin) > 0 and (xmax - xmin) > 0:
                boxes.append([xmin, ymin, xmax, ymax])
                labels.append(self.label_dict[obj_ids[i]])

        # convert everything into a torch.Tensor
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        # there is only one class
        labels = torch.as_tensor(np.array(labels), dtype=torch.int64)
        masks = torch.as_tensor(masks, dtype=torch.uint8)

        image_id = torch.tensor([idx])
        area = (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0])
        # suppose all instances are not crowd
        iscrowd = torch.zeros((num_objs,), dtype=torch.int64)

        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["masks"] = masks
        target["image_id"] = image_id
        target["area"] = area
        target["iscrowd"] = iscrowd

        if self.transforms is not None:
            i = random.randint(0, 150)
            img, target = self.transforms(img, target)
            # vis_img = F.to_pil_image(img)
            # # cv2.imwrite('/home/anaveen/image.png', img[0].numpy())
            # vis_img.save('/home/anaveen/augmentation/image' +str(i)+ '.png')
            # label = np.unique(target['masks'][0].numpy())[-1]
            # cv2.imwrite('/home/anaveen/augmentation/target' + str(i) + '.png', convert_mask_to_image(target['masks'][0].numpy(), label))

        return img, target

    def __len__(self):
        return len(self.imgs)
