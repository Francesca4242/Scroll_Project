#!/bin/env python3

import os
import glob
from PIL import Image
import requests
import numpy as np
import pandas as pd
from io import StringIO
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import grad
import functools

from PyQt5.QtGui import QImage, QColor


@functools.lru_cache(maxsize=10)
def getLayer(z):
    try:
        image = Image.open('0'+str(int(z))+'.webp')
    except FileNotFoundError:
        return None
    return image

def get_pixel(x, y, z):
    try:
        return getLayer(int(z)).getpixel((int(x), int(y)))
    except Exception:
        return (0,0,0)


def getTrainData():
    google_sheet_url = "https://docs.google.com/spreadsheets/d/put  your own sheet here/export?format=csv"
    response = requests.get(google_sheet_url)
    decoded_content = response.content.decode('utf-8')
    csv_data = StringIO(decoded_content)
    df = pd.read_csv(csv_data, usecols=[0,1,2,3,4,5], dtype=np.float32)
    #import pdb; pdb.set_trace()
    numpy_array = df.to_numpy()
    return (numpy_array[:,0:3], numpy_array[:,3:6])

outdata, indata = getTrainData()
indata =  torch.from_numpy(indata)
outdata =  torch.from_numpy(outdata)



# Applies a transformation from an (x,y,depth) location on an unwrapped page to
# an (x,y,z) location in the scroll.   depth = 0 is intended to be the middle of a sheet.
# All other coordinates are pixel coordinates.
class WarpNet(nn.Module):
    def __init__(self):
        super(WarpNet, self).__init__()

        # This toy size network seems plenty.  More seems to hurt.
        self.fc1 = nn.Linear(3, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 3)

    def forward(self, x):
        # Make pixel coordinates more sensible
        x = x / torch.Tensor([6000,6000,100]) + torch.Tensor([0,0,0])

        # Important to use a smooth loss function
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)

        x = x * torch.Tensor([4000,4000,2000])+ torch.Tensor([4000,4000,4600])
        return x

# Initialize the network, criterion and optimizer
net = WarpNet()
criterion = nn.MSELoss()
optimizer = optim.Adam(net.parameters(), lr=0.01)


def train():
    # Train the network
    for epoch in range(10000):
        optimizer.zero_grad()
        output = net(indata)
        loss = criterion(output, outdata)


        # Suggest you add loss functions to maintain distances.   Something like this, 
        # but applied only where Z is very near to zero (ie. the surface of the paper).
        # It needs some finesse to make it work well without causing 'wrinkling' everywhere.' 
        #dnet_by_dx1 = grad(net(indata), indata, create_graph=True)[0]

        # Suggest you add loss functions to Try to make the pixels either side of a sheet 
        # be darker than the sheet itself.

        # Suggest you add a loss function to avoid 'holes' in sheets - I typically just try
        # to minimize the standard deviation of all the pixels in a sheet.

        loss.backward()
        optimizer.step()

# Test the network
test_coords = torch.rand(10, 3)
new_coords = net(test_coords)
print(new_coords)


# Draws out a 100x100x1 cuboid of 'flat' image to visualize the currently trained neural net.
# Can also visualize slightly above/below the surface.
def flatten(start_point):
    #torch.nn.functional.grid_sample(input, grid, mode='bilinear', padding_mode='zeros')
    # make an image of a page, but flat

    x = torch.arange(100).view(1, -1).expand(100, 100) + start_point[0]
    y = torch.arange(100).view(-1, 1).expand(100, 100) + start_point[1]
    z = torch.Tensor([0]).view(-1, 1).expand(100, 100) + start_point[2]
    coords = torch.stack((x, y, z), dim=2).view(-1,3)
    
    output = net(coords)

    output = output.view(100,100,3)

    out_image = QImage(100, 100, QImage.Format_RGB888)


    # look up each pixel...    probably a big perf bottleneck.
    for y, row in enumerate(output):
      for x, pix in enumerate(row):
        pix = get_pixel(pix[0], pix[1], pix[2])
        out_image.setPixelColor(x, y, QColor(pix[0], pix[1], pix[2]))

    return out_image

# Translate just one position from a flat page back to the original warped page.
def translate_position(start_point):
    coords = torch.tensor(start_point, dtype=torch.float32).view(-1,3)

    output = net(coords)

    return tuple(output[0,:].detach().numpy())


