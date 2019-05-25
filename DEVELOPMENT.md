# DEVELOPMENT

## Publish Developing Version

```shell
make clean

# Bump the version
make version

make pack

# publish to test.pypi.org
make publish-test

# publish to pypi.org
# make publish

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

## TODO

- [ ] @huan Keep `version.py` clean by setting `VERSION = 0.0.0`
- [ ] @huan Only update `version.py` before publish to PyPI

## SEE ALSO

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
