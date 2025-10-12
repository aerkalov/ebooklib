import pytest


@pytest.fixture(scope="session")
def session_temp_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("ebooklib")
