clean:
	find . -type f -name '*.pyc' -exec rm -f {} +
	find . -type f -name '*.pyo' -exec rm -f {} +
	find . -type f -name '*.~' -exec rm -f {} +
	find . -type d -name '__pycache__' -exec rm -rf {} +

test:
	flake8 fmt
	# pylint fmt
	pip install -e .
	py.test tests -vvv

pkg:
	python setup.py bdist_wheel
	python setup.py sdist
