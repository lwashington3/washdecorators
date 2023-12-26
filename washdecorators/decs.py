import logging
from functools import wraps


__ALL__ = ["retry", "time_function", "memorize", "log_execution", "discord_on_completion", "ntfy", "ntfy_time"]


def _get_signature(*args, **kwargs) -> str:
	arg_repr = [repr(a) for a in args]
	kwarg_repr = [f"{key}={value!r}" for key, value in kwargs.items()]
	return ','.join(arg_repr + kwarg_repr)


def retry(max_tries=3, delay_seconds=1):
	"""
	Retries a function if a failure occurs.
	:param int max_tries: The maximum number of tries the system should attempt before throwing an error.
	:param float delay_seconds: The number of seconds between tries.
	:return: The returned value from the function.
	"""
	from time import sleep

	def retry_decorator(func):

		@wraps(func)
		def retry_wrapper(*args, **kwargs):
			tries = 0
			while tries < max_tries:
				try:
					return func(*args, **kwargs)
				except Exception as e:
					tries += 1
					if tries == max_tries:
						raise e
					sleep(delay_seconds)

		return retry_wrapper

	return retry_decorator


def time_function(log=True, nano_seconds=False):
	"""
	Times the execution of a function.
	:param bool log: If the execution time should be written using the logging.info function (True) or the print method (False).
	:param bool nano_seconds: If the timer should be in nano_seconds (True) or seconds (False).
	:returns: The return value from the given function.
	"""
	def time_decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			from time import perf_counter, perf_counter_ns
			timer = perf_counter_ns if nano_seconds else perf_counter

			start = timer()
			result = func(*args, **kwargs)
			end = timer()

			message = f"Execution time for: {func.__name__}: {end - start}{'ns' if nano_seconds else 's'}."
			if log:
				logging.info(message)
			else:
				print(message)

			return result
		return wrapper
	return time_decorator


def memorize(func):
	"""
	Memorizes the output of a function given its arguments. Works well with recursive functions.
	:param func: The function whose output should be memorized.
	:return: The output of the function.
	"""
	cache = {}

	def wrapper(*args, **kwargs):
		key = args
		if key in cache:
			return cache[key]
		result = func(*args, **kwargs)
		cache[key] = result
		return result

	return wrapper


def log_execution(func):
	"""
	Logs the execution of functions using the logging.info function.
	:param func:
	:returns:
	"""
	@wraps(func)
	def wrapper(*args, **kwargs):
		logging.info(f"Executing {func.__name__}")
		result = func(*args, **kwargs)
		logging.info(f"Finished executing {func.__name__}")
		return result
	return wrapper


def discord_on_completion(webhook_url):
	"""
	Sends a message to a Discord channel when a function fails via webhooks
	:param str webhook_url: The webhook url from Discord
	:returns: None
	"""
	def decorator(func):
		try:
			from requests import post
		except ModuleNotFoundError:
			raise ModuleNotFoundError("The 'requests' library could not be found. Please use `pip install requests in the command line and try again.`")

		def wrapper(*args, **kwargs):
			try:
				value = func(*args, **kwargs)
				plural = False
				if value is None:
					results = "None"
				elif isinstance(value, tuple):
					results = ','.join([f"{i!r}" for i in value])
					plural = True
				else:
					results = f"{value!r}"
				data = {
					"content": None,
					"embeds": [{
						"author": {"author": "Python Completion Notification"},
						"title": f"`{func.__name__}` Successfully Executed:",
						"description": f"Python function `{func.__name__}` has completed running and the following value{'s' if plural else ''} {'were' if plural else 'was'} returned: `{'(' if plural else ''}{results}{')' if plural else ''}`.",
						"color": 5814783
					}],
					"username": "Python Completion Notification",
					"attachments": []
				}
				post(webhook_url, json=data)
				return value
			except Exception as e:
				from traceback import format_exception
				data = {
					"content": None,
					"embeds": [{
						"author": {"name": "Python Traceback Error"},
						"title": f"{type(e).__name__}: {e.__cause__}",
						"description": f"```{' '.join(format_exception(e))}```",
						"color": 5814783
						}],
					"username": "Python Traceback Error",
					"attachments": []
				}
				post(webhook_url, json=data)
				raise e
		return wrapper
	return decorator


def log_signature(func):
	"""
	Logs the signature of a function using Python's logging.debug.
	:returns: The value from the given function.
	"""
	def wrapper(*args, **kwargs):
		signature = _get_signature(*args, **kwargs)
		logging.debug(f"Entering {func.__name__}({signature})")
		value = func(*args, **kwargs)
		logging.debug(f"Leaving {func.__name__}({signature}) with return value `{value!r}`.")
		return value
	return wrapper


def ntfy(ntfy_link:str, topic:str, on_completion="results", on_error="error"):
	"""
	Notify a user about the running of a function.
	:param str ntfy_link: The link to the NTFY server.
	:param str topic: The topic to notify.
	:param str | None on_completion: The message that should be sent when the function has successfully completed.
	Put "results" to send the exact results to the NTFY server.
	:param str | None on_error: The message that should be sent when the function has hit an error and did not finish.
	Put "error" to send the exact error to the NTFY server.
	:return:
	"""
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			data = None
			try:
				result = func(*args, **kwargs)
				if on_completion is None:
					return result
				elif on_completion == "results":
					data = str(result)
				else:
					data = on_completion
				return result
			except Exception as e:
				if on_error is None:
					raise e
				elif on_error == "error":
					from traceback import format_exception
					data = ' '.join(format_exception(e))
				else:
					data = on_error
				raise e
			finally:
				if data is None:
					return

				from requests import post
				post(f"{ntfy_link}/{topic}", data=data)
		return wrapper
	return decorator


def ntfy_time(ntfy_link:str, topic:str):
	"""
	Notify a user about the running of a function.
	:param str ntfy_link: The link to the NTFY server.
	:param str topic: The topic to notify.
	:return:
	"""
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			from time import perf_counter_ns as timer
			from datetime import timedelta
			from requests import post

			start = timer()

			def end_timer() -> timedelta:
				time_diff = timer() - start
				time = timedelta(microseconds=time_diff / 1_000)
				return time

			try:
				result = func(*args, **kwargs)
				time = end_timer()

				data = f"Function: {func.__name__} successfully run in: {str(time)} seconds."
				return result
			except Exception as e:
				time = end_timer()

				data = f"Function: {func.__name__} had an error thrown after: {str(time)} seconds."
				raise e
			finally:
				post(f"{ntfy_link}/{topic}", data=data)
		return wrapper
	return decorator
