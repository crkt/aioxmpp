import asyncio
import collections

class Token(collections.namedtuple("Token", ["key"])):
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __repr__(self):
        return "<Token key={!r} id={!r}>".format(
            self.key,
            id(self))


class CallbacksWithToken:
    def __init__(self, *keys, loop=None):
        super().__init__()
        self._loop = loop or asyncio.get_event_loop()
        self._callbacks = {
            key: {}
            for key in keys
        }

    def add_callback(self, key, fn):
        token = Token(key)
        self._callbacks[key][token] = fn
        return token

    def remove_callback(self, token):
        self._callbacks[token.key].pop(token)

    def remove_callback_fn(self, key, fn):
        self._callbacks[key].remove(fn)

    def emit(self, key, *args, **kwargs):
        for fn in self._callbacks[key].values():
            self._loop.call_soon(fn, *args, **kwargs)


class TagListener:
    def __init__(self, ondata, onerror=None):
        self._ondata = ondata
        self._onerror = onerror

    def data(self, data):
        self._ondata(data)

    def error(self, exc):
        if self._onerror is not None:
            self._onerror(exc)


class TagDispatcher:
    def __init__(self):
        self._listeners = {}

    def add_callback(self, tag, fn):
        return self.add_listener(tag, TagListener(fn))

    def add_listener(self, tag, listener):
        try:
            existing = self._listeners[tag]
        except KeyError:
            self._listeners[tag] = listener
        else:
            raise ValueError("only one listener is allowed per tag")

    def unicast(self, tag, data):
        cb = self._listeners[tag]
        cb.data(data)

    def remove_listener(self, tag):
        del self._listeners[tag]

    def broadcast_error(self, exc):
        for l in self._listeners.values():
            l.error(exc)

    def close_all(self, exc):
        self.broadcast_error(exc)
        self._listeners.clear()
