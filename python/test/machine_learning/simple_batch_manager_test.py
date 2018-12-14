#!/usr/bin/env python

import os, sys
if 'posix' == os.name:
	swl_python_home_dir_path = '/home/sangwook/work/SWL_github/python'
else:
	swl_python_home_dir_path = 'D:/work/SWL_github/python'
sys.path.append('../../src')

#--------------------
import numpy as np
from swl.machine_learning.batch_manager import SimpleBatchManager, SimpleBatchManagerWithFileInput, SimpleFileBatchManager, SimpleFileBatchManagerWithFileInput
from swl.util.directory_queue_manager import DirectoryQueueManager

def simple_batch_manager_example():
	num_examples = 100
	images = np.random.rand(num_examples, 64, 64, 1)
	labels = np.random.randint(2, size=(num_examples, 5))

	batch_size = 12
	num_epoches = 7
	shuffle = True
	is_time_major = False

	batchMgr = SimpleBatchManager(images, labels, batch_size, shuffle, is_time_major)
	for epoch in range(num_epoches):
		print('>>>>> Epoch #{}.'.format(epoch))

		batches = batchMgr.getBatches()
		for idx, batch in enumerate(batches):
			# Train with batch (images & labels).
			print(idx, batch[0].shape, batch[1].shape)

def simple_batch_manager_with_file_input_example():
	#num_examples = 130
	npy_filepath_pairs = np.array([
		('./batches/images_0.npy', './batches/labels_0.npy'),
		('./batches/images_1.npy', './batches/labels_1.npy'),
		('./batches/images_2.npy', './batches/labels_2.npy'),
		('./batches/images_3.npy', './batches/labels_3.npy'),
		('./batches/images_4.npy', './batches/labels_4.npy'),
		('./batches/images_5.npy', './batches/labels_5.npy'),
		('./batches/images_6.npy', './batches/labels_6.npy'),
		('./batches/images_7.npy', './batches/labels_7.npy'),
		('./batches/images_8.npy', './batches/labels_8.npy'),
		('./batches/images_9.npy', './batches/labels_9.npy'),
	])
	total_num_file_pairs = len(npy_filepath_pairs)
	num_file_pairs = 3
	num_file_pair_steps = ((total_num_file_pairs - 1) // num_file_pairs + 1) if total_num_file_pairs > 0 else 0

	batch_size = 12
	num_epoches = 7
	shuffle = True
	is_time_major = False

	#--------------------
	for epoch in range(num_epoches):
		print('>>>>> Epoch #{}.'.format(epoch))
		
		# Run in separate threads or processes.
		indices = np.arange(total_num_file_pairs)
		if shuffle:
			np.random.shuffle(indices)

		for step in range(num_file_pair_steps):
			print('\t>>>>> File pairs #{}.'.format(step))
			
			start = step * num_file_pairs
			end = start + num_file_pairs
			file_pair_indices = indices[start:end]
			if file_pair_indices.size > 0:  # If file_pair_indices is non-empty.
				sub_filepath_pairs = npy_filepath_pairs[file_pair_indices]
				if sub_filepath_pairs.size > 0:  # If sub_filepath_pairs is non-empty.
					batchMgr = SimpleBatchManagerWithFileInput(sub_filepath_pairs, batch_size, shuffle, is_time_major)
					for idx, batch in enumerate(batchMgr.getBatches()):
						# Train with batch (images & labels).
						print('\t', idx, batch[0].shape, batch[1].shape)

def simple_file_batch_manager_example():
	num_examples = 100
	if True:
		images = np.random.rand(num_examples, 64, 64, 1)
		labels = np.random.rand(num_examples, 64, 64, 1)
	else:
		images = np.random.rand(num_examples, 64, 64, 1)
		labels = np.random.randint(2, size=(num_examples, 5))

	batch_size = 12
	num_epoches = 7
	shuffle = True
	is_time_major = False

	base_dir_path = './batch_dir'
	num_dirs = 5
	dirQueueMgr = DirectoryQueueManager(base_dir_path, num_dirs)

	#--------------------
	for epoch in range(num_epoches):
		print('>>>>> Epoch #{}.'.format(epoch))

		dir_path = dirQueueMgr.getAvailableDirectory()
		if dir_path is None:
			break

		print('\t>>>>> Directory: {}.'.format(dir_path))

		# Run in separate threads or processes.
		batchMgr = SimpleFileBatchManager(images, labels, dir_path, batch_size, shuffle, is_time_major)
		batchMgr.putBatches()

		for idx, batch in enumerate(batchMgr.getBatches()):
			# Train with batch (images & labels).
			print('\t', idx, batch[0].shape, batch[1].shape)

		dirQueueMgr.returnDirectory(dir_path)				

def simple_file_batch_manager_with_file_input_example():
	#num_examples = 130
	npy_filepath_pairs = np.array([
		('./batches/images_0.npy', './batches/labels_0.npy'),
		('./batches/images_1.npy', './batches/labels_1.npy'),
		('./batches/images_2.npy', './batches/labels_2.npy'),
		('./batches/images_3.npy', './batches/labels_3.npy'),
		('./batches/images_4.npy', './batches/labels_4.npy'),
		('./batches/images_5.npy', './batches/labels_5.npy'),
		('./batches/images_6.npy', './batches/labels_6.npy'),
		('./batches/images_7.npy', './batches/labels_7.npy'),
		('./batches/images_8.npy', './batches/labels_8.npy'),
		('./batches/images_9.npy', './batches/labels_9.npy'),
	])
	total_num_file_pairs = len(npy_filepath_pairs)
	num_file_pairs = 3
	num_file_pair_steps = ((total_num_file_pairs - 1) // num_file_pairs + 1) if total_num_file_pairs > 0 else 0

	batch_size = 12
	num_epoches = 7
	shuffle = True
	is_time_major = False

	base_dir_path = './batch_dir'
	num_dirs = 5
	dirQueueMgr = DirectoryQueueManager(base_dir_path, num_dirs)

	#--------------------
	for epoch in range(num_epoches):
		print('>>>>> Epoch #{}.'.format(epoch))

		dir_path = dirQueueMgr.getAvailableDirectory()
		if dir_path is None:
			break

		print('\t>>>>> Directory: {}.'.format(dir_path))
		
		# Run in separate threads or processes.
		indices = np.arange(total_num_file_pairs)
		if shuffle:
			np.random.shuffle(indices)

		for step in range(num_file_pair_steps):
			print('\t\t>>>>> File pairs #{}.'.format(step))

			start = step * num_file_pairs
			end = start + num_file_pairs
			file_pair_indices = indices[start:end]
			if file_pair_indices.size > 0:  # If file_pair_indices is non-empty.
				sub_filepath_pairs = npy_filepath_pairs[file_pair_indices]
				if sub_filepath_pairs.size > 0:  # If sub_filepath_pairs is non-empty.
					batchMgr = SimpleFileBatchManagerWithFileInput(sub_filepath_pairs, dir_path, batch_size, shuffle, is_time_major)
					batchMgr.putBatches()

					for idx, batch in enumerate(batchMgr.getBatches()):
						# Train with batch (images & labels).
						print('\t\t', idx, batch[0].shape, batch[1].shape)

		dirQueueMgr.returnDirectory(dir_path)

def main():
	simple_batch_manager_example()
	#simple_batch_manager_with_file_input_example()

	#simple_file_batch_manager_example()
	#simple_file_batch_manager_with_file_input_example()

#%%------------------------------------------------------------------

if '__main__' == __name__:
	main()