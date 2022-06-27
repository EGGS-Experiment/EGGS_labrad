#!/usr/bin/python
# Copyright (C) 2013  Evan Jeffrey
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Registry
version = 1.0
description = Labrad Registry stored configuration information for experiments
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import sys
import os
# sys.path.insert(0, 'U://ejeffrey/src/pylabrad-0.93.1/')
# sys.path.insert(0, os.path.join(os.environ['HOME'], 'src/pylabrad-0.93.1/'))

from labrad import util, types as T
from labrad.server import LabradServer, setting, Signal
import datetime
from twisted.python import log
from twisted.internet import defer, reactor
import re
import weakref
import delphi_compat

reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM\d*', 'LPT\d*']

decoded = '%/\:*?"<>|.';
encoded = 'pfbcaqQlgPd';
READONLY = True


def encode_filename(s):
    result = ""
    for c in s:
        if c in decoded:
            result = result + "%" + encoded[decoded.find(c)]
        else:
            result = result + c
    return result


def decode_filename(s):
    result = ""
    escape = False
    for c in s:
        if c == '%':
            escape = True
        elif escape:
            result += decoded[encoded.index(c)]
            escape = False
        else:
            result += c
    return result


class RegistryDir(object):
    # This relies on python refcounting to empty the cache, or rmdir may fail

    cache = weakref.WeakValueDictionary()

    @staticmethod
    def safe_filename(name, ext=None):

        if name and (re.search(r'[][()"\/|?]', name) or name[0] in '.-'):
            raise ValueError("filename %s has illegal characters" % (name,))
        if ext:
            name = name + '.' + ext
        return name

    def __new__(cls, path, parent):
        try:
            return cls.cache[tuple(path), parent]
        except KeyError:
            obj = object.__new__(cls)
            obj.path = tuple(path)
            obj.parent = parent
            obj.listeners = set()
            cls.cache[tuple(path)] = obj
            return obj

    def get_dirpath(self, filename=''):
        if filename:
            filename = encode_filename(filename) + '.dir'
        path_list = [self.parent.root_path] + [encode_filename(p) + '.dir' for p in self.path] + [filename]
        return os.path.join(*path_list)

    def get_filepath(self, filename):
        filename = encode_filename(filename) + '.key'
        path_list = [self.parent.root_path] + [encode_filename(p) + '.dir' for p in self.path] + [filename]
        return os.path.join(*path_list)

    def set(self, key, value):
        if READONLY:
            raise RuntimeError("Registry set readonly")
        pathname = self.get_filepath(key)
        tempfile = pathname + ".tmp"
        with open(tempfile, 'wb') as f:
            # f.write(labrad.types.reprLRData(value))
            f.write(delphi_compat.data_to_string(value) + '\r\n')
            f.flush()
            os.fsync(f.fileno())
        if os.name != 'posix':  # Windows doesn't get atomic renames.  Sad.
            os.remove(pathname)
        os.rename(tempfile, pathname)
        self.do_callbacks(key, False, True)

    def get(self, key):
        pathname = self.get_filepath(key)
        with open(pathname, 'rb') as f:
            data = f.read().rstrip()
            return delphi_compat.string_to_data(data)

    def mkdir(self, dir_):
        pathname = self.get_dirpath(dir_)
        os.mkdir(pathname)
        self.do_callbacks(dir_, True, True)

    def getdir(self, dir_, create=False):
        if dir_ == '':
            return RegistryDir([], self.parent)
        if dir_ == '..':
            return RegistryDir(self.path[:-1], self.parent)
        pathname = self.get_dirpath(dir_)
        if not os.path.isdir(pathname) and create:
            self.mkdir(dir_)
        if os.path.isdir(pathname):
            return RegistryDir(self.path + (dir_,), self.parent)
        else:
            raise KeyError("Directory path %s does not exist" % (pathname,))

    def rmdir(self, dir_):
        target_path = self.path + (dir_,)
        if target_path in self.cache:
            raise RuntimeError('Path in use')
        else:
            os.rmdir(self.get_dirpath(dir))
            self.do_callbacks(dir, True, False)

    def rm(self, key):
        filepath = self.get_filepath(key)
        os.remove(filepath)
        self.do_callbacks(key, False, False)

    def dirs(self):
        pathname = self.get_dirpath()
        dirlist = os.listdir(pathname)

        return [decode_filename(x[:-4]) for x in dirlist if x.endswith('.dir')]

    def keys(self):
        dirlist = os.listdir(self.get_dirpath())
        return [decode_filename(x[:-4]) for x in dirlist if x.endswith('.key')]

    def do_callbacks(self, name, key_type, access_type):
        self.parent.onChange((name, key_type, access_type), self.listeners)

    def add_listener(self, ID, context, setting):
        key = (ID, context)
        if setting:
            self.listeners[key] = setting
        else:
            self.listeners.pop(key, None)


class Registry(LabradServer):
    """The Registry provides a central location for LabRAD Modules to store configuration data"""
    name = 'Registry'

    def __init__(self, registry_path):
        if not os.path.isdir(registry_path):
            os.mkdir(registry_path)  # If only the last directory is missing, create it, else fail

        self.root_path = os.path.join(registry_path, '')
        LabradServer.__init__(self)

    def initServer(self):
        print
        "starting registry with path %s" % (self.root_path,)
        # RegistryDir.parent = self
        pass

    def initContext(self, c):
        c['path'] = RegistryDir([], self)
        c['path'].listeners.add(c.ID)

    def expireContext(self, c):
        LabradServer.expireContext(self, c)

    #    def serverConnected(self, ID, name):
    #        print "Got server connection message (%s, %s)" % (ID, name)
    #    def serverDisconnected(self, ID, name):
    #        print "Got server disconnection message (%s, %s)" % (ID, name)

    @setting(1, returns='(*s,*s)')
    def dir(self, c):
        dirs = c['path'].dirs()
        keys = c['path'].keys()
        return (dirs, keys)

    @setting(10, target=['       : Return current directory',
                         's      : Enter this subdirectory',
                         '*s     : Enter these subdirectories in order',
                         'w      : Go up "w" directories',
                         '(s, b) : Enter subdirectory "s", creating it as needed if "b"=True',
                         '(*s, b): Enter subdirectories "*s", creating it as needed if "b"=True'],
             returns='*s')
    def cd(self, c, target=None):
        '''
        Change the current directory
        NOTE: The root directory is given by the empty string ('')
        '''
        create = False
        if target is None:
            return ('',) + c['path'].path
        if isinstance(target, tuple):
            target, create = target

        old_path = c['path']
        if isinstance(target, (int, long)):
            new_path = c['path'].path[:-target]
            c['path'] = RegistryDir(new_path, self)
        else:
            if isinstance(target, (basestring)):
                target = [target]
            current_path = c['path']
            for t in target:
                current_path = current_path.getdir(t, create)
            c['path'] = current_path
        old_path.listeners.remove(c.ID)
        c['path'].listeners.add(c.ID)
        return ('',) + c['path'].path

    @setting(15, name='s', returns='*s: full path of new directory')
    def mkdir(self, c, name):
        '''
        Create a new subdirectory in the current directory with the given name
        '''
        c['path'].mkdir(name)
        return ('',) + c['path'].path + (name,)

    @setting(16, name='s')
    def rmdir(self, c, name):
        '''
        Delete the given subdirectory from the current directory
        '''
        c['path'].rmdir(name)

    @setting(20, args=['s{Key}: Retreive the key',
                       '(s{Key}, s{Type}): Retreive the key converted to the specific type',
                       '(s{Key}, b{Set}, ?{default}): Tries to retrieve key, returning default if not found, storing the default into registry if set is true',
                       '(s{Key}, s{Type}, b{Set}, ?{default}): Tries to retrieve key converted to given type, returning default on failure, storing the default into registry if set is true'],
             returns='?: Resulting key')
    def get(self, c, args):
        '''
        Get the content of the given key in the current directory
        '''

        do_set = False
        default = None
        keytype = '?'
        if isinstance(args, str):
            key = args
        else:
            key = args[0]
            if len(args) == 2:
                keytype = args[1]
            if len(args) == 3:
                do_set = args[1]
                default = args[2]
            if len(args) == 4:
                keytype = args[1]
                do_set = args[2]
                default = args[3]
        try:
            result = c['path'].get(key)
        except Exception as e:
            if do_set:
                c['path'].set(key, default)
            if default is not None:
                result = default
            else:
                raise KeyError("Registry key %s not found" % (key,))
        # Coerce result to keytype
        return result

    @setting(30, key='s', val='?')
    def set(self, c, key, val):
        '''
        Set the content of the given key in the current directory to the given data
        '''
        c['path'].set(key, val)

    # @setting(35, key='s', val='?')
    # def override(self, c, key, val):
    #    full_key = c['path'].path + (key,)
    #    c['overrides'][full_key]
    #    pass

    @setting(40, 'del', target='s', returns='')
    def lr_del(self, c, target):
        '''
        Delete the given key from the current directory
        '''
        c['path'].rm(target)

    #    @setting(45, key='s')
    #    def revert(self, c, key=None):
    #        pass

    onChange = Signal(505050, 'signal: notify on change', '(s,b,b)')

    @setting(50, 'Notify On Change',
             args='(w, b): Enable ("b"=True) or disable ("b"=False) notifications to message ID "w"')
    def notify_on_change(self, c, args):
        '''
        Requests notifications if the contents of the current directory change

        NOTE: The notification messages are of the form "(s, b, b)",
        indicating the name (s) of the affected item, whether it is a
        directory (True) or key (False), and whether it was
        added/changed (True) or deleted (False).
        '''
        ID, enable = args
        self.onChange._handler_func(self, c, ID if enable else None)

    @setting(100, 'Duplicate Context', ctx='(w,w)')
    def duplicate_context(self, c, ctx):
        '''
        Copies the settings (current directory and key overrides) from the given context into the current one
        '''
        if not ctx[0]:
            ctx = c.ID[0], ctx[1]
        source_c = self.contexts.get(ctx, None)
        old_path = c['path']
        if source_c:
            c['path'] = source_c.data['path']
        else:
            c['path'] = RegistryDir([], self)
        old_path.listeners.remove(c.ID)
        c['path'].listeners.add(c.ID)


if __name__ == '__main__':
    root_path = os.path.join(os.environ['HOME'], 'labrad_registry', '')
    __server__ = Registry(root_path)

    from labrad import util

    util.runServer(__server__)
