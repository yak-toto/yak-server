rm -f .coverage

for version in "3.10" "3.11" "3.12" "3.13"; do
    uv run --isolated --all-extras --managed-python -p $version -- \
        pytest --cov=yak_server --cov=scripts --cov=tests --cov=testing \
        --cov-config=pyproject.toml \
        --cov-append \
        -vv
done

coverage html
