import random, functools
import numpy as np
import torch
import swl.language_processing.util as swl_langproc_util

#--------------------------------------------------------------------

def generate_font_colors(image_depth):
	#font_color = [255,] * image_depth  # White font color.
	font_color = [random.randrange(256) for _ in range(image_depth)]  # An RGB font color.
	#font_color = [random.randrange(256),] * image_depth  # A grayscale font color.
	#gray_val = random.randrange(255)
	#font_color = [gray_val,] * image_depth  # A lighter grayscale font color.
	#font_color = [random.randrange(gray_val, 256),] * image_depth  # A darker grayscale font color.
	#font_color = [random.randrange(128, 256),] * image_depth  # A light grayscale font color.
	#font_color = [random.randrange(0, 128),] * image_depth  # A dark grayscale font color.
	#bg_color = [0,] * image_depth  # Black background color.
	bg_color = [random.randrange(256) for _ in range(image_depth)]  # An RGB background color.
	#bg_color = [random.randrange(256),] * image_depth  # A grayscale background color.
	#bg_color = [random.randrange(gray_val, 256),] * image_depth  # A lighter grayscale background color.
	#bg_color = [gray_val,] * image_depth  # A darker grayscale background color.
	#bg_color = [random.randrange(0, 128),] * image_depth  # A dark grayscale background color.
	#bg_color = [random.randrange(128, 256),] * image_depth  # A light grayscale background color.
	return font_color, bg_color

class SingleCharacterDataset(torch.utils.data.Dataset):
	def __init__(self, num_examples_per_class, charset, fonts, font_size_interval, color_functor=None, transform=None, target_transform=None):
		self.charset = charset
		self.fonts = fonts
		self.font_size_interval = font_size_interval
		self.transform = transform
		self.target_transform = target_transform

		self.image_channel = 1
		if self.image_channel == 1:
			self.mode = 'L'
			#self.mode = '1'
		elif self.image_channel == 3:
			self.mode = 'RGB'
		elif self.image_channel == 4:
			self.mode = 'RGBA'
		else:
			raise ValueError('Invalid image channel, {}'.format(self.image_channel))

		self.color_functor = color_functor if color_functor else functools.partial(generate_font_colors, image_depth=self.image_channel)
		self.labels = list(self.charset * num_examples_per_class)
		random.shuffle(self.labels)

	def __len__(self):
		return len(self.labels)

	def __getitem__(self, idx):
		ch = self.labels[idx]
		target = self.charset.index(ch)
		font_type, font_index = random.choice(self.fonts)
		font_size = random.randint(*self.font_size_interval)
		font_color, bg_color = self.color_functor()

		#image, mask = swl_langproc_util.generate_text_image(ch, font_type, font_index, font_size, font_color, bg_color, image_size, image_size=None, text_offset=None, crop_text_area=True, char_space_ratio=None, mode=self.mode, mask=False, mask_mode='1')
		image = swl_langproc_util.generate_simple_text_image(ch, font_type, font_index, font_size, font_color, bg_color, image_size=None, text_offset=None, crop_text_area=True, draw_text_border=False, mode=self.mode)

		#image = image.convert('RGB')
		#image = np.array(image, np.uint8)

		if self.transform:
			image = self.transform(image)
		if self.target_transform:
			target = self.target_transform(target)

		return (image, target)

	@property
	def num_classes(self):
		return len(self.charset)

	@property
	def classes(self):
		return self.charset

#--------------------------------------------------------------------

class SingleNoisyCharacterDataset(torch.utils.data.Dataset):
	def __init__(self, num_examples_per_class, charset, fonts, font_size_interval, char_clipping_ratio_interval, color_functor=None, transform=None, target_transform=None):
		self.charset = charset
		self.fonts = fonts
		self.font_size_interval = font_size_interval
		self.char_clipping_ratio_interval = char_clipping_ratio_interval
		self.transform = transform
		self.target_transform = target_transform

		self.image_channel = 1
		if self.image_channel == 1:
			self.mode = 'L'
			#self.mode = '1'
		elif self.image_channel == 3:
			self.mode = 'RGB'
		elif self.image_channel == 4:
			self.mode = 'RGBA'
		else:
			raise ValueError('Invalid image channel, {}'.format(self.image_channel))

		self.color_functor = color_functor if color_functor else functools.partial(generate_font_colors, image_depth=self.image_channel)
		self.labels = list(self.charset * num_examples_per_class)
		random.shuffle(self.labels)

	def __len__(self):
		return len(self.labels)

	def __getitem__(self, idx):
		ch = self.labels[idx]
		ch2 = random.sample(self.charset, 2)
		ch3 = ch2[0] + ch + ch2[1]
		target = self.charset.index(ch)
		font_type, font_index = random.choice(self.fonts)
		font_size = random.randint(*self.font_size_interval)
		font_color, bg_color = self.color_functor()

		#image, mask = swl_langproc_util.generate_text_image(ch3, font_type, font_index, font_size, font_color, bg_color, image_size, image_size=None, text_offset=None, crop_text_area=True, char_space_ratio=None, mode=self.mode, mask=False, mask_mode='1')
		image = swl_langproc_util.generate_simple_text_image(ch3, font_type, font_index, font_size, font_color, bg_color, image_size=None, text_offset=None, crop_text_area=True, draw_text_border=False, mode=self.mode)

		# FIXME [modify] >> It's an experimental implementation.
		alpha, beta = 0.75, 0.5  # Min. character width ratio and min. font width ratio.
		if True:
			import math
			from PIL import Image, ImageDraw, ImageFont

			image_size = (math.ceil(len(ch3) * font_size * 1.1), math.ceil((ch3.count('\n') + 1) * font_size * 1.1))
			draw_img = Image.new(mode=self.mode, size=image_size, color=bg_color)
			draw = ImageDraw.Draw(draw_img)
			font = ImageFont.truetype(font=font_type, size=font_size, index=font_index)

			ch_widths = [draw.textsize(ch, font=font)[0] for ch in ch3]
			ch_width = max(alpha * ch_widths[1], beta * font_size)
			left_margin, right_margin = ch_widths[0] * random.uniform(*self.char_clipping_ratio_interval), ch_widths[2] * random.uniform(*self.char_clipping_ratio_interval)

			if image.size[0] - (left_margin + right_margin) < ch_width:
				ratio = (image.size[0] - ch_width) / (left_margin + right_margin)
				left_margin, right_margin = math.floor(ratio * left_margin), math.floor(ratio * right_margin)
		else:
			import math

			ch_width = alpha * font_size #max(alpha, beta) * font_size
			left_margin, right_margin = font_size * random.uniform(*self.char_clipping_ratio_interval), font_size * random.uniform(*self.char_clipping_ratio_interval)

			if image.size[0] - (left_margin + right_margin) < ch_width:
				ratio = (image.size[0] - ch_width) / (left_margin + right_margin)
				left_margin, right_margin = math.floor(ratio * left_margin), math.floor(ratio * right_margin)
		image = image.crop((left_margin, 0, image.size[0] - right_margin, image.size[1]))
		assert image.size[0] > 0 and image.size[1] > 0

		#image = image.convert('RGB')
		#image = np.array(image, np.uint8)

		if self.transform:
			image = self.transform(image)
		if self.target_transform:
			target = self.target_transform(target)

		return (image, target)

	@property
	def num_classes(self):
		return len(self.charset)

	@property
	def classes(self):
		return self.charset

#--------------------------------------------------------------------

class SingleWordDataset(torch.utils.data.Dataset):
	UNKNOWN = '<UNK>'  # Unknown label token.

	def __init__(self, num_examples, words, charset, fonts, font_size_interval, color_functor=None, transform=None, target_transform=None, default_value=-1):
		self.num_examples = num_examples
		self.words = words
		self.charset = list(charset) + [SingleWordDataset.UNKNOWN]
		self.fonts = fonts
		self.font_size_interval = font_size_interval
		self.transform = transform
		self.target_transform = target_transform
		self._default_value = default_value

		self.image_channel = 1
		if self.image_channel == 1:
			self.mode = 'L'
			#self.mode = '1'
		elif self.image_channel == 3:
			self.mode = 'RGB'
		elif self.image_channel == 4:
			self.mode = 'RGBA'
		else:
			raise ValueError('Invalid image channel, {}'.format(self.image_channel))

		self.color_functor = color_functor if color_functor else functools.partial(generate_font_colors, image_depth=self.image_channel)
		self.max_word_len = len(max(self.words, key=len))

	def __len__(self):
		return self.num_examples

	def __getitem__(self, idx):
		#word = random.choice(self.words)
		word = random.sample(self.words, 1)[0]
		target = [self.default_value,] * self.max_word_len
		target[:len(word)] = self.encode_label(word)
		font_type, font_index = random.choice(self.fonts)
		font_size = random.randint(*self.font_size_interval)
		font_color, bg_color = self.color_functor()

		#image, mask = swl_langproc_util.generate_text_image(word, font_type, font_index, font_size, font_color, bg_color, image_size, image_size=None, text_offset=None, crop_text_area=True, char_space_ratio=None, mode=self.mode, mask=False, mask_mode='1')
		image = swl_langproc_util.generate_simple_text_image(word, font_type, font_index, font_size, font_color, bg_color, image_size=None, text_offset=None, crop_text_area=True, draw_text_border=False, mode=self.mode)

		#image = image.convert('RGB')
		#image = np.array(image, np.uint8)

		if self.transform:
			image = self.transform(image)
		if self.target_transform:
			target = self.target_transform(target)

		return (image, target)

	@property
	def num_classes(self):
		return len(self.charset)

	@property
	def classes(self):
		return self.charset

	@property
	def default_value(self):
		return self._default_value

	# String label -> integer label.
	# REF [function] >> TextLineDatasetBase.encode_label() in text_line_data.py.
	def encode_label(self, label_str, *args, **kwargs):
		def label2index(ch):
			try:
				return self.charset.index(ch)
			except ValueError:
				print('[SWL] Error: Failed to encode a character, {} in {}.'.format(ch, label_str))
				return self.charset.index(SingleWordDataset.UNKNOWN)
		return list(label2index(ch) for ch in label_str)

	# Integer label -> string label.
	# REF [function] >> TextLineDatasetBase.decode_label() in text_line_data.py.
	def decode_label(self, label_int, *args, **kwargs):
		def index2label(id):
			try:
				return self.charset[id]
			except IndexError:
				print('[SWL] Error: Failed to decode an identifier, {} in {}.'.format(id, label_int))
				return SingleWordDataset.UNKNOWN  # TODO [check] >> Is it correct?
		return ''.join(list(index2label(id) for id in label_int if id != self._default_value))

#--------------------------------------------------------------------

class SingleTextLineDataset(torch.utils.data.Dataset):
	UNKNOWN = '<UNK>'  # Unknown label token.
	SPACE = ' '  # Space token.

	def __init__(self, num_examples, image_height, image_width, image_channel, words, charset, fonts, max_word_len, word_count_interval, space_count_interval, font_size_interval, char_space_ratio_interval, color_functor=None, transform=None, target_transform=None, default_value=-1):
		self.num_examples = num_examples
		self.image_height, self.image_width, self.image_channel = image_height, image_width, image_channel
		self.words = words
		self.charset = list(charset) + [SingleTextLineDataset.SPACE, SingleTextLineDataset.UNKNOWN]
		self.fonts = fonts
		self.max_word_len = max_word_len
		self.word_count_interval = word_count_interval
		self.space_count_interval = space_count_interval
		self.font_size_interval = font_size_interval
		self.char_space_ratio_interval = char_space_ratio_interval
		self.transform = transform
		self.target_transform = target_transform
		self._default_value = default_value

		if self.image_channel == 1:
			self.mode = 'L'
			#self.mode = '1'
		elif self.image_channel == 3:
			self.mode = 'RGB'
		elif self.image_channel == 4:
			self.mode = 'RGBA'
		else:
			raise ValueError('Invalid image channel, {}'.format(self.image_channel))

		self.color_functor = color_functor if color_functor else functools.partial(generate_font_colors, image_depth=self.image_channel)

	def __len__(self):
		return self.num_examples

	def __getitem__(self, idx):
		words = random.sample(self.words, random.randint(*self.word_count_interval))	
		textline = functools.reduce(lambda t, w: t + ' ' * random.randint(*self.space_count_interval) + w, words[1:], words[0])[:self.max_word_len]
		target = [self.default_value,] * self.max_word_len
		target[:len(textline)] = self.encode_label(textline)
		font_type, font_index = random.choice(self.fonts)
		font_size = random.randint(*self.font_size_interval)
		char_space_ratio = None if self.char_space_ratio_interval is None else random.uniform(*self.char_space_ratio_interval)
		font_color, bg_color = self.color_functor()

		#image, mask = swl_langproc_util.generate_text_image(textline, font_type, font_index, font_size, font_color, bg_color, image_size=None, text_offset=None, crop_text_area=True, draw_text_border=False, char_space_ratio=char_space_ratio, mode=self.mode, mask=True, mask_mode='1')
		image = swl_langproc_util.generate_text_image(textline, font_type, font_index, font_size, font_color, bg_color, image_size=None, text_offset=None, crop_text_area=True, draw_text_border=False, char_space_ratio=char_space_ratio, mode=self.mode)

		#image = np.array(image, np.uint8)

		if self.transform:
			image = self.transform(image)
		if self.target_transform:
			target = self.target_transform(target)

		return (image, target)

	@property
	def shape(self):
		return self.image_height, self.image_width, self.image_channel

	@property
	def num_classes(self):
		return len(self.charset)

	@property
	def classes(self):
		return self.charset

	@property
	def default_value(self):
		return self._default_value

	# String label -> integer label.
	# REF [function] >> TextLineDatasetBase.encode_label() in text_line_data.py.
	def encode_label(self, label_str, *args, **kwargs):
		def label2index(ch):
			try:
				return self.charset.index(ch)
			except ValueError:
				print('[SWL] Error: Failed to encode a character, {} in {}.'.format(ch, label_str))
				return self.charset.index(SingleTextLineDataset.UNKNOWN)
		return list(label2index(ch) for ch in label_str)

	# Integer label -> string label.
	# REF [function] >> TextLineDatasetBase.decode_label() in text_line_data.py.
	def decode_label(self, label_int, *args, **kwargs):
		def index2label(id):
			try:
				return self.charset[id]
			except IndexError:
				print('[SWL] Error: Failed to decode an identifier, {} in {}.'.format(id, label_int))
				return SingleTextLineDataset.UNKNOWN  # TODO [check] >> Is it correct?
		return ''.join(list(index2label(id) for id in label_int if id != self._default_value))
