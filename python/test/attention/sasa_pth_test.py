#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
sys.path.append('../../../src')

import os, shutil, collections, pickle, argparse, logging, logging.handlers, time, datetime
import numpy as np
import torch
import torchvision
#import swl.machine_learning.util as swl_ml_util
import utils
import sasa.model

#--------------------------------------------------------------------

class MyModel(torch.nn.Module):
	@staticmethod
	def create_model(model_name, num_classes, stem):
		if model_name == 'ResNet26':
			return sasa.model.ResNet26(num_classes=num_classes, stem=stem)
		elif model_name == 'ResNet38':
			return sasa.model.ResNet38(num_classes=num_classes, stem=stem)
		elif model_name == 'ResNet50':
			return sasa.model.ResNet50(num_classes=num_classes, stem=stem)

#--------------------------------------------------------------------

class MyRunner(object):
	def __init__(self, logger):
		self._logger = logger

	def train(self, model, criterion, optimizer, scheduler, train_dataloader, test_dataloader, model_checkpoint_filepath, output_dir_path, initial_epoch=0, final_epoch=10, recorder=None, device='cpu'):
		self._logger.info('Output path: {}.'.format(output_dir_path))
		self._logger.info('Model:\n{}.'.format(model))

		history = {
			'acc': list(),
			'loss': list(),
			'val_acc': list(),
			'val_loss': list()
		}

		if recorder:
			history['acc'] = recorder.epoch_accuracy[:,0].tolist()
			history['loss'] = recorder.epoch_losses[:,0].tolist()
			history['val_acc'] = recorder.epoch_accuracy[:,1].tolist()
			history['val_loss'] = recorder.epoch_losses[:,1].tolist()
			recorder.resize(final_epoch)
		else:
			recorder = utils.RecorderMeter(final_epoch)

		train_history_filepath = os.path.join(output_dir_path, 'train_history.pkl')
		train_result_image_filepath = os.path.join(output_dir_path, 'results.png')
		log_print_freq = 500

		#if torch.cuda.device_count() > 1:
		#	device_ids = [0, 1]
		#	model = torch.nn.DataParallel(model, device_ids=device_ids)
		model = model.to(device)

		#--------------------
		self._logger.info('Start training...')
		epoch_time = utils.AverageMeter()
		best_performance_measure = 0
		best_model_filepath = None
		start_total_time = start_epoch_time = time.time()
		for epoch in range(initial_epoch, final_epoch):
			self._logger.info('Epoch {}/{}'.format(epoch, final_epoch - 1))

			current_learning_rate = scheduler.get_lr() if scheduler else 0.0
			need_hour, need_mins, need_secs = utils.convert_secs2time(epoch_time.avg * (final_epoch - epoch))
			need_time = '[Need: {:02d}:{:02d}:{:02d}]'.format(need_hour, need_mins, need_secs)
			self._logger.info('==>>{:s} [Epoch={:03d}/{:03d}] {:s} [learning_rate={}]'.format(utils.time_string(), epoch, final_epoch, need_time, current_learning_rate) \
				+ ' [Best : Accuracy={:.2f}, Error={:.2f}].'.format(recorder.max_accuracy(False), 100 - recorder.max_accuracy(False)))

			#--------------------
			#start_time = time.time()
			losses, top1, top5 = self._train(model, criterion, optimizer, train_dataloader, epoch, log_print_freq, device)
			train_loss, train_acc = losses.avg, top1.avg
			self._logger.info('  **Train** Prec@1 {top1.avg:.3f} Prec@5 {top5.avg:.3f} Error@1 {error1:.3f}.'.format(top1=top1, top5=top5, error1=100 - top1.avg))
			#self._logger.info('\tTrain:      loss = {:.6f}, accuracy = {:.6f}: {} secs.'.format(train_loss, train_acc, time.time() - start_time))

			history['loss'].append(train_loss)
			history['acc'].append(train_acc)

			#--------------------
			#start_time = time.time()
			losses, top1, top5 = self._evaluate(model, criterion, test_dataloader, device)
			val_loss, val_acc = losses.avg, top1.avg
			self._logger.info('  **Validation** Prec@1 {top1.avg:.3f} Prec@5 {top5.avg:.3f} Error@1 {error1:.3f} Loss: {losses.avg:.3f}.'.format(top1=top1, top5=top5, error1=100 - top1.avg, losses=losses))
			#self._logger.info('\tValidation: loss = {:.6f}, accuracy = {:.6f}: {} secs.'.format(val_loss, val_acc, time.time() - start_time))

			history['val_loss'].append(val_loss)
			history['val_acc'].append(val_acc)

			if scheduler: scheduler.step()

			#--------------------
			dummy = recorder.update(epoch, train_loss, train_acc, val_loss, val_acc)

			if val_acc > best_performance_measure:
				best_model_filepath = model_checkpoint_filepath.format(epoch=epoch, val_acc=val_acc)
				self.save_model(best_model_filepath, model, optimizer, recorder, epoch)
				best_performance_measure = val_acc

			# Measure elapsed time.
			epoch_time.update(time.time() - start_epoch_time)
			start_epoch_time = time.time()
			recorder.plot_curve(train_result_image_filepath)
		
			#import pdb; pdb.set_trace()
			train_log = collections.OrderedDict()
			train_log['train_loss'] = history['loss']
			train_log['train_acc'] = history['acc']
			train_log['val_loss'] = history['val_loss']
			train_log['val_acc'] = history['val_acc']

			pickle.dump(train_log, open(train_history_filepath, 'wb'))
			utils.plotting(output_dir_path, train_history_filepath)

			sys.stdout.flush()
			time.sleep(0)
		self._logger.info('End training: {} secs.'.format(time.time() - start_total_time))

		return best_model_filepath, history

	def test(self, model, dataloader, device='cpu'):
		#if torch.cuda.device_count() > 1:
		#	device_ids = [0, 1]
		#	model = torch.nn.DataParallel(model, device_ids=device_ids)
		model = model.to(device)

		# Switch to evaluation mode.
		model.eval()

		self._logger.info('Start testing a model...')
		inferences, ground_truths = list(), list()
		start_time = time.time()
		with torch.no_grad():
			for batch_inputs, batch_outputs in dataloader:
				#batch_inputs, batch_outputs = batch_inputs.to(device), batch_outputs.to(device)
				batch_inputs = batch_inputs.to(device)

				model_outputs = model(batch_inputs)

				model_outputs = torch.argmax(model_outputs, -1)
				inferences.extend(model_outputs.cpu().numpy())
				ground_truths.extend(batch_outputs.numpy())
		self._logger.info('End testing a model: {} secs.'.format(time.time() - start_time))

		inferences, ground_truths = np.array(inferences), np.array(ground_truths)
		if inferences is not None and ground_truths is not None:
			self._logger.info('Test: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(inferences.shape, inferences.dtype, np.min(inferences), np.max(inferences)))

			correct_estimation_count = np.count_nonzero(np.equal(inferences, ground_truths))
			self._logger.info('Test: accuracy = {} / {} = {}.'.format(correct_estimation_count, ground_truths.size, correct_estimation_count / ground_truths.size))
		else:
			self._logger.warning('Invalid test results.')

	def infer(self, model, inputs, device='cpu'):
		#if torch.cuda.device_count() > 1:
		#	device_ids = [0, 1]
		#	model = torch.nn.DataParallel(model, device_ids=device_ids)
		model = model.to(device)

		# Switch to evaluation mode.
		model.eval()

		self._logger.info('Start inferring...')
		start_time = time.time()
		with torch.no_grad():
			inputs = inputs.to(device)
			model_outputs = model(inputs)
		self._logger.info('End inferring: {} secs.'.format(time.time() - start_time))
		return torch.argmax(model_outputs, -1)

	def load_model(self, model_filepath, model, optimizer=None, device='cpu'):
		try:
			self._logger.info('Start loading a model from {}...'.format(model_filepath))
			start_time = time.time()
			loaded_data = torch.load(model_filepath, map_location=device)
			epoch = loaded_data['epoch']
			#architecture = loaded_data['arch']
			model.load_state_dict(loaded_data['state_dict'])
			if optimizer: optimizer.load_state_dict(loaded_data['optimizer'])
			recorder = loaded_data['recorder']
			best_acc = recorder.max_accuracy(False)
			self._logger.info('End loading a model, accuracy={} (epoch {}): {} secs.'.format(best_acc, epoch, time.time() - start_time))
			return model, optimizer, recorder, epoch
		except Exception as ex:
			self._logger.error('Failed to load a model from {}: {}.'.format(model_filepath, ex))
			#return None, None, None, None
			return model, None, None, None

	def save_model(self, model_filepath, model, optimizer, recorder, epoch):
		try:
			self._logger.info('Start saving a model from {}...'.format(model_filepath))
			start_time = time.time()
			# Saves a model using either a .pt or .pth file extension.
			torch.save(
				{
					'epoch': epoch + 1,
					#'arch': architecture,
					'state_dict': model.state_dict(),
					'optimizer': optimizer.state_dict(),
					'recorder': recorder,
				},
				model_filepath
			)
			self._logger.info('End saving a model: {} secs.'.format(time.time() - start_time))
		except Exception as ex:
			self._logger.error('Failed to save a model from {}: {}.'.format(model_filepath, ex))

	# REF [function] >> load_data() in https://github.com/leaderj1001/Stand-Alone-Self-Attention/blob/master/preprocess.py
	def load_data(self, dataset_name, batch_size, num_workers=1):
		print('Load Dataset :: {}'.format(dataset_name))
		if dataset_name == 'CIFAR10':
			transform_train = torchvision.transforms.Compose([
				torchvision.transforms.RandomCrop(32, padding=4),
				torchvision.transforms.RandomHorizontalFlip(),
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.4914, 0.4822, 0.4465),
					std=(0.2470, 0.2435, 0.2616)
				)
			])

			transform_test = torchvision.transforms.Compose([
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.4914, 0.4822, 0.4465),
					std=(0.2470, 0.2435, 0.2616)
				)
			])

			train_loader = torch.utils.data.DataLoader(
				torchvision.datasets.CIFAR10('data', train=True, download=True, transform=transform_train),
				batch_size=batch_size,
				shuffle=True,
				num_workers=num_workers
			)

			test_loader = torch.utils.data.DataLoader(
				torchvision.datasets.CIFAR10('data', train=False, transform=transform_test),
				batch_size=batch_size,
				shuffle=False,
				num_workers=num_workers
			)

			num_classes = 10

		elif dataset_name == 'CIFAR100':
			transform_train = torchvision.transforms.Compose([
				torchvision.transforms.RandomCrop(32, padding=4),
				torchvision.transforms.RandomHorizontalFlip(),
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.5071, 0.4865, 0.4409),
					std=(0.2673, 0.2564, 0.2762)
				),
			])
			transform_test = torchvision.transforms.Compose([
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.5071, 0.4865, 0.4409),
					std=(0.2673, 0.2564, 0.2762)
				),
			])

			train_loader = torch.utils.data.DataLoader(
				torchvision.datasets.CIFAR100('data', train=True, download=True, transform=transform_train),
				batch_size=batch_size,
				shuffle=True,
				num_workers=num_workers
			)

			test_loader = torch.utils.data.DataLoader(
				torchvision.datasets.CIFAR100('data', train=False, transform=transform_test),
				batch_size=batch_size,
				shuffle=False,
				num_workers=num_workers
			)

			num_classes = 100

		elif dataset_name == 'MNIST':
			"""
			transform = torchvision.transforms.Compose([
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.1307,),
					std=(0.3081,)
				)
			])
			"""
			class ConvertChannel(object):
				def __call__(self, x):
					return x.convert('RGB')
					#return np.repeat(np.expand_dims(x, axis=0), 3, axis=0)
					#return torch.repeat_interleave(x, 3, dim=0)
					#return torch.repeat_interleave(torch.unsqueeze(x, dim=3), 3, dim=0)

			image_height, image_width = 32, 32
			transform = torchvision.transforms.Compose([
				ConvertChannel(),
				torchvision.transforms.Resize((image_height, image_width)),
				torchvision.transforms.ToTensor(),
				torchvision.transforms.Normalize(
					mean=(0.1307, 0.1307, 0.1307),
					std=(0.3081, 0.3081, 0.3081)
				)
			])
			train_loader = torch.utils.data.DataLoader(
				torchvision.datasets.MNIST('data', train=True, download=True, transform=transform),
				batch_size=batch_size,
				shuffle=True,
				num_workers=num_workers
			)

			test_loader = torch.utils.data.DataLoader(
				torchvision.datasets.MNIST('data', train=False, transform=transform),
				batch_size=batch_size,
				shuffle=False,
				num_workers=num_workers
			)

			num_classes = 10

		elif dataset_name == 'IMAGENET':
			num_classes = 1000

		return train_loader, test_loader, num_classes

	def show_data_info(self, train_dataloader, test_dataloader):
		data_iter = iter(train_dataloader)
		images, labels = data_iter.next()
		images, labels = images.numpy(), labels.numpy()
		self._logger.info('Train image: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(images.shape, images.dtype, np.min(images), np.max(images)))
		self._logger.info('Train label: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(labels.shape, labels.dtype, np.min(labels), np.max(labels)))

		data_iter = iter(test_dataloader)
		images, labels = data_iter.next()
		images, labels = images.numpy(), labels.numpy()
		self._logger.info('Test image: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(images.shape, images.dtype, np.min(images), np.max(images)))
		self._logger.info('Test label: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(labels.shape, labels.dtype, np.min(labels), np.max(labels)))

	def _train(self, model, criterion, optimizer, dataloader, epoch, log_print_freq, device):
		# Switch to train mode.
		model.train()

		batch_time, data_time = utils.AverageMeter(), utils.AverageMeter()
		losses, top1, top5 = utils.AverageMeter(), utils.AverageMeter(), utils.AverageMeter()
		#running_loss = 0.0
		#start_time = start_batch_time = time.time()
		start_batch_time = time.time()
		for batch_step, (batch_inputs, batch_outputs) in enumerate(dataloader):
			"""
			# One-hot encoding.
			batch_outputs_onehot = torch.LongTensor(batch_outputs.shape[0], self._dataset.num_classes)
			batch_outputs_onehot.zero_()
			batch_outputs_onehot.scatter_(1, batch_outputs.view(batch_outputs.shape[0], -1), 1)
			"""

			batch_inputs, batch_outputs = batch_inputs.to(device), batch_outputs.to(device)
			#batch_inputs, batch_outputs, batch_outputs_onehot = batch_inputs.to(device), batch_outputs.to(device), batch_outputs_onehot.to(device)

			data_time.update(time.time() - start_batch_time)

			# Zero the parameter gradients.
			optimizer.zero_grad()

			# Forward + backward + optimize.
			model_outputs = model(batch_inputs)
			loss = criterion(model_outputs, batch_outputs)
			loss.backward()
			"""
			# Gradient clipping.
			max_gradient_norm = 5
			torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=max_gradient_norm, norm_type=2)
			#for p in model.parameters():
			#	if p.grad is not None:
			#		p.grad.data.clamp_(min=-max_gradient_norm, max=max_gradient_norm)
			"""
			# Update weights.
			optimizer.step()
			#for p in model.parameters():
			#	p.data.add_(-lr, p.grad.data)  # p.data = p.data + (-lr * p.grad.data).

			# Measure accuracy and record loss.
			#model_outputs = torch.argmax(model_outputs, -1)
			prec1, prec5 = utils.accuracy(model_outputs, batch_outputs, topk=(1, 5))
			losses.update(loss.item(), batch_inputs.size(0))
			top1.update(prec1.item(), batch_inputs.size(0))
			top5.update(prec5.item(), batch_inputs.size(0))

			"""
			# Print statistics.
			running_loss += loss.item()
			if (batch_step + 1) % 100 == 0:
				self._logger.info('\tStep {}: loss = {:.6f}: {} secs.'.format(batch_step + 1, running_loss / 100, time.time() - start_time))
				running_loss = 0.0
			"""

			# Measure elapsed time.
			batch_time.update(time.time() - start_batch_time)
			start_batch_time = time.time()

			if (batch_step + 1) % log_print_freq == 0:
				self._logger.info('  Epoch: [{:03d}][{:03d}/{:03d}]   '
					'Time {batch_time.val:.3f} ({batch_time.avg:.3f})   '
					'Data {data_time.val:.3f} ({data_time.avg:.3f})   '
					'Loss {loss.val:.4f} ({loss.avg:.4f})   '
					'Prec@1 {top1.val:.3f} ({top1.avg:.3f})   '
					'Prec@5 {top5.val:.3f} ({top5.avg:.3f})   '.format(
					epoch, batch_step + 1, len(dataloader), batch_time=batch_time,
					data_time=data_time, loss=losses, top1=top1, top5=top5) + utils.time_string())
		return losses, top1, top5

	def _evaluate(self, model, criterion, dataloader, device):
		# Switch to evaluation mode.
		model.eval()

		losses, top1, top5 = utils.AverageMeter(), utils.AverageMeter(), utils.AverageMeter()
		with torch.no_grad():
			for batch_step, (batch_inputs, batch_outputs) in enumerate(dataloader):
				"""
				# One-hot encoding.
				batch_outputs_onehot = torch.LongTensor(batch_outputs.shape[0], self._dataset.num_classes)
				batch_outputs_onehot.zero_()
				batch_outputs_onehot.scatter_(1, batch_outputs.view(batch_outputs.shape[0], -1), 1)
				"""

				batch_inputs, batch_outputs = batch_inputs.to(device), batch_outputs.to(device)
				#batch_inputs, batch_outputs, batch_outputs_onehot = batch_inputs.to(device), batch_outputs.to(device), batch_outputs_onehot.to(device)

				model_outputs = model(batch_inputs)
				loss = criterion(model_outputs, batch_outputs)

				# Measure accuracy and record loss.
				#model_outputs = torch.argmax(model_outputs, -1)
				prec1, prec5 = utils.accuracy(model_outputs.data, batch_outputs, topk=(1, 5))
				losses.update(loss.item(), batch_inputs.size(0))
				top1.update(prec1.item(), batch_inputs.size(0))
				top5.update(prec5.item(), batch_inputs.size(0))
		return losses, top1, top5

#--------------------------------------------------------------------

# REF [site] >> https://github.com/pytorch/pytorch/blob/master/torch/optim/lr_scheduler.py
class MyLRScheduler(object):
	def __init__(self, optimizer, initial_learning_rate, last_epoch=-1):
		self.optimizer = optimizer
		self.initial_learning_rate = initial_learning_rate

		"""
		# Initialize epoch and base learning rates.
		if last_epoch == -1:
			for group in optimizer.param_groups:
				group.setdefault('initial_lr', group['lr'])
		else:
			for i, group in enumerate(optimizer.param_groups):
				if 'initial_lr' not in group:
					raise KeyError("param 'initial_lr' is not specified in param_groups[{}] when resuming an optimizer".format(i))
		self.base_lrs = list(map(lambda group: group['initial_lr'], optimizer.param_groups))
		"""
		self.last_epoch = last_epoch

		self.learning_rate = self.initial_learning_rate

	def get_lr(self):
		return self.learning_rate

	def step(self, epoch=None):
		if epoch is None:
			self.last_epoch += 1
		else:
			self.last_epoch = epoch
		# Sets the learning rate to the initial LR decayed by 10 every 30 epochs.
		self.learning_rate = self.initial_learning_rate * (0.1 ** (self.last_epoch // 30))
		for param_group in self.optimizer.param_groups:
			param_group['lr'] = self.learning_rate

#--------------------------------------------------------------------

def parse_command_line_options():
	parser = argparse.ArgumentParser(description='Train, test, or infer a CNN model for MNIST dataset.')

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
	parser.add_argument(
		'-e',
		'--epoch',
		type=int,
		help='Number of epochs to train',
		default=100
	)
	parser.add_argument(
		'-b',
		'--batch_size',
		type=int,
		help='Batch size',
		default=24
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
		'--log_level',
		type=int,
		help='Log level, [0, 50]',  # {NOTSET=0, DEBUG=10, INFO=20, WARNING=WARN=30, ERROR=40, CRITICAL=FATAL=50}.
		default=None
	)

	return parser.parse_args()

def get_logger(name, log_level=None, log_dir_path=None, is_rotating=True):
	if not log_level: log_level = logging.INFO
	if not log_dir_path: log_dir_path = './log'
	if not os.path.isdir(log_dir_path):
		os.mkdir(log_dir_path)

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

# REF [function] >> main() in ${SWL_PYTHON_HOME}/test/machine_learning/pytorch/run_simple_training3.py
def main():
	args = parse_command_line_options()

	logger = get_logger(os.path.basename(os.path.normpath(__file__)), args.log_level if args.log_level else logging.INFO, './log', is_rotating=True)
	logger.info('----------------------------------------------------------------------')
	logger.info('Logger: name = {}, level = {}.'.format(logger.name, logger.level))
	logger.info('Command-line arguments: {}.'.format(sys.argv))
	logger.info('Command-line options: {}.'.format(vars(args)))
	logger.info('Python version: {}.'.format(sys.version.replace('\n', ' ')))
	logger.info('Torch version: {}.'.format(torch.__version__))
	logger.info('cuDNN version: {}.'.format(torch.backends.cudnn.version()))

	if not args.train and not args.test and not args.infer:
		logger.error('At least one of command line options "--train", "--test", and "--infer" has to be specified.')
		return

	#if args.gpu:
	#	os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
	device = torch.device('cuda:{}'.format(args.gpu) if torch.cuda.is_available() and args.gpu else 'cpu')
	logger.info('Device: {}.'.format(device))

	#--------------------
	initial_epoch, final_epoch, batch_size = 0, args.epoch, args.batch_size
	is_resumed = args.model_file is not None
	num_workers = 4

	dataset_name = 'MNIST'  # {'CIFAR10', 'CIFAR100', 'IMAGENET', 'MNIST'}.
	model_name = 'ResNet26'  # {'ResNet26', 'ResNet38', 'ResNet50'}.
	stem = False

	model_filepath, output_dir_path = os.path.normpath(args.model_file) if args.model_file else None, os.path.normpath(args.out_dir) if args.out_dir else None
	if model_filepath:
		if not output_dir_path:
			output_dir_path = os.path.dirname(model_filepath)
	else:
		if not output_dir_path:
			output_dir_prefix = 'sasa_pth'
			output_dir_suffix = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
			output_dir_path = os.path.join('.', '{}_{}'.format(output_dir_prefix, output_dir_suffix))
		model_filepath = os.path.join(output_dir_path, 'model.pth')

	#--------------------
	runner = MyRunner(logger)

	# Load datasets.
	train_dataloader, test_dataloader, num_classes = runner.load_data(dataset_name, batch_size, num_workers=num_workers)
	runner.show_data_info(train_dataloader, test_dataloader)

	logger.info('Dataset name = {}, model name = {}, #classes = {}, stem = {}.'.format(dataset_name, model_name, num_classes, stem))

	if args.train:
		model_checkpoint_filepath = os.path.join(output_dir_path, 'model_ckpt.{epoch:04d}-{val_acc:.5f}.pth')
		if output_dir_path and output_dir_path.strip() and not os.path.exists(output_dir_path):
			os.makedirs(output_dir_path, exist_ok=True)

		# Create a model.
		model = MyModel.create_model(model_name, num_classes, stem)

		# Create a trainer.
		criterion = torch.nn.CrossEntropyLoss().to(device)
		initial_learning_rate, momentum, weight_decay = 0.1, 0.9, 0.0001
		optimizer = torch.optim.SGD(model.parameters(), lr=initial_learning_rate, momentum=momentum, weight_decay=weight_decay, nesterov=True)
		#scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
		scheduler = MyLRScheduler(optimizer, initial_learning_rate)

		# Load a model.
		if is_resumed:
			model, optimizer, recorder, loaded_initial_epoch = runner.load_model(model_filepath, model, optimizer, device=device)
			if loaded_initial_epoch:
				initial_epoch += loaded_initial_epoch
				final_epoch += loaded_initial_epoch
		else:
			recorder = None

		if model:
			# Train a model.
			best_model_filepath, history = runner.train(model, criterion, optimizer, scheduler, train_dataloader, test_dataloader, model_checkpoint_filepath, output_dir_path, initial_epoch, final_epoch, recorder, device=device)

			# Save a model.
			model_filepath = os.path.join(output_dir_path, 'best_model.pth')
			if best_model_filepath:
				try:
					shutil.copyfile(best_model_filepath, model_filepath)
					logger.info('Copied the best trained model to {}.'.format(model_filepath))
				except (FileNotFoundError, PermissionError) as ex:
					logger.error('Failed to copy the best trained model to {}: {}.'.format(model_filepath, ex))
					model_filepath = None
			else:
				runner.save_model(model_filepath, model, optimizer, recorder, final_epoch)

			#logger.info('Train history = {}.'.format(history))
			#swl_ml_util.display_train_history(history)
			#if os.path.exists(output_dir_path):
			#	swl_ml_util.save_train_history(history, output_dir_path)

	if args.test or args.infer:
		if model_filepath and os.path.exists(model_filepath):
			# Create a model.
			model = MyModel()
			# Load a model.
			model, _, _, _ = runner.load_model(model_filepath, model, None, device=device)

			if args.test and model:
				runner.test(model, test_dataloader, device=device)

			if args.infer and model:
				#inputs = torch.cat([batch_data[0] for batch_data in test_dataloader], dim=0)
				data_iter = iter(test_dataloader)
				inputs, _ = data_iter.next()

				inferences = runner.infer(model, inputs, device=device)

				inferences = inferences.cpu().numpy()
				if inferences is not None:
					logger.info('Inference: shape = {}, dtype = {}, (min, max) = ({}, {}).'.format(inferences.shape, inferences.dtype, np.min(inferences), np.max(inferences)))

					results = {idx: inf for idx, inf in enumerate(inferences) if idx < 100}
					logger.info('Inference results (index: inference): {}.'.format(results))
				else:
					logger.warning('Invalid inference results.')
		else:
			logger.error('Model file, {} does not exist.'.format(model_filepath))

#--------------------------------------------------------------------

# Usage:
#	python sasa_pth_test.py --train --test --infer --epoch 20 --gpu 0

if '__main__' == __name__:
	main()
