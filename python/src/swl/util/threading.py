import threading

# REF [site] >> http://anandology.com/blog/using-iterators-and-generators/
class ThreadSafeIterator:
	"""
	Takes an iterator/generator and makes it thread-safe by serializing call to the `next` method of given iterator/generator.
	"""
	def __init__(self, it):
		self.it = it
		self.lock = threading.Lock()

	def __iter__(self):
		return self

	def __next__(self):
		with self.lock:
			return self.it.next()

class ThreadSafeGenerator:
	"""
	Takes a generator and makes it thread-safe by serializing call to the `next` method of given iterator/generator.
	"""
	def __init__(self, gen):
		self.gen = gen
		self.lock = threading.Lock()

	def __iter__(self):
		return self

	def __next__(self):
		with self.lock:
			return next(self.gen)