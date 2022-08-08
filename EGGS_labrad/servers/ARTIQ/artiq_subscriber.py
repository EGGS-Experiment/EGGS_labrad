from asyncio import get_event_loop
from sipyco.sync_struct import Subscriber
from sipyco.asyncio_tools import atexit_register_coroutine


class ARTIQ_subscriber(object):
    """
    A wrapper for a sipyco Subscriber object that listens
    to notifications from artiq_master.
    """

    def __init__(self, notify_cb):
        self._notify_cb = notify_cb
        self._struct_holder = struct_holder(dict())
        self._subscriber = Subscriber('schedule', self._target_builder, self._notify_cb)

    def connect(self, host, port):
        get_event_loop().run_until_complete(self._subscriber.connect(host, port))
        # todo: is atexit_register_coroutine necessary?
        atexit_register_coroutine(self._subscriber.close)

    def _target_builder(self, struct_init):
        self._struct_holder = struct_holder(struct_init)
        return self._struct_holder


class struct_holder:
    def __init__(self, init):
        self.backing_store = init

    def __setitem__(self, k, v):
        self.backing_store[k] = v

    def __delitem__(self, k):
        del self.backing_store[k]

    def __getitem__(self, k):
        def update():
            self[k] = self.backing_store[k]
        return substructexample(update, self.backing_store[k])


class substruct_holder:
    def __init__(self, update_cb, ref):
        self.update_cb = update_cb
        self.ref = ref

    def append(self, x):
        self.ref.append(x)
        self.update_cb()

    def insert(self, i, x):
        self.ref.insert(i, x)
        self.update_cb()

    def pop(self, i=-1):
        self.ref.pop(i)
        self.update_cb()

    def __setitem__(self, key, value):
        self.ref[key] = value
        self.update_cb()

    def __delitem__(self, key):
        self.ref.__delitem__(key)
        self.update_cb()

    def __getitem__(self, key):
        return substruct_holder(self.update_cb, self.ref[key])
