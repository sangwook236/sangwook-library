import numpy as np
from scipy import ndimage, misc
import os, re
from .dataset import Dataset

class DataLoader(object):
	def __init__(self, width=0, height=0):
		self.width = width
		self.height = height

	def load(self, data_dir_path, label_dir_path=None, data_suffix='', data_extension='png', label_suffix='', label_extension='png'):
		data = []
		labels = []
		if None == label_dir_path:
			for root, dirnames, filenames in os.walk(data_dir_path):
				for filename in filenames:
					if re.search(label_suffix + "\." + label_extension + "$", filename):
						filepath = os.path.join(root, filename)
						label = np.uint16(ndimage.imread(filepath, flatten=True))
						#label = np.uint16(ndimage.imread(filepath))  # Do not correctly work.
						if (self.height > 0 and label.shape[0] != self.height) or (self.width > 0 and label.shape[1] != self.width):
							labels.append(misc.imresize(label, (self.height, self.width)))
						else:
							labels.append(label)
					elif re.search(data_suffix + "\." + data_extension + "$", filename):
						filepath = os.path.join(root, filename)
						image = ndimage.imread(filepath, mode="RGB")
						#image = ndimage.imread(filepath)
						if (self.height > 0 and image.shape[0] != self.height) or (self.width > 0 and image.shape[1] != self.width):
							data.append(misc.imresize(image, (self.height, self.width)))
						else:
							data.append(image)
		else:
			for root, dirnames, filenames in os.walk(data_dir_path):
				for filename in filenames:
					if re.search(data_suffix + "\." + data_extension + "$", filename):
						filepath = os.path.join(root, filename)
						image = ndimage.imread(filepath, mode="RGB")
						#image = ndimage.imread(filepath)
						if (self.height > 0 and image.shape[0] != self.height) or (self.width > 0 and image.shape[1] != self.width):
							data.append(misc.imresize(image, (self.height, self.width)))
						else:
							data.append(image)
			for root, dirnames, filenames in os.walk(label_dir_path):
				for filename in filenames:
					if re.search(label_suffix + "\." + label_extension + "$", filename):
						filepath = os.path.join(root, filename)
						label = np.uint16(ndimage.imread(filepath, flatten=True))
						#label = np.uint16(ndimage.imread(filepath))  # Do not correctly work.
						if (self.height > 0 and label.shape[0] != self.height) or (self.width > 0 and label.shape[1] != self.width):
							labels.append(misc.imresize(label, (self.height, self.width)))
						else:
							labels.append(label)
		return Dataset(data = np.array(data), labels = np.array(labels))