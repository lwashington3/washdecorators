import logging
from functools import wraps


__ALL__ = ["retry", "time_function", "memorize", "log_execution", "discord_on_failure"]


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
	:param bool log: If the execution time should be written using the logging module (True) or the print method (False).
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
	Logs the execution of functions using the logging module.
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


def discord_on_failure(webhook_url):
	"""
	Sends a message to a Discord channel when a function fails via webhooks
	:param str webhook_url: The webhook url from Discord
	:returns: None
	"""
	def decorator(func):
		def wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				from requests import post
				from traceback import format_exception

				data = {
					"content": None,
					"embeds": [{
						"author": "Python Traceback Error",
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
