from tests import TestCase
from catsnap.singleton import Singleton

class TestSingleton(TestCase):
    def test_it_is_a_singleton(self):
        singleton1 = Singleton()
        singleton2 = Singleton()
        assert singleton1 is singleton2


