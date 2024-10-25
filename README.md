# Submission is possible back-end

## Poetry Project

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

### Install Poetry:

You can use pip to install it globally:

```bash
pip install poetry
```

### Add dependencies:

You can add project dependencies using the add command:

```bash
poetry add package-name
```

### Define versions and constraints:

Poetry allows you to specify package versions and constraints. For example:

```bash
peotry add package-name@^1.0
```

### Install Dependencies

```bash
poetry install
```
### Update dependencies

```bash
poetry update
```

## Django

This project uses [Django](https://www.djangoproject.com/) as the web framework.

### Run Django:

You can run the Django development server using the following command:

```bash
poetry run python back_end/manage.py runserver
```


## Pytest
This project uses [Pytest](https://docs.pytest.org/en/stable/) for testing.

### Install Pytest:

You can install pytest using pip:

```bash
pip install pytest
```

### Run tests:

You can run tests using the following command:

```bash
poetry run pytest
```
