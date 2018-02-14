import tensorflow as tf
from simple_neural_net import SimpleNeuralNet
from swl.machine_learning.tensorflow.attention_mechanism import BahdanauAttentionMechanism, LuongAttentionMechanism

#%%------------------------------------------------------------------

class SimpleEncoderDecoderWithAttention(SimpleNeuralNet):
	def __init__(self, input_shape, output_shape, is_dynamic=True, is_bidirectional=True, is_time_major=False):
		self._is_dynamic = is_dynamic
		self._is_bidirectional = is_bidirectional
		self._is_time_major = is_time_major
		super().__init__(input_shape, output_shape)

	def _create_model(self, input_tensor, output_tensor, is_training_tensor, input_shape, output_shape):
		with tf.variable_scope('simple_encdec_attention', reuse=tf.AUTO_REUSE):
			if self._is_dynamic:
				num_classes = output_shape[-1]
				if self._is_bidirectional:
					return self._create_dynamic_bidirectional_model(input_tensor, is_training_tensor, num_classes, self._is_time_major)
				else:
					return self._create_dynamic_model(input_tensor, is_training_tensor, num_classes, self._is_time_major)
			else:
				if self._is_time_major:
					num_time_steps, num_classes = input_shape[0], output_shape[-1]
				else:
					num_time_steps, num_classes = input_shape[1], output_shape[-1]
				if self._is_bidirectional:
					return self._create_static_bidirectional_model(input_tensor, is_training_tensor, num_time_steps, num_classes, self._is_time_major)
				else:
					return self._create_static_model(input_tensor, is_training_tensor, num_time_steps, num_classes, self._is_time_major)

	def _create_dynamic_model(self, input_tensor, is_training_tensor, num_classes, is_time_major):
		"""
		num_enc_hidden_units = 128
		num_dec_hidden_units = 128
		keep_prob = 1.0
		"""
		num_enc_hidden_units = 256
		num_dec_hidden_units = 256
		keep_prob = 0.5

		# Defines cells.
		enc_cell = self._create_unit_cell(num_enc_hidden_units)
		enc_cell = tf.contrib.rnn.DropoutWrapper(enc_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#enc_cell = tf.contrib.rnn.AttentionCellWrapper(enc_cell, attention_window_len, state_is_tuple=True)
		dec_cell = self._create_unit_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#dec_cell = tf.contrib.rnn.AttentionCellWrapper(dec_cell, attention_window_len, state_is_tuple=True)

		# Encoder.
		#enc_cell_outputs, enc_cell_state = tf.nn.dynamic_rnn(enc_cell, input_tensor, time_major=is_time_major, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _ = tf.nn.dynamic_rnn(enc_cell, input_tensor, time_major=is_time_major, dtype=tf.float32, scope='enc')

		input_shape = tf.shape(input_tensor[0])
		batch_size = input_shape[0]
		dec_cell_state = dec_cell.zero_state(batch_size, tf.float32)
		attention = BahdanauAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		#attention = LuongAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		dec_cell_outputs = []
		for _ in range(num_time_steps):
			# Attention.
			context = attention(enc_cell_outputs, dec_cell_state.c)  # dec_cell_state.h or dec_cell_state.c?

			# Decoder.
			# dec_cell_state is an instance of LSTMStateTuple, which stores (c, h), where c is the hidden state and h is the output.
			#dec_cell_output, dec_cell_state = dec_cell(tf.concat([context, cell_output], axis=-1), dec_cell_state, scope='dec')
			#dec_cell_output, dec_cell_state = dec_cell(cell_output, tf.concat([context, dec_cell_state], axis=-1), scope='dec')
			dec_cell_output, dec_cell_state = dec_cell(context, dec_cell_state, scope='dec')
			dec_cell_outputs.append(dec_cell_output)
		cell_outputs = dec_cell_outputs

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

	def _create_dynamic_bidirectional_model(self, input_tensor, is_training_tensor, num_classes, is_time_major):
		"""
		num_enc_hidden_units = 64
		num_dec_hidden_units = 128
		keep_prob = 1.0
		"""
		num_enc_hidden_units = 128
		num_dec_hidden_units = 256
		keep_prob = 0.5

		# Defines cells.
		enc_cell_fw = self._create_unit_cell(num_enc_hidden_units)  # Forward cell.
		enc_cell_fw = tf.contrib.rnn.DropoutWrapper(enc_cell_fw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		enc_cell_bw = self._create_unit_cell(num_enc_hidden_units)  # Backward cell.
		enc_cell_bw = tf.contrib.rnn.DropoutWrapper(enc_cell_bw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		dec_cell = self._create_unit_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)

		# Encoder.
		#enc_cell_outputs, enc_cell_states = tf.nn.bidirectional_dynamic_rnn(enc_cell_fw, enc_cell_bw, input_tensor, time_major=is_time_major, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _ = tf.nn.bidirectional_dynamic_rnn(enc_cell_fw, enc_cell_bw, input_tensor, time_major=is_time_major, dtype=tf.float32, scope='enc')
		enc_cell_outputs = tf.concat(enc_cell_outputs, axis=-1)
		#enc_cell_states = tf.contrib.rnn.LSTMStateTuple(tf.concat((enc_cell_states[0].c, enc_cell_states[1].c), axis=-1), tf.concat((enc_cell_states[0].h, enc_cell_states[1].h), axis=-1))

		input_shape = tf.shape(input_tensor[0])
		batch_size = input_shape[0]
		dec_cell_state = dec_cell.zero_state(batch_size, tf.float32)
		attention = BahdanauAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		#attention = LuongAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		dec_cell_outputs = []
		for _ in range(num_time_steps):
			# Attention.
			context = attention(enc_cell_outputs, dec_cell_state.c)  # dec_cell_state.h or dec_cell_state.c?

			# Decoder.
			# dec_cell_state is an instance of LSTMStateTuple, which stores (c, h), where c is the hidden state and h is the output.
			#dec_cell_output, dec_cell_state = dec_cell(tf.concat([context, cell_output], axis=-1), dec_cell_state, scope='dec')
			#dec_cell_output, dec_cell_state = dec_cell(cell_output, tf.concat([context, dec_cell_state], axis=-1), scope='dec')
			dec_cell_output, dec_cell_state = dec_cell(context, dec_cell_state, scope='dec')
			dec_cell_outputs.append(dec_cell_output)
		cell_outputs = dec_cell_outputs

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

	def _create_static_model(self, input_tensor, is_training_tensor, num_time_steps, num_classes, is_time_major):
		num_enc_hidden_units = 128
		num_dec_hidden_units = 128
		keep_prob = 1.0
		"""
		num_enc_hidden_units = 256
		num_dec_hidden_units = 256
		keep_prob = 0.5
		"""

		# Defines cells.
		enc_cell = self._create_unit_cell(num_enc_hidden_units)
		enc_cell = tf.contrib.rnn.DropoutWrapper(enc_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#enc_cell = tf.contrib.rnn.AttentionCellWrapper(enc_cell, attention_window_len, state_is_tuple=True)
		dec_cell = self._create_unit_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		# REF [paper] >> "Long Short-Term Memory-Networks for Machine Reading", arXiv 2016.
		#dec_cell = tf.contrib.rnn.AttentionCellWrapper(dec_cell, attention_window_len, state_is_tuple=True)

		# Unstack: a tensor of shape (samples, time-steps, features) -> a list of 'time-steps' tensors of shape (samples, features).
		if is_time_major:
			input_tensor = tf.unstack(input_tensor, num_time_steps, axis=0)
		else:
			input_tensor = tf.unstack(input_tensor, num_time_steps, axis=1)

		# Encoder.
		#enc_cell_outputs, enc_cell_state = tf.nn.static_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _ = tf.nn.static_rnn(enc_cell, input_tensor, dtype=tf.float32, scope='enc')

		input_shape = tf.shape(input_tensor[0])
		batch_size = input_shape[0]
		dec_cell_state = dec_cell.zero_state(batch_size, tf.float32)
		attention = BahdanauAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		#attention = LuongAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		dec_cell_outputs = []
		for _ in range(num_time_steps):
			# Attention.
			context = attention(enc_cell_outputs, dec_cell_state.c)  # dec_cell_state.h or dec_cell_state.c?
			#context = enc_cell_outputs[-1]  # For testing.

			# Decoder.
			# dec_cell_state is an instance of LSTMStateTuple, which stores (c, h), where c is the hidden state and h is the output.
			#dec_cell_output, dec_cell_state = dec_cell(tf.concat([context, dec_cell_output], axis=-1), dec_cell_state, scope='dec')
			#dec_cell_output, dec_cell_state = dec_cell(dec_cell_output, tf.concat([context, dec_cell_state], axis=-1), scope='dec')
			dec_cell_output, dec_cell_state = dec_cell(context, dec_cell_state, scope='dec')
			dec_cell_outputs.append(dec_cell_output)

		# Stack: a list of 'time-steps' tensors of shape (samples, features) -> a tensor of shape (samples, time-steps, features).
		if is_time_major:
			cell_outputs = tf.stack(dec_cell_outputs, axis=0)
		else:
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

	def _create_static_bidirectional_model(self, input_tensor, is_training_tensor, num_time_steps, num_classes, is_time_major):
		num_enc_hidden_units = 64
		num_dec_hidden_units = 128
		keep_prob = 1.0
		"""
		num_enc_hidden_units = 128
		num_dec_hidden_units = 256
		keep_prob = 0.5
		"""

		# Defines cells.
		enc_cell_fw = self._create_unit_cell(num_enc_hidden_units)  # Forward cell.
		enc_cell_fw = tf.contrib.rnn.DropoutWrapper(enc_cell_fw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		enc_cell_bw = self._create_unit_cell(num_enc_hidden_units)  # Backward cell.
		enc_cell_bw = tf.contrib.rnn.DropoutWrapper(enc_cell_bw, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)
		dec_cell = self._create_unit_cell(num_dec_hidden_units)
		dec_cell = tf.contrib.rnn.DropoutWrapper(dec_cell, input_keep_prob=keep_prob, output_keep_prob=1.0, state_keep_prob=keep_prob)

		# Unstack: a tensor of shape (samples, time-steps, features) -> a list of 'time-steps' tensors of shape (samples, features).
		if is_time_major:
			input_tensor = tf.unstack(input_tensor, num_time_steps, axis=0)
		else:
			input_tensor = tf.unstack(input_tensor, num_time_steps, axis=1)

		# Encoder.
		#enc_cell_outputs, enc_cell_state_fw, enc_cell_state_bw = tf.nn.static_bidirectional_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32, scope='enc')
		enc_cell_outputs, _, _ = tf.nn.static_bidirectional_rnn(enc_cell_fw, enc_cell_bw, input_tensor, dtype=tf.float32, scope='enc')
		#enc_cell_outputs = tf.concat(enc_cell_outputs, axis=-1)  # Don't need.
		#enc_cell_states = tf.contrib.rnn.LSTMStateTuple(tf.concat((enc_cell_state_fw.c, enc_cell_state_bw.c), axis=-1), tf.concat((enc_cell_state_fw.h, enc_cell_state_bw.h), axis=-1))

		input_shape = tf.shape(input_tensor[0])
		batch_size = input_shape[0]
		dec_cell_state = dec_cell.zero_state(batch_size, tf.float32)
		attention = BahdanauAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		#attention = LuongAttentionMechanism(enc_cell_outputs[0].shape[-1], dec_cell_state.c.shape[-1])
		dec_cell_outputs = []
		for _ in range(num_time_steps):
			# Attention.
			context = attention(enc_cell_outputs, dec_cell_state.c)  # dec_cell_state.h or dec_cell_state.c?

			# Decoder.
			# dec_cell_state is an instance of LSTMStateTuple, which stores (c, h), where c is the hidden state and h is the output.
			#dec_cell_output, dec_cell_state = dec_cell(tf.concat([context, dec_cell_output], axis=-1), dec_cell_state, scope='dec')
			#dec_cell_output, dec_cell_state = dec_cell(dec_cell_output, tf.concat([context, dec_cell_state], axis=-1), scope='dec')
			dec_cell_output, dec_cell_state = dec_cell(context, dec_cell_state, scope='dec')
			dec_cell_outputs.append(dec_cell_output)

		# Stack: a list of 'time-steps' tensors of shape (samples, features) -> a tensor of shape (samples, time-steps, features).
		if is_time_major:
			cell_outputs = tf.stack(dec_cell_outputs, axis=0)
		else:
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

	def _create_unit_cell(self, num_units):
		#return tf.contrib.rnn.BasicRNNCell(num_units)
		#return tf.contrib.rnn.RNNCell(num_units)

		return tf.contrib.rnn.BasicLSTMCell(num_units, forget_bias=1.0)
		#return tf.contrib.rnn.LSTMCell(num_units, forget_bias=1.0)

		#return tf.contrib.rnn.GRUCell(num_units)