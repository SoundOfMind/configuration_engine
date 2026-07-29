import configuration_engine


def test_import() -> None:
    assert configuration_engine is not None


def test_version() -> None:
    assert configuration_engine.__version__ == "0.1.0"
    