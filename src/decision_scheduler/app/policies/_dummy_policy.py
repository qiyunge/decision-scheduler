from ._base import Policy


class DummyPolicy(Policy):
    def select(self, obs):
        return None