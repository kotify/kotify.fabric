import pytest


class FakeDeploy:
    def __init__(self, context):
        self.context = context
        self._sudos = []
        self._runs = []

    def sudo(self, cmd, msg=None):
        self._sudos.append({"cmd": cmd, "msg": msg})

    def run(self, cmd, msg=None):
        self._runs.append({"cmd": cmd, "msg": msg})

    def reset_fake(self):
        del self._sudos[:]
        del self._runs[:]


@pytest.fixture
def fake_deploy():
    return FakeDeploy({})
