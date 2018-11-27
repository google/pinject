# DEVELOPMENT

## Publish Developing Version

```shell
make clean
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

## SEE ALSO

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
