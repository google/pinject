# DEVELOPMENT

## Publish Developing Version

```shell
rm -f dist/*
python3 setup.py sdist bdist_wheel
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## Install Developing Version

```shell
sudo pip install \
    --no-deps \
    --no-cache \
    --upgrade \
    --index-url https://test.pypi.org/simple/ \
    pinject
```

## SEE ALSO

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
