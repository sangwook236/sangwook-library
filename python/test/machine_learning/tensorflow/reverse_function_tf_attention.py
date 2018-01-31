import tensorflow as tf
from reverse_function_rnn import ReverseFunctionRNN

#%%------------------------------------------------------------------

class ReverseFunctionTensorFlowEncoderDecoderWithAttention(ReverseFunctionRNN):
	def __init__(self, input_shape, output_shape, is_dynamic=True, is_bidirectional=True):
		self._is_dynamic = is_dynamic
		self._is_bidirectional = is_bidirectional
		super().__init__(input_shape, output_shape)

	def _create_model(self, input_tensor, is_training_tensor, input_shape, output_shape):
		with tf.variable_scope('reverse_function_tf_attention', reuse=tf.AUTO_REUSE):
			if self._is_dynamic:
				num_classes = output_shape[-1]
				if self._is_bidirectional:
					return self._create_dynamic_bidirectional_model(input_tensor, is_training_tensor, num_classes)
				else:
					return self._create_dynamic_model(input_tensor, is_training_tensor, num_classes)
			else:
				num_time_steps, num_classes = input_shape[0], output_shape[-1]
				if self._is_bidirectional:
					return self._create_static_bidirectional_model(input_tensor, is_training_tensor, num_time_steps, num_classes)
				else:
					return self._create_static_model(input_tensor, is_training_tensor, num_time_steps, num_classes)

	def _create_dynamic_model(self, input_tensor, is_training_tensor, num_classes):
		num_enc_hidden_units = 128
		num_dec_hidden_units = 128
		keep_prob = 0.75

		# Defines cells.
		enc_cell = self._create_cell(num_enc_hidden_units)
		enc_cell = tf.contrib.rnn.DropoutWrapper(enc_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#enc_cell = tf.contrib.rnn.AttentionCellWrapper(enc_cell, attention_window_len, state_is_tuple=True)
		dec_cell = self._create_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#dec_cell = tf.contrib.rnn.AttentionCellWrapper(dec_cell, attention_window_len, state_is_tuple=True)

		# Encoder.
		#enc_cell_outputs, enc_cell_state = tf.nn.dynamic_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _ = tf.nn.dynamic_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')

		# Attention.

		# Decoder.
		#cell_outputs, dec_cell_state = tf.nn.dynamic_rnn(dec_cell, enc_cell_outputs, initial_state=dec_cell_state, dtype=tf.float32, scope='dec')

		#with tf.variable_scope('enc-dec', reuse=tf.AUTO_REUSE):
		#	dropout_rate = 1 - keep_prob
		#	# NOTE [info] >> If dropout_rate=0.0, dropout layer is not created.
		#	cell_outputs = tf.layers.dropout(cell_outputs, rate=dropout_rate, training=is_training_tensor, name='dropout')

		with tf.variable_scope('fc1', reuse=tf.AUTO_REUSE):
			if 1 == num_classes:
				fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			elif num_classes >= 2:
				fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			else:
				assert num_classes > 0, 'Invalid number of classes.'

			return fc1

	def _create_dynamic_bidirectional_model(self, input_tensor, is_training_tensor, num_classes):
		num_enc_hidden_units = 64
		num_dec_hidden_units = 128
		keep_prob = 0.75

		# Defines cells.
		enc_cell_fw = self._create_cell(num_enc_hidden_units)  # Forward cell.
		enc_cell_fw = tf.contrib.rnn.DropoutWrapper(enc_cell_fw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		enc_cell_bw = self._create_cell(num_enc_hidden_units)  # Backward cell.
		enc_cell_bw = tf.contrib.rnn.DropoutWrapper(enc_cell_bw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		dec_cell = self._create_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)

		# Encoder.
		#enc_cell_outputs, cell_states = tf.nn.bidirectional_dynamic_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32)
		enc_cell_outputs, _ = tf.nn.bidirectional_dynamic_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32)
		enc_cell_outputs = tf.concat(enc_cell_outputs, 2)
		#enc_cell_states = tf.concat(enc_cell_states, 2)

		# Attention.
		with tf.name_scope('attention'):
			self._attend()

		# Decoder.
		#cell_outputs, dec_cell_state = tf.nn.dynamic_rnn(dec_cell, enc_cell_outputs, dtype=tf.float32, scope='dec')
		cell_outputs, _ = tf.nn.dynamic_rnn(dec_cell, enc_cell_outputs, dtype=tf.float32, scope='dec')

		#with tf.variable_scope('attention', reuse=tf.AUTO_REUSE):
		#	dropout_rate = 1 - keep_prob
		#	# NOTE [info] >> If dropout_rate=0.0, dropout layer is not created.
		#	cell_outputs = tf.layers.dropout(dec_cell_outputs, rate=dropout_rate, training=is_training_tensor, name='dropout')

		with tf.variable_scope('fc1', reuse=tf.AUTO_REUSE):
			if 1 == num_classes:
				fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			elif num_classes >= 2:
				fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			else:
				assert num_classes > 0, 'Invalid number of classes.'

			return fc1

	def _create_static_model(self, input_tensor, is_training_tensor, num_time_steps, num_classes):
		num_enc_hidden_units = 128
		num_dec_hidden_units = 128
		keep_prob = 0.75

		# Defines cells.
		enc_cell = self._create_cell(num_enc_hidden_units)
		enc_cell = tf.contrib.rnn.DropoutWrapper(enc_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#enc_cell = tf.contrib.rnn.AttentionCellWrapper(enc_cell, attention_window_len, state_is_tuple=True)
		dec_cell = self._create_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#dec_cell = tf.contrib.rnn.AttentionCellWrapper(dec_cell, attention_window_len, state_is_tuple=True)

		# Unstack: a tensor of shape (samples, time-steps, features) -> a list of 'time-steps' tensors of shape (samples, features).
		input_tensor = tf.unstack(input_tensor, num_time_steps, axis=1)

		# Encoder.
		#enc_cell_outputs, enc_cell_state = tf.nn.static_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _ = tf.nn.static_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')

		input_shape = tf.shape(input_tensor)
		batch_size = input_shape[0]
		dec_cell_state = dec_cell.zero_state(batch_size, tf.float32)
		dec_cell_outputs = []
		for _ in range(num_time_steps):
			# Attention.
			context = self._attend_additively(enc_cell_outputs, dec_cell_state)
			#context = self._attend_multiplicatively(enc_cell_outputs, dec_cell_state)

			# Decoder.
			dec_cell_output, dec_cell_state = tf.nn.static_rnn(dec_cell, context, initial_state=dec_cell_state, dtype=tf.float32, scope='dec')
			dec_cell_outputs.append(dec_cell_output)

		# Stack: a list of 'time-steps' tensors of shape (samples, features) -> a tensor of shape (samples, time-steps, features).
		cell_outputs = tf.stack(dec_cell_outputs, axis=1)

		#with tf.variable_scope('enc-dec', reuse=tf.AUTO_REUSE):
		#	dropout_rate = 1 - keep_prob
		#	# NOTE [info] >> If dropout_rate=0.0, dropout layer is not created.
		#	cell_outputs = tf.layers.dropout(cell_outputs, rate=dropout_rate, training=is_training_tensor, name='dropout')

		with tf.variable_scope('fc1', reuse=tf.AUTO_REUSE):
			if 1 == num_classes:
				fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			elif num_classes >= 2:
				fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			else:
				assert num_classes > 0, 'Invalid number of classes.'

			return fc1

	def _create_static_bidirectional_model(self, input_tensor, is_training_tensor, num_time_steps, num_classes):
		num_enc_hidden_units = 64
		num_dec_hidden_units = 128
		keep_prob = 0.75

		# Defines cells.
		enc_cell_fw = self._create_cell(num_enc_hidden_units)  # Forward cell.
		enc_cell_fw = tf.contrib.rnn.DropoutWrapper(enc_cell_fw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		enc_cell_bw = self._create_cell(num_enc_hidden_units)  # Backward cell.
		enc_cell_bw = tf.contrib.rnn.DropoutWrapper(enc_cell_bw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		dec_cell = self._create_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)

		# Unstack: a tensor of shape (samples, time-steps, features) -> a list of 'time-steps' tensors of shape (samples, features).
		input_tensor = tf.unstack(input_tensor, num_time_steps, axis=1)

		# Encoder.
		#enc_cell_outputs, enc_cell_state_fw, enc_cell_state_bw = tf.nn.bidirectional_dynamic_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32, scope='enc')
		#enc_cell_states = tf.concat((enc_cell_state_fw, enc_cell_state_bw), 2)  # ?
		enc_cell_outputs, _, _ = tf.nn.static_bidirectional_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32, scope='enc')

		# Attention.

		# Decoder.
		#dec_cell_outputs, dec_cell_state = tf.nn.static_rnn(dec_cell, enc_cell_outputs, dtype=tf.float32, scope='dec')
		dec_cell_outputs, _ = tf.nn.static_rnn(dec_cell, enc_cell_outputs, dtype=tf.float32, scope='dec')

		# Stack: a list of 'time-steps' tensors of shape (samples, features) -> a tensor of shape (samples, time-steps, features).
		cell_outputs = tf.stack(dec_cell_outputs, axis=1)

		#with tf.variable_scope('enc-dec', reuse=tf.AUTO_REUSE):
		#	dropout_rate = 1 - keep_prob
		#	# NOTE [info] >> If dropout_rate=0.0, dropout layer is not created.
		#	cell_outputs = tf.layers.dropout(cell_outputs, rate=dropout_rate, training=is_training_tensor, name='dropout')

		with tf.variable_scope('fc1', reuse=tf.AUTO_REUSE):
			if 1 == num_classes:
				fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, 1, activation=tf.sigmoid, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			elif num_classes >= 2:
				fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, name='fc')
				#fc1 = tf.layers.dense(cell_outputs, num_classes, activation=tf.nn.softmax, activity_regularizer=tf.contrib.layers.l2_regularizer(0.0001), name='fc')
			else:
				assert num_classes > 0, 'Invalid number of classes.'

			return fc1

	def _create_cell(self, num_units):
		#return tf.contrib.rnn.BasicRNNCell(num_units, forget_bias=1.0)
		return tf.contrib.rnn.BasicLSTMCell(num_units, forget_bias=1.0)
		#return tf.contrib.rnn.RNNCell(num_units, forget_bias=1.0)
		#return tf.contrib.rnn.LSTMCell(num_units, forget_bias=1.0)
		#return tf.contrib.rnn.GRUCell(num_units, forget_bias=1.0)

	# REF [function] >> _weight_variable() in ./mnist_tf_cnn.py.
	# We can't initialize these variables to 0 - the network will get stuck.
	def _weight_variable(self, shape, name):
		"""Create a weight variable with appropriate initialization."""
		#initial = tf.truncated_normal(shape, stddev=0.1)
		#return tf.Variable(initial, name=name)
		return tf.get_variable(name, shape, initializer=tf.truncated_normal_initializer(stddev=0.1))

	# REF [function] >> _variable_summaries() in ./mnist_tf_cnn.py.
	def _variable_summaries(self, var, is_filter=False):
		"""Attach a lot of summaries to a Tensor (for TensorBoard visualization)."""
		with tf.name_scope('summaries'):
			mean = tf.reduce_mean(var)
			tf.summary.scalar('mean', mean)
			with tf.name_scope('stddev'):
				stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
			tf.summary.scalar('stddev', stddev)
			tf.summary.scalar('max', tf.reduce_max(var))
			tf.summary.scalar('min', tf.reduce_min(var))
			tf.summary.histogram('histogram', var)
			if is_filter:
				tf.summary.image('filter', var)  # Visualizes filters.

	# REF [paper] >> "Neural Machine Translation by Jointly Learning to Align and Translate", arXiv 2016.
	# REF [site] >> https://www.tensorflow.org/api_guides/python/contrib.seq2seq
	# REF [site] >> https://talbaumel.github.io/attention/
	def _attend_additively(self, inputs, state):
		input_shape = tf.shape(inputs)
		state_shape = tf.shape(state)

		with tf.name_scope('attention_W1'):
			attention_W1 = self._weight_variable((input_shape[-1], input_shape[-1]))
			self._variable_summaries(attention_W1)
		with tf.name_scope('attention_W2'):
			attention_W2 = self._weight_variable((state_shape[-1], input_shape[-1]))
			self._variable_summaries(attention_W2)
		with tf.name_scope('attention_V'):
			attention_V = self._weight_variable((input_shape[-1], 1))
			self._variable_summaries(attention_V)

		attention_weights = []
		for inp in inputs:
			attention_weight = tf.matmul(inp, attention_W1) + tf.matmul(state, attention_W2)
			attention_weight = tf.matmul(tf.tanh(attention_weight), attention_V)
			attention_weights.append(attention_weight)

		attention_weights = tf.nn.softmax(tf.convert_to_tensor(attention_weights, dtype=tf.float32))
		return tf.reduce_sum(tf.convert_to_tensor([inp * weight for inp, weight in zip(inputs, attention_weights)], dtype=tf.float32), axis=1)

	# REF [paper] >> "Effective Approaches to Attention-based Neural Machine Translation", arXiv 2015.
	# REF [site] >> https://www.tensorflow.org/api_guides/python/contrib.seq2seq
	def _attend_multiplicatively(self, inputs, state):
		raise NotImplementedError
