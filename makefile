clean: clean-pyc
test: run-tests

clean-pyc:
	find . -type f -name '*.pyc' -exec rm -f {} +
	find . -type f -name '*.pyo' -exec rm -f {} +
	find . -type f -name '*.~' -exec rm -f {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +

run-tests:
	flake8 fmt
	# pylint fmt
	pip install -e .
	py.test tests -vvv
