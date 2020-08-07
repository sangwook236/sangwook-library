#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
sys.path.append('../../src')

import os, math, time, datetime, functools, itertools, glob, csv
import numpy as np
import tensorflow as tf
import swl.language_processing.util as swl_langproc_util
import swl.machine_learning.util as swl_ml_util
import text_line_data
import TextRecognitionDataGenerator_data
import my_keras_applications

#--------------------------------------------------------------------

def create_augmenter():
	#import imgaug as ia
	from imgaug import augmenters as iaa

	"""
	augmenter = iaa.Sequential([
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.Crop(px=(0, 100)),  # Crop images from each side by 0 to 16px (randomly chosen).
			iaa.Crop(percent=(0, 0.1)),  # Crop images by 0-10% of their height/width.
			#iaa.Fliplr(0.5),  # Horizontally flip 50% of the images.
			#iaa.Flipud(0.5),  # Vertically flip 50% of the images.
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.Affine(
				scale={'x': (0.8, 1.2), 'y': (0.8, 1.2)},  # Scale images to 80-120% of their size, individually per axis.
				translate_percent={'x': (-0.1, 0.1), 'y': (-0.1, 0.1)},  # Translate by -10 to +10 percent (per axis).
				rotate=(-10, 10),  # Rotate by -10 to +10 degrees.
				shear=(-5, 5),  # Shear by -5 to +5 degrees.
				#order=[0, 1],  # Use nearest neighbour or bilinear interpolation (fast).
				order=0,  # Use nearest neighbour or bilinear interpolation (fast).
				#cval=(0, 255),  # If mode is constant, use a cval between 0 and 255.
				#mode=ia.ALL  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
				#mode='edge'  # Use any of scikit-image's warping modes (see 2nd image from the top for examples).
			),
			#iaa.PiecewiseAffine(scale=(0.01, 0.05)),  # Move parts of the image around. Slow.
			iaa.PerspectiveTransform(scale=(0.01, 0.1)),
			iaa.ElasticTransformation(alpha=(15.0, 30.0), sigma=5.0),  # Move pixels locally around (with random strengths).
		])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.OneOf([
				iaa.GaussianBlur(sigma=(1.5, 2.5)),
				iaa.AverageBlur(k=(3, 6)),
				iaa.MedianBlur(k=(3, 5)),
				iaa.MotionBlur(k=(3, 7), angle=(0, 360), direction=(-1.0, 1.0), order=1),
			]),
			iaa.OneOf([
				iaa.AdditiveGaussianNoise(loc=0, scale=(0.1 * 255, 0.3 * 255), per_channel=False),
				#iaa.AdditiveLaplaceNoise(loc=0, scale=(0.1 * 255, 0.3 * 255), per_channel=False),
				#iaa.AdditivePoissonNoise(lam=(32, 64), per_channel=False),
				iaa.CoarseSaltAndPepper(p=(0.1, 0.3), size_percent=(0.2, 0.9), per_channel=False),
				iaa.CoarseSalt(p=(0.1, 0.3), size_percent=(0.2, 0.9), per_channel=False),
				#iaa.CoarsePepper(p=(0.1, 0.3), size_percent=(0.2, 0.9), per_channel=False),
				iaa.CoarseDropout(p=(0.1, 0.3), size_percent=(0.05, 0.3), per_channel=False),
			]),
			#iaa.OneOf([
			#	#iaa.MultiplyHueAndSaturation(mul=(-10, 10), per_channel=False),
			#	#iaa.AddToHueAndSaturation(value=(-255, 255), per_channel=False),
			#	#iaa.LinearContrast(alpha=(0.5, 1.5), per_channel=False),

			#	iaa.Invert(p=1, per_channel=False),

			#	#iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
			#	iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),
			#]),
		])),
		#iaa.Scale(size={'height': image_height, 'width': image_width})  # Resize.
	])
	"""
	augmenter = iaa.Sequential([
		#iaa.Sometimes(0.5, iaa.OneOf([
		#	iaa.Crop(px=(0, 100)),  # Crop images from each side by 0 to 16px (randomly chosen).
		#	iaa.Crop(percent=(0, 0.1)),  # Crop images by 0-10% of their height/width.
		#	#iaa.Fliplr(0.5),  # Horizontally flip 50% of the images.
		#	#iaa.Flipud(0.5),  # Vertically flip 50% of the images.
		#])),
		iaa.Sometimes(0.5, iaa.OneOf([
			iaa.Affine(
				#scale={'x': (0.8, 1.2), 'y': (0.8, 1.2)},  # Scale images to 80-120% of their size, individually per axis.
				translate_percent={'x': (-0.1, 0.1), 'y': (-0.1, 0.1)},  # Translate by -10 to +10 percent along x-axis and -10 to +10 percent along y-axis.
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
			iaa.OneOf([
				iaa.GaussianBlur(sigma=(0.5, 1.5)),
				iaa.AverageBlur(k=(2, 4)),
				iaa.MedianBlur(k=(3, 3)),
				iaa.MotionBlur(k=(3, 4), angle=(0, 360), direction=(-1.0, 1.0), order=1),
			]),
			iaa.Sequential([
				iaa.OneOf([
					iaa.AdditiveGaussianNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
					#iaa.AdditiveLaplaceNoise(loc=0, scale=(0.05 * 255, 0.2 * 255), per_channel=False),
					iaa.AdditivePoissonNoise(lam=(20, 30), per_channel=False),
					iaa.CoarseSaltAndPepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
					iaa.CoarseSalt(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
					iaa.CoarsePepper(p=(0.01, 0.1), size_percent=(0.2, 0.9), per_channel=False),
					#iaa.CoarseDropout(p=(0.1, 0.3), size_percent=(0.8, 0.9), per_channel=False),
				]),
				iaa.GaussianBlur(sigma=(0.7, 1.0)),
			]),
			#iaa.OneOf([
			#	#iaa.MultiplyHueAndSaturation(mul=(-10, 10), per_channel=False),
			#	#iaa.AddToHueAndSaturation(value=(-255, 255), per_channel=False),
			#	#iaa.LinearContrast(alpha=(0.5, 1.5), per_channel=False),

			#	iaa.Invert(p=1, per_channel=False),

			#	#iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),
			#	iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),
			#]),
		])),
		#iaa.Scale(size={'height': image_height, 'width': image_width})  # Resize.
	])

	return augmenter

def generate_font_colors(image_depth):
	import random
	#font_color = (255,) * image_depth  # White font color.
	font_color = tuple(random.randrange(256) for _ in range(image_depth))  # An RGB font color.
	#font_color = (random.randrange(256),) * image_depth  # A grayscale font color.
	#gray_val = random.randrange(255)
	#font_color = (gray_val,) * image_depth  # A lighter grayscale font color.
	#font_color = (random.randrange(gray_val, 256),) * image_depth  # A darker grayscale font color.
	#font_color = (random.randrange(128, 256),) * image_depth  # A light grayscale font color.
	#font_color = (random.randrange(0, 128),) * image_depth  # A dark grayscale font color.
	#bg_color = (0,) * image_depth  # Black background color.
	bg_color = tuple(random.randrange(256) for _ in range(image_depth))  # An RGB background color.
	#bg_color = (random.randrange(256),) * image_depth  # A grayscale background color.
	#bg_color = (random.randrange(gray_val, 256),) * image_depth  # A lighter grayscale background color.
	#bg_color = (gray_val,) * image_depth  # A darker grayscale background color.
	#bg_color = (random.randrange(0, 128),) * image_depth  # A dark grayscale background color.
	#bg_color = (random.randrange(128, 256),) * image_depth  # A light grayscale background color.
	return font_color, bg_color

class MyRunTimeHangeulJamoAlphaMatteTextLineDataset(text_line_data.RunTimeHangeulJamoAlphaMatteTextLineDataset):
	def __init__(self, label_converter, text_set, image_height, image_width, image_channel, font_list, char_images_dict, alpha_matte_mode='1', use_NWHC=False):
		super().__init__(label_converter, text_set, image_height, image_width, image_channel, font_list, char_images_dict, functools.partial(generate_font_colors, image_depth=image_channel), alpha_matte_mode, use_NWHC)

		self._augmenter = create_augmenter()

	def augment(self, inputs, outputs, *args, **kwargs):
		if outputs is None:
			return self._augmenter.augment_images(inputs), None
		else:
			augmenter_det = self._augmenter.to_deterministic()  # Call this for each batch again, NOT only once at the start.
			return augmenter_det.augment_images(inputs), augmenter_det.augment_images(outputs)

class MyHangeulJamoTextLineDataset(TextRecognitionDataGenerator_data.HangeulJamoTextRecognitionDataGeneratorTextLineDataset):
	def __init__(self, label_converter, data_dir_path, image_height, image_width, image_channel, train_test_ratio, max_label_len, shuffle=True, use_NWHC=False):
		super().__init__(label_converter, data_dir_path, image_height, image_width, image_channel, train_test_ratio, max_label_len, shuffle, use_NWHC)

		self._augmenter = create_augmenter()

	def augment(self, inputs, outputs, *args, **kwargs):
		if outputs is None:
			return self._augmenter.augment_images(inputs), None
		else:
			augmenter_det = self._augmenter.to_deterministic()  # Call this for each batch again, NOT only once at the start.
			return augmenter_det.augment_images(inputs), augmenter_det.augment_images(outputs)

#--------------------------------------------------------------------

class MyModel(object):
	def __init__(self, image_height, image_width, image_channel, blank_label, default_value=-1):
		# TODO [decide] >>
		#	When _is_sparse_output = True, CTC loss, CTC beam search decoding, and edit distance are applied.
		#		tf.nn.ctc_loss() is used to calculate a loss.
		#		tf.nn.ctc_beam_search_decoder() and tf.edit_distance() are too slow.
		#		Because computing accuracy requires heavy computation resources, model_output['decoded_label'] can be used to compute an accuracy.
		#	When _is_sparse_output = False, CTC loss is only applied.
		#		tf.keras.backend.ctc_batch_cost() is used to calculate a loss.
		self._is_sparse_output = True
		self._model_output_len = 0
		self._default_value = default_value

		# FIXME [check] >> Different input shape is used.
		self._input_shape = (image_height, image_width, image_channel)

		self._input_ph = tf.placeholder(tf.float32, shape=(None, image_height, image_width, image_channel), name='input_ph')
		if self._is_sparse_output:
			self._output_ph = tf.sparse_placeholder(tf.int32, name='output_ph')
		else:
			self._output_ph = tf.placeholder(tf.int32, shape=(None, None), name='output_ph')
		# Use output lengths.
		self._output_len_ph = tf.placeholder(tf.int32, shape=(None,), name='output_len_ph')
		self._model_output_len_ph = tf.placeholder(tf.int32, shape=(None,), name='model_output_len_ph')

		#--------------------
		if self._is_sparse_output:
			#self._decode_functor = lambda args: args  # Dense tensor.
			self._decode_functor = lambda args: swl_ml_util.sparse_to_sequences(*args, dtype=np.int32) if args[1].size else list()  # Sparse tensor.
			self._get_feed_dict_functor = self._get_feed_dict_for_sparse
		else:
			self._decode_functor = functools.partial(MyModel._decode_label, blank_label=blank_label)
			self._get_feed_dict_functor = self._get_feed_dict_for_dense

	def get_feed_dict(self, data, num_data, *args, **kwargs):
		return self._get_feed_dict_functor(data, num_data, *args, **kwargs)

	def create_model(self, num_classes, is_training=False):
		model_output = self._create_model(self._input_ph, num_classes)

		if is_training:
			if self._is_sparse_output:
				#loss = self._get_loss_from_sparse_label(model_output['logit'], self._output_ph, self._model_output_len_ph, None)
				# Use output lengths.
				loss = self._get_loss_from_sparse_label(model_output['logit'], self._output_ph, self._model_output_len_ph, self._output_len_ph)
				accuracy = self._get_accuracy_from_sparse_label(model_output['decoded_label'], self._output_ph)
				#accuracy = None
			else:
				loss = self._get_loss_from_dense_label(model_output['logit'], self._output_ph, self._model_output_len_ph, self._output_len_ph)
				#accuracy = self._get_accuracy_from_logit(model_output['logit'], self._output_ph)
				accuracy = None
			return model_output, loss, accuracy
		else:
			return model_output

	def decode_label(self, labels):
		return self._decode_functor(labels) if not self._is_sparse_output or labels[2][1] > 0 else list()

	def _get_feed_dict_for_sparse(self, data, num_data, *args, **kwargs):
		len_data = len(data)
		model_output_len = [self._model_output_len] * num_data
		if 1 == len_data:
			feed_dict = {self._input_ph: data[0], self._model_output_len_ph: model_output_len}
		elif 2 == len_data:
			"""
			feed_dict = {self._input_ph: data[0], self._output_ph: swl_ml_util.sequences_to_sparse(data[1], dtype=np.int32), self._model_output_len_ph: model_output_len}
			"""
			# Use output lengths.
			output_len = list(map(lambda lbl: len(lbl), data[1]))
			feed_dict = {self._input_ph: data[0], self._output_ph: swl_ml_util.sequences_to_sparse(data[1], dtype=np.int32), self._output_len_ph: output_len, self._model_output_len_ph: model_output_len}
		else:
			raise ValueError('Invalid number of feed data: {}'.format(len_data))
		return feed_dict

	def _get_feed_dict_for_dense(self, data, num_data, *args, **kwargs):
		len_data = len(data)
		model_output_len = [self._model_output_len] * num_data
		if 1 == len_data:
			feed_dict = {self._input_ph: data[0], self._model_output_len_ph: model_output_len}
		elif 2 == len_data:
			"""
			feed_dict = {self._input_ph: data[0], self._output_ph: swl_ml_util.sequences_to_dense(data[1], default_value=self._default_value, dtype=np.int32), self._model_output_len_ph: model_output_len}
			"""
			# Use output lengths.
			output_len = list(map(lambda lbl: len(lbl), data[1]))
			feed_dict = {self._input_ph: data[0], self._output_ph: swl_ml_util.sequences_to_dense(data[1], default_value=self._default_value, dtype=np.int32), self._output_len_ph: output_len, self._model_output_len_ph: model_output_len}
		else:
			raise ValueError('Invalid number of feed data: {}'.format(len_data))
		return feed_dict

	def _create_model(self, inputs, num_classes):
		# TODO [decide] >>
		#kernel_initializer = None
		kernel_initializer = tf.initializers.he_normal()
		#kernel_initializer = tf.initializers.he_uniform()
		#kernel_initializer = tf.initializers.truncated_normal(mean=0.0, stddev=1.0)
		#kernel_initializer = tf.initializers.uniform_unit_scaling(factor=1.0)
		#kernel_initializer = tf.initializers.variance_scaling(scale=1.0, mode='fan_in', distribution='truncated_normal')
		#kernel_initializer = tf.initializers.glorot_normal()  # Xavier normal initialization.
		#kernel_initializer = tf.initializers.glorot_uniform()  # Xavier uniform initialization.
		#kernel_initializer = tf.initializers.orthogonal()

		#--------------------
		# Preprocessing.
		#with tf.variable_scope('preprocessing', reuse=tf.AUTO_REUSE):
		#	inputs = tf.nn.local_response_normalization(inputs, depth_radius=5, bias=1, alpha=1, beta=0.5, name='lrn')

		#--------------------
		with tf.variable_scope('cnn', reuse=tf.AUTO_REUSE):
			cnn_output = MyModel._create_densenet121(inputs, kernel_initializer, input_shape=self._input_shape, weights=None)

		with tf.variable_scope('rnn', reuse=tf.AUTO_REUSE):
			rnn_input_shape = cnn_output.shape #cnn_output.shape.as_list()
			rnn_input = tf.reshape(cnn_output, (-1, rnn_input_shape[1] * rnn_input_shape[2], rnn_input_shape[3]), name='reshape')
			self._model_output_len = rnn_input.shape[1]  # Model output time-steps.

			# TODO [decide] >>
			rnn_input = tf.layers.dense(rnn_input, 64, activation=tf.nn.relu, kernel_initializer=kernel_initializer, name='dense')

			rnn_output = MyModel._create_bidirectionnal_rnn(rnn_input, self._model_output_len_ph, kernel_initializer)

		with tf.variable_scope('transcription', reuse=tf.AUTO_REUSE):
			if self._is_sparse_output:
				logits = tf.layers.dense(rnn_output, num_classes, activation=tf.nn.relu, kernel_initializer=kernel_initializer, name='dense')

				# CTC beam search decoding.
				logits = tf.transpose(logits, (1, 0, 2))  # Time-major.
				# NOTE [info] >> CTC beam search decoding is too slow. It seems to run on CPU, not GPU.
				#	If the number of classes increases, its computation time becomes much slower.
				beam_width = 10 #100
				#decoded, log_prob = tf.nn.ctc_beam_search_decoder(inputs=logits, sequence_length=self._model_output_len_ph, beam_width=beam_width, top_paths=1, merge_repeated=False)
				decoded, log_prob = tf.nn.ctc_beam_search_decoder_v2(inputs=logits, sequence_length=self._model_output_len_ph, beam_width=beam_width, top_paths=1)
				decoded_best = decoded[0]  # Sparse tensor.
				#decoded_best = tf.sparse.to_dense(decoded[0], default_value=self._default_value)  # Dense tensor.

				return {'logit': logits, 'decoded_label': decoded_best}
			else:
				logits = tf.layers.dense(rnn_output, num_classes, activation=tf.nn.softmax, kernel_initializer=kernel_initializer, name='dense')

				"""
				# Decoding.
				decoded = tf.argmax(logits, axis=-1)
				# FIXME [fix] >> This does not work correctly.
				#	Refer to MyModel._decode_label().
				decoded = tf.numpy_function(lambda x: list(map(lambda lbl: list(k for k, g in itertools.groupby(lbl) if k < self._blank_label), x)), [decoded], [tf.int32])  # Removes repetitive labels.

				return {'logit': logits, 'decoded_label': decoded}
				"""
				# No decoding.
				#return {'logit': logits}
				return {'logit': logits, 'decoded_label': logits}

	def _get_loss_from_sparse_label(self, y, t_sparse, y_len, t_len, is_time_major=True):
		# TODO [decide] >> Which one should be used, sequence_length=y_len or sequence_length=t_len?
		loss = tf.nn.ctc_loss(labels=t_sparse, inputs=y, sequence_length=y_len, preprocess_collapse_repeated=False, ctc_merge_repeated=True, ignore_longer_outputs_than_inputs=False, time_major=is_time_major)
		#loss = tf.nn.ctc_loss_v2(labels=t_sparse, logits=y, label_length=t_len, logit_length=y_len, logits_time_major=is_time_major, unique=None, blank_index=self._blank_label)
		#loss = tf.nn.ctc_loss_v2(labels=t, logits=y, label_length=t_len, logit_length=y_len, logits_time_major=is_time_major, unique=None, blank_index=self._blank_label)
		loss = tf.reduce_mean(loss)

		return loss

	def _get_loss_from_dense_label(self, y, t, y_len, t_len):
		y_len, t_len = tf.reshape(y_len, (-1, 1)), tf.reshape(t_len, (-1, 1))
		loss = tf.keras.backend.ctc_batch_cost(y_true=t, y_pred=y, input_length=y_len, label_length=t_len)
		# NOTE [info] >> This model is not trained when using tf.nn.ctc_loss() instead of tf.keras.backend.ctc_batch_cost().
		#	I don't know why.
		#t_sparse = tf.contrib.layers.dense_to_sparse(t, eos_token=self._default_value)
		#loss = tf.nn.ctc_loss(labels=t_sparse, inputs=y, sequence_length=y_len, preprocess_collapse_repeated=False, ctc_merge_repeated=True, ignore_longer_outputs_than_inputs=False, time_major=False)
		loss = tf.reduce_mean(loss)

		return loss

	# When logits are used as y.
	def _get_accuracy_from_logit(self, y, t):
		"""
		correct_prediction = tf.equal(tf.argmax(y, axis=-1), tf.cast(t, tf.int64))  # Error: The time-steps of y and t are different.
		accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

		return accuracy
		"""
		"""
		# FIXME [implement] >> The below logic has to be implemented in TensorFlow.
		correct_prediction = len(list(filter(lambda xx: len(list(filter(lambda x: x[0] == x[1], zip(xx[0], xx[1])))) == max(len(xx[0]), len(xx[1])), zip(tf.argmax(y, axis=-1), t))))
		accuracy = correct_prediction / max(len(y), len(t))

		return accuracy
		"""
		raise NotImplementedError

	# When sparse labels which are decoded by CTC beam search are used as y.
	def _get_accuracy_from_sparse_label(self, y_sparse, t_sparse):
		# Inaccuracy: label error rate.
		# NOTE [info] >> tf.edit_distance() is too slow. It seems to run on CPU, not GPU.
		#	Accuracy may not be calculated to speed up the training.
		ler = tf.reduce_mean(tf.edit_distance(hypothesis=tf.cast(y_sparse, tf.int32), truth=t_sparse, normalize=True))  # int64 -> int32.
		accuracy = 1.0 - ler

		return accuracy

	# REF [function] >> densenet_test() in ${SWDT_PYTHON_HOME}/rnd/test/machine_learning/keras/keras_applications_test.py.
	@staticmethod
	def _create_densenet121(inputs, kernel_initializer=None, input_shape=None, weights=None):
		kwargs = {'backend': tf.keras.backend, 'layers': tf.keras.layers, 'models': tf.keras.models, 'utils': tf.keras.utils}

		# DenseNet121, DenseNet169, DenseNet201.
		model = my_keras_applications.densenet.DenseNet121_Text(
			include_top=False,
			weights=weights,
			input_tensor=None,
			input_shape=input_shape,
			pooling=None,
			classes=None,
			**kwargs
		)
		#print(model.summary())

		return model(inputs)

	@staticmethod
	def _create_bidirectionnal_rnn(inputs, input_len=None, kernel_initializer=None):
		with tf.variable_scope('birnn_1', reuse=tf.AUTO_REUSE):
			fw_cell_1, bw_cell_1 = MyModel._create_unit_cell(256, kernel_initializer, 'fw_cell'), MyModel._create_unit_cell(256, kernel_initializer, 'bw_cell')

			# Attention.
			num_attention_units = 128
			# TODO [decide] >>
			if True:
				# Additive attention.
				# REF [paper] >> "Neural Machine Translation by Jointly Learning to Align and Translate", arXiv 2016.
				attention_mechanism = tf.contrib.seq2seq.BahdanauAttention(num_attention_units, memory=inputs, memory_sequence_length=input_len)
			else:
				# Multiplicative attention.
				# REF [paper] >> "Effective Approaches to Attention-based Neural Machine Translation", arXiv 2015.
				attention_mechanism = tf.contrib.seq2seq.LuongAttention(num_attention_units, memory=inputs, memory_sequence_length=input_len)
			# TODO [decide] >> Are different attention_mechanisms used for fw_cell_1 and bw_cell_1?
			fw_cell_1 = tf.contrib.seq2seq.AttentionWrapper(fw_cell_1, attention_mechanism, attention_layer_size=num_attention_units)
			bw_cell_1 = tf.contrib.seq2seq.AttentionWrapper(bw_cell_1, attention_mechanism, attention_layer_size=num_attention_units)

			outputs_1, _ = tf.nn.bidirectional_dynamic_rnn(fw_cell_1, bw_cell_1, inputs, input_len, dtype=tf.float32)
			outputs_1 = tf.concat(outputs_1, 2)
			outputs_1 = tf.layers.batch_normalization(outputs_1, name='batchnorm')

		with tf.variable_scope('birnn_2', reuse=tf.AUTO_REUSE):
			# TODO [decide] >> Are attention_mechanisms applied to the second Bi-RNN?

			fw_cell_2, bw_cell_2 = MyModel._create_unit_cell(256, kernel_initializer, 'fw_cell'), MyModel._create_unit_cell(256, kernel_initializer, 'bw_cell')

			outputs_2, _ = tf.nn.bidirectional_dynamic_rnn(fw_cell_2, bw_cell_2, outputs_1, input_len, dtype=tf.float32)
			outputs_2 = tf.concat(outputs_2, 2)
			# TODO [decide] >>
			outputs_2 = tf.layers.batch_normalization(outputs_2, name='batchnorm')

		return outputs_2

	@staticmethod
	def _create_unit_cell(num_units, kernel_initializer=None, name=None):
		#return tf.nn.rnn_cell.RNNCell(num_units, name=name)
		return tf.nn.rnn_cell.LSTMCell(num_units, forget_bias=1.0, initializer=kernel_initializer, name=name)
		#return tf.nn.rnn_cell.GRUCell(num_units, kernel_initializer=kernel_initializer, name=name)

	@staticmethod
	def _decode_label(labels, blank_label):
		#if 0 == labels.size:
		#	return list()
		labels = np.argmax(labels, axis=-1)
		return list(map(lambda lbl: list(k for k, g in itertools.groupby(lbl) if k < blank_label), labels))  # Removes repetitive labels.

#--------------------------------------------------------------------

class MyRunner(object):
	def __init__(self, is_dataset_generated_at_runtime, data_dir_path=None, train_test_ratio=0.8):
		# Set parameters.
		# TODO [modify] >> Depends on a model.
		#	model_output_time_steps = image_width / width_downsample_factor or image_width / width_downsample_factor - 1.
		#	REF [function] >> MyModel.create_model().
		#width_downsample_factor = 8
		if False:
			image_height, image_width, image_channel = 32, 320, 1  # TODO [modify] >> image_height is hard-coded and image_channel is fixed.
			model_output_time_steps = 160  # (image_height / width_downsample_factor) * (image_width / width_downsample_factor).
		else:
			image_height, image_width, image_channel = 64, 640, 1  # TODO [modify] >> image_height is hard-coded and image_channel is fixed.
			model_output_time_steps = 640  # (image_height / width_downsample_factor) * (image_width / width_downsample_factor).
		max_label_len = 80 #model_output_time_steps  # max_label_len <= model_output_time_steps.

		#SOJ, EOJ = '<SOJ>', '<EOJ>'
		EOJ = '<EOJ>'

		#--------------------
		# Create a dataset.
		import hangeul_util as hg_util
		# NOTE [info] >> Some special Hangeul jamos (e.g. 'ㆍ', 'ㆅ', 'ㆆ') are ignored in the hgtk library.
		hangeul2jamo_functor = lambda hangeul_str: hg_util.hangeul2jamo(hangeul_str, eojc_str=EOJ, use_separate_consonants=False, use_separate_vowels=True)
		# NOTE [info] >> Some special Hangeul jamos (e.g. 'ㆍ', 'ㆅ', 'ㆆ') are ignored in the hgtk library.
		jamo2hangeul_functor = lambda jamo_str: hg_util.jamo2hangeul(jamo_str, eojc_str=EOJ, use_separate_consonants=False, use_separate_vowels=True)

		if is_dataset_generated_at_runtime:
			import text_generation_util as tg_util

			word_dictionary_filepath = '../../data/language_processing/dictionary/korean_wordslistUnique.txt'

			print('[SWL] Info: Start loading a Korean dictionary...')
			start_time = time.time()
			with open(word_dictionary_filepath, 'r', encoding='UTF-8') as fd:
				#dictionary_words = fd.readlines()
				#dictionary_words = fd.read().strip('\n')
				dictionary_words = fd.read().splitlines()
			print('[SWL] Info: End loading a Korean dictionary: {} secs.'.format(time.time() - start_time))

			print('[SWL] Info: Start generating text lines...')
			texts = tg_util.generate_random_text_lines(dictionary_words, min_word_len=1, max_word_len=5)
			print('[SWL] Info: End generating text lines, {} text lines generated: {} secs.'.format(len(texts), time.time() - start_time))

			if max_label_len > 0:
				texts = set(filter(lambda txt: len(txt) <= max_label_len, texts))

			if False:
				from swl.language_processing.util import draw_character_histogram
				draw_character_histogram(texts, charset=None)

			labels = functools.reduce(lambda x, txt: x.union(hangeul2jamo_functor(txt)), texts, set())
			labels.remove(EOJ)
			labels = sorted(labels)
			#labels = ''.join(sorted(labels))

			self._label_converter = swl_langproc_util.JamoTokenConverter(labels, hangeul2jamo_functor, jamo2hangeul_functor, eoj=EOJ, pad=None)
			# NOTE [info] >> The ID of the blank label is reserved as label_converter.num_tokens.
			print('[SWL] Info: Labels = {}.'.format(self._label_converter.tokens))
			print('[SWL] Info: #labels = {}.'.format(self._label_converter.num_tokens))

			#--------------------
			if 'posix' == os.name:
				system_font_dir_path = '/usr/share/fonts'
				font_base_dir_path = '/home/sangwook/work/font'
			else:
				system_font_dir_path = 'C:/Windows/Fonts'
				font_base_dir_path = 'D:/work/font'
			font_dir_path = font_base_dir_path + '/kor'
			#font_dir_path = font_base_dir_path + '/kor_small'
			#font_dir_path = font_base_dir_path + '/kor_large'

			font_filepaths = glob.glob(os.path.join(font_dir_path, '*.ttf'))
			font_list = tg_util.generate_hangeul_font_list(font_filepaths)
			#char_images_dict = tg_util.generate_phd08_dict(from_npy=True)
			char_images_dict = None

			print('[SWL] Info: Start creating a Hangeul jamo dataset...')
			start_time = time.time()
			self._dataset = MyRunTimeHangeulJamoAlphaMatteTextLineDataset(self._label_converter, texts, image_height, image_width, image_channel, font_list, char_images_dict, alpha_matte_mode='1')
			print('[SWL] Info: End creating a Hangeul jamo dataset: {} secs.'.format(time.time() - start_time))

			self._train_examples_per_epoch, self._test_examples_per_epoch = 200000, 10000 #500000, 10000  # Uses a subset of texts per epoch.
			#self._train_examples_per_epoch, self._test_examples_per_epoch = None, None  # Uses the whole set of texts per epoch.
		else:
			#hangeul_jamo_charset = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅐㅑㅒㅓㅔㅕㅖㅗㅛㅜㅠㅡㅣ'
			hangeul_jamo_charset = 'ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅃㅄㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎㅏㅐㅑㅒㅓㅔㅕㅖㅗㅛㅜㅠㅡㅣ'
			#hangeul_jamo_charset = 'ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅃㅄㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'

			import string
			labels = \
				hangeul_jamo_charset + \
				string.ascii_uppercase + \
				string.ascii_lowercase + \
				string.digits + \
				string.punctuation + \
				' '
			# There are words of Unicode Hangeul letters besides KS X 1001.
			labels = functools.reduce(lambda x, fpath: x.union(hangeul2jamo_functor(fpath.split('_')[0])), os.listdir(data_dir_path), set(labels))
			labels.remove(EOJ)
			labels = sorted(labels)
			#labels = ''.join(sorted(labels))

			self._label_converter = swl_langproc_util.JamoTokenConverter(labels, hangeul2jamo_functor, jamo2hangeul_functor, eoj=EOJ, pad=None)
			# NOTE [info] >> The ID of the blank label is reserved as label_converter.num_tokens.
			print('[SWL] Info: Labels = {}.'.format(self._label_converter.tokens))
			print('[SWL] Info: #labels = {}.'.format(self._label_converter.num_tokens))

			self._dataset = MyHangeulJamoTextLineDataset(self._label_converter, data_dir_path, image_height, image_width, image_channel, train_test_ratio, max_label_len)

			self._train_examples_per_epoch, self._test_examples_per_epoch = None, None

	@property
	def label_converter(self):
		return self._label_converter

	@property
	def dataset(self):
		return self._dataset

	def train(self, checkpoint_dir_path, batch_size, final_epoch, initial_epoch=0, is_training_resumed=False):
		graph = tf.Graph()
		with graph.as_default():
			# Create a model.
			model = MyModel(*self._dataset.shape, blank_label=self._label_converter.num_tokens, default_value=self._label_converter.pad_id)
			model_output, loss, accuracy = model.create_model(self._label_converter.num_tokens + 1, is_training=True)

			# Create a trainer.
			global_step = tf.Variable(initial_epoch, name='global_step', trainable=False)
			#global_step = None
			if True:
				learning_rate = 0.001
			elif False:
				lr_boundaries = [20, 30, 40, 50]
				lr_values = [1.0e-3, 1.0e-4, 1.0e-5, 1.0e-6, 1.0e-7]
				learning_rate = tf.train.piecewise_constant_decay(global_step, lr_boundaries, lr_values)
			#optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
			#optimizer = tf.train.MomentumOptimizer(learning_rate=learning_rate, momentum=0.9, use_nesterov=True)
			#optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate, beta1=0.9, beta2=0.999, epsilon=1e-08)
			optimizer = tf.train.AdadeltaOptimizer(learning_rate=1.0, rho=0.95, epsilon=1e-08)
			if True:
				train_op = optimizer.minimize(loss, global_step=global_step)
			else:  # Gradient clipping.
				max_gradient_norm = 5
				var_list = None #tf.trainable_variables()
				# Method 1.
				grads_and_vars = optimizer.compute_gradients(loss, var_list=var_list)
				grads_and_vars = list(map(lambda gv: (tf.clip_by_norm(gv[0], clip_norm=max_gradient_norm), gv[1]), grads_and_vars))
				#gradients = list(map(lambda gv: gv[0], grads_and_vars))
				train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)
				"""
				# Method 2.
				#	REF [site] >> https://www.tensorflow.org/tutorials/seq2seq
				if var_list is None:
					var_list = tf.trainable_variables()
				gradients = tf.gradients(loss, var_list)
				gradients, _ = tf.clip_by_global_norm(gradients, clip_norm=max_gradient_norm)  # Clip gradients.
				train_op = optimizer.apply_gradients(zip(gradients, var_list), global_step=global_step)
				"""

			# Create a saver.
			saver = tf.train.Saver(max_to_keep=5, keep_checkpoint_every_n_hours=2)

			initializer = tf.global_variables_initializer()

		with tf.Session(graph=graph).as_default() as sess:
			sess.run(initializer)

			# Restore a model.
			if is_training_resumed:
				print('[SWL] Info: Start restoring a model...')
				start_time = time.time()
				ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
				ckpt_filepath = ckpt.model_checkpoint_path if ckpt else None
				#ckpt_filepath = tf.train.latest_checkpoint(checkpoint_dir_path)
				if ckpt_filepath:
					initial_epoch = int(ckpt_filepath.split('-')[1]) + 1
					saver.restore(sess, ckpt_filepath)
				else:
					print('[SWL] Error: Failed to restore a model from {}.'.format(checkpoint_dir_path))
					return
				print('[SWL] Info: End restoring a model from {}: {} secs.'.format(ckpt_filepath, time.time() - start_time))

			history = {
				'acc': list(),
				'loss': list(),
				'val_acc': list(),
				'val_loss': list()
			}

			#--------------------
			if is_training_resumed:
				print('[SWL] Info: Resume training...')
			else:
				print('[SWL] Info: Start training...')
			start_total_time = time.time()
			train_steps_per_epoch = None if self._train_examples_per_epoch is None else math.ceil(self._train_examples_per_epoch / batch_size)
			test_steps_per_epoch = None if self._test_examples_per_epoch is None else math.ceil(self._test_examples_per_epoch / batch_size)
			best_performance_measure = None
			for epoch in range(initial_epoch, final_epoch):
				print('Epoch {}/{}:'.format(epoch, final_epoch - 1))
				is_best_model = False

				start_time = time.time()
				train_loss, train_acc, num_examples = 0.0, 0.0, 0
				for batch_step, (batch_data, num_batch_examples) in enumerate(self._dataset.create_train_batch_generator(batch_size, train_steps_per_epoch, shuffle=True)):
					#batch_images, batch_labels_str, batch_labels_int = batch_data
					#_, batch_loss, batch_acc = sess.run(
					#	[train_op, loss, accuracy],
					_, batch_loss, batch_labels_int = sess.run(
						[train_op, loss, model_output['decoded_label']],
						feed_dict=model.get_feed_dict((batch_data[0], batch_data[2]), num_batch_examples)
					)

					train_loss += batch_loss * num_batch_examples
					#train_acc += batch_acc * num_batch_examples
					train_acc += len(list(filter(lambda x: x[1] == self._label_converter.decode(x[0]), zip(model.decode_label(batch_labels_int), batch_data[1]))))
					num_examples += num_batch_examples

					if (batch_step + 1) % 100 == 0:
						print('\tStep {}: Loss = {:.6f}: {} secs.'.format(batch_step + 1, batch_loss, time.time() - start_time))
						sys.stdout.flush()
				train_loss /= num_examples
				train_acc /= num_examples
				print('\tTrain:      Loss = {:.6f}, accuracy = {:.6f}: {} secs.'.format(train_loss, train_acc, time.time() - start_time))

				history['loss'].append(train_loss)
				history['acc'].append(train_acc)
				"""
				train_loss, train_acc, num_examples = 0.0, None, 0
				for batch_step, (batch_data, num_batch_examples) in enumerate(self._dataset.create_train_batch_generator(batch_size, train_steps_per_epoch, shuffle=True)):
					#batch_images, batch_labels_str, batch_labels_int = batch_data
					_, batch_loss = sess.run(
						[train_op, loss],
						feed_dict=model.get_feed_dict((batch_data[0], batch_data[2]), num_batch_examples)
					)

					train_loss += batch_loss * num_batch_examples
					num_examples += num_batch_examples

					if (batch_step + 1) % 100 == 0:
						print('\tStep {}: Loss = {:.6f}: {} secs.'.format(batch_step + 1, batch_loss, time.time() - start_time))
						sys.stdout.flush()
				train_loss /= num_examples
				print('\tTrain:      Loss = {:.6f}, accuracy = {}: {} secs.'.format(train_loss, train_acc, time.time() - start_time))

				history['loss'].append(train_loss)
				#history['acc'].append(train_acc)
				"""

				#--------------------
				# TODO [check] >> Accuracy is computed.
				#if epoch % 10 == 0:
				if True:
					start_time = time.time()
					val_loss, val_acc, num_examples = 0.0, 0.0, 0
					for batch_step, (batch_data, num_batch_examples) in enumerate(self._dataset.create_test_batch_generator(batch_size, test_steps_per_epoch, shuffle=False)):
						#batch_images, batch_labels_str, batch_labels_int = batch_data
						#batch_loss, batch_acc = sess.run(
						#	[loss, accuracy],
						batch_loss, batch_labels_int = sess.run(
							[loss, model_output['decoded_label']],
							feed_dict=model.get_feed_dict((batch_data[0], batch_data[2]), num_batch_examples)
						)

						val_loss += batch_loss * num_batch_examples
						#val_acc += batch_acc * num_batch_examples
						val_acc += len(list(filter(lambda x: x[1] == self._label_converter.decode(x[0]), zip(model.decode_label(batch_labels_int), batch_data[1]))))
						num_examples += num_batch_examples

						# Show some results.
						if 0 == batch_step:
							preds, gts = list(), list()
							for count, (inf, gt) in enumerate(zip(model.decode_label(batch_labels_int), batch_data[1])):
								inf = self._label_converter.decode(inf)
								preds.append(inf)
								gts.append(gt)
								if (count + 1) >= 10:
									break
							print('\tValidation: G/T         = {}.'.format(gts))	
							print('\tValidation: Predictions = {}.'.format(preds))	
					val_loss /= num_examples
					val_acc /= num_examples
					print('\tValidation: Loss = {:.6f}, accuracy = {:.6f}: {} secs.'.format(val_loss, val_acc, time.time() - start_time))

					history['val_loss'].append(val_loss)
					history['val_acc'].append(val_acc)

					if best_performance_measure is None or val_acc > best_performance_measure:
						best_performance_measure = val_acc
						is_best_model = True
				else:
					start_time = time.time()
					val_loss, val_acc, num_examples = 0.0, None, 0
					for batch_step, (batch_data, num_batch_examples) in enumerate(self._dataset.create_test_batch_generator(batch_size, test_steps_per_epoch, shuffle=False)):
						#batch_images, batch_labels_str, batch_labels_int = batch_data
						batch_loss = sess.run(
							loss,
							feed_dict=model.get_feed_dict((batch_data[0], batch_data[2]), num_batch_examples)
						)

						val_loss += batch_loss * num_batch_examples
						num_examples += num_batch_examples
					val_loss /= num_examples
					print('\tValidation: Loss = {:.6f}, accuracy = {}: {} secs.'.format(val_loss, val_acc, time.time() - start_time))

					history['val_loss'].append(val_loss)
					#history['val_acc'].append(val_acc)

					if best_performance_measure is None or val_loss < best_performance_measure:
						best_performance_measure = val_loss
						is_best_model = True

				#--------------------
				if is_best_model:
					print('[SWL] Info: Start saving a model...')
					start_time = time.time()
					saved_model_path = saver.save(sess, os.path.join(checkpoint_dir_path, 'model_ckpt'), global_step=epoch)
					print('[SWL] Info: End saving a model to {}: {} secs.'.format(saved_model_path, time.time() - start_time))

				sys.stdout.flush()
				time.sleep(0)
			print('[SWL] Info: End training: {} secs.'.format(time.time() - start_total_time))

			return history

	def test(self, checkpoint_dir_path, test_dir_path, batch_size):
		graph = tf.Graph()
		with graph.as_default():
			# Create a model.
			model = MyModel(*self._dataset.shape, blank_label=self._label_converter.num_tokens, default_value=self._label_converter.pad_id)
			model_output = model.create_model(self._label_converter.num_tokens + 1, is_training=False)

			# Create a saver.
			saver = tf.train.Saver()

		with tf.Session(graph=graph).as_default() as sess:
			# Load a model.
			print('[SWL] Info: Start loading a model...')
			start_time = time.time()
			ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
			ckpt_filepath = ckpt.model_checkpoint_path if ckpt else None
			#ckpt_filepath = tf.train.latest_checkpoint(checkpoint_dir_path)
			if ckpt_filepath:
				saver.restore(sess, ckpt_filepath)
			else:
				print('[SWL] Error: Failed to load a model from {}.'.format(checkpoint_dir_path))
				return
			print('[SWL] Info: End loading a model from {}: {} secs.'.format(ckpt_filepath, time.time() - start_time))

			#--------------------
			print('[SWL] Info: Start testing...')
			start_time = time.time()
			test_steps_per_epoch = None if self._test_examples_per_epoch is None else math.ceil(self._test_examples_per_epoch / batch_size)
			inferences, ground_truths = list(), list()
			for batch_data, num_batch_examples in self._dataset.create_test_batch_generator(batch_size, test_steps_per_epoch, shuffle=False):
				#batch_images, batch_labels_str, batch_labels_int = batch_data
				batch_labels_int = sess.run(
					model_output['decoded_label'],
					feed_dict=model.get_feed_dict((batch_data[0],), num_batch_examples)
				)
				inferences.extend(model.decode_label(batch_labels_int))
				ground_truths.extend(batch_data[1])
			print('[SWL] Info: End testing: {} secs.'.format(time.time() - start_time))

			if inferences and ground_truths:
				#print('Test: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(inferences.shape, inferences.dtype, np.min(inferences), np.max(inferences)))

				# REF [function] >> compute_simple_text_recognition_accuracy() in ${SWL_PYTHON_HOME}/src/swl/language_processing/util.py.
				correct_text_count, correct_word_count, total_word_count, correct_char_count, total_char_count = 0, 0, 0, 0, 0
				total_text_count = max(len(inferences), len(ground_truths))
				for inf_lbl, gt_lbl in zip(inferences, ground_truths):
					inf_lbl = self._label_converter.decode(inf_lbl)

					if inf_lbl == gt_lbl:
						correct_text_count += 1

					inf_words, gt_words = inf_lbl.split(' '), gt_lbl.split(' ')
					total_word_count += max(len(inf_words), len(gt_words))
					#correct_word_count += len(list(filter(lambda x: x[0] == x[1], zip(inf_words, gt_words))))
					correct_word_count += len(list(filter(lambda x: x[0].lower() == x[1].lower(), zip(inf_words, gt_words))))

					total_char_count += max(len(inf_lbl), len(gt_lbl))
					#correct_char_count += len(list(filter(lambda x: x[0] == x[1], zip(inf_lbl, gt_lbl))))
					correct_char_count += len(list(filter(lambda x: x[0].lower() == x[1].lower(), zip(inf_lbl, gt_lbl))))
				print('\tTest: Text accuracy = {} / {} = {}.'.format(correct_text_count, total_text_count, correct_text_count / total_text_count))
				print('\tTest: Word accuracy = {} / {} = {}.'.format(correct_word_count, total_word_count, correct_word_count / total_word_count))
				print('\tTest: Char accuracy = {} / {} = {}.'.format(correct_char_count, total_char_count, correct_char_count / total_char_count))

				# Output to a file.
				csv_filepath = os.path.join(test_dir_path, 'test_results.csv')
				with open(csv_filepath, 'w', newline='', encoding='UTF8') as csvfile:
					writer = csv.writer(csvfile, delimiter=',')

					for inf, gt in zip(inferences, ground_truths):
						inf = self._label_converter.decode(inf)
						writer.writerow([gt, inf])
			else:
				print('[SWL] Warning: Invalid test results.')

	def infer(self, checkpoint_dir_path, inputs, batch_size=None):
		graph = tf.Graph()
		with graph.as_default():
			# Create a model.
			model = MyModel(*self._dataset.shape, blank_label=self._label_converter.num_tokens, default_value=self._label_converter.pad_id)
			model_output = model.create_model(self._label_converter.num_tokens + 1, is_training=False)

			# Create a saver.
			saver = tf.train.Saver()

		with tf.Session(graph=graph).as_default() as sess:
			# Load a model.
			print('[SWL] Info: Start loading a model...')
			start_time = time.time()
			ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
			ckpt_filepath = ckpt.model_checkpoint_path if ckpt else None
			#ckpt_filepath = tf.train.latest_checkpoint(checkpoint_dir_path)
			if ckpt_filepath:
				saver.restore(sess, ckpt_filepath)
			else:
				print('[SWL] Error: Failed to load a model from {}.'.format(checkpoint_dir_path))
				return
			print('[SWL] Info: End loading a model from {}: {} secs.'.format(ckpt_filepath, time.time() - start_time))

			#--------------------
			num_examples = len(inputs)
			if batch_size is None:
				batch_size = num_examples
			if batch_size <= 0:
				raise ValueError('Invalid batch size: {}'.format(batch_size))

			indices = np.arange(num_examples)

			#--------------------
			print('[SWL] Info: Start inferring...')
			start_time = time.time()
			inferences = list()
			start_idx = 0
			while True:
				end_idx = start_idx + batch_size
				batch_indices = indices[start_idx:end_idx]
				if batch_indices.size > 0:  # If batch_indices is non-empty.
					# FIXME [fix] >> Does not work correctly in time-major data.
					batch_images = inputs[batch_indices]
					if batch_images.size > 0:  # If batch_images is non-empty.
						batch_labels_int = sess.run(
							model_output['decoded_label'],
							feed_dict=model.get_feed_dict((batch_images,), len(batch_images))
						)
						inferences.append(model.decode_label(batch_labels_int))

				if end_idx >= num_examples:
					break
				start_idx = end_idx
			print('[SWL] Info: End inferring: {} secs.'.format(time.time() - start_time))
			return inferences

#--------------------------------------------------------------------

def check_data(dataset, label_converter, batch_size):
	train_examples_per_epoch, test_examples_per_epoch = None, None
	train_steps_per_epoch = None if train_examples_per_epoch is None else math.ceil(train_examples_per_epoch / batch_size)
	test_steps_per_epoch = None if test_examples_per_epoch is None else math.ceil(test_examples_per_epoch / batch_size)

	#SOJ, EOJ = '<SOJ>', '<EOJ>'
	EOJ = '<EOJ>'

	import hangeul_util as hg_util
	# NOTE [info] >> Some special Hangeul jamos (e.g. 'ㆍ', 'ㆅ', 'ㆆ') are ignored in the hgtk library.
	hangeul2jamo_functor = lambda hangeul_str: hg_util.hangeul2jamo(hangeul_str, eojc_str=EOJ, use_separate_consonants=False, use_separate_vowels=True)
	# NOTE [info] >> Some special Hangeul jamos (e.g. 'ㆍ', 'ㆅ', 'ㆆ') are ignored in the hgtk library.
	jamo2hangeul_functor = lambda jamo_str: hg_util.jamo2hangeul(jamo_str, eojc_str=EOJ, use_separate_consonants=False, use_separate_vowels=True)

	generator = runner.dataset.create_train_batch_generator(batch_size, train_steps_per_epoch, shuffle=False)
	for batch_step, (batch_data, num_batch_examples) in enumerate(generator):
		#batch_images (np.array), batch_labels_str (a list of strings), batch_labels_int (a list of sequences) = batch_data

		if 0 == batch_step:
			print('type(batch_data) = {}, len(batch_data) = {}.'.format(type(batch_data), len(batch_data)))
			print('type(batch_data[0]) = {}.'.format(type(batch_data[0])))
			print('\tbatch_data[0].shape = {}, batch_data[0].dtype = {}, (min, max) = ({}, {}).'.format(batch_data[0].shape, batch_data[0].dtype, np.min(batch_data[0]), np.max(batch_data[0])))
			print('type(batch_data[1]) = {}, len(batch_data[1]) = {}.'.format(type(batch_data[1]), len(batch_data[1])))
			print('type(batch_data[2]) = {}, len(batch_data[2]) = {}.'.format(type(batch_data[2]), len(batch_data[2])))

		if batch_size != batch_data[0].shape[0]:
			print('Invalid image size: {} != {}.'.format(batch_size, batch_data[0].shape[0]))
		if batch_size != len(batch_data[1]) or batch_size != len(batch_data[2]):
			print('Invalid label size: {0} != {1} or {0} != {2}.'.format(batch_size, len(batch_data[1]), len(batch_data[1])))

		batch_data2_decoded = map(lambda x: label_converter.decode(x), batch_data[2])
		for idx, (lbl, lbl_int, lbl_int_decoded) in enumerate(zip(batch_data[1], batch_data[2], batch_data2_decoded)):
			if len(lbl) != len(lbl_int_decoded):
				print('Unmatched label length: {} != {}.'.format(lbl, lbl_int))
			if 0 == len(lbl_int):
				print('Zero-length label: {}, {}.'.format(lbl, lbl_int))

			jamo_lbl = hangeul2jamo_functor(lbl)
			letter_lbl = jamo2hangeul_functor(jamo_lbl)
			if letter_lbl != lbl:
				print('Unmatched encoded/decoded labels: {} != {} ({}).'.format(lbl, letter_lbl, jamo_lbl))

		sparse = swl_ml_util.sequences_to_sparse(batch_data[2], dtype=np.int32)
		sequences = swl_ml_util.sparse_to_sequences(*sparse, dtype=np.int32)
		#print('Sparse tensor = {}.'.format(sparse))
		dense = swl_ml_util.sequences_to_dense(batch_data[2], default_value=label_converter.pad_id, dtype=np.int32)
		sequences = swl_ml_util.dense_to_sequences(dense, default_value=label_converter.pad_id, dtype=np.int32)
		#print('Dense tensor = {}.'.format(dense))

		break

	#generator = dataset.create_train_batch_generator(batch_size, train_steps_per_epoch, shuffle=False)
	dataset.visualize(generator, num_examples=10)

#--------------------------------------------------------------------

def main():
	#os.environ['CUDA_VISIBLE_DEVICES'] = '0'
	#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'  # [0, 3].

	#--------------------
	is_trained, is_tested, is_inferred = True, True, False
	is_training_resumed = False
	initial_epoch, final_epoch, batch_size = 0, 50, 128
	train_test_ratio = 0.8

	is_dataset_generated_at_runtime = True
	if not is_dataset_generated_at_runtime and (is_trained or is_tested):
		# Data generation.
		#	REF [function] >> generate_single_letter_dataset() in text_generation_util_test.py.
		#	REF [function] >> HangeulJamoTextRecognitionDataGeneratorTextLineDataset_test() in TextRecognitionDataGenerator_data_test.py.

		#data_dir_path = './single_letters_train'
		#data_dir_path = './double_letters_train'
		data_dir_path = './text_line_samples_kr_train'

		if not os.path.isdir(data_dir_path) or not os.path.exists(data_dir_path):
			print('[SWL] Error: Data directory not found, {}.'.format(data_dir_path))
			return
	else:
		data_dir_path = None

	#--------------------
	runner = MyRunner(is_dataset_generated_at_runtime, data_dir_path, train_test_ratio)

	if False:
		print('[SWL] Info: Start checking data...')
		start_time = time.time()
		check_data(runner.dataset, runner.label_converter, batch_size)
		print('[SWL] Info: End checking data: {} secs.'.format(time.time() - start_time))

	#--------------------
	checkpoint_dir_path, output_dir_path = None, None
	if checkpoint_dir_path:
		if not output_dir_path:
			output_dir_path = os.path.dirname(checkpoint_dir_path)
	else:
		if not output_dir_path:
			output_dir_prefix = 'hangeul_jamo_carnet_densenet'
			output_dir_suffix = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
			output_dir_path = os.path.join('.', '{}_{}'.format(output_dir_prefix, output_dir_suffix))
		checkpoint_dir_path = os.path.join(output_dir_path, 'tf_checkpoint')

	test_dir_path = None
	if not test_dir_path:
		test_dir_path = os.path.join(output_dir_path, 'test')
	inference_dir_path = None
	if not inference_dir_path:
		inference_dir_path = os.path.join(output_dir_path, 'inference')

	#--------------------
	if is_trained:
		if checkpoint_dir_path and checkpoint_dir_path.strip() and not os.path.exists(checkpoint_dir_path):
			os.makedirs(checkpoint_dir_path, exist_ok=True)

		history = runner.train(checkpoint_dir_path, batch_size, final_epoch, initial_epoch, is_training_resumed)

		#print('History =', history)
		#swl_ml_util.display_train_history(history)
		if os.path.exists(output_dir_path):
			swl_ml_util.save_train_history(history, output_dir_path)

	if is_tested:
		if not checkpoint_dir_path or not os.path.exists(checkpoint_dir_path):
			print('[SWL] Error: Model directory, {} does not exist.'.format(checkpoint_dir_path))
			return
		if test_dir_path and test_dir_path.strip() and not os.path.exists(test_dir_path):
			os.makedirs(test_dir_path, exist_ok=True)

		runner.test(checkpoint_dir_path, test_dir_path, batch_size)

	if is_inferred:
		if not checkpoint_dir_path or not os.path.exists(checkpoint_dir_path):
			print('[SWL] Error: Model directory, {} does not exist.'.format(checkpoint_dir_path))
			return
		if inference_dir_path and inference_dir_path.strip() and not os.path.exists(inference_dir_path):
			os.makedirs(inference_dir_path, exist_ok=True)

		if 'posix' == os.name:
			data_base_dir_path = '/home/sangwook/work/dataset'
		else:
			data_base_dir_path = 'D:/work/dataset'

		#image_filepaths = glob.glob('./single_letters_test/*.jpg', recursive=False)
		#image_filepaths = glob.glob('./double_letters_test/*.jpg', recursive=False)
		#image_filepaths = glob.glob('./text_line_samples_kr_test/**/*.jpg', recursive=False)
		image_filepaths = glob.glob(data_base_dir_path + '/text/receipt/epapyrus/epapyrus_20190618/receipt_text_line/*.png', recursive=False)
		#image_filepaths = glob.glob(data_base_dir_path + '/text/receipt/sminds/receipt_text_line/*.png', recursive=False)
		if not image_filepaths:
			print('[SWL] Error: No image file for inference.')
			return
		image_filepaths.sort()

		print('[SWL] Info: Start loading images...')
		start_time = time.time()
		inf_images, image_filepaths = runner.dataset.load_images_from_files(image_filepaths, is_grayscale=True)
		print('[SWL] Info: End loading images: {} secs.'.format(time.time() - start_time))
		print('[SWL] Info: Loaded images: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(inf_images.shape, inf_images.dtype, np.min(inf_images), np.max(inf_images)))

		inferences = runner.infer(checkpoint_dir_path, inf_images, batch_size)

		if inferences:
			#print('Inference: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(inferences.shape, inferences.dtype, np.min(inferences), np.max(inferences)))

			inferences_str = list()
			for inf in inferences:
				inferences_str.extend(map(lambda x: runner.dataset.decode_label(x), inf))

			# Output to a file.
			csv_filepath = os.path.join(inference_dir_path, 'inference_results.csv')
			with open(csv_filepath, 'w', newline='', encoding='UTF8') as csvfile:
				writer = csv.writer(csvfile, delimiter=',')

				for fpath, inf in zip(image_filepaths, inferences_str):
					writer.writerow([fpath, inf])
		else:
			print('[SWL] Warning: Invalid inference results.')

#--------------------------------------------------------------------

if '__main__' == __name__:
	main()
