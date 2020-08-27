#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
sys.path.append('../../src')
sys.path.append('./src')

import os, random, functools, itertools, operator, shutil, glob, datetime, time
import argparse, logging, logging.handlers
import numpy as np
import torch
import torchvision
from PIL import Image, ImageOps
import cv2
import matplotlib.pyplot as plt
import swl.language_processing.util as swl_langproc_util
import text_generation_util as tg_util
import text_data, aihub_data
import opennmt_util
#import mixup.vgg, mixup.resnet

# Define a global logger.
glogger = None
# Define a global variable, print.
print = print

def save_model(model_filepath, model):
	#torch.save(model.state_dict(), model_filepath)
	torch.save({'state_dict': model.state_dict()}, model_filepath)
	glogger.info('Saved a model to {}.'.format(model_filepath))

def load_model(model_filepath, model, device='cpu'):
	loaded_data = torch.load(model_filepath, map_location=device)
	#model.load_state_dict(loaded_data)
	model.load_state_dict(loaded_data['state_dict'])
	glogger.info('Loaded a model from {}.'.format(model_filepath))
	return model

# REF [function] >> construct_font() in font_test.py.
def construct_font(korean=True, english=True):
	if 'posix' == os.name:
		system_font_dir_path = '/usr/share/fonts'
		font_base_dir_path = '/home/sangwook/work/font'
	else:
		system_font_dir_path = 'C:/Windows/Fonts'
		font_base_dir_path = 'D:/work/font'

	font_dir_paths = list()
	if korean:
		font_dir_paths.append(font_base_dir_path + '/kor')
		#font_dir_paths.append(font_base_dir_path + '/kor_small')
		#font_dir_paths.append(font_base_dir_path + '/kor_large')
		#font_dir_paths.append(font_base_dir_path + '/kor_receipt')
	if english:
		font_dir_paths.append(font_base_dir_path + '/eng')
		#font_dir_paths.append(font_base_dir_path + '/eng_small')
		#font_dir_paths.append(font_base_dir_path + '/eng_large')
		#font_dir_paths.append(font_base_dir_path + '/eng_receipt')

	return tg_util.construct_font(font_dir_paths)

def create_char_augmenter():
	#import imgaug as ia
	from imgaug import augmenters as iaa

	augmenter = iaa.Sequential([
		iaa.Sometimes(0.25,
			iaa.Grayscale(alpha=(0.0, 1.0)),  # Requires RGB images.
		),
		#iaa.Sometimes(0.5, iaa.OneOf([
		#	iaa.Crop(px=(0, 100)),  # Crop images from each side by 0 to 16px (randomly chosen).
		#	iaa.Crop(percent=(0, 0.1)),  # Crop images by 0-10% of their height/width.
		#	#iaa.Fliplr(0.5),  # Horizontally flip 50% of the images.
		#	#iaa.Flipud(0.5),  # Vertically flip 50% of the images.
		#])),
		iaa.Sometimes(0.8, iaa.OneOf([
			iaa.Affine(
				#scale={'x': (0.8, 1.2), 'y': (0.8, 1.2)},  # Scale images to 80-120% of their size, individually per axis.
				translate_percent={'x': (-0.2, 0.2), 'y': (-0.2, 0.2)},  # Translate by -20 to +20 percent along x-axis and -20 to +20 percent along y-axis.
				rotate=(-30, 30),  # Rotate by -10 to +10 degrees.
				shear=(-10, 10),  # Shear by -10 to +10 degrees.
				order=[0, 1],  # Use nearest neighbour or bilinear interpolation (fast).
				#order=0,  # Use nearest neighbour or bilinear interpolation (fast).
				#cval=(0, 255),  # If mode is constant, use a cval between 0 and 255.
				#mode=ia.ALL  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
				#mode='edge'  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
			),
			#iaa.PiecewiseAffine(scale=(0.01, 0.05)),  # Move parts of the image around. Slow.
			#iaa.PerspectiveTransform(scale=(0.01, 0.1)),
			iaa.ElasticTransformation(alpha=(20.0, 40.0), sigma=(6.0, 8.0)),  # Move pixels locally around (with random strengths).
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.AdditiveGaussianNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			#iaa.AdditiveLaplaceNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			iaa.AdditivePoissonNoise(lam=(20, 30), per_channel=False),
			iaa.CoarseSaltAndPepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarseSalt(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarsePepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			#iaa.CoarseDropout(p=(0.1, 0.3), size_percent=(0.8, 0.9), per_channel=False),
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.GaussianBlur(sigma=(0.5, 1.5)),
			iaa.AverageBlur(k=(2, 4)),
			iaa.MedianBlur(k=(3, 3)),
			iaa.MotionBlur(k=(3, 4), angle=(0, 360), direction=(-1.0, 1.0), order=1),
		])),
		#iaa.Sometimes(0.8, iaa.OneOf([
		#	#iaa.MultiplyHueAndSaturation(mul=(-10, 10), per_channel=False),
		#	#iaa.AddToHueAndSaturation(value=(-255, 255), per_channel=False),
		#	#iaa.LinearContrast(alpha=(0.5, 1.5), per_channel=False),

		#	iaa.Invert(p=1, per_channel=False),

		#	#iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
		#	iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),
		#])),
		#iaa.Scale(size={'height': image_height, 'width': image_width})  # Resize.
	])

	return augmenter

def create_word_augmenter():
	#import imgaug as ia
	from imgaug import augmenters as iaa

	augmenter = iaa.Sequential([
		iaa.Sometimes(0.25,
			iaa.Grayscale(alpha=(0.0, 1.0)),  # Requires RGB images.
		),
		#iaa.Sometimes(0.5, iaa.OneOf([
		#	iaa.Crop(px=(0, 100)),  # Crop images from each side by 0 to 16px (randomly chosen).
		#	iaa.Crop(percent=(0, 0.1)),  # Crop images by 0-10% of their height/width.
		#	#iaa.Fliplr(0.5),  # Horizontally flip 50% of the images.
		#	#iaa.Flipud(0.5),  # Vertically flip 50% of the images.
		#])),
		iaa.Sometimes(0.8, iaa.OneOf([
			iaa.Affine(
				#scale={'x': (0.8, 1.2), 'y': (0.8, 1.2)},  # Scale images to 80-120% of their size, individually per axis.
				translate_percent={'x': (-0.1, 0.1), 'y': (-0.1, 0.1)},  # Translate by -10 to +10 percent along x-axis and -10 to +10 percent along y-axis.
				rotate=(-10, 10),  # Rotate by -10 to +10 degrees.
				shear=(-5, 5),  # Shear by -5 to +5 degrees.
				order=[0, 1],  # Use nearest neighbour or bilinear interpolation (fast).
				#order=0,  # Use nearest neighbour or bilinear interpolation (fast).
				#cval=(0, 255),  # If mode is constant, use a cval between 0 and 255.
				#mode=ia.ALL  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
				#mode='edge'  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
			),
			#iaa.PiecewiseAffine(scale=(0.01, 0.05)),  # Move parts of the image around. Slow.
			#iaa.PerspectiveTransform(scale=(0.01, 0.1)),
			iaa.ElasticTransformation(alpha=(20.0, 40.0), sigma=(6.0, 8.0)),  # Move pixels locally around (with random strengths).
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.AdditiveGaussianNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			#iaa.AdditiveLaplaceNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			iaa.AdditivePoissonNoise(lam=(20, 30), per_channel=False),
			iaa.CoarseSaltAndPepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarseSalt(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarsePepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			#iaa.CoarseDropout(p=(0.1, 0.3), size_percent=(0.8, 0.9), per_channel=False),
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.GaussianBlur(sigma=(0.5, 1.5)),
			iaa.AverageBlur(k=(2, 4)),
			iaa.MedianBlur(k=(3, 3)),
			iaa.MotionBlur(k=(3, 4), angle=(0, 360), direction=(-1.0, 1.0), order=1),
		])),
		#iaa.Sometimes(0.8, iaa.OneOf([
		#	#iaa.MultiplyHueAndSaturation(mul=(-10, 10), per_channel=False),
		#	#iaa.AddToHueAndSaturation(value=(-255, 255), per_channel=False),
		#	#iaa.LinearContrast(alpha=(0.5, 1.5), per_channel=False),

		#	iaa.Invert(p=1, per_channel=False),

		#	#iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
		#	iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),
		#])),
		#iaa.Scale(size={'height': image_height, 'width': image_width})  # Resize.
	])

	return augmenter

def create_textline_augmenter():
	#import imgaug as ia
	from imgaug import augmenters as iaa

	augmenter = iaa.Sequential([
		iaa.Sometimes(0.25,
			iaa.Grayscale(alpha=(0.0, 1.0)),  # Requires RGB images.
		),
		#iaa.Sometimes(0.5, iaa.OneOf([
		#	iaa.Crop(px=(0, 100)),  # Crop images from each side by 0 to 16px (randomly chosen).
		#	iaa.Crop(percent=(0, 0.1)),  # Crop images by 0-10% of their height/width.
		#	#iaa.Fliplr(0.5),  # Horizontally flip 50% of the images.
		#	#iaa.Flipud(0.5),  # Vertically flip 50% of the images.
		#])),
		iaa.Sometimes(0.8, iaa.OneOf([
			iaa.Affine(
				#scale={'x': (0.8, 1.2), 'y': (0.8, 1.2)},  # Scale images to 80-120% of their size, individually per axis.
				translate_percent={'x': (-0.05, 0.05), 'y': (-0.05, 0.05)},  # Translate by -5 to +5 percent along x-axis and -5 to +5 percent along y-axis.
				rotate=(-2, 2),  # Rotate by -2 to +2 degrees.
				shear=(-2, 2),  # Shear by -2 to +2 degrees.
				order=[0, 1],  # Use nearest neighbour or bilinear interpolation (fast).
				#order=0,  # Use nearest neighbour or bilinear interpolation (fast).
				#cval=(0, 255),  # If mode is constant, use a cval between 0 and 255.
				#mode=ia.ALL  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
				#mode='edge'  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
			),
			#iaa.PiecewiseAffine(scale=(0.01, 0.05)),  # Move parts of the image around. Slow.
			#iaa.PerspectiveTransform(scale=(0.01, 0.1)),
			iaa.ElasticTransformation(alpha=(20.0, 40.0), sigma=(6.0, 8.0)),  # Move pixels locally around (with random strengths).
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.AdditiveGaussianNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			#iaa.AdditiveLaplaceNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
			iaa.AdditivePoissonNoise(lam=(20, 30), per_channel=False),
			iaa.CoarseSaltAndPepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarseSalt(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			iaa.CoarsePepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
			#iaa.CoarseDropout(p=(0.1, 0.3), size_percent=(0.8, 0.9), per_channel=False),
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.GaussianBlur(sigma=(0.5, 1.5)),
			iaa.AverageBlur(k=(2, 4)),
			iaa.MedianBlur(k=(3, 3)),
			iaa.MotionBlur(k=(3, 4), angle=(0, 360), direction=(-1.0, 1.0), order=1),
		])),
		#iaa.Sometimes(0.8, iaa.OneOf([
		#	#iaa.MultiplyHueAndSaturation(mul=(-10, 10), per_channel=False),
		#	#iaa.AddToHueAndSaturation(value=(-255, 255), per_channel=False),
		#	#iaa.LinearContrast(alpha=(0.5, 1.5), per_channel=False),

		#	iaa.Invert(p=1, per_channel=False),

		#	#iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
		#	iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),
		#])),
		#iaa.Scale(size={'height': image_height, 'width': image_width})  # Resize.
	])

	return augmenter

def generate_font_colors(image_depth):
	#random_val = random.randrange(1, 255)

	#font_color = (255,) * image_depth  # White font color.
	font_color = tuple(random.randrange(256) for _ in range(image_depth))  # An RGB font color.
	#font_color = (random.randrange(256),) * image_depth  # A grayscale font color.
	#font_color = (random_val,) * image_depth  # A grayscale font color.
	#font_color = (random.randrange(random_val),) * image_depth  # A darker grayscale font color.
	#font_color = (random.randrange(random_val + 1, 256),) * image_depth  # A lighter grayscale font color.
	#font_color = (random.randrange(128),) * image_depth  # A dark grayscale font color.
	#font_color = (random.randrange(128, 256),) * image_depth  # A light grayscale font color.

	#bg_color = (0,) * image_depth  # Black background color.
	bg_color = tuple(random.randrange(256) for _ in range(image_depth))  # An RGB background color.
	#bg_color = (random.randrange(256),) * image_depth  # A grayscale background color.
	#bg_color = (random_val,) * image_depth  # A grayscale background color.
	#bg_color = (random.randrange(random_val),) * image_depth  # A darker grayscale background color.
	#bg_color = (random.randrange(random_val + 1, 256),) * image_depth  # A lighter grayscale background color.
	#bg_color = (random.randrange(128),) * image_depth  # A dark grayscale background color.
	#bg_color = (random.randrange(128, 256),) * image_depth  # A light grayscale background color.
	return font_color, bg_color

class RandomAugment(object):
	def __init__(self, augmenter, is_pil=True):
		if is_pil:
			self.augment_functor = lambda x: Image.fromarray(augmenter.augment_image(np.array(x)))
			#self.augment_functor = lambda x: Image.fromarray(augmenter.augment_images(np.array(x)))
		else:
			self.augment_functor = lambda x: augmenter.augment_image(x)
			#self.augment_functor = lambda x: augmenter.augment_images(x)

	def __call__(self, x):
		return self.augment_functor(x)

class RandomInvert(object):
	def __call__(self, x):
		return ImageOps.invert(x) if random.randrange(2) else x

class ConvertPILMode(object):
	def __init__(self, mode='RGB'):
		self.mode = mode

	def __call__(self, x):
		return x.convert(self.mode)

class ConvertNumpyToRGB(object):
	def __call__(self, x):
		if x.ndim == 1:
			return np.repeat(np.expand_dims(x, axis=0), 3, axis=0)
		elif x.ndim == 3:
			return x
		else: raise ValueError('Invalid dimension, {}.'.format(x.ndim))

class ResizeImageToFixedSizeWithPadding(object):
	def __init__(self, height, width, warn_about_small_image=False, is_pil=True):
		self.height, self.width = height, width
		self.resize_functor = self._resize_by_pil if is_pil else self._resize_by_opencv

		self.min_height_threshold, self.min_width_threshold = 20, 20
		self.warn = self._warn_about_small_image if warn_about_small_image else lambda *args, **kwargs: None

	def __call__(self, x):
		return self.resize_functor(x, self.height, self.width)

	# REF [function] >> RunTimeTextLineDatasetBase._resize_by_opencv() in text_line_data.py.
	def _resize_by_opencv(self, input, height, width, *args, **kwargs):
		interpolation = cv2.INTER_AREA
		"""
		hi, wi = input.shape[:2]
		if wi >= width:
			return cv2.resize(input, (width, height), interpolation=interpolation)
		else:
			aspect_ratio = height / hi
			#min_width = min(width, int(wi * aspect_ratio))
			min_width = max(min(width, int(wi * aspect_ratio)), height // 2)
			assert min_width > 0 and height > 0
			input = cv2.resize(input, (min_width, height), interpolation=interpolation)
			if min_width < width:
				image_zeropadded = np.zeros((height, width) + input.shape[2:], dtype=input.dtype)
				image_zeropadded[:,:min_width] = input[:,:min_width]
				return image_zeropadded
			else:
				return input
		"""
		hi, wi = input.shape[:2]
		self.warn(hi, wi)
		aspect_ratio = height / hi
		#min_width = min(width, int(wi * aspect_ratio))
		min_width = max(min(width, int(wi * aspect_ratio)), height // 2)
		assert min_width > 0 and height > 0
		zeropadded = np.zeros((height, width) + input.shape[2:], dtype=input.dtype)
		zeropadded[:,:min_width] = cv2.resize(input, (min_width, height), interpolation=interpolation)
		return zeropadded
		"""
		return cv2.resize(input, (width, height), interpolation=interpolation)
		"""

	# REF [function] >> RunTimeTextLineDatasetBase._resize_by_pil() in text_line_data.py.
	def _resize_by_pil(self, input, height, width, *args, **kwargs):
		interpolation = Image.BICUBIC
		wi, hi = input.size
		self.warn(hi, wi)
		aspect_ratio = height / hi
		#min_width = min(width, int(wi * aspect_ratio))
		min_width = max(min(width, int(wi * aspect_ratio)), height // 2)
		assert min_width > 0 and height > 0
		zeropadded = Image.new(input.mode, (width, height), color=0)
		zeropadded.paste(input.resize((min_width, height), resample=interpolation), (0, 0, min_width, height))
		return zeropadded
		"""
		return input.resize((width, height), resample=interpolation)
		"""

	def _warn_about_small_image(self, height, width):
		if height < self.min_height_threshold:
			glogger.info('Too small image: The image height {} should be larger than or equal to {}.'.format(height, self.min_height_threshold))
		#if width < self.min_width_threshold:
		#	glogger.info('Too small image: The image width {} should be larger than or equal to {}.'.format(width, self.min_width_threshold))

class ResizeImageWithMaxWidth(object):
	def __init__(self, height, max_width, warn_about_small_image, is_pil=True):
		self.height, self.max_width = height, max_width
		self.resize_functor = self._resize_by_pil if is_pil else self._resize_by_opencv

		self.min_height_threshold, self.min_width_threshold = 20, 20
		self.warn = self._warn_about_small_image if warn_about_small_image else lambda *args, **kwargs: None

	def __call__(self, x):
		return self.resize_functor(x, self.height, self.max_width)

	def _resize_by_opencv(self, input, height, max_width, *args, **kwargs):
		interpolation = cv2.INTER_AREA
		hi, wi = input.shape[:2]
		self.warn(hi, wi)
		aspect_ratio = height / hi
		#min_width = min(max_width, int(wi * aspect_ratio))
		min_width = max(min(max_width, int(wi * aspect_ratio)), height // 2)
		assert min_width > 0 and height > 0
		return cv2.resize(input, (min_width, height), interpolation=interpolation)

	def _resize_by_pil(self, input, height, max_width, *args, **kwargs):
		interpolation = Image.BICUBIC
		wi, hi = input.size
		self.warn(hi, wi)
		aspect_ratio = height / hi
		#min_width = min(max_width, int(wi * aspect_ratio))
		min_width = max(min(max_width, int(wi * aspect_ratio)), height // 2)
		assert min_width > 0 and height > 0
		return input.resize((min_width, height), resample=interpolation)

	def _warn_about_small_image(self, height, width):
		if height < self.min_height_threshold:
			glogger.info('Too small image: The image height {} should be larger than or equal to {}.'.format(height, self.min_height_threshold))
		#if width < self.min_width_threshold:
		#	glogger.info('Too small image: The image width {} should be larger than or equal to {}.'.format(width, self.min_width_threshold))

class ToIntTensor(object):
	def __call__(self, lst):
		return torch.IntTensor(lst)

class MySubsetDataset(torch.utils.data.Dataset):
	def __init__(self, subset, transform=None, target_transform=None):
		self.subset = subset
		self.transform = transform
		self.target_transform = target_transform

	def __getitem__(self, idx):
		dat = list(self.subset[idx])
		if self.transform:
			dat[0] = self.transform(dat[0])
		if self.target_transform:
			dat[1] = self.target_transform(dat[1])
		return dat

	def __len__(self):
		return len(self.subset)

def create_char_data_loaders(char_type, label_converter, charset, num_train_examples_per_class, num_test_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_char_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])

	glogger.info('Start creating datasets...')
	start_time = time.time()
	if char_type == 'simple_char':
		chars = list(charset * num_train_examples_per_class)
		random.shuffle(chars)
		train_dataset = text_data.SimpleCharacterDataset(label_converter, chars, image_channel, font_list, font_size_interval, color_functor=color_functor, transform=train_transform)
		chars = list(charset * num_test_examples_per_class)
		random.shuffle(chars)
		test_dataset = text_data.SimpleCharacterDataset(label_converter, chars, image_channel, font_list, font_size_interval, color_functor=color_functor, transform=test_transform)
	elif char_type == 'noisy_char':
		chars = list(charset * num_train_examples_per_class)
		random.shuffle(chars)
		train_dataset = text_data.NoisyCharacterDataset(label_converter, chars, image_channel, char_clipping_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=train_transform)
		chars = list(charset * num_test_examples_per_class)
		random.shuffle(chars)
		test_dataset = text_data.NoisyCharacterDataset(label_converter, chars, image_channel, char_clipping_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=test_transform)
	elif char_type == 'file_based_char':
		if 'posix' == os.name:
			data_base_dir_path = '/home/sangwook/work/dataset'
		else:
			data_base_dir_path = 'D:/work/dataset'

		datasets = list()
		if True:
			# REF [function] >> generate_chars_from_chars74k_data() in chars74k_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/chars74k/English/Img/char_images.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# REF [function] >> generate_chars_from_e2e_mlt_data() in e2e_mlt_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/char_images_kr.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# REF [function] >> generate_chars_from_e2e_mlt_data() in e2e_mlt_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/char_images_en.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# REF [function] >> generate_chars_from_rrc_mlt_2019_data() in icdar_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/char_images_kr.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# REF [function] >> generate_chars_from_rrc_mlt_2019_data() in icdar_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/char_images_en.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
		assert datasets, 'NO Dataset'

		dataset = torch.utils.data.ConcatDataset(datasets)
		num_examples = len(dataset)
		num_train_examples = int(num_examples * train_test_ratio)

		train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
		train_dataset = MySubsetDataset(train_subset, transform=train_transform)
		test_dataset = MySubsetDataset(test_subset, transform=test_transform)
	else:
		raise ValueError('Invalid dataset type: {}'.format(char_type))
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def create_mixed_char_data_loaders(label_converter, charset, num_simple_char_examples_per_class, num_noisy_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_char_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	glogger.info('Start creating datasets...')
	start_time = time.time()
	datasets = list()
	if True:
		chars = list(charset * num_simple_char_examples_per_class)
		random.shuffle(chars)
		datasets.append(text_data.SimpleCharacterDataset(label_converter, chars, image_channel, font_list, font_size_interval, color_functor=color_functor))
	if True:
		chars = list(charset * num_noisy_examples_per_class)
		random.shuffle(chars)
		datasets.append(text_data.NoisyCharacterDataset(label_converter, chars, image_channel, char_clipping_ratio_interval, font_list, font_size_interval, color_functor=color_functor))
	if True:
		# REF [function] >> generate_chars_from_chars74k_data() in chars74k_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/chars74k/English/Img/char_images.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# REF [function] >> generate_chars_from_e2e_mlt_data() in e2e_mlt_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/char_images_kr.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# REF [function] >> generate_chars_from_e2e_mlt_data() in e2e_mlt_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/char_images_en.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# REF [function] >> generate_chars_from_rrc_mlt_2019_data() in icdar_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/char_images_kr.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# REF [function] >> generate_chars_from_rrc_mlt_2019_data() in icdar_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/char_images_en.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.FileBasedCharacterDataset(label_converter, image_label_info_filepath, image_channel, is_preloaded_image_used=is_preloaded_image_used))
	assert datasets, 'NO Dataset'

	dataset = torch.utils.data.ConcatDataset(datasets)
	num_examples = len(dataset)
	num_train_examples = int(num_examples * train_test_ratio)

	train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
	train_dataset = MySubsetDataset(train_subset, transform=train_transform)
	test_dataset = MySubsetDataset(test_subset, transform=test_transform)
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_word_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	train_target_transform = ToIntTensor()
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	glogger.info('Start creating datasets...')
	start_time = time.time()
	if word_type == 'simple_word':
		train_dataset = text_data.SimpleWordDataset(label_converter, wordset, num_train_examples, image_channel, max_word_len, font_list, font_size_interval, color_functor=color_functor, transform=train_transform, target_transform=train_target_transform)
		test_dataset = text_data.SimpleWordDataset(label_converter, wordset, num_test_examples, image_channel, max_word_len, font_list, font_size_interval, color_functor=color_functor, transform=test_transform, target_transform=test_target_transform)
	elif word_type == 'random_word':
		train_dataset = text_data.RandomWordDataset(label_converter, chars, num_train_examples, image_channel, max_word_len, word_len_interval, font_list, font_size_interval, color_functor=color_functor, transform=train_transform, target_transform=train_target_transform)
		test_dataset = text_data.RandomWordDataset(label_converter, chars, num_test_examples, image_channel, max_word_len, word_len_interval, font_list, font_size_interval, color_functor=color_functor, transform=test_transform, target_transform=test_target_transform)
	elif textline_type == 'aihub_word':
		if 'posix' == os.name:
			data_base_dir_path = '/home/sangwook/work/dataset'
		else:
			data_base_dir_path = 'D:/work/dataset'

		# AI-Hub printed text dataset.
		aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
		aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

		image_types_to_load = ['word']  # {'syllable', 'word', 'sentence'}.
		is_preloaded_image_used = False
		dataset = aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_word_len, is_preloaded_image_used)

		num_examples = len(dataset)
		num_train_examples = int(num_examples * train_test_ratio)

		train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
		train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
		test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	elif word_type == 'file_based_word':
		if 'posix' == os.name:
			data_base_dir_path = '/home/sangwook/work/dataset'
		else:
			data_base_dir_path = 'D:/work/dataset'

		datasets = list()
		if True:
			# E2E-MLT Korean dataset.
			# REF [function] >> generate_words_from_e2e_mlt_data() in e2e_mlt_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/word_images_kr.txt'
			is_preloaded_image_used = False
			datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# E2E-MLT English dataset.
			# REF [function] >> generate_words_from_e2e_mlt_data() in e2e_mlt_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/word_images_en.txt'
			is_preloaded_image_used = False
			datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# ICDAR RRC-MLT 2019 Korean dataset.
			# REF [function] >> generate_words_from_rrc_mlt_2019_data() in icdar_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/word_images_kr.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# ICDAR RRC-MLT 2019 English dataset.
			# REF [function] >> generate_words_from_rrc_mlt_2019_data() in icdar_data_test.py
			image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/word_images_en.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
		assert datasets, 'NO Dataset'

		dataset = torch.utils.data.ConcatDataset(datasets)
		num_examples = len(dataset)
		num_train_examples = int(num_examples * train_test_ratio)

		train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
		train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
		test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	else:
		raise ValueError('Invalid dataset type: {}'.format(word_type))
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_word_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	train_target_transform = ToIntTensor()
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	glogger.info('Start creating datasets...')
	start_time = time.time()
	datasets = list()
	if True:
		datasets.append(text_data.SimpleWordDataset(label_converter, wordset, num_simple_examples, image_channel, max_word_len, font_list, font_size_interval, color_functor=color_functor))
	if True:
		datasets.append(text_data.RandomWordDataset(label_converter, chars, num_random_examples, image_channel, max_word_len, word_len_interval, font_list, font_size_interval, color_functor=color_functor))
	if True:
		# AI-Hub printed text dataset.
		aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
		aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

		image_types_to_load = ['word']  # {'syllable', 'word', 'sentence'}.
		is_preloaded_image_used = False
		datasets.append(aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_word_len, is_preloaded_image_used))
	if True:
		# E2E-MLT Korean dataset.
		# REF [function] >> generate_words_from_e2e_mlt_data() in e2e_mlt_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/word_images_kr.txt'
		is_preloaded_image_used = False
		datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# E2E-MLT English dataset.
		# REF [function] >> generate_words_from_e2e_mlt_data() in e2e_mlt_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/e2e_mlt/word_images_en.txt'
		is_preloaded_image_used = False
		datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# ICDAR RRC-MLT 2019 Korean dataset.
		# REF [function] >> generate_words_from_rrc_mlt_2019_data() in icdar_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/word_images_kr.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# ICDAR RRC-MLT 2019 English dataset.
		# REF [function] >> generate_words_from_rrc_mlt_2019_data() in icdar_data_test.py
		image_label_info_filepath = data_base_dir_path + '/text/icdar_mlt_2019/word_images_en.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.InfoFileBasedWordDataset(label_converter, image_label_info_filepath, image_channel, max_word_len, is_preloaded_image_used=is_preloaded_image_used))
	assert datasets, 'NO Dataset'

	dataset = torch.utils.data.ConcatDataset(datasets)
	num_examples = len(dataset)
	num_train_examples = int(num_examples * train_test_ratio)

	train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
	train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
	test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def create_textline_data_loaders(textline_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_textline_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	train_target_transform = ToIntTensor()
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	glogger.info('Start creating datasets...')
	start_time = time.time()
	if textline_type == 'simple_textline':
		train_dataset = text_data.SimpleTextLineDataset(label_converter, wordset, num_train_examples, image_channel, max_textline_len, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=train_transform, target_transform=train_target_transform)
		test_dataset = text_data.SimpleTextLineDataset(label_converter, wordset, num_test_examples, image_channel, max_textline_len, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=test_transform, target_transform=test_target_transform)
	elif textline_type == 'random_textline':
		train_dataset = text_data.RandomTextLineDataset(label_converter, chars, num_train_examples, image_channel, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=train_transform, target_transform=train_target_transform)
		test_dataset = text_data.RandomTextLineDataset(label_converter, chars, num_test_examples, image_channel, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor, transform=test_transform, target_transform=test_target_transform)
	elif textline_type == 'trdg_textline':
		# REF [site] >> https://github.com/Belval/TextRecognitionDataGenerator
		font_size = image_height
		num_words = word_count_interval[1]  # TODO [check] >>
		is_variable_length = True

		generator_kwargs = {
			'skewing_angle': 0, 'random_skew': False,  # In degrees counter clockwise.
			#'blur': 0, 'random_blur': False,  # Blur radius.
			'blur': 2, 'random_blur': True,  # Blur radius.
			#'distorsion_type': 0, 'distorsion_orientation': 0,  # distorsion_type = 0 (no distortion), 1 (sin), 2 (cos), 3 (random). distorsion_orientation = 0 (vertical), 1 (horizontal), 2 (both).
			'distorsion_type': 3, 'distorsion_orientation': 2,  # distorsion_type = 0 (no distortion), 1 (sin), 2 (cos), 3 (random). distorsion_orientation = 0 (vertical), 1 (horizontal), 2 (both).
			'background_type': 0,  # background_type = 0 (Gaussian noise), 1 (plain white), 2 (quasicrystal), 3 (image).
			'width': -1,  # Specify a background width when width > 0.
			'alignment': 1,  # Align an image in a background image. alignment = 0 (left), 1 (center), the rest (right).
			'image_dir': None,  # Background image directory which is used when background_type = 3.
			'is_handwritten': False,
			#'text_color': '#282828',
			'text_color': '#000000,#FFFFFF',  # (0x00, 0x00, 0x00) ~ (0xFF, 0xFF, 0xFF).
			'orientation': 0,  # orientation = 0 (horizontal), 1 (vertical).
			'space_width': 1.0,  # The ratio of space width.
			'character_spacing': 0,  # Control space between characters (in pixels).
			'margins': (5, 5, 5, 5),  # For finer layout control. (top, left, bottom, right).
			'fit': False,  # For finer layout control. Specify if images and masks are cropped or not.
			'output_mask': False,  # Specify if a character-level mask for each image is outputted or not.
			'word_split': False  # Split on word instead of per-character. This is useful for ligature-based languages.
		}

		if True:
			lang = 'en'  # {'ar', 'cn', 'de', 'en', 'es', 'fr', 'hi'}.
			#font_filepaths = trdg.utils.load_fonts(lang)
			font_filepaths = list()

			is_randomly_generated = False
			train_dataset_en = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_train_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=train_transform, target_transform=train_target_transform, **generator_kwargs)
			test_dataset_en = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_test_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=test_transform, target_transform=test_target_transform, **generator_kwargs)
			is_randomly_generated = True
			train_dataset_en_rnd = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_train_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=train_transform, target_transform=train_target_transform, **generator_kwargs)
			test_dataset_en_rnd = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_test_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=test_transform, target_transform=test_target_transform, **generator_kwargs)
		if True:
			lang = 'kr'
			font_filepaths = construct_font(korean=True, english=False)
			font_filepaths, _ = zip(*font_filepaths)

			is_randomly_generated = False
			train_dataset_kr = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_train_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=train_transform, target_transform=train_target_transform, **generator_kwargs)
			test_dataset_kr = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_test_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=test_transform, target_transform=test_target_transform, **generator_kwargs)
			is_randomly_generated = True
			train_dataset_kr_rnd = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_train_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=train_transform, target_transform=train_target_transform, **generator_kwargs)
			test_dataset_kr_rnd = text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_test_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=test_transform, target_transform=test_target_transform, **generator_kwargs)
		train_dataset = torch.utils.data.ConcatDataset([train_dataset_en, train_dataset_en_rnd, train_dataset_kr, train_dataset_kr_rnd])
		test_dataset = torch.utils.data.ConcatDataset([test_dataset_en, test_dataset_en_rnd, test_dataset_kr, test_dataset_kr_rnd])
	elif textline_type == 'aihub_textline':
		# AI-Hub printed text dataset.
		aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
		aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

		image_types_to_load = ['sentence']  # {'syllable', 'word', 'sentence'}.
		#image_types_to_load = ['word', 'sentence']  # {'syllable', 'word', 'sentence'}.
		is_preloaded_image_used = False
		dataset = aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_textline_len, is_preloaded_image_used)

		num_examples = len(dataset)
		num_train_examples = int(num_examples * train_test_ratio)

		train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
		train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
		test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	elif textline_type == 'file_based_textline':
		if 'posix' == os.name:
			data_base_dir_path = '/home/sangwook/work/dataset'
		else:
			data_base_dir_path = 'D:/work/dataset'

		datasets = list()
		if True:
			# ICDAR 2019 SROIE dataset.
			is_preloaded_image_used = False
			image_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_train_text_line/*.jpg', recursive=False))
			labels_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_train_text_line/*.txt', recursive=False))
			datasets.append(text_data.ImageLabelFileBasedTextLineDataset(label_converter, image_filepaths, labels_filepaths, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
			if True:
				image_label_info_filepath = data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_test_text_line/labels.txt'
				datasets.append(text_data.InfoFileBasedTextLineDataset(label_converter, image_label_info_filepath, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# ePapyrus data.
			image_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/epapyrus/epapyrus_20190618/receipt_text_line/*.png', recursive=False))
			label_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/epapyrus/epapyrus_20190618/receipt_text_line/*.txt', recursive=False))
			is_preloaded_image_used = True
			datasets.append(text_data.ImageLabelFileBasedTextLineDataset(label_converter, image_filepaths, label_filepaths, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			# SiliconMinds data.
			image_label_info_filepath = data_base_dir_path + '/text/receipt/sminds/receipt_text_line/labels.txt'
			is_preloaded_image_used = True
			datasets.append(text_data.InfoFileBasedTextLineDataset(label_converter, image_label_info_filepath, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
		assert datasets, 'NO Dataset'

		dataset = torch.utils.data.ConcatDataset(datasets)
		num_examples = len(dataset)
		num_train_examples = int(num_examples * train_test_ratio)

		train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
		train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
		test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	else:
		raise ValueError('Invalid dataset type: {}'.format(textline_type))
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def create_mixed_textline_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, num_trdg_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers):
	# Load and normalize datasets.
	train_transform = torchvision.transforms.Compose([
		RandomAugment(create_textline_augmenter()),
		RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height_before_crop, image_width_before_crop),
		#torchvision.transforms.Resize((image_height_before_crop, image_width_before_crop)),
		#torchvision.transforms.RandomCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	train_target_transform = ToIntTensor()
	test_transform = torchvision.transforms.Compose([
		#RandomInvert(),
		#ConvertPILMode(mode='RGB'),
		ResizeImageToFixedSizeWithPadding(image_height, image_width),
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		#torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	glogger.info('Start creating datasets...')
	start_time = time.time()
	datasets = list()
	if True:
		datasets.append(text_data.SimpleTextLineDataset(label_converter, wordset, num_simple_examples, image_channel, max_textline_len, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor))
	if True:
		datasets.append(text_data.RandomTextLineDataset(label_converter, chars, num_random_examples, image_channel, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor=color_functor))
	if True:
		# REF [site] >> https://github.com/Belval/TextRecognitionDataGenerator
		font_size = image_height
		num_words = word_count_interval[1]  # TODO [check] >>
		is_variable_length = True

		generator_kwargs = {
			'skewing_angle': 0, 'random_skew': False,  # In degrees counter clockwise.
			#'blur': 0, 'random_blur': False,  # Blur radius.
			'blur': 2, 'random_blur': True,  # Blur radius.
			#'distorsion_type': 0, 'distorsion_orientation': 0,  # distorsion_type = 0 (no distortion), 1 (sin), 2 (cos), 3 (random). distorsion_orientation = 0 (vertical), 1 (horizontal), 2 (both).
			'distorsion_type': 3, 'distorsion_orientation': 2,  # distorsion_type = 0 (no distortion), 1 (sin), 2 (cos), 3 (random). distorsion_orientation = 0 (vertical), 1 (horizontal), 2 (both).
			'background_type': 0,  # background_type = 0 (Gaussian noise), 1 (plain white), 2 (quasicrystal), 3 (image).
			'width': -1,  # Specify a background width when width > 0.
			'alignment': 1,  # Align an image in a background image. alignment = 0 (left), 1 (center), the rest (right).
			'image_dir': None,  # Background image directory which is used when background_type = 3.
			'is_handwritten': False,
			#'text_color': '#282828',
			'text_color': '#000000,#FFFFFF',  # (0x00, 0x00, 0x00) ~ (0xFF, 0xFF, 0xFF).
			'orientation': 0,  # orientation = 0 (horizontal), 1 (vertical).
			'space_width': 1.0,  # The ratio of space width.
			'character_spacing': 0,  # Control space between characters (in pixels).
			'margins': (5, 5, 5, 5),  # For finer layout control. (top, left, bottom, right).
			'fit': False,  # For finer layout control. Specify if images and masks are cropped or not.
			'output_mask': False,  # Specify if a character-level mask for each image is outputted or not.
			'word_split': False  # Split on word instead of per-character. This is useful for ligature-based languages.
		}

		if True:
			lang = 'en'  # {'ar', 'cn', 'de', 'en', 'es', 'fr', 'hi'}.
			#font_filepaths = trdg.utils.load_fonts(lang)
			font_filepaths = list()

			is_randomly_generated = False
			datasets.append(text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_trdg_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=None, target_transform=None, **generator_kwargs))
			is_randomly_generated = True
			datasets.append(text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_trdg_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=None, target_transform=None, **generator_kwargs))
		if True:
			lang = 'kr'
			font_filepaths = construct_font(korean=True, english=False)
			font_filepaths, _ = zip(*font_filepaths)

			is_randomly_generated = False
			datasets.append(text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_trdg_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=None, target_transform=None, **generator_kwargs))
			is_randomly_generated = True
			datasets.append(text_data.TextRecognitionDataGeneratorTextLineDataset(label_converter, lang, num_trdg_examples // 4, image_channel, max_textline_len, font_filepaths, font_size, num_words, is_variable_length, is_randomly_generated, transform=None, target_transform=None, **generator_kwargs))
	if True:
		# AI-Hub printed text dataset.
		aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
		aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

		image_types_to_load = ['sentence']  # {'syllable', 'word', 'sentence'}.
		#image_types_to_load = ['word', 'sentence']  # {'syllable', 'word', 'sentence'}.
		is_preloaded_image_used = False
		datasets.append(aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_textline_len, is_preloaded_image_used))
	if True:
		# ICDAR 2019 SROIE dataset.
		is_preloaded_image_used = False
		image_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_train_text_line/*.jpg', recursive=False))
		labels_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_train_text_line/*.txt', recursive=False))
		datasets.append(text_data.ImageLabelFileBasedTextLineDataset(label_converter, image_filepaths, labels_filepaths, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
		if True:
			image_label_info_filepath = data_base_dir_path + '/text/receipt/icdar2019_sroie/task1_test_text_line/labels.txt'
			datasets.append(text_data.InfoFileBasedTextLineDataset(label_converter, image_label_info_filepath, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# ePapyrus data.
		image_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/epapyrus/epapyrus_20190618/receipt_text_line/*.png', recursive=False))
		label_filepaths = sorted(glob.glob(data_base_dir_path + '/text/receipt/epapyrus/epapyrus_20190618/receipt_text_line/*.txt', recursive=False))
		is_preloaded_image_used = True
		datasets.append(text_data.ImageLabelFileBasedTextLineDataset(label_converter, image_filepaths, label_filepaths, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
	if True:
		# SiliconMinds data.
		image_label_info_filepath = data_base_dir_path + '/text/receipt/sminds/receipt_text_line/labels.txt'
		is_preloaded_image_used = True
		datasets.append(text_data.InfoFileBasedTextLineDataset(label_converter, image_label_info_filepath, image_channel, max_textline_len, is_preloaded_image_used=is_preloaded_image_used))
	assert datasets, 'NO Dataset'

	dataset = torch.utils.data.ConcatDataset(datasets)
	num_examples = len(dataset)
	num_train_examples = int(num_examples * train_test_ratio)

	train_subset, test_subset = torch.utils.data.random_split(dataset, [num_train_examples, num_examples - num_train_examples])
	train_dataset = MySubsetDataset(train_subset, transform=train_transform, target_transform=train_target_transform)
	test_dataset = MySubsetDataset(test_subset, transform=test_transform, target_transform=test_target_transform)
	glogger.info('End creating datasets: {} secs.'.format(time.time() - start_time))
	glogger.info('#train examples = {}, #test examples = {}.'.format(len(train_dataset), len(test_dataset)))

	#--------------------
	glogger.info('Start creating data loaders...')
	start_time = time.time()
	train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	glogger.info('End creating data loaders: {} secs.'.format(time.time() - start_time))

	return train_dataloader, test_dataloader

def concatenate_labels(labels, eos_id, lengths=None):
	concat_labels = list()
	if lengths == None:
		for lbl in labels:
			try:
				concat_labels.append(lbl[:lbl.index(eos_id)+1])
			except ValueError as ex:
				concat_labels.append(lbl)
	else:
		for lbl, ll in zip(labels, lengths):
			concat_labels.append(lbl[:ll])
	return list(itertools.chain(*concat_labels))

def show_image(img):
	img = img / 2 + 0.5  # Unnormalize.
	npimg = img.numpy()
	plt.imshow(np.transpose(npimg, (1, 2, 0)))
	plt.show()

def show_char_data_info(dataloader, label_converter, visualize=True, mode='Train'):
	dataiter = iter(dataloader)
	images, labels = dataiter.next()
	images_np, labels_np = images.numpy(), labels.numpy()

	glogger.info('{} image: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(mode, images_np.shape, images_np.dtype, np.min(images_np), np.max(images_np)))
	glogger.info('{} label: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(mode, labels_np.shape, labels_np.dtype, np.min(labels_np), np.max(labels_np)))

	if visualize:
		glogger.info('Labels: {}.'.format(' '.join(label_converter.decode(labels_np))))
		show_image(torchvision.utils.make_grid(images))

def show_text_data_info(dataloader, label_converter, visualize=True, mode='Train'):
	dataiter = iter(dataloader)
	images, labels, label_lens = dataiter.next()
	images_np, labels_np, label_lens_np = images.numpy(), labels.numpy(), label_lens.numpy()

	glogger.info('{} image: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(mode, images_np.shape, images_np.dtype, np.min(images_np), np.max(images_np)))
	glogger.info('{} label: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(mode, labels_np.shape, labels_np.dtype, np.min(labels_np), np.max(labels_np)))
	glogger.info('{} label length: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(mode, label_lens_np.shape, label_lens_np.dtype, np.min(label_lens_np), np.max(label_lens_np)))

	if visualize:
		#glogger.info('Labels: {}.'.format(' '.join([label_converter.decode(lbl) for lbl in images_np])))
		for idx, (lbl, ll) in enumerate(zip(labels_np, label_lens_np)):
			glogger.info('Label #{} (len = {}): {} (int), {} (str).'.format(idx, ll, lbl, label_converter.decode(lbl)))
		show_image(torchvision.utils.make_grid(images))

def show_per_char_accuracy(correct_char_class_count, total_char_class_count, classes, num_classes, show_acc_per_char=False):
	#for idx in range(num_classes):
	#	glogger.info('Accuracy of {:5s} = {:2d} %.'.format(classes[idx], 100 * correct_char_class_count[idx] / total_char_class_count[idx] if total_char_class_count[idx] > 0 else -1))
	accuracies = [100 * correct_char_class_count[idx] / total_char_class_count[idx] if total_char_class_count[idx] > 0 else -1 for idx in range(num_classes)]
	#glogger.info('Accuracy: {}.'.format(accuracies))
	hist, bin_edges = np.histogram(accuracies, bins=range(-1, 101), density=False)
	#hist, bin_edges = np.histogram(accuracies, bins=range(0, 101), density=False)
	#glogger.info('Per-character accuracy histogram: {}.'.format({bb: hh for bb, hh in zip(bin_edges, hist)}))
	glogger.info('Per-character accuracy histogram: {}.'.format({bb: hh for bb, hh in zip(bin_edges, hist) if hh > 0}))

	if show_acc_per_char:
		valid_accuracies = [100 * correct_char_class_count[idx] / total_char_class_count[idx] for idx in range(num_classes) if total_char_class_count[idx] > 0]
		acc_thresh = 98
		glogger.info('Per-character accuracy: min = {}, max = {}.'.format(np.min(valid_accuracies), np.max(valid_accuracies)))
		glogger.info('Per-character accuracy (< {}) = {}.'.format(acc_thresh, {classes[idx]: round(acc, 2) for idx, acc in sorted(enumerate(valid_accuracies), key=lambda x: x[1]) if acc < acc_thresh}))

def train_char_recognition_model(model, train_forward_functor, criterion, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler=None, max_gradient_norm=None, model_params=None, device='cpu'):
	best_measure = 0.0
	best_model_filepath = None
	for epoch in range(num_epochs):  # Loop over the dataset multiple times.
		start_time = time.time()
		model.train()
		running_loss = 0.0
		for idx, batch in enumerate(train_dataloader):
			# Zero the parameter gradients.
			optimizer.zero_grad()

			# Forward + backward + optimize.
			loss = train_forward_functor(model, batch, device)
			loss.backward()
			if max_gradient_norm: torch.nn.utils.clip_grad_norm_(model_params, max_norm=max_gradient_norm)  # Gradient clipping.
			optimizer.step()

			# Print statistics.
			running_loss += loss.item()
			if idx % log_print_freq == (log_print_freq - 1):
				glogger.info('[{}, {:5d}] loss = {:.6g}: {:.3f} secs.'.format(epoch + 1, idx + 1, running_loss / log_print_freq, time.time() - start_time))
				running_loss = 0.0

			sys.stdout.flush()
			time.sleep(0)
		glogger.info('Epoch {} completed: {} secs.'.format(epoch + 1, time.time() - start_time))

		glogger.info('Start evaluating...')
		start_time = time.time()
		model.eval()
		acc = evaluate_char_recognition_model(model, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=False, is_error_cases_saved=False, device=device)
		glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

		if scheduler: scheduler.step()

		if acc >= best_measure:
			ckpt_fpath = model_filepath_format.format('_acc{:.4f}_epoch{}'.format(acc, epoch + 1))
			# Save a checkpoint.
			save_model(ckpt_fpath, model)
			best_measure = acc
			best_model_filepath = ckpt_fpath

	return model, best_model_filepath

def train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler=None, max_gradient_norm=None, model_params=None, device='cpu'):
	best_measure = 0.0
	best_model_filepath = None
	for epoch in range(num_epochs):  # Loop over the dataset multiple times.
		start_time = time.time()
		model.train()
		running_loss = 0.0
		for idx, batch in enumerate(train_dataloader):
			# Zero the parameter gradients.
			optimizer.zero_grad()

			# Forward + backward + optimize.
			loss = train_forward_functor(model, criterion, batch, device)
			loss.backward()
			if max_gradient_norm: torch.nn.utils.clip_grad_norm_(model_params, max_norm=max_gradient_norm)  # Gradient clipping.
			optimizer.step()

			# Print statistics.
			running_loss += loss.item()
			if idx % log_print_freq == (log_print_freq - 1):
				glogger.info('[{}, {:5d}] loss = {:.6g}: {:.3f} secs.'.format(epoch + 1, idx + 1, running_loss / log_print_freq, time.time() - start_time))
				running_loss = 0.0

			sys.stdout.flush()
			time.sleep(0)
		glogger.info('Epoch {} completed: {} secs.'.format(epoch + 1, time.time() - start_time))

		glogger.info('Start evaluating...')
		start_time = time.time()
		model.eval()
		acc = evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=False, error_cases_dir_path=None, device=device)
		glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

		if scheduler: scheduler.step()

		if acc >= best_measure:
			ckpt_fpath = model_filepath_format.format('_acc{:.4f}_epoch{}'.format(acc, epoch + 1))
			# Save a checkpoint.
			save_model(ckpt_fpath, model)
			best_measure = acc
			best_model_filepath = ckpt_fpath

	return model, best_model_filepath

def evaluate_char_recognition_model(model, label_converter, dataloader, is_case_sensitive=False, show_acc_per_char=False, is_error_cases_saved=False, device='cpu'):
	classes, num_classes = label_converter.tokens, label_converter.num_tokens

	error_cases_dir_path = './char_error_cases'
	if is_error_cases_saved:
		os.makedirs(error_cases_dir_path, exist_ok=True)

	correct_char_count, total_char_count = 0, 0
	correct_char_class_count, total_char_class_count = [0] * num_classes, [0] * num_classes
	error_cases = list()
	error_idx = 0
	is_first = True
	with torch.no_grad():
		for images, labels in dataloader:
			predictions = model(images.to(device))

			_, predictions = torch.max(predictions, 1)
			predictions = predictions.cpu().numpy()
			gts = labels.numpy()

			for gl, pl in zip(gts, predictions):
				if gl == pl: correct_char_class_count[gl] += 1
				total_char_class_count[gl] += 1

			gts, predictions = label_converter.decode(gts), label_converter.decode(predictions)
			gts_case, predictions_case = (gts, predictions) if is_case_sensitive else (gts.lower(), predictions.lower())

			total_char_count += max(len(gts), len(predictions))
			#correct_char_count += (gts_case == predictions_case).sum()
			correct_char_count += len(list(filter(lambda gp: gp[0] == gp[1], zip(gts_case, predictions_case))))

			if is_error_cases_saved:
				images_np = images.numpy()
				if images_np.ndim == 4: images_np = images_np.transpose(0, 2, 3, 1)
				#minval, maxval = np.min(images_np), np.max(images_np)
				minval, maxval = -1, 1
				images_np = np.round((images_np - minval) * 255 / (maxval - minval)).astype(np.uint8)

				for img, gt, pred, gt_case, pred_case in zip(images_np.numpy(), gts, predictions, gts_case, predictions_case):
					if gt_case != pred_case:
						cv2.imwrite(os.path.join(error_cases_dir_path, 'image_{}.png'.format(error_idx)), img)
						error_cases.append((gt, pred))
						error_idx += 1

			if is_first:
				# Show images.
				#show_image(torchvision.utils.make_grid(images))

				#glogger.info('G/T:        {}.'.format(' '.join(gts)))
				#glogger.info('Prediction: {}.'.format(' '.join(predictions)))
				#for gt, pred in zip(gts, predictions):
				#	glogger.info('G/T - prediction: {}, {}.'.format(gt, pred))
				glogger.info('G/T - prediction:\n{}.'.format([(gt, pred) for gt, pred in zip(gts, predictions)]))

				is_first = False

	if is_error_cases_saved:
		err_fpath = os.path.join(error_cases_dir_path, 'error_cases.txt')
		try:
			with open(err_fpath, 'w', encoding='UTF8') as fd:
				for idx, (gt, pred) in enumerate(error_cases):
					fd.write('{}\t{}\t{}\n'.format(idx, gt, pred))
		except UnicodeDecodeError as ex:
			glogger.warning('Unicode decode error in {}: {}.'.format(err_fpath, ex))
		except FileNotFoundError as ex:
			glogger.warning('File not found, {}: {}.'.format(err_fpath, ex))

	show_per_char_accuracy(correct_char_class_count, total_char_class_count, classes, num_classes, show_acc_per_char)
	glogger.info('Char accuracy = {} / {} = {}.'.format(correct_char_count, total_char_count, correct_char_count / total_char_count))

	return correct_char_count / total_char_count

def compute_simple_matching_accuracy(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path=None, error_idx=0):
	is_error_cases_saved = error_cases_dir_path is not None

	total_text_count = len(outputs)
	correct_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count = 0, 0, 0, 0, 0
	correct_char_class_count, total_char_class_count = [0] * label_converter.num_tokens, [0] * label_converter.num_tokens
	error_cases = list()
	for img, gt, pred in zip(inputs, outputs, predictions):
		for gl, pl in zip(gt, pred):
			if gl == pl: correct_char_class_count[gl] += 1
			total_char_class_count[gl] += 1

		gt, pred = label_converter.decode(gt), label_converter.decode(pred)
		gt_case, pred_case = (gt, pred) if is_case_sensitive else (gt.lower(), pred.lower())

		if gt_case == pred_case:
			correct_text_count += 1
		elif is_error_cases_saved:
			cv2.imwrite(os.path.join(error_cases_dir_path, 'image_{}.png'.format(error_idx)), img)
			error_cases.append((gt, pred))
			error_idx += 1

		gt_words, pred_words = gt_case.split(' '), pred_case.split(' ')
		total_word_count += max(len(gt_words), len(pred_words))
		correct_word_count += len(list(filter(lambda gp: gp[0] == gp[1], zip(gt_words, pred_words))))

		total_char_count += max(len(gt), len(pred))
		correct_char_count += len(list(filter(lambda gp: gp[0] == gp[1], zip(gt_case, pred_case))))

	return correct_text_count, total_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count, correct_char_class_count, total_char_class_count, error_cases

def compute_sequence_matching_ratio(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path=None, error_idx=0):
	import difflib

	isjunk = None
	#isjunk = lambda x: x == '\n\r'
	#isjunk = lambda x: x == ' \t\n\r'

	is_error_cases_saved = error_cases_dir_path is not None

	total_matching_ratio = 0
	correct_char_class_count, total_char_class_count = [0] * label_converter.num_tokens, [0] * label_converter.num_tokens
	error_cases = list()
	for img, gt, pred in zip(inputs, outputs, predictions):
		matcher = difflib.SequenceMatcher(isjunk, gt, pred)
		#matcher = difflib.SequenceMatcher(isjunk, gt_case, pred_case)
		for mth in matcher.get_matching_blocks():
			if mth.size != 0:
				for idx in range(mth.a, mth.a + mth.size):
					correct_char_class_count[gt[idx]] += 1
		for gl in gt:
			total_char_class_count[gl] += 1

		gt, pred = label_converter.decode(gt), label_converter.decode(pred)
		gt_case, pred_case = (gt, pred) if is_case_sensitive else (gt.lower(), pred.lower())

		matching_ratio = difflib.SequenceMatcher(isjunk, gt_case, pred_case).ratio()
		total_matching_ratio += matching_ratio
		if matching_ratio < 1 and is_error_cases_saved:
			cv2.imwrite(os.path.join(error_cases_dir_path, 'image_{}.png'.format(error_idx)), img)
			error_cases.append((gt, pred))
			error_idx += 1

	return total_matching_ratio, correct_char_class_count, total_char_class_count, error_cases

def evaluate_text_recognition_model(model, infer_functor, label_converter, dataloader, is_case_sensitive=False, show_acc_per_char=False, error_cases_dir_path=None, device='cpu'):
	is_error_cases_saved = error_cases_dir_path is not None
	if is_error_cases_saved:
		os.makedirs(error_cases_dir_path, exist_ok=True)

	classes, num_classes = label_converter.tokens, label_converter.num_tokens

	is_sequence_matching_ratio_used, is_simple_matching_accuracy_used = True, True
	total_matching_ratio, num_examples = 0, 0
	correct_text_count, total_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count = 0, 0, 0, 0, 0, 0
	correct_char_class_count, total_char_class_count = [0] * num_classes, [0] * num_classes
	error_cases = list()
	error_idx = 0
	is_first = True
	with torch.no_grad():
		for images, labels, label_lens in dataloader:
			predictions, gts = infer_functor(model, images, labels, label_lens, device)

			images_np = images.numpy()
			if images_np.ndim == 4: images_np = images_np.transpose(0, 2, 3, 1)
			#minval, maxval = np.min(images_np), np.max(images_np)
			minval, maxval = -1, 1
			images_np = np.round((images_np - minval) * 255 / (maxval - minval)).astype(np.uint8)

			if is_sequence_matching_ratio_used:
				batch_total_matching_ratio, batch_correct_char_class_count, batch_total_char_class_count, batch_error_cases = compute_sequence_matching_ratio(images_np, gts, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=error_idx)
				total_matching_ratio += batch_total_matching_ratio
				num_examples += len(images_np)
			if is_simple_matching_accuracy_used:
				batch_correct_text_count, batch_total_text_count, batch_correct_word_count, batch_total_word_count, batch_correct_char_count, batch_total_char_count, batch_correct_char_class_count, batch_total_char_class_count, batch_error_cases = compute_simple_matching_accuracy(images_np, gts, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=error_idx)
				correct_text_count += batch_correct_text_count
				total_text_count += batch_total_text_count
				correct_word_count += batch_correct_word_count
				total_word_count += batch_total_word_count
				correct_char_count += batch_correct_char_count
				total_char_count += batch_total_char_count
			correct_char_class_count = list(map(operator.add, correct_char_class_count, batch_correct_char_class_count))
			total_char_class_count = list(map(operator.add, total_char_class_count, batch_total_char_class_count))
			error_idx += len(batch_error_cases)
			error_cases += batch_error_cases

			if is_first:
				# Show images.
				#show_image(torchvision.utils.make_grid(images))

				#glogger.info('G/T:        {}.'.format(' '.join([label_converter.decode(lbl) for lbl in gts])))
				#glogger.info('Prediction: {}.'.format(' '.join([label_converter.decode(lbl) for lbl in predictions])))
				#for gt, pred in zip(gts, predictions):
				#	glogger.info('G/T - prediction: {}, {}.'.format(label_converter.decode(gt), label_converter.decode(pred)))
				glogger.info('G/T - prediction:\n{}.'.format([(label_converter.decode(gt), label_converter.decode(pred)) for gt, pred in zip(gts, predictions)]))

				is_first = False

	if is_error_cases_saved:
		err_fpath = os.path.join(error_cases_dir_path, 'error_cases.txt')
		try:
			with open(err_fpath, 'w', encoding='UTF8') as fd:
				for idx, (gt, pred) in enumerate(error_cases):
					fd.write('{}\t{}\t{}\n'.format(idx, gt, pred))
		except UnicodeDecodeError as ex:
			glogger.warning('Unicode decode error in {}: {}.'.format(err_fpath, ex))
		except FileNotFoundError as ex:
			glogger.warning('File not found, {}: {}.'.format(err_fpath, ex))

	show_per_char_accuracy(correct_char_class_count, total_char_class_count, classes, num_classes, show_acc_per_char)
	if is_sequence_matching_ratio_used:
		#num_examples = len(dataloader)
		ave_matching_ratio = total_matching_ratio / num_examples if num_examples > 0 else 0
		glogger.info('Average sequence matching ratio = {}.'.format(ave_matching_ratio))
	if is_simple_matching_accuracy_used:
		glogger.info('Text: Simple matching accuracy = {} / {} = {}.'.format(correct_text_count, total_text_count, correct_text_count / total_text_count if total_text_count > 0 else 0))
		glogger.info('Word: Simple matching accuracy = {} / {} = {}.'.format(correct_word_count, total_word_count, correct_word_count / total_word_count if total_word_count > 0 else 0))
		glogger.info('Char: Simple matching accuracy = {} / {} = {}.'.format(correct_char_count, total_char_count, correct_char_count / total_char_count if total_char_count > 0 else 0))

	if is_sequence_matching_ratio_used:
		return ave_matching_ratio
	elif is_simple_matching_accuracy_used:
		return correct_char_count / total_char_count if total_char_count > 0 else 0
	else: return -1

def infer_using_text_recognition_model(model, infer_functor, label_converter, inputs, outputs=None, batch_size=None, is_case_sensitive=False, show_acc_per_char=False, error_cases_dir_path=None, device='cpu'):
	if batch_size is None: batch_size = len(inputs)

	with torch.no_grad():
		predictions = list()
		for idx in range(0, len(inputs), batch_size):
			predictions.append(infer_functor(model, inputs[idx:idx+batch_size], device=device)[0])
	inputs, predictions = inputs.numpy(), np.vstack(predictions)
	glogger.info('Inference: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(predictions.shape, predictions.dtype, np.min(predictions), np.max(predictions)))

	if outputs is None:
		num_iters = 0
		for idx in range(0, len(predictions), batch_size):
			# Show images.
			#show_image(torchvision.utils.make_grid(inputs[idx:idx+batch_size]))

			glogger.info('Prediction:\n{}.'.format('\n'.join([label_converter.decode(pred) for pred in predictions[idx:idx+batch_size]])))

			num_iters += 1
			if num_iters >= 5: break
	else:
		if error_cases_dir_path:
			os.makedirs(error_cases_dir_path, exist_ok=True)

		outputs = outputs.numpy()

		num_iters = 0
		for idx in range(0, len(predictions), batch_size):
			inps, outps, preds = inputs[idx:idx+batch_size], outputs[idx:idx+batch_size], predictions[idx:idx+batch_size]

			# Show images.
			#show_image(torchvision.utils.make_grid(inps))

			#glogger.info('G/T:        {}.'.format(' '.join([label_converter.decode(lbl) for lbl in outps])))
			#glogger.info('Prediction: {}.'.format(' '.join([label_converter.decode(lbl) for lbl in preds])))
			#for gt, pred in zip(outps, preds):
			#	glogger.info('G/T - prediction: {}, {}.'.format(label_converter.decode(gt), label_converter.decode(pred)))
			glogger.info('G/T - prediction:\n{}.'.format([(label_converter.decode(gt), label_converter.decode(pred)) for gt, pred in zip(outps, preds)]))

			num_iters += 1
			if num_iters >= 5: break

		#--------------------
		if inputs.ndim == 4: inputs = inputs.transpose(0, 2, 3, 1)
		#minval, maxval = np.min(inputs), np.max(inputs)
		minval, maxval = -1, 1
		inputs = np.round((inputs - minval) * 255 / (maxval - minval)).astype(np.uint8)

		is_sequence_matching_ratio_used, is_simple_matching_accuracy_used = True, True
		if is_sequence_matching_ratio_used:
			total_matching_ratio, correct_char_class_count, total_char_class_count, error_cases = compute_sequence_matching_ratio(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=0)
		if is_simple_matching_accuracy_used:
			correct_text_count, total_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count, correct_char_class_count, total_char_class_count, error_cases = compute_simple_matching_accuracy(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=0)

		if error_cases_dir_path:
			err_fpath = os.path.join(error_cases_dir_path, 'error_cases.txt')
			try:
				with open(err_fpath, 'w', encoding='UTF8') as fd:
					for idx, (gt, pred) in enumerate(error_cases):
						fd.write('{}\t{}\t{}\n'.format(idx, gt, pred))
			except UnicodeDecodeError as ex:
				glogger.warning('Unicode decode error in {}: {}.'.format(err_fpath, ex))
			except FileNotFoundError as ex:
				glogger.warning('File not found, {}: {}.'.format(err_fpath, ex))

		show_per_char_accuracy(correct_char_class_count, total_char_class_count, label_converter.tokens, label_converter.num_tokens, show_acc_per_char)
		if is_sequence_matching_ratio_used:
			#num_examples = len(outputs)
			num_examples = min(len(inputs), len(outputs), len(predictions))
			ave_matching_ratio = total_matching_ratio / num_examples if num_examples > 0 else 0
			glogger.info('Average sequence matching ratio = {}.'.format(ave_matching_ratio))
		if is_simple_matching_accuracy_used:
			glogger.info('Text: Simple matching accuracy = {} / {} = {}.'.format(correct_text_count, total_text_count, correct_text_count / total_text_count if total_text_count > 0 else 0))
			glogger.info('Word: Simple matching accuracy = {} / {} = {}.'.format(correct_word_count, total_word_count, correct_word_count / total_word_count if total_word_count > 0 else 0))
			glogger.info('Char: Simple matching accuracy = {} / {} = {}.'.format(correct_char_count, total_char_count, correct_char_count / total_char_count if total_char_count > 0 else 0))

def infer_one_by_one_using_text_recognition_model(model, infer_functor, label_converter, inputs, outputs=None, is_case_sensitive=False, show_acc_per_char=False, error_cases_dir_path=None, device='cpu'):
	num_examples_to_show = 50

	with torch.no_grad():
		predictions = list(infer_functor(model, inp, device=device)[0][0] for inp in inputs)
	#glogger.info('Inference: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(predictions.shape, predictions.dtype, np.min(predictions), np.max(predictions)))

	if outputs is None:
		glogger.info('Prediction:\n{}.'.format('\n'.join([label_converter.decode(pred) for pred in predictions[:num_examples_to_show]])))
	else:
		minval, maxval = -1, 1
		def transform(img):
			#minval, maxval = np.min(img), np.max(img)
			return np.round((img.transpose(1, 2, 0) - minval) * 255 / (maxval - minval)).astype(np.uint8)

		inputs = list(transform(inp[0].numpy()) for inp in inputs)
		outputs = list(outp[0].numpy() for outp in outputs)

		#glogger.info('G/T:        {}.'.format(' '.join([label_converter.decode(lbl) for lbl in outputs[:num_examples_to_show]])))
		#glogger.info('Prediction: {}.'.format(' '.join([label_converter.decode(lbl) for lbl in predictions[:num_examples_to_show]])))
		#for gt, pred in zip(outputs[:num_examples_to_show], predictions[:num_examples_to_show]):
		#	glogger.info('G/T - prediction: {}, {}.'.format(label_converter.decode(gt), label_converter.decode(pred)))
		glogger.info('G/T - prediction:\n{}.'.format([(label_converter.decode(gt), label_converter.decode(pred)) for gt, pred in zip(outputs[:num_examples_to_show], predictions[:num_examples_to_show])]))

		#--------------------
		is_sequence_matching_ratio_used, is_simple_matching_accuracy_used = True
		if is_sequence_matching_ratio_used:
			total_matching_ratio, correct_char_class_count, total_char_class_count, error_cases = compute_sequence_matching_ratio(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=0)
		if is_simple_matching_accuracy_used:
			correct_text_count, total_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count, correct_char_class_count, total_char_class_count, error_cases = compute_simple_matching_accuracy(inputs, outputs, predictions, label_converter, is_case_sensitive, show_acc_per_char, error_cases_dir_path, error_idx=0)

		if error_cases_dir_path:
			err_fpath = os.path.join(error_cases_dir_path, 'error_cases.txt')
			try:
				with open(err_fpath, 'w', encoding='UTF8') as fd:
					for idx, (gt, pred) in enumerate(error_cases):
						fd.write('{}\t{}\t{}\n'.format(idx, gt, pred))
			except UnicodeDecodeError as ex:
				glogger.warning('Unicode decode error in {}: {}.'.format(err_fpath, ex))
			except FileNotFoundError as ex:
				glogger.warning('File not found, {}: {}.'.format(err_fpath, ex))

		show_per_char_accuracy(correct_char_class_count, total_char_class_count, label_converter.tokens, label_converter.num_tokens, show_acc_per_char)
		if is_sequence_matching_ratio_used:
			#num_examples = len(outputs)
			num_examples = min(len(inputs), len(outputs), len(predictions))
			ave_matching_ratio = total_matching_ratio / num_examples if num_examples > 0 else 0
			glogger.info('Average sequence matching ratio = {}.'.format(ave_matching_ratio))
		if is_simple_matching_accuracy_used:
			glogger.info('Text: Simple matching accuracy = {} / {} = {}.'.format(correct_text_count, total_text_count, correct_text_count / total_text_count if total_text_count > 0 else 0))
			glogger.info('Word: Simple matching accuracy = {} / {} = {}.'.format(correct_word_count, total_word_count, correct_word_count / total_word_count if total_word_count > 0 else 0))
			glogger.info('Char: Simple matching accuracy = {} / {} = {}.'.format(correct_char_count, total_char_count, correct_char_count / total_char_count if total_char_count > 0 else 0))

def build_char_model(label_converter, image_channel, loss_type, lang):
	model_name = 'ResNet'  # {'VGG', 'ResNet', 'RCNN'}.
	input_channel, output_channel = image_channel, 1024

	# Define a loss function.
	if loss_type == 'xent':
		criterion = torch.nn.CrossEntropyLoss()
	elif loss_type == 'nll':
		criterion = torch.nn.NLLLoss(reduction='sum')
	else:
		raise ValueError('Invalid loss type, {}'.format(loss_type))

	def train_forward(model, criterion, batch, device):
		inputs, outputs = batch
		inputs, outputs = inputs.to(device), outputs.to(device)

		model_outputs = model(inputs)
		return criterion(model_outputs, outputs)

	import rare.model_char
	model = rare.model_char.create_model(model_name, input_channel, output_channel, label_converter.num_tokens)

	return model, train_forward, criterion

def build_char_mixup_model(label_converter, image_channel, loss_type, lang):
	model_name = 'ResNet'  # {'VGG', 'ResNet', 'RCNN'}.
	input_channel, output_channel = image_channel, 1024

	mixup_input, mixup_hidden, mixup_alpha = True, True, 2.0
	cutout, cutout_size = True, 4

	# Define a loss function.
	if loss_type == 'xent':
		criterion = torch.nn.CrossEntropyLoss()
	elif loss_type == 'nll':
		criterion = torch.nn.NLLLoss(reduction='sum')
	else:
		raise ValueError('Invalid loss type, {}'.format(loss_type))

	def train_forward(model, criterion, batch, device):
		inputs, outputs = batch
		inputs, outputs = inputs.to(device), outputs.to(device)

		model_outputs, outputs = model(inputs, outputs, mixup_input, mixup_hidden, mixup_alpha, cutout, cutout_size, device)
		return criterion(model_outputs, torch.argmax(outputs, dim=1))

	# REF [function] >> mnist_predefined_mixup_test() in ${SWL_PYTHON_HOME}/test/machine_learning/pytorch/run_mnist_cnn.py.
	import rare.model_char
	model = rare.model_char.create_mixup_model(model_name, input_channel, output_channel, label_converter.num_tokens)

	return model, train_forward, criterion

def build_rare1_model(label_converter, image_height, image_width, image_channel, loss_type, lang, max_text_len, num_suffixes, sos_id, blank_label=None):
	transformer = None  # The type of transformer. {None, 'TPS'}.
	feature_extractor = 'VGG'  # The type of feature extractor. {'VGG', 'RCNN', 'ResNet'}.
	sequence_model = 'BiLSTM'  # The type of sequence model. {None, 'BiLSTM'}.
	if loss_type == 'ctc':
		decoder = 'CTC'  # The type of decoder. {'CTC', 'Attn'}.
	elif loss_type in ['xent', 'nll']:
		decoder = 'Attn'  # The type of decoder. {'CTC', 'Attn'}.

	num_fiducials = 20  # The number of fiducial points of TPS-STN.
	input_channel = image_channel  # The number of input channel of feature extractor.
	output_channel = 512  # The number of output channel of feature extractor.
	if lang == 'kor':
		hidden_size = 1024  # The size of the LSTM hidden states.
	else:
		hidden_size = 512  # The size of the LSTM hidden states.

	if loss_type == 'ctc':
		# Define a loss function.
		criterion = torch.nn.CTCLoss(blank=blank_label, zero_infinity=True)  # The BLANK label.

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch

			model_outputs = model(inputs.to(device), None, is_train=True, device=device).log_softmax(2)

			N, T = model_outputs.shape[:2]
			model_outputs = model_outputs.permute(1, 0, 2)  # (N, T, C) -> (T, N, C).
			model_output_lens = torch.full([N], T, dtype=torch.int32, device=device)

			# TODO [check] >> To avoid CTC loss issue, disable cuDNN for the computation of the CTC loss.
			# https://github.com/jpuigcerver/PyLaia/issues/16
			torch.backends.cudnn.enabled = False
			cost = criterion(model_outputs, outputs.to(device), model_output_lens, output_lens.to(device))
			torch.backends.cudnn.enabled = True
			return cost

		def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
			raise NotImplementedError

	elif loss_type in ['xent', 'nll']:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			# Construct inputs for one-step look-ahead.
			decoder_inputs = outputs[:,:-1]
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1

			model_outputs = model(inputs.to(device), decoder_inputs.to(device), is_train=True, device=device)

			# TODO [check] >> How to compute loss?
			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.to(device).contiguous().view(-1))
			"""
			mask = torch.full(decoder_outputs.shape[:2], False, dtype=torch.bool)
			for idx, ll in enumerate(decoder_output_lens):
				mask[idx,:ll].fill_(True)
			model_outputs[mask == False] = label_converter.pad_id
			return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.to(device).contiguous().view(-1))
			"""
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))

		def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
			model_outputs = model(inputs.to(device), None, is_train=False, device=device)

			_, model_outputs = torch.max(model_outputs, dim=-1)
			if outputs is None or output_lens is None:
				return model_outputs.cpu().numpy(), None
			else:
				return model_outputs.cpu().numpy(), outputs.numpy()

	import rare.model
	model = rare.model.Model(image_height, image_width, label_converter.num_tokens, num_fiducials, input_channel, output_channel, hidden_size, max_text_len + num_suffixes, sos_id, label_converter.pad_id, transformer, feature_extractor, sequence_model, decoder)

	return model, infer, train_forward, criterion

def build_rare1_mixup_model(label_converter, image_height, image_width, image_channel, loss_type, lang, max_text_len, num_suffixes, sos_id, blank_label=None):
	transformer = None  # The type of transformer. {None, 'TPS'}.
	feature_extractor = 'VGG'  # The type of feature extractor. {'VGG', 'RCNN', 'ResNet'}.
	sequence_model = 'BiLSTM'  # The type of sequence model. {None, 'BiLSTM'}.
	if loss_type == 'ctc':
		decoder = 'CTC'  # The type of decoder. {'CTC', 'Attn'}.
	elif loss_type in ['xent', 'nll']:
		decoder = 'Attn'  # The type of decoder. {'CTC', 'Attn'}.

	num_fiducials = 20  # The number of fiducial points of TPS-STN.
	input_channel = image_channel  # The number of input channel of feature extractor.
	output_channel = 512  # The number of output channel of feature extractor.
	if lang == 'kor':
		hidden_size = 1024  # The size of the LSTM hidden states.
	else:
		hidden_size = 512  # The size of the LSTM hidden states.

	mixup_input, mixup_hidden, mixup_alpha = True, True, 2.0
	cutout, cutout_size = True, 4

	if loss_type == 'ctc':
		# Define a loss function.
		criterion = torch.nn.CTCLoss(blank=blank_label, zero_infinity=True)  # The BLANK label.

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch

			model_outputs = model(inputs.to(device), None, mixup_input, mixup_hidden, mixup_alpha, cutout, cutout_size, is_train=True, device=device).log_softmax(2)

			N, T = model_outputs.shape[:2]
			model_outputs = model_outputs.permute(1, 0, 2)  # (N, T, C) -> (T, N, C).
			model_output_lens = torch.full([N], T, dtype=torch.int32, device=device)

			# TODO [check] >> To avoid CTC loss issue, disable cuDNN for the computation of the CTC loss.
			# https://github.com/jpuigcerver/PyLaia/issues/16
			torch.backends.cudnn.enabled = False
			cost = criterion(model_outputs, outputs.to(device), model_output_lens, output_lens.to(device))
			torch.backends.cudnn.enabled = True
			return cost

		def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
			raise NotImplementedError

	elif loss_type in ['xent', 'nll']:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			# Construct inputs for one-step look-ahead.
			decoder_inputs = outputs[:,:-1]
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1

			model_outputs = model(inputs.to(device), decoder_inputs.to(device), is_train=True, device=device)

			# TODO [check] >> How to compute loss?
			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.to(device).contiguous().view(-1))
			"""
			mask = torch.full(decoder_outputs.shape[:2], False, dtype=torch.bool)
			for idx, ll in enumerate(decoder_output_lens):
				mask[idx,:ll].fill_(True)
			model_outputs[mask == False] = label_converter.pad_id
			return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.to(device).contiguous().view(-1))
			"""
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))

		def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
			model_outputs = model(inputs.to(device), None, is_train=False, device=device)

			_, model_outputs = torch.max(model_outputs, dim=-1)
			if outputs is None or output_lens is None:
				return model_outputs.cpu().numpy(), None
			else:
				return model_outputs.cpu().numpy(), outputs.numpy()

	# FIXME [error] >> rare.model.Model_MixUp is not working.
	import rare.model
	model = rare.model.Model_MixUp(image_height, image_width, label_converter.num_tokens, num_fiducials, input_channel, output_channel, hidden_size, max_text_len + num_suffixes, sos_id, label_converter.pad_id, transformer, feature_extractor, sequence_model, decoder)

	return model, infer, train_forward, criterion

def build_rare2_model(label_converter, image_height, image_width, image_channel, lang, loss_type=None, max_time_steps=0, sos_id=0):
	if lang == 'kor':
		hidden_size = 512  # The size of the LSTM hidden states.
	else:
		hidden_size = 256  # The size of the LSTM hidden states.
	num_rnns = 2
	embedding_size = 256
	use_leaky_relu = False

	if loss_type is not None:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
		else:
			raise ValueError('Invalid loss type, {}'.format(loss_type))

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			# Construct inputs for one-step look-ahead.
			decoder_inputs = outputs[:,:-1]
			decoder_input_lens = output_lens - 1
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1

			model_outputs = model(inputs.to(device), decoder_inputs.to(device), decoder_input_lens.to(device), device=device)

			# TODO [check] >> How to compute loss?
			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), outputs.to(device).contiguous().view(-1))
			"""
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
			"""
			"""
			concat_decoder_outputs = list()
			for do, dl in zip(decoder_outputs, decoder_output_lens):
				concat_decoder_outputs.append(do[:dl])
			return criterion(model_outputs, torch.cat(concat_decoder_outputs, 0).to(device))
			"""
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
	else:
		criterion = None
		train_forward = None

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		#model_outputs = model(inputs.to(device), decoder_inputs.to(device), decoder_input_lens.to(device), device=device)
		model_outputs = model(inputs.to(device), None, None, device=device)

		_, model_outputs = torch.max(model_outputs, dim=-1)
		model_outputs = model_outputs.cpu().numpy()

		if outputs is None or output_lens is None:
			return model_outputs, None
		else:
			outputs = outputs.long()

			# Construct inputs for one-step look-ahead.
			#decoder_inputs = outputs[:,:-1]
			#decoder_input_lens = output_lens - 1
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1

			"""
			separated_model_outputs = np.zeros(decoder_outputs.shape, model_outputs.dtype)
			start_idx = 0
			for idx, dl in enumerate(decoder_output_lens):
				end_idx = start_idx + dl
				separated_model_outputs[idx,:dl] = model_outputs[start_idx:end_idx]
				start_idx = end_idx
			return separated_model_outputs, decoder_outputs.numpy()
			"""
			return model_outputs, decoder_outputs.numpy()

	import rare.crnn_lang
	model = rare.crnn_lang.CRNN(imgH=image_height, nc=image_channel, nclass=label_converter.num_tokens, nh=hidden_size, n_rnn=num_rnns, num_embeddings=embedding_size, leakyRelu=use_leaky_relu, max_time_steps=max_time_steps, sos_id=sos_id)

	return model, infer, train_forward, criterion

def build_aster_model(label_converter, image_height, image_width, image_channel, lang, max_text_len, eos_id):
	if lang == 'kor':
		hidden_size = 512  # The size of the LSTM hidden states.
	else:
		hidden_size = 256  # The size of the LSTM hidden states.

	import aster.config
	#sys_args = aster.config.get_args(sys.argv[1:])
	sys_args = aster.config.get_args([])
	sys_args.with_lstm = True
	#sys_args.STN_ON = True

	glogger.info('ASTER options: {}.'.format(vars(sys_args)))

	# Define a loss function.
	#if loss_type == 'xent':
	#	criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
	#elif loss_type == 'nll':
	#	criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
	#else:
	#	raise ValueError('Invalid loss type, {}'.format(loss_type))

	def train_forward(model, criterion, batch, device):
		inputs, outputs, output_lens = batch

		"""
		# Construct inputs for one-step look-ahead.
		if eos_id != pad_id:
			decoder_inputs = outputs[:,:-1].clone()
			decoder_inputs[decoder_inputs == eos_id] = pad_id  # Remove <EOS> tokens.
		else: decoder_inputs = outputs[:,:-1]
		"""
		# Construct outputs for one-step look-ahead.
		decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
		decoder_output_lens = output_lens - 1

		input_dict = dict()
		input_dict['images'] = inputs.to(device)
		input_dict['rec_targets'] = decoder_outputs.to(device)
		input_dict['rec_lengths'] = decoder_output_lens.to(device)

		model_output_dict = model(input_dict, device=device)

		loss = model_output_dict['losses']['loss_rec']  # aster.sequence_cross_entropy_loss.SequenceCrossEntropyLoss.
		return loss

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		if outputs is None or output_lens is None:
			input_dict = dict()
			input_dict['images'] = inputs.to(device)
			input_dict['rec_targets'] = None
			input_dict['rec_lengths'] = None

			model_output_dict = model(input_dict, device=device)

			model_outputs = model_output_dict['output']['pred_rec']  # [batch size, max label len].
			#model_output_scores = model_output_dict['output']['pred_rec_score']  # [batch size, max label len].

			return model_outputs.cpu().numpy(), None
		else:
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1

			input_dict = dict()
			input_dict['images'] = inputs.to(device)
			input_dict['rec_targets'] = decoder_outputs.to(device)
			input_dict['rec_lengths'] = decoder_output_lens.to(device)

			model_output_dict = model(input_dict, device=device)

			#loss = model_output_dict['losses']['loss_rec']
			model_outputs = model_output_dict['output']['pred_rec']  # [batch size, max label len].
			#model_output_scores = model_output_dict['output']['pred_rec_score']  # [batch size, max label len].

			# TODO [check] >>
			#return model_outputs.cpu().numpy(), outputs.numpy()
			return model_outputs.cpu().numpy(), decoder_outputs.numpy()

	import aster.model_builder
	model = aster.model_builder.ModelBuilder(
		sys_args, arch=sys_args.arch, input_height=image_height, input_channel=image_channel,
		hidden_size=hidden_size, rec_num_classes=label_converter.num_tokens,
		sDim=sys_args.decoder_sdim, attDim=sys_args.attDim,
		max_len_labels=max_text_len + label_converter.num_affixes, eos=eos_id,
		STN_ON=sys_args.STN_ON
	)

	return model, infer, train_forward, sys_args

def build_decoder_and_generator_for_opennmt(num_classes, word_vec_size, hidden_size, num_layers=2, bidirectional_encoder=True):
	import onmt

	embedding_dropout = 0.3
	rnn_type = 'LSTM'
	num_layers = num_layers
	#hidden_size = hidden_size
	dropout = 0.3

	tgt_embeddings = onmt.modules.Embeddings(
		word_vec_size=word_vec_size,
		word_vocab_size=num_classes,
		word_padding_idx=1,
		position_encoding=False,
		feat_merge='concat',
		feat_vec_exponent=0.7,
		feat_vec_size=-1,
		feat_padding_idx=[],
		feat_vocab_sizes=[],
		dropout=embedding_dropout,
		sparse=False,
		fix_word_vecs=False
	)

	decoder = onmt.decoders.InputFeedRNNDecoder(
		rnn_type=rnn_type, bidirectional_encoder=bidirectional_encoder,
		num_layers=num_layers, hidden_size=hidden_size,
		attn_type='general', attn_func='softmax',
		coverage_attn=False, context_gate=None,
		copy_attn=False, dropout=dropout, embeddings=tgt_embeddings,
		reuse_copy_attn=False, copy_attn_type='general'
	)
	generator = torch.nn.Sequential(
		torch.nn.Linear(in_features=hidden_size, out_features=num_classes, bias=True),
		onmt.modules.util_class.Cast(dtype=torch.float32),
		torch.nn.LogSoftmax(dim=-1)
	)
	return decoder, generator

def build_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, encoder_type, lang, loss_type=None):
	bidirectional_encoder = True
	num_encoder_layers, num_decoder_layers = 2, 2
	if lang == 'kor':
		word_vec_size = 80
		encoder_rnn_size, decoder_hidden_size = 1024, 1024
	else:
		word_vec_size = 80
		encoder_rnn_size, decoder_hidden_size = 512, 512

	if loss_type is not None:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
		else:
			raise ValueError('Invalid loss type, {}'.format(loss_type))

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1
			outputs.unsqueeze_(dim=-1)  # [B, T] -> [B, T, 1]. No one-hot encoding.
			outputs = torch.transpose(outputs, 0, 1)  # [B, T, 1] -> [T, B, 1].

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model.generator(model_output_tuple[0]).transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes] where T-1 is for one-step look-ahead.
			#attentions = model_output_tuple[1]['std']

			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			# TODO [decide] >> Which is better, tensor.contiguous().to(device) or tensor.to(device).contiguous()?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.contiguous().to(device).view(-1))
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
	else:
		criterion = None
		train_forward = None

	#--------------------
	import onmt, onmt.translate
	import torchtext
	import torchtext_util

	tgt_field = torchtext.data.Field(
		sequential=True, use_vocab=True, init_token=label_converter.SOS, eos_token=label_converter.EOS, fix_length=None,
		dtype=torch.int64, preprocessing=None, postprocessing=None, lower=False,
		tokenize=None, tokenizer_language='kr',  # TODO [check] >> tokenizer_language is not valid.
		#tokenize=functools.partial(onmt.inputters.inputter._feature_tokenize, layer=0, feat_delim=None, truncate=None), tokenizer_language='en',
		include_lengths=False, batch_first=False, pad_token=label_converter.PAD, pad_first=False, unk_token=label_converter.UNKNOWN,
		truncate_first=False, stop_words=None, is_target=False
	)
	#tgt_field.build_vocab([label_converter.tokens], specials=[label_converter.UNKNOWN, label_converter.PAD], specials_first=False)  # Sort vocabulary + add special tokens, <unknown>, <pad>, <bos>, and <eos>.
	if label_converter.PAD in [label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN]:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	else:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.PAD, label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	assert label_converter.num_tokens == len(tgt_field.vocab.itos)
	assert len(list(filter(lambda pair: pair[0] != pair[1], zip(label_converter.tokens, tgt_field.vocab.itos)))) == 0

	tgt_vocab = tgt_field.vocab
	tgt_unk = tgt_vocab.stoi[tgt_field.unk_token]
	tgt_bos = tgt_vocab.stoi[tgt_field.init_token]
	tgt_eos = tgt_vocab.stoi[tgt_field.eos_token]
	tgt_pad = tgt_vocab.stoi[tgt_field.pad_token]

	scorer = onmt.translate.GNMTGlobalScorer(alpha=0.7, beta=0.0, length_penalty='avg', coverage_penalty='none')

	is_beam_search_used = True
	if is_beam_search_used:
		beam_size = 30
		n_best = 1
		ratio = 0.0
	else:
		beam_size = 1
		random_sampling_topk, random_sampling_temp = 1, 1
		n_best = 1  # Fixed. For handling translation results.
	max_time_steps = max_label_len + label_converter.num_affixes
	min_length, max_length = 0, max_time_steps
	block_ngram_repeat = 0
	#ignore_when_blocking = frozenset()
	#exclusion_idxs = {tgt_vocab.stoi[t] for t in ignore_when_blocking}
	exclusion_idxs = set()

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		if outputs is None or output_lens is None:
			batch_size = len(inputs)

			if is_beam_search_used:
				decode_strategy = opennmt_util.create_beam_search_strategy(batch_size, scorer, beam_size, n_best, ratio, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)
			else:
				decode_strategy = opennmt_util.create_greedy_search_strategy(batch_size, random_sampling_topk, random_sampling_temp, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)

			model_output_dict = opennmt_util.translate_batch_with_strategy(model, decode_strategy, inputs.to(device), batch_size, beam_size, tgt_unk, tgt_vocab, src_vocabs=[])

			model_outputs = model_output_dict['predictions']
			#scores = model_output_dict['scores']
			#attentions = model_output_dict['attention']
			#alignment = model_output_dict['alignment']

			rank_id = 0  # rank_id < n_best.
			#max_time_steps = functools.reduce(lambda x, y: x if x >= len(y[rank_id]) else len(y[rank_id]), model_outputs, 0)
			new_model_outputs = torch.full((len(model_outputs), max_time_steps), tgt_pad, dtype=torch.int)
			for idx, moutp in enumerate(model_outputs):
				new_model_outputs[idx,:len(moutp[rank_id])] = moutp[rank_id]

			return new_model_outputs.cpu().numpy(), None
		else:
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			outputs = torch.unsqueeze(outputs, dim=-1).transpose(0, 1).long()  # [B, T] -> [T, B, 1]. No one-hot encoding.

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model.generator(model_output_tuple[0]).transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes].
			#attentions = model_output_tuple[1]['std']

			_, model_outputs = torch.max(model_outputs, dim=-1)
			return model_outputs.cpu().numpy(), decoder_outputs.numpy()

	if encoder_type == 'onmt':
		#embedding_dropout = 0.3
		dropout = 0.3

		#src_embeddings = None

		encoder = onmt.encoders.ImageEncoder(
			num_layers=num_encoder_layers, bidirectional=bidirectional_encoder,
			rnn_size=encoder_rnn_size, dropout=dropout, image_chanel_size=image_channel
		)
	elif encoder_type == 'rare1':
		transformer = None  # The type of transformer. {None, 'TPS'}.
		feature_extractor = 'VGG'  # The type of feature extractor. {'VGG', 'RCNN', 'ResNet'}.
		sequence_model = 'BiLSTM'  # The type of sequence model. {None, 'BiLSTM'}.

		num_fiducials = 20  # The number of fiducial points of TPS-STN.
		output_channel = 512  # The number of output channel of feature extractor.

		encoder = opennmt_util.Rare1ImageEncoder(
			image_height, image_width, image_channel, output_channel,
			hidden_size=encoder_rnn_size, num_layers=num_encoder_layers, bidirectional=bidirectional_encoder,
			transformer=transformer, feature_extractor=feature_extractor, sequence_model=sequence_model,
			num_fiducials=num_fiducials
		)
	elif encoder_type == 'rare2':
		is_stn_used = False
		if is_stn_used:
			num_fiducials = 20  # The number of fiducial points of TPS-STN.
		else:
			num_fiducials = 0  # No TPS-STN.

		encoder = opennmt_util.Rare2ImageEncoder(
			image_height, image_width, image_channel,
			hidden_size=encoder_rnn_size, num_layers=num_encoder_layers, bidirectional=bidirectional_encoder,
			num_fiducials=num_fiducials
		)
	elif encoder_type == 'aster':
		is_stn_used = False
		if is_stn_used:
			num_fiducials = 20  # The number of fiducial points of TPS-STN.
		else:
			num_fiducials = 0  # No TPS-STN.

		encoder = opennmt_util.AsterImageEncoder(
			image_height, image_width, image_channel, num_classes,
			hidden_size=encoder_rnn_size,
			num_fiducials=num_fiducials
		)
	else:
		raise ValueError('Invalid encoder type: {}'.format(encoder_type))
	decoder, generator = build_decoder_and_generator_for_opennmt(label_converter.num_tokens, word_vec_size, hidden_size=decoder_hidden_size, num_layers=num_decoder_layers, bidirectional_encoder=bidirectional_encoder)

	import onmt
	model = onmt.models.NMTModel(encoder, decoder)
	model.add_module('generator', generator)

	return model, infer, train_forward, criterion

def build_rare1_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device='cpu'):
	transformer = None  # The type of transformer. {None, 'TPS'}.
	feature_extractor = 'VGG'  # The type of feature extractor. {'VGG', 'RCNN', 'ResNet'}.
	sequence_model = 'BiLSTM'  # The type of sequence model. {None, 'BiLSTM'}.

	num_fiducials = 20  # The number of fiducial points of TPS-STN.
	#input_channel = image_channel  # The number of input channel of feature extractor.
	output_channel = 512  # The number of output channel of feature extractor.
	bidirectional_encoder = True
	num_encoder_layers, num_decoder_layers = 2, 2
	if lang == 'kor':
		word_vec_size = 80
		encoder_rnn_size = 512
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size
	else:
		word_vec_size = 80
		encoder_rnn_size = 256
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size

	if loss_type is not None:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
		else:
			raise ValueError('Invalid loss type, {}'.format(loss_type))

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1
			outputs.unsqueeze_(dim=-1)  # [B, T] -> [B, T, 1]. No one-hot encoding.
			outputs = torch.transpose(outputs, 0, 1)  # [B, T, 1] -> [T, B, 1].

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes] where T-1 is for one-step look-ahead.
			#attentions = model_output_tuple[1]['std']

			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			# TODO [decide] >> Which is better, tensor.contiguous().to(device) or tensor.to(device).contiguous()?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.contiguous().to(device).view(-1))
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
	else:
		criterion = None
		train_forward = None

	#--------------------
	import onmt, onmt.translate
	import torchtext
	import torchtext_util

	tgt_field = torchtext.data.Field(
		sequential=True, use_vocab=True, init_token=label_converter.SOS, eos_token=label_converter.EOS, fix_length=None,
		dtype=torch.int64, preprocessing=None, postprocessing=None, lower=False,
		tokenize=None, tokenizer_language='kr',  # TODO [check] >> tokenizer_language is not valid.
		#tokenize=functools.partial(onmt.inputters.inputter._feature_tokenize, layer=0, feat_delim=None, truncate=None), tokenizer_language='en',
		include_lengths=False, batch_first=False, pad_token=label_converter.PAD, pad_first=False, unk_token=label_converter.UNKNOWN,
		truncate_first=False, stop_words=None, is_target=False
	)
	#tgt_field.build_vocab([label_converter.tokens], specials=[label_converter.UNKNOWN, label_converter.PAD], specials_first=False)  # Sort vocabulary + add special tokens, <unknown>, <pad>, <bos>, and <eos>.
	if label_converter.PAD in [label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN]:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	else:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.PAD, label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	assert label_converter.num_tokens == len(tgt_field.vocab.itos)
	assert len(list(filter(lambda pair: pair[0] != pair[1], zip(label_converter.tokens, tgt_field.vocab.itos)))) == 0

	tgt_vocab = tgt_field.vocab
	tgt_unk = tgt_vocab.stoi[tgt_field.unk_token]
	tgt_bos = tgt_vocab.stoi[tgt_field.init_token]
	tgt_eos = tgt_vocab.stoi[tgt_field.eos_token]
	tgt_pad = tgt_vocab.stoi[tgt_field.pad_token]

	scorer = onmt.translate.GNMTGlobalScorer(alpha=0.7, beta=0.0, length_penalty='avg', coverage_penalty='none')

	is_beam_search_used = True
	if is_beam_search_used:
		beam_size = 30
		n_best = 1
		ratio = 0.0
	else:
		beam_size = 1
		random_sampling_topk, random_sampling_temp = 1, 1
		n_best = 1  # Fixed. For handling translation results.
	max_time_steps = max_label_len + label_converter.num_affixes
	min_length, max_length = 0, max_time_steps
	block_ngram_repeat = 0
	#ignore_when_blocking = frozenset()
	#exclusion_idxs = {tgt_vocab.stoi[t] for t in ignore_when_blocking}
	exclusion_idxs = set()

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		if outputs is None or output_lens is None:
			batch_size = len(inputs)

			if is_beam_search_used:
				decode_strategy = opennmt_util.create_beam_search_strategy(batch_size, scorer, beam_size, n_best, ratio, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)
			else:
				decode_strategy = opennmt_util.create_greedy_search_strategy(batch_size, random_sampling_topk, random_sampling_temp, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)

			model_output_dict = opennmt_util.translate_batch_with_strategy(model, decode_strategy, inputs.to(device), batch_size, beam_size, tgt_unk, tgt_vocab, src_vocabs=[])

			model_outputs = model_output_dict['predictions']
			#scores = model_output_dict['scores']
			#attentions = model_output_dict['attention']
			#alignment = model_output_dict['alignment']

			rank_id = 0  # rank_id < n_best.
			#max_time_steps = functools.reduce(lambda x, y: x if x >= len(y[rank_id]) else len(y[rank_id]), model_outputs, 0)
			new_model_outputs = torch.full((len(model_outputs), max_time_steps), tgt_pad, dtype=torch.int)
			for idx, moutp in enumerate(model_outputs):
				new_model_outputs[idx,:len(moutp[rank_id])] = moutp[rank_id]

			return new_model_outputs.cpu().numpy(), None
		else:
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			outputs = torch.unsqueeze(outputs, dim=-1).transpose(0, 1).long()  # [B, T] -> [T, B, 1]. No one-hot encoding.

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes].
			#attentions = model_output_tuple[1]['std']

			_, model_outputs = torch.max(model_outputs, dim=-1)
			return model_outputs.cpu().numpy(), decoder_outputs.numpy()

	class MyCompositeModel(torch.nn.Module):
		def __init__(self, image_height, image_width, input_channel, output_channel, num_classes, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_encoder_layers, num_decoder_layers, bidirectional_encoder, transformer=None, feature_extractor='VGG', sequence_model='BiLSTM', num_fiducials=0):
			super().__init__()

			self.encoder = opennmt_util.Rare1ImageEncoder(image_height, image_width, input_channel, output_channel, hidden_size=encoder_rnn_size, num_layers=num_encoder_layers, bidirectional=bidirectional_encoder, transformer=transformer, feature_extractor=feature_extractor, sequence_model=sequence_model, num_fiducials=num_fiducials)
			self.decoder, self.generator = build_decoder_and_generator_for_opennmt(num_classes, word_vec_size, hidden_size=decoder_hidden_size, num_layers=num_decoder_layers, bidirectional_encoder=bidirectional_encoder)

		# REF [function] >> NMTModel.forward() in https://github.com/OpenNMT/OpenNMT-py/blob/master/onmt/models/model.py
		def forward(self, src, tgt=None, lengths=None, bptt=False, with_align=False):
			enc_hiddens, enc_outputs, lengths = self.encoder(src, lengths=lengths, device=device)

			if tgt is None or lengths is None:
				raise NotImplementedError
			else:
				dec_in = tgt[:-1]  # Exclude last target from inputs.

				# TODO [check] >> Is it proper to use enc_outputs & enc_hiddens?
				if bptt is False:
					self.decoder.init_state(src, enc_outputs, enc_hiddens)
				dec_outs, attns = self.decoder(dec_in, enc_outputs, memory_lengths=lengths, with_align=with_align)
				outs = self.generator(dec_outs)
				return outs, attns

	model = MyCompositeModel(image_height, image_width, image_channel, output_channel, label_converter.num_tokens, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_encoder_layers, num_decoder_layers, bidirectional_encoder, transformer=transformer, feature_extractor=feature_extractor, sequence_model=sequence_model, num_fiducials=num_fiducials)

	return model, infer, forward, criterion

def build_rare2_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device='cpu'):
	is_stn_used = False
	if is_stn_used:
		num_fiducials = 20  # The number of fiducial points of TPS-STN.
	else:
		num_fiducials = 0  # No TPS-STN.
	bidirectional_encoder = True
	num_encoder_layers, num_decoder_layers = 2, 2
	if lang == 'kor':
		word_vec_size = 80
		encoder_rnn_size = 512
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size
	else:
		word_vec_size = 80
		encoder_rnn_size = 256
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size

	if loss_type is not None:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
		else:
			raise ValueError('Invalid loss type, {}'.format(loss_type))

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1
			outputs.unsqueeze_(dim=-1)  # [B, T] -> [B, T, 1]. No one-hot encoding.
			outputs = torch.transpose(outputs, 0, 1)  # [B, T, 1] -> [T, B, 1].

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes] where T-1 is for one-step look-ahead.
			#attentions = model_output_tuple[1]['std']

			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			# TODO [decide] >> Which is better, tensor.contiguous().to(device) or tensor.to(device).contiguous()?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.contiguous().to(device).view(-1))
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
	else:
		criterion = None
		train_forward = None

	#--------------------
	import onmt, onmt.translate
	import torchtext
	import torchtext_util

	tgt_field = torchtext.data.Field(
		sequential=True, use_vocab=True, init_token=label_converter.SOS, eos_token=label_converter.EOS, fix_length=None,
		dtype=torch.int64, preprocessing=None, postprocessing=None, lower=False,
		tokenize=None, tokenizer_language='kr',  # TODO [check] >> tokenizer_language is not valid.
		#tokenize=functools.partial(onmt.inputters.inputter._feature_tokenize, layer=0, feat_delim=None, truncate=None), tokenizer_language='en',
		include_lengths=False, batch_first=False, pad_token=label_converter.PAD, pad_first=False, unk_token=label_converter.UNKNOWN,
		truncate_first=False, stop_words=None, is_target=False
	)
	#tgt_field.build_vocab([label_converter.tokens], specials=[label_converter.UNKNOWN, label_converter.PAD], specials_first=False)  # Sort vocabulary + add special tokens, <unknown>, <pad>, <bos>, and <eos>.
	if label_converter.PAD in [label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN]:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	else:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.PAD, label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	assert label_converter.num_tokens == len(tgt_field.vocab.itos)
	assert len(list(filter(lambda pair: pair[0] != pair[1], zip(label_converter.tokens, tgt_field.vocab.itos)))) == 0

	tgt_vocab = tgt_field.vocab
	tgt_unk = tgt_vocab.stoi[tgt_field.unk_token]
	tgt_bos = tgt_vocab.stoi[tgt_field.init_token]
	tgt_eos = tgt_vocab.stoi[tgt_field.eos_token]
	tgt_pad = tgt_vocab.stoi[tgt_field.pad_token]

	scorer = onmt.translate.GNMTGlobalScorer(alpha=0.7, beta=0.0, length_penalty='avg', coverage_penalty='none')

	is_beam_search_used = True
	if is_beam_search_used:
		beam_size = 30
		n_best = 1
		ratio = 0.0
	else:
		beam_size = 1
		random_sampling_topk, random_sampling_temp = 1, 1
		n_best = 1  # Fixed. For handling translation results.
	max_time_steps = max_label_len + label_converter.num_affixes
	min_length, max_length = 0, max_time_steps
	block_ngram_repeat = 0
	#ignore_when_blocking = frozenset()
	#exclusion_idxs = {tgt_vocab.stoi[t] for t in ignore_when_blocking}
	exclusion_idxs = set()

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		if outputs is None or output_lens is None:
			batch_size = len(inputs)

			if is_beam_search_used:
				decode_strategy = opennmt_util.create_beam_search_strategy(batch_size, scorer, beam_size, n_best, ratio, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)
			else:
				decode_strategy = opennmt_util.create_greedy_search_strategy(batch_size, random_sampling_topk, random_sampling_temp, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)

			model_output_dict = opennmt_util.translate_batch_with_strategy(model, decode_strategy, inputs.to(device), batch_size, beam_size, tgt_unk, tgt_vocab, src_vocabs=[])

			model_outputs = model_output_dict['predictions']
			#scores = model_output_dict['scores']
			#attentions = model_output_dict['attention']
			#alignment = model_output_dict['alignment']

			rank_id = 0  # rank_id < n_best.
			#max_time_steps = functools.reduce(lambda x, y: x if x >= len(y[rank_id]) else len(y[rank_id]), model_outputs, 0)
			new_model_outputs = torch.full((len(model_outputs), max_time_steps), tgt_pad, dtype=torch.int)
			for idx, moutp in enumerate(model_outputs):
				new_model_outputs[idx,:len(moutp[rank_id])] = moutp[rank_id]

			return new_model_outputs.cpu().numpy(), None
		else:
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			outputs = torch.unsqueeze(outputs, dim=-1).transpose(0, 1).long()  # [B, T] -> [T, B, 1]. No one-hot encoding.

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes].
			#attentions = model_output_tuple[1]['std']

			_, model_outputs = torch.max(model_outputs, dim=-1)
			return model_outputs.cpu().numpy(), decoder_outputs.numpy()

	class MyCompositeModel(torch.nn.Module):
		def __init__(self, image_height, image_width, input_channel, num_classes, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_encoder_layers, num_decoder_layers, bidirectional_encoder, num_fiducials):
			super().__init__()

			self.encoder = opennmt_util.Rare2ImageEncoder(image_height, image_width, input_channel, hidden_size=encoder_rnn_size, num_layers=num_encoder_layers, bidirectional=bidirectional_encoder, num_fiducials=num_fiducials)
			self.decoder, self.generator = build_decoder_and_generator_for_opennmt(num_classes, word_vec_size, hidden_size=decoder_hidden_size, num_layers=num_decoder_layers, bidirectional_encoder=bidirectional_encoder)

		# REF [function] >> NMTModel.forward() in https://github.com/OpenNMT/OpenNMT-py/blob/master/onmt/models/model.py
		def forward(self, src, tgt=None, lengths=None, bptt=False, with_align=False):
			enc_hiddens, enc_outputs, lengths = self.encoder(src, lengths=lengths, device=device)

			if tgt is None or lengths is None:
				raise NotImplementedError
			else:
				dec_in = tgt[:-1]  # Exclude last target from inputs.

				# TODO [check] >> Is it proper to use enc_outputs & enc_hiddens?
				if bptt is False:
					self.decoder.init_state(src, enc_outputs, enc_hiddens)
				dec_outs, attns = self.decoder(dec_in, enc_outputs, memory_lengths=lengths, with_align=with_align)
				outs = self.generator(dec_outs)
				return outs, attns

	model = MyCompositeModel(image_height, image_width, image_channel, label_converter.num_tokens, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_encoder_layers, num_decoder_layers, bidirectional_encoder, num_fiducials)

	return model, infer, train_forward, criterion

def build_aster_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device='cpu'):
	is_stn_used = False
	if is_stn_used:
		num_fiducials = 20  # The number of fiducial points of TPS-STN.
	else:
		num_fiducials = 0  # No TPS-STN.
	bidirectional_encoder = True
	num_decoder_layers = 2
	if lang == 'kor':
		word_vec_size = 80
		encoder_rnn_size = 512
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size
	else:
		word_vec_size = 80
		encoder_rnn_size = 256
		decoder_hidden_size = encoder_rnn_size * 2 if bidirectional_encoder else encoder_rnn_size

	if loss_type is not None:
		# Define a loss function.
		if loss_type == 'xent':
			criterion = torch.nn.CrossEntropyLoss(ignore_index=label_converter.pad_id)  # Ignore the PAD ID.
		elif loss_type == 'nll':
			criterion = torch.nn.NLLLoss(ignore_index=label_converter.pad_id, reduction='sum')  # Ignore the PAD ID.
		else:
			raise ValueError('Invalid loss type, {}'.format(loss_type))

		def train_forward(model, criterion, batch, device):
			inputs, outputs, output_lens = batch
			outputs = outputs.long()

			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			decoder_output_lens = output_lens - 1
			outputs.unsqueeze_(dim=-1)  # [B, T] -> [B, T, 1]. No one-hot encoding.
			outputs = torch.transpose(outputs, 0, 1)  # [B, T, 1] -> [T, B, 1].

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes] where T-1 is for one-step look-ahead.
			#attentions = model_output_tuple[1]['std']

			# NOTE [info] >> All examples in a batch are concatenated together.
			#	Can each example be handled individually?
			# TODO [decide] >> Which is better, tensor.contiguous().to(device) or tensor.to(device).contiguous()?
			#return criterion(model_outputs.contiguous().view(-1, model_outputs.shape[-1]), decoder_outputs.contiguous().to(device).view(-1))
			concat_model_outputs, concat_decoder_outputs = list(), list()
			for mo, do, dl in zip(model_outputs, decoder_outputs, decoder_output_lens):
				concat_model_outputs.append(mo[:dl])
				concat_decoder_outputs.append(do[:dl])
			return criterion(torch.cat(concat_model_outputs, 0).to(device), torch.cat(concat_decoder_outputs, 0).to(device))
	else:
		criterion = None
		train_forward = None

	#--------------------
	import onmt, onmt.translate
	import torchtext
	import torchtext_util

	tgt_field = torchtext.data.Field(
		sequential=True, use_vocab=True, init_token=label_converter.SOS, eos_token=label_converter.EOS, fix_length=None,
		dtype=torch.int64, preprocessing=None, postprocessing=None, lower=False,
		tokenize=None, tokenizer_language='kr',
		#tokenize=functools.partial(onmt.inputters.inputter._feature_tokenize, layer=0, feat_delim=None, truncate=None), tokenizer_language='en',
		include_lengths=False, batch_first=False, pad_token=label_converter.PAD, pad_first=False, unk_token=label_converter.UNKNOWN,
		truncate_first=False, stop_words=None, is_target=False
	)
	#tgt_field.build_vocab([label_converter.tokens], specials=[label_converter.UNKNOWN, label_converter.PAD], specials_first=False)  # Sort vocabulary + add special tokens, <unknown>, <pad>, <bos>, and <eos>.
	if label_converter.PAD in [label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN]:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	else:
		tgt_field.vocab = torchtext_util.build_vocab_from_lexicon(label_converter.tokens, specials=[label_converter.PAD, label_converter.SOS, label_converter.EOS, label_converter.UNKNOWN], specials_first=False, sort=False)
	assert label_converter.num_tokens == len(tgt_field.vocab.itos)
	assert len(list(filter(lambda pair: pair[0] != pair[1], zip(label_converter.tokens, tgt_field.vocab.itos)))) == 0

	tgt_vocab = tgt_field.vocab
	tgt_unk = tgt_vocab.stoi[tgt_field.unk_token]
	tgt_bos = tgt_vocab.stoi[tgt_field.init_token]
	tgt_eos = tgt_vocab.stoi[tgt_field.eos_token]
	tgt_pad = tgt_vocab.stoi[tgt_field.pad_token]

	scorer = onmt.translate.GNMTGlobalScorer(alpha=0.7, beta=0.0, length_penalty='avg', coverage_penalty='none')

	is_beam_search_used = True
	if is_beam_search_used:
		beam_size = 30
		n_best = 1
		ratio = 0.0
	else:
		beam_size = 1
		random_sampling_topk, random_sampling_temp = 1, 1
		n_best = 1  # Fixed. For handling translation results.
	max_time_steps = max_label_len + label_converter.num_affixes
	min_length, max_length = 0, max_time_steps
	block_ngram_repeat = 0
	#ignore_when_blocking = frozenset()
	#exclusion_idxs = {tgt_vocab.stoi[t] for t in ignore_when_blocking}
	exclusion_idxs = set()

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		if outputs is None or output_lens is None:
			batch_size = len(inputs)

			if is_beam_search_used:
				decode_strategy = opennmt_util.create_beam_search_strategy(batch_size, scorer, beam_size, n_best, ratio, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)
			else:
				decode_strategy = opennmt_util.create_greedy_search_strategy(batch_size, random_sampling_topk, random_sampling_temp, min_length, max_length, block_ngram_repeat, tgt_bos, tgt_eos, tgt_pad, exclusion_idxs)

			model_output_dict = opennmt_util.translate_batch_with_strategy(model, decode_strategy, inputs.to(device), batch_size, beam_size, tgt_unk, tgt_vocab, src_vocabs=[])

			model_outputs = model_output_dict['predictions']
			#scores = model_output_dict['scores']
			#attentions = model_output_dict['attention']
			#alignment = model_output_dict['alignment']

			rank_id = 0  # rank_id < n_best.
			#max_time_steps = functools.reduce(lambda x, y: x if x >= len(y[rank_id]) else len(y[rank_id]), model_outputs, 0)
			new_model_outputs = torch.full((len(model_outputs), max_time_steps), tgt_pad, dtype=torch.int)
			for idx, moutp in enumerate(model_outputs):
				new_model_outputs[idx,:len(moutp[rank_id])] = moutp[rank_id]

			return new_model_outputs.cpu().numpy(), None
		else:
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.
			outputs = torch.unsqueeze(outputs, dim=-1).transpose(0, 1).long()  # [B, T] -> [T, B, 1]. No one-hot encoding.

			model_output_tuple = model(inputs.to(device), outputs.to(device), output_lens.to(device))

			model_outputs = model_output_tuple[0].transpose(0, 1)  # [T-1, B, #classes] -> [B, T-1, #classes].
			#attentions = model_output_tuple[1]['std']

			_, model_outputs = torch.max(model_outputs, dim=-1)
			return model_outputs.cpu().numpy(), decoder_outputs.numpy()

	class MyCompositeModel(torch.nn.Module):
		def __init__(self, image_height, image_width, input_channel, num_classes, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_decoder_layers, bidirectional_encoder, num_fiducials):
			super().__init__()

			self.encoder = opennmt_util.AsterImageEncoder(image_height, image_width, input_channel, num_classes, hidden_size=encoder_rnn_size, num_fiducials=num_fiducials)
			self.decoder, self.generator = build_decoder_and_generator_for_opennmt(num_classes, word_vec_size, hidden_size=decoder_hidden_size, num_layers=num_decoder_layers, bidirectional_encoder=bidirectional_encoder)

		# REF [function] >> NMTModel.forward() in https://github.com/OpenNMT/OpenNMT-py/blob/master/onmt/models/model.py
		def forward(self, src, tgt=None, lengths=None, bptt=False, with_align=False):
			enc_hiddens, enc_outputs, lengths = self.encoder(src, lengths=lengths, device=device)

			if tgt is None or lengths is None:
				raise NotImplementedError
			else:
				dec_in = tgt[:-1]  # Exclude last target from inputs.

				# TODO [check] >> Is it proper to use enc_outputs & enc_hiddens?
				if bptt is False:
					self.decoder.init_state(src, enc_outputs, enc_hiddens)
				dec_outs, attns = self.decoder(dec_in, enc_outputs, memory_lengths=lengths, with_align=with_align)
				outs = self.generator(dec_outs)
				return outs, attns

	model = MyCompositeModel(image_height, image_width, image_channel, label_converter.num_tokens, word_vec_size, encoder_rnn_size, decoder_hidden_size, num_decoder_layers, bidirectional_encoder, num_fiducials)

	return model, infer, train_forward, criterion

# REF [site] >> https://github.com/fengxinjie/Transformer-OCR
def build_transformer_ocr_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, is_train=False):
	import transformer_ocr.model, transformer_ocr.train, transformer_ocr.predict, transformer_ocr.dataset

	num_layers = 4
	num_heads = 8  # The number of head for MultiHeadedAttention.
	dropout = 0.1  # Dropout probability. [0, 1.0].
	if lang == 'kor':
		d_model = 256  # The dimension of keys/values/queries in MultiHeadedAttention, also the input size of the first-layer of the PositionwiseFeedForward.
		d_ff = 1024  # The second-layer of the PositionwiseFeedForward.
		d_feature = 1024  # The dimension of features in FeatureExtractor.
	else:
		d_model = 256  # The dimension of keys/values/queries in MultiHeadedAttention, also the input size of the first-layer of the PositionwiseFeedForward.
		d_ff = 1024  # The second-layer of the PositionwiseFeedForward.
		d_feature = 1024  # The dimension of features in FeatureExtractor.
	smoothing = 0.1
	# TODO [check] >> Check if PAD ID or PAD index is used.
	#pad_id = 0
	pad_id = label_converter.pad_id
	sos_id, eos_id = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
	max_time_steps = max_label_len + label_converter.num_affixes

	if is_train:
		# Define a loss function.
		criterion = transformer_ocr.train.LabelSmoothing(size=label_converter.num_tokens, padding_idx=pad_id, smoothing=smoothing)

		def train_forward(model, criterion, batch, device):
			inputs, outputs, _ = batch
			outputs = outputs.long()

			# Construct inputs for one-step look-ahead.
			if eos_id != pad_id:
				decoder_inputs = outputs[:,:-1].clone()
				decoder_inputs[decoder_inputs == eos_id] = pad_id  # Remove <EOS> tokens.
			else: decoder_inputs = outputs[:,:-1]
			# Construct outputs for one-step look-ahead.
			decoder_outputs = outputs[:,1:]  # Remove <SOS> tokens.

			batch = transformer_ocr.dataset.Batch(inputs, decoder_inputs, decoder_outputs, pad=pad_id, device=device)
			model_outputs = model(batch.src, batch.tgt_input, batch.src_mask, batch.tgt_input_mask)

			# REF [function] >> transformer_ocr.train.SimpleLossCompute.__call__().
			model_outputs = model.generator(model_outputs)
			return criterion(model_outputs.contiguous().view(-1, model_outputs.size(-1)), batch.tgt_output.contiguous().view(-1)) / batch.num_tokens
	else:
		criterion = None
		train_forward = None

	def infer(model, inputs, outputs=None, output_lens=None, device='cpu'):
		# Predict a single input.
		#src_mask = torch.autograd.Variable(torch.from_numpy(np.ones([1, 1, 36], dtype=np.bool)).to(device))
		src_mask = torch.autograd.Variable(torch.full([1, 1, 320], True, dtype=torch.bool)).to(device)

		inputs = inputs.to(device)
		model_outputs = np.full((len(inputs), max_time_steps), pad_id, dtype=np.int)
		for idx, src in enumerate(inputs):
			src = src.unsqueeze(dim=0)
			model_outp = transformer_ocr.predict.greedy_decode(model, src, src_mask, max_len=max_time_steps, sos=sos_id, eos=eos_id, device=device)
			model_outputs[idx,:len(model_outp)] = model_outp

		return model_outputs, None if outputs is None else outputs[:,1:].numpy()

	model = transformer_ocr.model.make_model(label_converter.num_tokens, N=num_layers, d_model=d_model, d_ff=d_ff, d_feature=d_feature, h=num_heads, dropout=dropout)

	return model, infer, train_forward, criterion

# REF [site] >> https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html
def train_character_recognizer(num_epochs=100, batch_size=128, device='cpu'):
	image_height, image_width, image_channel = 64, 64, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	# File-based chars: 78,838.
	is_mixed_chars_used = True
	if is_mixed_chars_used:
		num_simple_char_examples_per_class, num_noisy_examples_per_class = 300, 300  # For mixed chars.
	else:
		char_type = 'simple_char'  # {'simple_char', 'noisy_char', 'file_based_char'}.
		num_train_examples_per_class, num_test_examples_per_class = 500, 50  # For simple and noisy chars.
	char_clipping_ratio_interval = (0.8, 1.25)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 5  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	model_filepath_base = './char_recognition_{}_{}_{}_{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, lang, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset = tg_util.construct_charset()
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset = tg_util.construct_charset(hangeul=False)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	label_converter = swl_langproc_util.TokenConverter(list(charset))
	if is_mixed_chars_used:
		train_dataloader, test_dataloader = create_mixed_char_data_loaders(label_converter, charset, num_simple_char_examples_per_class, num_noisy_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_char_data_loaders(char_type, label_converter, charset, num_train_examples_per_class, num_test_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))

	# Show data info.
	show_char_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_char_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, train_forward_functor, criterion = build_char_model(label_converter, image_channel, loss_type, lang)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'initialized_variable_name' in name:
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = model.to(criterion)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	optimizer = torch.optim.SGD(model_params, lr=0.001, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_char_recognition_model(model, train_forward_functor, criterion, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_char_recognition_model(model, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, is_error_cases_saved=False, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

# REF [site] >> https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html
def train_character_recognizer_using_mixup(num_epochs=100, batch_size=128, device='cpu'):
	image_height, image_width, image_channel = 64, 64, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	# File-based chars: 78,838.
	is_mixed_chars_used = True
	if is_mixed_chars_used:
		num_simple_char_examples_per_class, num_noisy_examples_per_class = 300, 300  # For mixed chars.
	else:
		char_type = 'simple_char'  # {'simple_char', 'noisy_char', 'file_based_char'}.
		num_train_examples_per_class, num_test_examples_per_class = 500, 50  # For simple and noisy chars.
	char_clipping_ratio_interval = (0.8, 1.25)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 5  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	model_filepath_base = './char_recognition_mixup_{}_{}_{}_{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, lang, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset = tg_util.construct_charset()
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset = tg_util.construct_charset(hangeul=False)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	label_converter = swl_langproc_util.TokenConverter(list(charset))
	if is_mixed_chars_used:
		train_dataloader, test_dataloader = create_mixed_char_data_loaders(label_converter, charset, num_simple_char_examples_per_class, num_noisy_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_char_data_loaders(char_type, label_converter, charset, num_train_examples_per_class, num_test_examples_per_class, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, char_clipping_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))

	# Show data info.
	show_char_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_char_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, train_forward_functor, criterion = build_char_mixup_model(label_converter, image_channel, loss_type, lang)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'initialized_variable_name' in name:
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	optimizer = torch.optim.SGD(model_params, lr=0.001, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_char_recognition_model(model, train_forward_functor, criterion, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_char_recognition_model(model, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, is_error_cases_saved=False, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_rare1(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'ctc', 'xent', 'nll'}.
	max_gradient_norm = 5  # Gradient clipping value.
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	if loss_type == 'ctc':
		model_filepath_base = './word_recognition_rare1_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	elif loss_type in ['xent', 'nll']:
		model_filepath_base = './word_recognition_rare1_attn_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	else:
		raise ValueError('Invalid loss type, {}'.format(loss_type))
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	if loss_type == 'ctc':
		BLANK_LABEL = '<BLANK>'  # The BLANK label for CTC.
		label_converter = swl_langproc_util.TokenConverter([BLANK_LABEL] + list(charset), pad=None)  # NOTE [info] >> It's a trick. The ID of the BLANK label is set to 0.
		assert label_converter.encode([BLANK_LABEL], is_bare_output=True)[0] == 0, '{} != 0'.format(label_converter.encode([BLANK_LABEL], is_bare_output=True)[0])
		BLANK_LABEL_ID = 0 #label_converter.encode([BLANK_LABEL], is_bare_output=True)[0]
		SOS_ID, EOS_ID = None, None
		num_suffixes = 0
	elif loss_type in ['xent', 'nll']:
		BLANK_LABEL = None
		SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
		if is_separate_pad_id_used:
			# When <PAD> token has a separate valid token ID.
			PAD_TOKEN = '<PAD>'
			PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
			label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
			assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
			assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
		else:
			#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
			label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
		del SOS_TOKEN, EOS_TOKEN
		assert label_converter.PAD is not None
		SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
		num_suffixes = 1

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_rare1_model(label_converter, image_height, image_width, image_channel, loss_type, lang, max_word_len, num_suffixes, SOS_ID, BLANK_LABEL if loss_type == 'ctc' else None)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
				glogger.info(f'Skip {name} as it has already been initialized.')
				continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_rare2(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	max_gradient_norm = 5  # Gradient clipping value.
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_rare2_attn_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None
	SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
	num_suffixes = 1

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_rare2_model(label_converter, image_height, image_width, image_channel, lang, loss_type, max_word_len + num_suffixes, SOS_ID)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_aster(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	#loss_type = 'sxent'  # Sequence cross entropy.
	#max_gradient_norm = 5  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_aster_sxent_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None
	SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, sys_args = build_aster_model(label_converter, image_height, image_width, image_channel, lang, max_word_len, EOS_ID)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	#optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	optimizer = torch.optim.Adadelta(model_params, lr=sys_args.lr, weight_decay=sys_args.weight_decay)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, None, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_opennmt(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	encoder_type = 'onmt'  # {'onmt', 'rare1', 'rare2', 'aster'}.

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_onmt_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_opennmt_model(label_converter, image_height, image_width, image_channel, max_word_len, encoder_type, lang, loss_type)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	model.generator = model.generator.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	#optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_rare1_and_opennmt(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_rare1+onmt_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_rare1_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_word_len, lang, loss_type, device)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
				glogger.info(f'Skip {name} as it has already been initialized.')
				continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_rare2_and_opennmt(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_rare2+onmt_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_rare2_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_word_len, lang, loss_type, device)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
				glogger.info(f'Skip {name} as it has already been initialized.')
				continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_based_on_aster_and_opennmt(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 5  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './word_recognition_aster+onmt_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_aster_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_word_len, lang, loss_type, device)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
				glogger.info(f'Skip {name} as it has already been initialized.')
				continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_word_recognizer_using_mixup(num_epochs=20, batch_size=64, device='cpu'):
	image_height, image_width, image_channel = 32, 100, 3
	#image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_word_len = 25  # Max. word length.
	# File-based words: 504,279.
	is_mixed_words_used = True
	if is_mixed_words_used:
		num_simple_examples, num_random_examples = int(5e5), int(5e5)  # For mixed words.
	else:
		word_type = 'simple_word'  # {'simple_word', 'random_word', 'aihub_word', 'file_based_word'}.
		num_train_examples, num_test_examples = int(1e6), int(1e4)  # For simple and random words.
	word_len_interval = (1, max_word_len)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'ctc', 'xent', 'nll'}.
	max_gradient_norm = 5  # Gradient clipping value.
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	if loss_type == 'ctc':
		model_filepath_base = './word_recognition_mixup_rare1_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	elif loss_type in ['xent', 'nll']:
		model_filepath_base = './word_recognition_mixup_rare1_attn_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_word_len, image_height, image_width, image_channel)
	else:
		raise ValueError('Invalid loss type, {}'.format(loss_type))
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	if loss_type == 'ctc':
		BLANK_LABEL = '<BLANK>'  # The BLANK label for CTC.
		label_converter = swl_langproc_util.TokenConverter([BLANK_LABEL] + list(charset), pad=None)  # NOTE [info] >> It's a trick. The ID of the BLANK label is set to 0.
		assert label_converter.encode([BLANK_LABEL], is_bare_output=True)[0] == 0, '{} != 0'.format(label_converter.encode([BLANK_LABEL], is_bare_output=True)[0])
		BLANK_LABEL_ID = 0 #label_converter.encode([BLANK_LABEL], is_bare_output=True)[0]
		SOS_ID, EOS_ID = None, None
		num_suffixes = 0
	elif loss_type in ['xent', 'nll']:
		BLANK_LABEL = None
		SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
		if is_separate_pad_id_used:
			# When <PAD> token has a separate valid token ID.
			PAD_TOKEN = '<PAD>'
			PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
			label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
			assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
			assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
		else:
			#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
			label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
		del SOS_TOKEN, EOS_TOKEN
		assert label_converter.PAD is not None
		SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
		num_suffixes = 1

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_words_used:
		train_dataloader, test_dataloader = create_mixed_word_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_word_data_loaders(word_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_word_len, word_len_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_rare1_mixup_model(label_converter, image_height, image_width, image_channel, loss_type, lang, max_word_len, num_suffixes, SOS_ID, BLANK_LABEL if loss_type == 'ctc' else None)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
				glogger.info(f'Skip {name} as it has already been initialized.')
				continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def evaluate_word_recognizer_using_aihub_data(max_label_len, batch_size, is_separate_pad_id_used=False, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height, image_width, image_channel = 64, 1920, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	image_types_to_load = ['word']  # {'syllable', 'word', 'sentence'}.
	is_preloaded_image_used = False

	shuffle = False
	num_workers = 8

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	gpu = 0
	device = torch.device('cuda:{}'.format(gpu) if torch.cuda.is_available() and gpu >= 0 else 'cpu')
	glogger.info('Device: {}.'.format(device))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None
	SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
	num_suffixes = 1

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
	aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

	test_transform = torchvision.transforms.Compose([
		#ResizeImageToFixedSizeWithPadding(image_height, image_width, warn_about_small_image=True),
		ResizeImageWithMaxWidth(image_height, image_width, warn_about_small_image=True),  # batch_size must be 1.
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	glogger.info('Start creating a dataset and a dataloader...')
	start_time = time.time()
	test_dataset = aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_label_len, is_preloaded_image_used, transform=test_transform, target_transform=test_target_transform)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('End creating a dataset and a dataloader: {} secs.'.format(time.time() - start_time))
	glogger.info('#examples = {}.'.format(len(test_dataset)))
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	glogger.info('Start building a model...')
	start_time = time.time()
	if True:
		# For RARE2.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_rare2_attn_xent_gradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9514_epoch3.pth'

		model, infer_functor, _, _ = build_rare2_model(label_converter, image_height, image_width, image_channel, lang, loss_type=None, max_time_steps=max_label_len + num_suffixes, sos_id=SOS_ID)
	elif False:
		# For ASTER + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster_sxent_nogradclip_allparams_nopad_kor_ch5_64x640x3_acc0.8449_epoch3.pth'

		model, infer_functor, _, _ = build_aster_model(label_converter, image_height, image_width, image_channel, lang, max_label_len, EOS_ID)
	elif False:
		# For ASTER + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster+onmt_xent_nogradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9325_epoch2.pth'

		model, infer_functor, _, _ = build_aster_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device=device)
	else:
		raise ValueError('Undefined model')
	assert model_filepath_to_load is not None
	glogger.info('End building a model: {} secs.'.format(time.time() - start_time))

	# Load a model.
	glogger.info('Start loading a pretrained model from {}.'.format(model_filepath_to_load))
	start_time = time.time()
	model = load_model(model_filepath_to_load, model, device=device)
	glogger.info('End loading a pretrained model: {} secs.'.format(time.time() - start_time))

	model = model.to(device)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	error_cases_dir_path = './text_error_cases'
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=error_cases_dir_path, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_textline_recognizer_based_on_opennmt(num_epochs=20, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	#image_height, image_width, image_channel = 64, 640, 3
	image_height, image_width, image_channel = 64, 1280, 3
	#image_height, image_width, image_channel = 64, 1920, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	encoder_type = 'onmt'  # {'onmt', 'rare1', 'rare2', 'aster'}.

	lang = 'kor'  # {'kor', 'eng'}.
	max_textline_len = 50  # Max. text line length.
	# File-based text lines: 55,835.
	is_mixed_textlines_used = True
	if is_mixed_textlines_used:
		num_simple_examples, num_random_examples, num_trdg_examples = int(5e4), int(5e4), int(5e4)  # For mixed text lines.
	else:
		textline_type = 'simple_textline'  # {'simple_textline', 'random_textline', 'trdg_textline', 'aihub_textline', 'file_based_textline'}.
		num_train_examples, num_test_examples = int(2e5), int(2e3)  # For simple, random, and TRDG text lines.
	word_len_interval = (1, 20)
	word_count_interval = (1, 5)
	space_count_interval = (1, 3)
	char_space_ratio_interval = (0.8, 1.25)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'xent'  # {'xent', 'nll'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './textline_recognition_onmt_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_textline_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_textlines_used:
		train_dataloader, test_dataloader = create_mixed_textline_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, num_trdg_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_textline_data_loaders(textline_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_opennmt_model(label_converter, image_height, image_width, image_channel, max_textline_len, encoder_type, lang, loss_type)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	model.generator = model.generator.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	#optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[4, 5], gamma=0.1)

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def train_textline_recognizer_based_on_transformer(num_epochs=40, batch_size=64, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	#image_height, image_width, image_channel = 64, 640, 3
	image_height, image_width, image_channel = 64, 1280, 3
	#image_height, image_width, image_channel = 64, 1920, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	max_textline_len = 50  # Max. text line length.
	# File-based text lines: 55,835.
	is_mixed_textlines_used = True
	if is_mixed_textlines_used:
		num_simple_examples, num_random_examples, num_trdg_examples = int(5e4), int(5e4), int(5e4)  # For mixed text lines.
	else:
		textline_type = 'simple_textline'  # {'simple_textline', 'random_textline', 'trdg_textline', 'aihub_textline', 'file_based_textline'}.
		num_train_examples, num_test_examples = int(2e5), int(2e3)  # For simple, random, and TRDG text lines.
	word_len_interval = (1, 20)
	word_count_interval = (1, 5)
	space_count_interval = (1, 3)
	char_space_ratio_interval = (0.8, 1.25)
	font_size_interval = (10, 100)
	color_functor = functools.partial(generate_font_colors, image_depth=image_channel)

	loss_type = 'kldiv'  # {'kldiv'}.
	#max_gradient_norm = 20  # Gradient clipping value.
	max_gradient_norm = None
	train_test_ratio = 0.8
	shuffle = True
	num_workers = 8
	log_print_freq = 1000

	model_filepath_to_load = None
	is_model_loaded = model_filepath_to_load is not None
	is_model_initialized = True
	is_all_model_params_optimized = True
	is_separate_pad_id_used = False

	assert not is_model_loaded or (is_model_loaded and model_filepath_to_load is not None)

	gradclip_nogradclip = 'gradclip' if max_gradient_norm else 'nogradclip'
	allparams_gradparams = 'allparams' if is_all_model_params_optimized else 'gradparams'
	pad_nopad = 'pad' if is_separate_pad_id_used else 'nopad'
	model_filepath_base = './textline_recognition_transformer_{}_{}_{}_{}_{}_ch{}_{}x{}x{}'.format(loss_type, gradclip_nogradclip, allparams_gradparams, pad_nopad, lang, max_textline_len, image_height, image_width, image_channel)
	model_filepath_format = model_filepath_base + '{}.pth'
	glogger.info('Model filepath: {}.'.format(model_filepath_format.format('')))

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None

	chars = charset.replace(' ', '')  # Remove the blank space. Can make the number of each character different.
	if is_mixed_textlines_used:
		train_dataloader, test_dataloader = create_mixed_textline_data_loaders(label_converter, wordset, chars, num_simple_examples, num_random_examples, num_trdg_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	else:
		train_dataloader, test_dataloader = create_textline_data_loaders(textline_type, label_converter, wordset, chars, num_train_examples, num_test_examples, train_test_ratio, image_height, image_width, image_channel, image_height_before_crop, image_width_before_crop, max_textline_len, word_len_interval, word_count_interval, space_count_interval, char_space_ratio_interval, font_list, font_size_interval, color_functor, batch_size, shuffle, num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0], label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(train_dataloader, label_converter, visualize=False, mode='Train')
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	#--------------------
	# Build a model.

	model, infer_functor, train_forward_functor, criterion = build_transformer_ocr_model(label_converter, image_height, image_width, image_channel, max_textline_len, lang, is_train=True)

	if is_model_initialized:
		# Initialize model weights.
		for name, param in model.named_parameters():
			#if 'localization_fc2' in name:  # Exists in rare.modules.transformation.TPS_SpatialTransformerNetwork.
			#	glogger.info(f'Skip {name} as it has already been initialized.')
			#	continue
			try:
				if 'bias' in name:
					torch.nn.init.constant_(param, 0.0)
				elif 'weight' in name:
					torch.nn.init.kaiming_normal_(param)
			except Exception as ex:  # For batch normalization.
				if 'weight' in name:
					param.data.fill_(1)
				continue
	if is_model_loaded:
		# Load a model.
		model = load_model(model_filepath_to_load, model, device=device)

	model = model.to(device)
	criterion = criterion.to(device)

	#--------------------
	# Train the model.

	if is_all_model_params_optimized:
		model_params = list(model.parameters())
	else:
		# Filter model parameters only that require gradients.
		#model_params = filter(lambda p: p.requires_grad, model.parameters())
		model_params, num_model_params = list(), 0
		for p in filter(lambda p: p.requires_grad, model.parameters()):
			model_params.append(p)
			num_model_params += np.prod(p.size())
		glogger.info('#trainable model parameters = {}.'.format(num_model_params))
		#glogger.info('Trainable model parameters:')
		#[glogger.info(name, p.numel()) for name, p in filter(lambda p: p[1].requires_grad, model.named_parameters())]

	# Define an optimizer.
	#optimizer = torch.optim.SGD(model_params, lr=1.0, momentum=0.9, dampening=0, weight_decay=0, nesterov=False)
	#optimizer = torch.optim.Adam(model_params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
	#optimizer = torch.optim.Adadelta(model_params, lr=1.0, rho=0.9, eps=1e-06, weight_decay=0)
	#optimizer = torch.optim.Adagrad(model_params, lr=0.1, lr_decay=0, weight_decay=0, initial_accumulator_value=0, eps=1e-10)
	#optimizer = torch.optim.RMSprop(model_params, lr=0.01, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0, centered=False)
	import transformer_ocr.train
	optimizer = torch.optim.Adam(model_params, lr=0, betas=(0.9, 0.98), eps=1e-09, weight_decay=0, amsgrad=False)
	optimizer = transformer_ocr.train.NoamOpt(model.tgt_embed[0].d_model, factor=1, warmup=2000, optimizer=optimizer)
	#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
	scheduler = None

	#--------------------
	glogger.info('Start training...')
	start_time = time.time()
	model, best_model_filepath = train_text_recognition_model(model, criterion, train_forward_functor, infer_functor, label_converter, train_dataloader, test_dataloader, optimizer, num_epochs, log_print_freq, model_filepath_format, scheduler, max_gradient_norm, model_params, device)
	glogger.info('End training: {} secs.'.format(time.time() - start_time))

	# Save a model.
	if best_model_filepath:
		model_filepath = model_filepath_format.format('_best_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
		try:
			shutil.copyfile(best_model_filepath, model_filepath)
			glogger.info('Copied the best trained model to {}.'.format(model_filepath))
		except (FileNotFoundError, PermissionError) as ex:
			glogger.warning('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
	else:
		if model:
			model_filepath = model_filepath_format.format('_final_{}'.format(datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))
			save_model(model_filepath, model)

	#--------------------
	# Evaluate the model.

	glogger.info('Start evaluating...')
	start_time = time.time()
	model.eval()
	evaluate_text_recognition_model(model, infer_functor, label_converter, test_dataloader, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=None, device=device)
	glogger.info('End evaluating: {} secs.'.format(time.time() - start_time))

def recognize_character_using_craft(device='cpu'):
	import craft.imgproc as imgproc
	#import craft.file_utils as file_utils
	import craft.test_utils as test_utils

	image_height, image_width, image_channel = 64, 64, 3

	model_name = 'ResNet'  # {'VGG', 'ResNet', 'RCNN'}.
	input_channel, output_channel = image_channel, 1024

	charset = tg_util.construct_charset()

	# For CRAFT.
	craft_trained_model_filepath = './craft/craft_mlt_25k.pth'
	craft_refiner_model_filepath = './craft/craft_refiner_CTW1500.pth'  # Pretrained refiner model.
	craft_refine = False  # Enable link refiner.
	craft_cuda = gpu >= 0  # Use cuda for inference.

	# For char recognizer.
	#recognizer_model_filepath = './craft/char_recognition.pth'
	recognizer_model_filepath = './craft/char_recognition_mixup.pth'

	#image_filepath = './craft/images/I3.jpg'
	image_filepath = './craft/images/book_1.png'
	#image_filepath = './craft/images/book_2.png'

	output_dir_path = './char_recog_results'

	#--------------------
	label_converter = swl_langproc_util.TokenConverter(list(charset))
	num_classes = label_converter.num_tokens

	glogger.info('Start loading CRAFT...')
	start_time = time.time()
	craft_net, craft_refine_net = test_utils.load_craft(craft_trained_model_filepath, craft_refiner_model_filepath, craft_refine, craft_cuda)
	glogger.info('End loading CRAFT: {} secs.'.format(time.time() - start_time))

	glogger.info('Start loading char recognizer...')
	start_time = time.time()
	import rare.model_char
	recognizer = rare.model_char.create_model(model_name, input_channel, output_channel, num_classes)

	recognizer = load_model(recognizer_model_filepath, recognizer, device=device)
	recognizer = recognizer.to(device)
	glogger.info('End loading char recognizer: {} secs.'.format(time.time() - start_time))

	#--------------------
	glogger.info('Start running CRAFT...')
	start_time = time.time()
	rgb = imgproc.loadImage(image_filepath)  # RGB order.
	bboxes, ch_bboxes_lst, score_text = test_utils.run_char_craft(rgb, craft_net, craft_refine_net, craft_cuda)
	glogger.info('End running CRAFT: {} secs.'.format(time.time() - start_time))

	if len(bboxes) > 0:
		os.makedirs(output_dir_path, exist_ok=True)

		glogger.info('Start inferring...')
		start_time = time.time()
		image = cv2.imread(image_filepath)

		"""
		cv2.imshow('Input', image)
		rgb1, rgb2 = image.copy(), image.copy()
		for bbox, ch_bboxes in zip(bboxes, ch_bboxes_lst):
			color = (random.randint(128, 255), random.randint(128, 255), random.randint(128, 255))
			cv2.drawContours(rgb1, [np.round(np.expand_dims(bbox, axis=1)).astype(np.int32)], 0, color, 1, cv2.LINE_AA)
			for bbox in ch_bboxes:
				cv2.drawContours(rgb2, [np.round(np.expand_dims(bbox, axis=1)).astype(np.int32)], 0, color, 1, cv2.LINE_AA)
		cv2.imshow('Word BBox', rgb1)
		cv2.imshow('Char BBox', rgb2)
		cv2.waitKey(0)
		"""

		ch_images = list()
		rgb = image.copy()
		for i, ch_bboxes in enumerate(ch_bboxes_lst):
			imgs = list()
			color = (random.randint(128, 255), random.randint(128, 255), random.randint(128, 255))
			for j, bbox in enumerate(ch_bboxes):
				(x1, y1), (x2, y2) = np.min(bbox, axis=0), np.max(bbox, axis=0)
				x1, y1, x2, y2 = round(float(x1)), round(float(y1)), round(float(x2)), round(float(y2))
				img = image[y1:y2+1,x1:x2+1]
				imgs.append(img)

				cv2.imwrite(os.path.join(output_dir_path, 'ch_{}_{}.png'.format(i, j)), img)

				cv2.rectangle(rgb, (x1, y1), (x2, y2), color, 1, cv2.LINE_4)
			ch_images.append(imgs)
		cv2.imwrite(os.path.join(output_dir_path, 'char_bbox.png'), rgb)

		#--------------------
		transform = torchvision.transforms.Compose([
			#RandomInvert(),
			ConvertPILMode(mode='RGB'),
			# TODO [decide] >> Which one is correct?
			ResizeImageToFixedSizeWithPadding(image_height, image_width, warn_about_small_image=True),
			#ResizeImageWithMaxWidth(image_height, image_width, warn_about_small_image=True),  # batch_size must be 1.
			#torchvision.transforms.Resize((image_height, image_width)),
			#torchvision.transforms.CenterCrop((image_height, image_width)),
			torchvision.transforms.ToTensor(),
			torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
		])

		recognizer.eval()
		with torch.no_grad():
			for idx, imgs in enumerate(ch_images):
				imgs = torch.stack([transform(Image.fromarray(img)) for img in imgs]).to(device)

				predictions = recognizer(imgs)

				_, predictions = torch.max(predictions, 1)
				predictions = predictions.cpu().numpy()
				glogger.info('\t{}: {} (int), {} (str).'.format(idx, predictions, ''.join(label_converter.decode(predictions))))
		glogger.info('End inferring: {} secs.'.format(time.time() - start_time))
	else:
		glogger.info('No text detected.')

def recognize_word_using_craft(device='cpu'):
	import craft.imgproc as imgproc
	#import craft.file_utils as file_utils
	import craft.test_utils as test_utils

	image_height, image_width, image_channel = 64, 64, 3

	num_fiducials = 20  # The number of fiducial points of TPS-STN.
	input_channel = image_channel  # The number of input channel of feature extractor.
	output_channel = 512  # The number of output channel of feature extractor.
	hidden_size = 256  # The size of the LSTM hidden states.
	transformer = 'TPS'  # The type of transformer. {None, 'TPS'}.
	feature_extractor = 'VGG'  # The type of feature extractor. {'VGG', 'RCNN', 'ResNet'}.
	sequence_model = 'BiLSTM'  # The type of sequence model. {None, 'BiLSTM'}.
	decoder = 'Attn'  # The type of decoder. {'CTC', 'Attn'}.
	max_word_len = 25  # Max. word length.

	charset = tg_util.construct_charset()

	# For CRAFT.
	craft_trained_model_filepath = './craft/craft_mlt_25k.pth'
	craft_refiner_model_filepath = './craft/craft_refiner_CTW1500.pth'  # Pretrained refiner model.
	craft_refine = False  # Enable link refiner.
	craft_cuda = gpu >= 0  # Use cuda for inference.

	# For word recognizer.
	recognizer_model_filepath = './craft/word_recognition.pth'
	#recognizer_model_filepath = './craft/word_recognition_mixup.pth'

	#image_filepath = './craft/images/I3.jpg'
	image_filepath = './craft/images/book_1.png'
	#image_filepath = './craft/images/book_2.png'

	output_dir_path = './word_recog_results'

	#--------------------
	if decoder == 'CTC':
		BLANK_LABEL = '<BLANK>'  # The BLANK label for CTC.
		label_converter = swl_langproc_util.TokenConverter([BLANK_LABEL] + list(charset), pad=None)  # NOTE [info] >> It's a trick. The ID of the BLANK label is set to 0.
		assert label_converter.encode([BLANK_LABEL], is_bare_output=True)[0] == 0, '{} != 0'.format(label_converter.encode([BLANK_LABEL], is_bare_output=True)[0])
		BLANK_LABEL_ID = 0 #label_converter.encode([BLANK_LABEL], is_bare_output=True)[0]
		SOS_ID, EOS_ID = None, None
		num_suffixes = 0
	else:
		is_separate_pad_id_used = False
		BLANK_LABEL = None
		SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
		if is_separate_pad_id_used:
			# When <PAD> token has a separate valid token ID.
			PAD_TOKEN = '<PAD>'
			PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
			label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
			assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
			assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
		else:
			#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
			label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
		del SOS_TOKEN, EOS_TOKEN
		assert label_converter.PAD is not None
		SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
		num_suffixes = 1
	num_classes = label_converter.num_tokens

	glogger.info('Start loading CRAFT...')
	start_time = time.time()
	craft_net, craft_refine_net = test_utils.load_craft(craft_trained_model_filepath, craft_refiner_model_filepath, craft_refine, craft_cuda)
	glogger.info('End loading CRAFT: {} secs.'.format(time.time() - start_time))

	glogger.info('Start loading word recognizer...')
	start_time = time.time()
	import rare.model
	recognizer = rare.model.Model(image_height, image_width, num_classes, num_fiducials, input_channel, output_channel, hidden_size, max_word_len + num_suffixes, SOS_ID, label_converter.pad_id, transformer, feature_extractor, sequence_model, decoder)

	recognizer = load_model(recognizer_model_filepath, recognizer, device=device)
	recognizer = recognizer.to(device)
	glogger.info('End loading word recognizer: {} secs.'.format(time.time() - start_time))

	#--------------------
	glogger.info('Start running CRAFT...')
	start_time = time.time()
	rgb = imgproc.loadImage(image_filepath)  # RGB order.
	bboxes, polys, score_text = test_utils.run_word_craft(rgb, craft_net, craft_refine_net, craft_cuda)
	glogger.info('End running CRAFT: {} secs.'.format(time.time() - start_time))

	if len(bboxes) > 0:
		os.makedirs(output_dir_path, exist_ok=True)

		glogger.info('Start inferring...')
		start_time = time.time()
		image = cv2.imread(image_filepath)

		"""
		cv2.imshow('Input', image)
		rgb1, rgb2 = image.copy(), image.copy()
		for bbox, poly in zip(bboxes, polys):
			color = (random.randint(128, 255), random.randint(128, 255), random.randint(128, 255))
			cv2.drawContours(rgb1, [np.round(np.expand_dims(bbox, axis=1)).astype(np.int32)], 0, color, 1, cv2.LINE_AA)
			cv2.drawContours(rgb2, [np.round(np.expand_dims(poly, axis=1)).astype(np.int32)], 0, color, 1, cv2.LINE_AA)
		cv2.imshow('BBox', rgb1)
		cv2.imshow('Poly', rgb2)
		cv2.waitKey(0)
		"""

		word_images = list()
		rgb = image.copy()
		for idx, bbox in enumerate(bboxes):
			(x1, y1), (x2, y2) = np.min(bbox, axis=0), np.max(bbox, axis=0)
			x1, y1, x2, y2 = round(float(x1)), round(float(y1)), round(float(x2)), round(float(y2))
			img = image[y1:y2+1,x1:x2+1]
			word_images.append(img)

			cv2.imwrite(os.path.join(output_dir_path, 'word_{}.png'.format(idx)), img)

			cv2.rectangle(rgb, (x1, y1), (x2, y2), (random.randint(128, 255), random.randint(128, 255), random.randint(128, 255)), 1, cv2.LINE_4)
		cv2.imwrite(os.path.join(output_dir_path, 'word_bbox.png'), rgb)

		#--------------------
		transform = torchvision.transforms.Compose([
			#RandomInvert(),
			ConvertPILMode(mode='RGB'),
			#ResizeImageToFixedSizeWithPadding(image_height, image_width, warn_about_small_image=True),
			ResizeImageWithMaxWidth(image_height, image_width, warn_about_small_image=True),  # batch_size must be 1.
			#torchvision.transforms.Resize((image_height, image_width)),
			#torchvision.transforms.CenterCrop((image_height, image_width)),
			torchvision.transforms.ToTensor(),
			torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
		])

		recognizer.eval()
		with torch.no_grad():
			imgs = torch.stack([transform(Image.fromarray(img)) for img in word_images]).to(device)

			predictions = recognizer(imgs)

			_, predictions = torch.max(predictions, 1)
			predictions = predictions.cpu().numpy()
			for idx, pred in enumerate(predictions):
				glogger.info('\t{}: {} (int), {} (str).'.format(idx, pred, ''.join(label_converter.decode(pred))))
		glogger.info('End inferring: {} secs.'.format(time.time() - start_time))
	else:
		glogger.info('No text detected.')

def recognize_text_using_aihub_data(image_types_to_load, max_label_len, batch_size, is_separate_pad_id_used=True, device='cpu'):
	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height, image_width, image_channel = 64, 1920, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	is_preloaded_image_used = False

	shuffle = False
	num_workers = 8

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None
	SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
	num_suffixes = 1

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
	aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

	test_transform = torchvision.transforms.Compose([
		#ResizeImageToFixedSizeWithPadding(image_height, image_width, warn_about_small_image=True),
		ResizeImageWithMaxWidth(image_height, image_width, warn_about_small_image=True),  # batch_size must be 1.
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	glogger.info('Start creating a dataset and a dataloader...')
	start_time = time.time()
	test_dataset = aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_label_len, is_preloaded_image_used, transform=test_transform, target_transform=test_target_transform)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('End creating a dataset and a dataloader: {} secs.'.format(time.time() - start_time))
	glogger.info('#examples = {}.'.format(len(test_dataset)))
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	inputs, outputs = list(), list()
	try:
		for images, labels, _ in test_dataloader:
			inputs.append(images)
			outputs.append(labels)
	except Exception as ex:
		glogger.warning('Exception raised: {}.'.format(ex))
	inputs = torch.cat(inputs)
	outputs = torch.cat(outputs)

	#--------------------
	# Build a model.

	glogger.info('Start building a model...')
	start_time = time.time()
	if False:
		# For RARE2.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_rare2_attn_xent_gradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9514_epoch3.pth'

		model, infer_functor, _, _ = build_rare2_model(label_converter, image_height, image_width, image_channel, lang, loss_type=None, max_time_steps=max_label_len + num_suffixes, sos_id=SOS_ID)
	elif False:
		# For ASTER.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster_sxent_nogradclip_allparams_nopad_kor_ch5_64x640x3_acc0.8449_epoch3.pth'

		model, infer_functor, _, _ = build_aster_model(label_converter, image_height, image_width, image_channel, lang, max_label_len, EOS_ID)
	elif True:
		# For OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_onmt_xent_nogradclip_allparams_nopad_kor_ch5_64x640x3_best_20200725T115106.pth'

		encoder_type = 'onmt'  # {'onmt', 'rare1', 'rare2', 'aster'}.
		model, infer_functor, _, _ = build_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, encoder_type, lang, loss_type=None)
	elif False:
		# For RARE2 + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_rare2+onmt_xent_nogradclip_allparams_nopad_kor_ch5_64x640x3_acc0.9441_epoch20_new.pth'

		model, infer_functor, _, _ = build_rare2_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device=device)
	elif False:
		# For ASTER + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster+onmt_xent_nogradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9325_epoch2_new.pth'

		model, infer_functor, _, _ = build_aster_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device=device)
	elif False:
		# For transformer.
		model_filepath_to_load = './training_outputs_textline_recognition/textline_recognition_transformer_kldiv_nogradclip_allparams_pad_kor_ch10_64x1280x3_acc0.9794_epoch19.pth'

		model, infer_functor, _, _ = build_transformer_ocr_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, is_train=False)
	else:
		raise ValueError('Undefined model')
	assert model_filepath_to_load is not None
	glogger.info('End building a model: {} secs.'.format(time.time() - start_time))

	# Load a model.
	glogger.info('Start loading a pretrained model from {}.'.format(model_filepath_to_load))
	start_time = time.time()
	model = load_model(model_filepath_to_load, model, device=device)
	glogger.info('End loading a pretrained model: {} secs.'.format(time.time() - start_time))

	model = model.to(device)

	#--------------------
	# Infer by the model.

	glogger.info('Start inferring...')
	start_time = time.time()
	model.eval()
	#outputs = None
	error_cases_dir_path = './text_error_cases'
	infer_using_text_recognition_model(model, infer_functor, label_converter, inputs, outputs=outputs, batch_size=batch_size, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=error_cases_dir_path, device=device)
	glogger.info('End inferring: {} secs.'.format(time.time() - start_time))

def recognize_text_one_by_one_using_aihub_data(image_types_to_load, max_label_len, is_separate_pad_id_used=True, device='cpu'):
	batch_size = 1

	#image_height, image_width, image_channel = 32, 100, 3
	image_height, image_width, image_channel = 64, 640, 3
	#image_height, image_width, image_channel = 64, 1280, 3
	#image_height, image_width, image_channel = 64, 1920, 3
	#image_height_before_crop, image_width_before_crop = int(image_height * 1.1), int(image_width * 1.1)
	image_height_before_crop, image_width_before_crop = image_height, image_width

	lang = 'kor'  # {'kor', 'eng'}.
	is_preloaded_image_used = False

	shuffle = False
	num_workers = 8

	if lang == 'kor':
		charset, wordset = tg_util.construct_charset(), tg_util.construct_word_set(korean=True, english=True)
		font_list = construct_font(korean=True, english=False)
	elif lang == 'eng':
		charset, wordset = tg_util.construct_charset(hangeul=False), tg_util.construct_word_set(korean=False, english=True)
		font_list = construct_font(korean=False, english=True)
	else:
		raise ValueError('Invalid language, {}'.format(lang))

	#--------------------
	# Prepare data.

	SOS_TOKEN, EOS_TOKEN = '<SOS>', '<EOS>'
	if is_separate_pad_id_used:
		# When <PAD> token has a separate valid token ID.
		PAD_TOKEN = '<PAD>'
		PAD_ID = len(charset)  # NOTE [info] >> It's a trick which makes <PAD> token have a separate valid token.
		label_converter = swl_langproc_util.TokenConverter(list(charset) + [PAD_TOKEN], sos=SOS_TOKEN, eos=EOS_TOKEN, pad=PAD_ID)
		assert label_converter.pad_id == PAD_ID, '{} != {}'.format(label_converter.pad_id, PAD_ID)
		assert label_converter.encode([PAD_TOKEN], is_bare_output=True)[0] == PAD_ID, '{} != {}'.format(label_converter.encode([PAD_TOKEN], is_bare_output=True)[0], PAD_ID)
	else:
		#label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=SOS_TOKEN)  # <PAD> = <SOS>.
		label_converter = swl_langproc_util.TokenConverter(list(charset), sos=SOS_TOKEN, eos=EOS_TOKEN, pad=EOS_TOKEN)  # <PAD> = <EOS>.
	del SOS_TOKEN, EOS_TOKEN
	assert label_converter.PAD is not None
	SOS_ID, EOS_ID = label_converter.encode([label_converter.SOS], is_bare_output=True)[0], label_converter.encode([label_converter.EOS], is_bare_output=True)[0]
	num_suffixes = 1

	if 'posix' == os.name:
		data_base_dir_path = '/home/sangwook/work/dataset'
	else:
		data_base_dir_path = 'D:/work/dataset'

	aihub_data_json_filepath = data_base_dir_path + '/ai_hub/korean_font_image/printed/printed_data_info.json'
	aihub_data_dir_path = data_base_dir_path + '/ai_hub/korean_font_image/printed'

	test_transform = torchvision.transforms.Compose([
		#ResizeImageToFixedSizeWithPadding(image_height, image_width, warn_about_small_image=True),
		ResizeImageWithMaxWidth(image_height, image_width, warn_about_small_image=True),  # batch_size must be 1.
		#torchvision.transforms.Resize((image_height, image_width)),
		#torchvision.transforms.CenterCrop((image_height, image_width)),
		torchvision.transforms.ToTensor(),
		torchvision.transforms.Normalize(mean=(0.5,) * image_channel, std=(0.5,) * image_channel)  # [0, 1] -> [-1, 1].
	])
	test_target_transform = ToIntTensor()

	glogger.info('Start creating a dataset and a dataloader...')
	start_time = time.time()
	test_dataset = aihub_data.AiHubPrintedTextDataset(label_converter, aihub_data_json_filepath, aihub_data_dir_path, image_types_to_load, image_height, image_width, image_channel, max_label_len, is_preloaded_image_used, transform=test_transform, target_transform=test_target_transform)
	test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)
	classes, num_classes = label_converter.tokens, label_converter.num_tokens
	glogger.info('End creating a dataset and a dataloader: {} secs.'.format(time.time() - start_time))
	glogger.info('#examples = {}.'.format(len(test_dataset)))
	glogger.info('#classes = {}.'.format(num_classes))
	glogger.info('<PAD> = {}, <SOS> = {}, <EOS> = {}, <UNK> = {}.'.format(label_converter.pad_id, SOS_ID, EOS_ID, label_converter.encode([label_converter.UNKNOWN], is_bare_output=True)[0]))

	# Show data info.
	show_text_data_info(test_dataloader, label_converter, visualize=False, mode='Test')

	inputs, outputs = list(), list()
	try:
		for images, labels, _ in test_dataloader:
			inputs.append(images)
			outputs.append(labels)
	except Exception as ex:
		glogger.warning('Exception raised: {}.'.format(ex))

	#--------------------
	# Build a model.

	glogger.info('Start building a model...')
	start_time = time.time()
	if False:
		# For RARE2.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_rare2_attn_xent_gradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9514_epoch3.pth'

		model, infer_functor, _, _ = build_rare2_model(label_converter, image_height, image_width, image_channel, lang, loss_type=None, max_time_steps=max_label_len + num_suffixes, sos_id=SOS_ID)
	elif False:
		# For ASTER.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster_sxent_nogradclip_allparams_nopad_kor_ch5_64x640x3_acc0.8449_epoch3.pth'

		model, infer_functor, _, _ = build_aster_model(label_converter, image_height, image_width, image_channel, lang, max_label_len, EOS_ID)
	elif True:
		# For OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_onmt_xent_nogradclip_allparams_nopad_kor_ch5_64x640x3_best_20200725T115106.pth'

		encoder_type = 'onmt'  # {'onmt', 'rare1', 'rare2', 'aster'}.
		model, infer_functor, _, _ = build_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, encoder_type, lang, loss_type=None)
	elif False:
		# For RARE2 + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_rare2+onmt_xent_nogradclip_allparams_nopad_kor_ch5_64x640x3_acc0.9441_epoch20_new.pth'

		model, infer_functor, _, _ = build_rare2_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device=device)
	elif False:
		# For ASTER + OpenNMT.
		model_filepath_to_load = './training_outputs_word_recognition/word_recognition_aster+onmt_xent_nogradclip_allparams_nopad_kor_large_ch20_64x1280x3_acc0.9325_epoch2_new.pth'

		model, infer_functor, _, _ = build_aster_and_opennmt_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, loss_type=None, device=device)
	elif False:
		# For transformer.
		model_filepath_to_load = './training_outputs_textline_recognition/textline_recognition_transformer_kldiv_nogradclip_allparams_pad_kor_ch10_64x1280x3_acc0.9794_epoch19.pth'

		model, infer_functor, _, _ = build_transformer_ocr_model(label_converter, image_height, image_width, image_channel, max_label_len, lang, is_train=False)
	else:
		raise ValueError('Undefined model')
	assert model_filepath_to_load is not None
	glogger.info('End building a model: {} secs.'.format(time.time() - start_time))

	# Load a model.
	glogger.info('Start loading a pretrained model from {}.'.format(model_filepath_to_load))
	start_time = time.time()
	model = load_model(model_filepath_to_load, model, device=device)
	glogger.info('End loading a pretrained model: {} secs.'.format(time.time() - start_time))

	model = model.to(device)

	#--------------------
	# Infer by the model.

	glogger.info('Start inferring...')
	start_time = time.time()
	model.eval()
	#outputs = None
	error_cases_dir_path = './text_error_cases'
	infer_one_by_one_using_text_recognition_model(model, infer_functor, label_converter, inputs, outputs=outputs, is_case_sensitive=False, show_acc_per_char=True, error_cases_dir_path=error_cases_dir_path, device=device)
	glogger.info('End inferring: {} secs.'.format(time.time() - start_time))

#--------------------------------------------------------------------

def parse_command_line_options():
	parser = argparse.ArgumentParser(description='Runner for text recognition models.')

	"""
	parser.add_argument(
		'--train',
		action='store_true',
		help='Specify whether to train a model'
	)
	parser.add_argument(
		'--test',
		action='store_true',
		help='Specify whether to test a trained model'
	)
	parser.add_argument(
		'--infer',
		action='store_true',
		help='Specify whether to infer by a trained model'
	)
	"""
	parser.add_argument(
		'-m',
		'--model_file',
		type=str,
		#nargs='?',
		help='The model file path where a trained model is saved or a pretrained model is loaded',
		#required=True,
		default=None
	)
	parser.add_argument(
		'-o',
		'--out_dir',
		type=str,
		#nargs='?',
		help='The output directory path to save results such as images and log',
		#required=True,
		default=None
	)
	"""
	parser.add_argument(
		'-tr',
		'--train_data_dir',
		type=str,
		#nargs='?',
		help='The directory path of training data',
		default='./train_data'
	)
	parser.add_argument(
		'-te',
		'--test_data_dir',
		type=str,
		#nargs='?',
		help='The directory path of test data',
		default='./test_data'
	)
	"""
	parser.add_argument(
		'-e',
		'--epoch',
		type=int,
		help='Number of epochs to train',
		default=20
	)
	parser.add_argument(
		'-b',
		'--batch_size',
		type=int,
		help='Batch size',
		default=64
	)
	parser.add_argument(
		'-g',
		'--gpu',
		type=str,
		help='Specify GPU to use',
		default='0'
	)
	parser.add_argument(
		'-l',
		'--log',
		type=str,
		help='The name of logger and log files',
		default=None
	)
	parser.add_argument(
		'-ll',
		'--log_level',
		type=int,
		help='Log level, [0, 50]',  # {NOTSET=0, DEBUG=10, INFO=20, WARNING=WARN=30, ERROR=40, CRITICAL=FATAL=50}.
		default=None
	)
	parser.add_argument(
		'-ld',
		'--log_dir',
		type=str,
		help='The directory path to log',
		default=None
	)

	return parser.parse_args()

def get_logger(name, log_level=None, log_dir_path=None, is_rotating=True):
	if not log_level: log_level = logging.INFO
	if not log_dir_path: log_dir_path = './log'
	if not os.path.isdir(log_dir_path):
		os.makedirs(log_dir_path, exist_ok=True)

	log_filepath = os.path.join(log_dir_path, (name if name else 'swl') + '.log')
	if is_rotating:
		file_handler = logging.handlers.RotatingFileHandler(log_filepath, maxBytes=10000000, backupCount=10)
	else:
		file_handler = logging.FileHandler(log_filepath)
	stream_handler = logging.StreamHandler()

	formatter = logging.Formatter('[%(levelname)s][%(filename)s:%(lineno)s][%(asctime)s] [SWL] %(message)s')
	#formatter = logging.Formatter('[%(levelname)s][%(asctime)s] [SWL] %(message)s')
	file_handler.setFormatter(formatter)
	stream_handler.setFormatter(formatter)

	logger = logging.getLogger(name if name else __name__)
	logger.setLevel(log_level)  # {NOTSET=0, DEBUG=10, INFO=20, WARNING=WARN=30, ERROR=40, CRITICAL=FATAL=50}.
	logger.addHandler(file_handler) 
	logger.addHandler(stream_handler) 

	return logger

def main():
	args = parse_command_line_options()

	logger = get_logger(args.log if args.log else os.path.basename(os.path.normpath(__file__)), args.log_level if args.log_level else logging.INFO, args.log_dir, is_rotating=True)
	logger.info('----------------------------------------------------------------------')
	logger.info('Logger: name = {}, level = {}.'.format(logger.name, logger.level))
	logger.info('Command-line arguments: {}.'.format(sys.argv))
	logger.info('Command-line options: {}.'.format(vars(args)))
	logger.info('Python version: {}.'.format(sys.version.replace('\n', ' ')))
	logger.info('Torch version: {}.'.format(torch.__version__))
	logger.info('cuDNN version: {}.'.format(torch.backends.cudnn.version()))

	global glogger
	glogger = logger
	if glogger is not None:
		# REF [function] >> main() in ${SWDT_PYTHON_HOME}/ext/test/logging/logging_main.py.
		global print
		#print = glogger.info
		print = lambda *objects, sep=' ', end='\n', file=sys.stdout, flush=False: glogger.error(*objects) if file == sys.stderr else glogger.info(*objects)
	else:
		raise ValueError('Invalid global logger: {}'.format(glogger))

	"""
	if not args.train and not args.test and not args.infer:
		logger.error('At least one of command line options "--train", "--test", and "--infer" has to be specified.')
		return
	"""

	#if args.gpu:
	#	os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
	device = torch.device('cuda:{}'.format(args.gpu) if torch.cuda.is_available() and int(args.gpu) >= 0 else 'cpu')
	logger.info('Device: {}.'.format(device))

	#--------------------
	is_resumed = args.model_file is not None

	model_filepath, output_dir_path = os.path.normpath(args.model_file) if args.model_file else None, os.path.normpath(args.out_dir) if args.out_dir else None
	if model_filepath:
		if not output_dir_path:
			output_dir_path = os.path.dirname(model_filepath)
	else:
		if not output_dir_path:
			output_dir_prefix = 'text_recognition'
			output_dir_suffix = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
			output_dir_path = os.path.join('.', '{}_{}'.format(output_dir_prefix, output_dir_suffix))
		model_filepath = os.path.join(output_dir_path, 'model.pth')

	#--------------------
	#train_character_recognizer(args.epoch, args.batch_size, device)
	#train_character_recognizer_using_mixup(args.epoch, args.batch_size, device)

	#--------------------
	#train_word_recognizer_based_on_rare1(args.epoch, args.batch_size, device)  # Use RARE #1.
	#train_word_recognizer_based_on_rare2(args.epoch, args.batch_size, device)  # Use RARE #2.
	#train_word_recognizer_based_on_aster(args.epoch, args.batch_size, device)  # Use ASTER.

	#train_word_recognizer_based_on_opennmt(args.epoch, args.batch_size, device)  # Use OpenNMT.

	#train_word_recognizer_based_on_rare1_and_opennmt(args.epoch, args.batch_size, device)  # Use RARE #1 (encoder) + OpenNMT (decoder).
	#train_word_recognizer_based_on_rare2_and_opennmt(args.epoch, args.batch_size, device)  # Use RARE #2 (encoder) + OpenNMT (decoder).
	#train_word_recognizer_based_on_aster_and_opennmt(args.epoch, args.batch_size, device)  # Use ASTER (encoder) + OpenNMT (decoder).

	#train_word_recognizer_using_mixup(args.epoch, args.batch_size, device)  # Use RARE #1. Not working.

	#evaluate_word_recognizer_using_aihub_data(max_label_len=10, batch_size=args.batch_size, is_separate_pad_id_used=False, device=device)

	#--------------------
	#train_textline_recognizer_based_on_opennmt(args.epoch, args.batch_size, device)  # Use OpenNMT.

	train_textline_recognizer_based_on_transformer(args.epoch, args.batch_size, device)  # Use Transformer.

	#--------------------
	# Recognize text using CRAFT (scene text detector) + character recognizer.
	#recognize_character_using_craft(device)

	# Recognize word using CRAFT (scene text detector) + word recognizer.
	#recognize_word_using_craft(device)  # Use RARE #1.

	if False:
		# For word recognition.
		image_types_to_load = ['word']  # {'syllable', 'word', 'sentence'}.
		max_label_len = 10
	else:
		# For textline recognition.
		image_types_to_load = ['word', 'sentence']  # {'syllable', 'word', 'sentence'}.
		max_label_len = 30
	#recognize_text_using_aihub_data(image_types_to_load, max_label_len, batch_size=args.batch_size, is_separate_pad_id_used=True, device=device)
	#recognize_text_one_by_one_using_aihub_data(image_types_to_load, max_label_len, is_separate_pad_id_used=True, device=device)  # batch_size = 1.

#--------------------------------------------------------------------

# Usage:
#	python run_text_recognition.py --epoch 20 --batch 64 --gpu 0 --log text_recognition --log_dir ./log

if '__main__' == __name__:
	main()
