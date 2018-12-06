import time
import numpy as np
import tensorflow as tf
from swl.machine_learning.tensorflow.neural_net_trainer import NeuralNetTrainer
from swl.machine_learning.tensorflow.neural_net_evaluator import NeuralNetEvaluator
from swl.machine_learning.tensorflow.neural_net_inferrer import NeuralNetInferrer
import swl.machine_learning.util as swl_ml_util

#%%------------------------------------------------------------------

# Supports lists of dense or sparse labels.
def train_neural_net_by_batch_list(session, nnTrainer, train_inputs_list, train_outputs_list, val_inputs_list, val_outputs_list, num_epochs, shuffle, does_resume_training, saver, output_dir_path, checkpoint_dir_path, train_summary_dir_path, val_summary_dir_path, is_time_major, is_sparse_label):
	num_train_batches, num_val_batches = len(train_inputs_list), len(val_inputs_list)
	if len(train_outputs_list) != num_train_batches or len(val_outputs_list) != num_val_batches:
		raise ValueError('Invalid parameter length')

	if does_resume_training:
		print('[SWL] Info: Resume training...')

		# Load a model.
		# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
		# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
		ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
		saver.restore(session, ckpt.model_checkpoint_path)
		#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
		print('[SWL] Info: Restored a model.')
	else:
		print('[SWL] Info: Start training...')

	# Create writers to write all the summaries out to a directory.
	train_summary_writer = tf.summary.FileWriter(train_summary_dir_path, session.graph) if train_summary_dir_path is not None else None
	val_summary_writer = tf.summary.FileWriter(val_summary_dir_path) if val_summary_dir_path is not None else None

	history = {
		'acc': [],
		'loss': [],
		'val_acc': [],
		'val_loss': []
	}

	batch_axis = 1 if is_time_major else 0

	best_val_acc = 0.0
	for epoch in range(1, num_epochs + 1):
		print('Epoch {}/{}'.format(epoch, num_epochs))

		start_time = time.time()

		indices = np.arange(num_train_batches)
		if shuffle:
			np.random.shuffle(indices)

		print('>-', sep='', end='')
		processing_ratio = 0.05
		train_loss, train_acc, num_train_examples = 0.0, 0.0, 0
		for step in indices:
			train_inputs, train_outputs = train_inputs_list[step], train_outputs_list[step]
			batch_acc, batch_loss = nnTrainer.train_by_batch(session, train_inputs, train_outputs, train_summary_writer, is_time_major, is_sparse_label)

			# TODO [check] >> Are these calculations correct?
			batch_size = train_inputs.shape[batch_axis]
			train_acc += batch_acc * batch_size
			train_loss += batch_loss * batch_size
			num_train_examples += batch_size

			if step / num_train_batches >= processing_ratio:
				print('-', sep='', end='')
				processing_ratio = round(step / num_train_batches, 2) + 0.05
		print('<')

		train_acc /= num_train_examples
		train_loss /= num_train_examples

		#--------------------
		indices = np.arange(num_val_batches)
		#if shuffle:
		#	np.random.shuffle(indices)

		val_loss, val_acc, num_val_examples = 0.0, 0.0, 0
		for step in indices:
			val_inputs, val_outputs = val_inputs_list[step], val_outputs_list[step]
			batch_acc, batch_loss = nnTrainer.evaluate_training_by_batch(session, val_inputs, val_outputs, val_summary_writer, is_time_major, is_sparse_label)

			# TODO [check] >> Are these calculations correct?
			batch_size = val_inputs.shape[batch_axis]
			val_acc += batch_acc * batch_size
			val_loss += batch_loss * batch_size
			num_val_examples += batch_size

		val_acc /= num_val_examples
		val_loss /= num_val_examples

		history['acc'].append(train_acc)
		history['loss'].append(train_loss)
		history['val_acc'].append(val_acc)
		history['val_loss'].append(val_loss)

		# Save a model.
		if saver is not None and checkpoint_dir_path is not None and val_acc >= best_val_acc:
			saved_model_path = saver.save(session, checkpoint_dir_path + '/model.ckpt', global_step=nnTrainer.global_step)
			best_val_acc = val_acc
			print('[SWL] Info: Accurary is improved and the model is saved at {}.'.format(saved_model_path))

		print('\tTraining time = {}'.format(time.time() - start_time))
		print('\tLoss = {}, accuracy = {}, validation loss = {}, validation accurary = {}'.format(train_loss, train_acc, val_loss, val_acc))

	# Close writers.
	if train_summary_writer is not None:
		train_summary_writer.close()
	if val_summary_writer is not None:
		val_summary_writer.close()

	#--------------------
	# Save a graph.
	#tf.train.write_graph(session.graph_def, output_dir_path, 'crnn_graph.pb', as_text=False)
	##tf.train.write_graph(session.graph_def, output_dir_path, 'crnn_graph.pbtxt', as_text=True)

	# Save a serving model.
	#builder = tf.saved_model.builder.SavedModelBuilder(output_dir_path + '/serving_model')
	#builder.add_meta_graph_and_variables(session, [tf.saved_model.tag_constants.SERVING], saver=saver)
	#builder.save(as_text=False)

	# Display results.
	#swl_ml_util.display_train_history(history)
	if output_dir_path is not None:
		swl_ml_util.save_train_history(history, output_dir_path)
	print('[SWL] Info: End training...')

# Supports a dense label only.
def train_neural_net_after_generating_batch_list(session, nnTrainer, train_inputs, train_outputs, val_inputs, val_outputs, batch_size, num_epochs, shuffle, does_resume_training, saver, output_dir_path, checkpoint_dir_path, train_summary_dir_path, val_summary_dir_path, is_time_major):
	batch_axis = 1 if is_time_major else 0

	num_train_examples, num_train_steps = 0, 0
	if train_inputs is not None and train_outputs is not None:
		if train_inputs.shape[batch_axis] == train_outputs.shape[batch_axis]:
			num_train_examples = train_inputs.shape[batch_axis]
		num_train_steps = ((num_train_examples - 1) // batch_size + 1) if num_train_examples > 0 else 0
	num_val_examples, num_val_steps = 0, 0
	if val_inputs is not None and val_outputs is not None:
		if val_inputs.shape[batch_axis] == val_outputs.shape[batch_axis]:
			num_val_examples = val_inputs.shape[batch_axis]
		num_val_steps = ((num_val_examples - 1) // batch_size + 1) if num_val_examples > 0 else 0

	indices = np.arange(num_train_examples)
	if shuffle:
		np.random.shuffle(indices)

	train_inputs_list, train_outputs_list = list(), list()
	for step in range(num_train_steps):
		start = step * batch_size
		end = start + batch_size
		batch_indices = indices[start:end]
		if batch_indices.size > 0:  # If batch_indices is non-empty.
			train_inputs_list.append(train_inputs[batch_indices])
			train_outputs_list.append(train_outputs[batch_indices])

	#--------------------
	indices = np.arange(num_val_examples)
	if shuffle:
		np.random.shuffle(indices)

	val_inputs_list, val_outputs_list = list(), list()
	for step in range(num_val_steps):
		start = step * batch_size
		end = start + batch_size
		batch_indices = indices[start:end]
		if batch_indices.size > 0:  # If batch_indices is non-empty.
			val_inputs_list.append(val_inputs[batch_indices])
			val_outputs_list.append(val_outputs[batch_indices])

	train_neural_net_by_batch_list(session, nnTrainer, train_inputs_list, train_outputs_list, val_inputs_list, val_outputs_list, num_epochs, shuffle, does_resume_training, saver, output_dir_path, checkpoint_dir_path, train_summary_dir_path, val_summary_dir_path, is_time_major, False)

# Supports a dense label only.
def train_neural_net(session, nnTrainer, train_images, train_labels, val_images, val_labels, batch_size, num_epochs, shuffle, does_resume_training, saver, output_dir_path, checkpoint_dir_path, train_summary_dir_path, val_summary_dir_path):
	if does_resume_training:
		print('[SWL] Info: Resume training...')

		# Load a model.
		# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
		# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
		ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
		saver.restore(session, ckpt.model_checkpoint_path)
		#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
		print('[SWL] Info: Restored a model.')
	else:
		print('[SWL] Info: Start training...')

	start_time = time.time()
	history = nnTrainer.train(session, train_images, train_labels, val_images, val_labels, batch_size, num_epochs, shuffle, saver=saver, model_save_dir_path=checkpoint_dir_path, train_summary_dir_path=train_summary_dir_path, val_summary_dir_path=val_summary_dir_path)
	print('\tTraining time = {}'.format(time.time() - start_time))

	# Save a graph.
	#tf.train.write_graph(session.graph_def, output_dir_path, 'crnn_graph.pb', as_text=False)
	##tf.train.write_graph(session.graph_def, output_dir_path, 'crnn_graph.pbtxt', as_text=True)

	# Save a serving model.
	#builder = tf.saved_model.builder.SavedModelBuilder(output_dir_path + '/serving_model')
	#builder.add_meta_graph_and_variables(session, [tf.saved_model.tag_constants.SERVING], saver=saver)
	#builder.save(as_text=False)

	# Display results.
	#swl_ml_util.display_train_history(history)
	if output_dir_path is not None:
		swl_ml_util.save_train_history(history, output_dir_path)
	print('[SWL] Info: End training...')

# Supports lists of dense or sparse labels.
def evaluate_neural_net_by_batch_list(session, nnEvaluator, val_inputs_list, val_outputs_list, saver=None, checkpoint_dir_path=None, is_time_major=False, is_sparse_label=False):
	num_val_batches = len(val_inputs_list)
	if len(val_outputs_list) != num_val_batches:
		raise ValueError('Invalid parameter length')

	batch_axis = 1 if is_time_major else 0

	if saver is not None and checkpoint_dir_path is not None:
		# Load a model.
		# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
		# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
		ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
		saver.restore(session, ckpt.model_checkpoint_path)
		#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
		print('[SWL] Info: Loaded a model.')

	print('[SWL] Info: Start evaluation...')
	start_time = time.time()
	indices = np.arange(num_val_batches)
	#if shuffle:
	#	np.random.shuffle(indices)

	val_loss, val_acc, num_val_examples = 0.0, 0.0, 0
	for step in indices:
		batch_acc, batch_loss = nnEvaluator.evaluate_by_batch(session, val_inputs_list[step], val_outputs_list[step], is_time_major, is_sparse_label)

		# TODO [check] >> Are these calculations correct?
		batch_size = val_inputs_list[step].shape[batch_axis]
		val_acc += batch_acc * batch_size
		val_loss += batch_loss * batch_size
		num_val_examples += batch_size

	val_acc /= num_val_examples
	val_loss /= num_val_examples
	print('\tEvaluation time = {}'.format(time.time() - start_time))
	print('\tValidation loss = {}, validation accurary = {}'.format(val_loss, val_acc))
	print('[SWL] Info: End evaluation...')

# Supports dense or sparse labels.
# But when labels are sparse, all dataset is processed at once.
def evaluate_neural_net(session, nnEvaluator, val_images, val_labels, batch_size, saver=None, checkpoint_dir_path=None, is_time_major=False, is_sparse_label=False):
	batch_axis = 1 if is_time_major else 0

	num_val_examples = 0
	if val_images is not None and val_labels is not None:
		if is_sparse_label:
			num_val_examples = val_images.shape[batch_axis]
		else:
			if val_images.shape[batch_axis] == val_labels.shape[batch_axis]:
				num_val_examples = val_images.shape[batch_axis]

	if num_val_examples > 0:
		if saver is not None and checkpoint_dir_path is not None:
			# Load a model.
			# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
			# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
			ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
			saver.restore(session, ckpt.model_checkpoint_path)
			#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
			print('[SWL] Info: Loaded a model.')

		print('[SWL] Info: Start evaluation...')
		start_time = time.time()
		#val_loss, val_acc = nnEvaluator.evaluate(session, val_images, val_labels, batch_size)
		val_loss, val_acc = nnEvaluator.evaluate(session, val_images, val_labels, num_val_examples if is_sparse_label else batch_size)
		print('\tEvaluation time = {}'.format(time.time() - start_time))
		print('\tValidation loss = {}, validation accurary = {}'.format(val_loss, val_acc))
		print('[SWL] Info: End evaluation...')
	else:
		print('[SWL] Error: The number of validation images is not equal to that of validation labels.')

# Supports lists of dense or sparse labels.
def infer_from_batch_list_by_neural_net(session, nnInferrer, inf_inputs_list, saver=None, checkpoint_dir_path=None, is_time_major=False):
	num_inf_batches = len(inf_inputs_list)

	batch_axis = 1 if is_time_major else 0

	if saver is not None and checkpoint_dir_path is not None:
		# Load a model.
		# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
		# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
		ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
		saver.restore(session, ckpt.model_checkpoint_path)
		#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
		print('[SWL] Info: Loaded a model.')

	print('[SWL] Info: Start inferring...')
	start_time = time.time()
	indices = np.arange(num_inf_batches)
	#if shuffle:
	#	np.random.shuffle(indices)

	inf_outputs_list = list()
	for step in indices:
		batch_outputs = nnInferrer.infer_by_batch(session, inf_inputs_list[step], is_time_major)
		inf_outputs_list.append(batch_outputs)
	print('\tInference time = {}'.format(time.time() - start_time))
	print('[SWL] Info: End inferring...')

	return inf_outputs_list

# Supports dense or sparse labels.
# But when labels are sparse, all dataset is processed at once.
def infer_by_neural_net(session, nnInferrer, test_images, batch_size, saver=None, checkpoint_dir_path=None, is_time_major=False, is_sparse_label=False):
	batch_axis = 1 if is_time_major else 0

	num_inf_examples = 0
	if test_images is not None:
		num_inf_examples = test_images.shape[batch_axis]

	if num_inf_examples > 0:
		if saver is not None and checkpoint_dir_path is not None:
			# Load a model.
			# REF [site] >> https://www.tensorflow.org/programmers_guide/saved_model
			# REF [site] >> http://cv-tricks.com/tensorflow-tutorial/save-restore-tensorflow-models-quick-complete-tutorial/
			ckpt = tf.train.get_checkpoint_state(checkpoint_dir_path)
			saver.restore(session, ckpt.model_checkpoint_path)
			#saver.restore(session, tf.train.latest_checkpoint(checkpoint_dir_path))
			print('[SWL] Info: Loaded a model.')

		print('[SWL] Info: Start inferring...')
		start_time = time.time()
		#inferences = nnInferrer.infer(session, test_images, batch_size)
		inferences = nnInferrer.infer(session, test_images, num_inf_examples if is_sparse_label else batch_size)
		print('\tInference time = {}'.format(time.time() - start_time))
		print('[SWL] Info: End inferring...')

		return inferences
	else:
		print('[SWL] Error: The number of test images is not equal to that of test labels.')
		return None
