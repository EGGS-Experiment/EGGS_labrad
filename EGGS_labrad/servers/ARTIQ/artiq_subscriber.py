from asyncio import get_event_loop
from sipyco.sync_struct import Subscriber
from sipyco.asyncio_tools import atexit_register_coroutine


class ARTIQ_subscriber(object):
    """
    A wrapper for a sipyco Subscriber object that listens
    to notifications from artiq_master.
    """

    def __init__(self, notify_cb):
        self.loop = get_event_loop()
        self._notify_cb = notify_cb
        self._struct_holder = None
        self._subscriber = Subscriber('schedule', self._target_builder, self._notify_cb)
        print('artiq_subscriber: subscriber created')

    def connect(self, host, port):
        print('artiq_subscriber: connecting...')
        self.loop.run_until_complete(self._suscriber.connect(host, port))
        # todo: is atexit_register_coroutine necessary?
        atexit_register_coroutine(self._subscriber.close)
        print('artiq_subscriber: finished connecting...')

    def _target_builder(self, struct_init):
        print('artiq_subscriber: target builder called')
        self._struct_holder = structexample(struct_init)


class structexample:
    def __init__(self, init):
        print('init:', init)
        self.backing_store = init

    def __setitem__(self, k, v):
        print('setitem called: {}'.format(self.backing_store.keys()))
        self.backing_store[k] = v
        print(self.backing_store)

    def __delitem__(self, k):
        print('delitem called: {}'.format(self.backing_store.keys()))
        del self.backing_store[k]
        print(self.backing_store)

    def __getitem__(self, k):
        print('getitem called: {}'.format(self.backing_store.keys()))
        def update():
            self[k] = self.backing_store[k]
        return substructexample(update, self.backing_store[k])


class substructexample:
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
        return substructexample(self.update_cb, self.ref[key])
