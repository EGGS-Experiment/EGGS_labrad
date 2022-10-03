"""
Contains the class structures needed for creating data files and directories.
"""
import os
import re
import h5py
from datetime import datetime
from weakref import WeakValueDictionary

from . import backend, errors, util
# todo: move session/sessionstore/dataset objects into a different file
# todo: move shared functions into util


## Filename translation.
_encodings = [
    ('%', '%p'),  # this one MUST be first for encode/decode to work properly
    ('/', '%f'),
    ('\\', '%b'),
    (':', '%c'),
    ('*', '%a'),
    ('?', '%q'),
    ('"', '%r'),
    ('<', '%l'),
    ('>', '%g'),
    ('|', '%v')
]
# todo: generalize file extension support


def filename_encode(name):
    """
    Encode special characters to produce a name that can be used as a filename.
    """
    for char, code in _encodings:
        name = name.replace(char, code)
    return name


def filename_decode(name):
    """
    Decode a string that has been encoded using filename_encode.
    """
    for char, code in _encodings[1:] + _encodings[0:1]:
        name = name.replace(code, char)
    return name


def filedir(datadir, path):
    return os.path.join(datadir, *[filename_encode(d) for d in path[1:]])


## time formatting
TIME_FORMAT = '%Y-%m-%d, %H:%M:%S'


def time_to_str(t):
    return t.strftime(TIME_FORMAT)


def time_from_str(s):
    return datetime.strptime(s, TIME_FORMAT)


## variable parsing
_re_label = re.compile(r'^([^\[(]*)')  # matches up to the first [ or (
_re_legend = re.compile(r'\((.*)\)')  # matches anything inside ( )
_re_units = re.compile(r'\[(.*)\]')  # matches anything inside [ ]


def _get_match(pat, s, default=None):
    matches = re.findall(pat, s)
    if len(matches) == 0:
        if default is None:
            raise Exception("Cannot parse '{0}'.".format(s))
        return default
    return matches[0].strip()


def parse_independent(s):
    label = _get_match(_re_label, s)
    units = _get_match(_re_units, s, '')
    return label, units


def parse_dependent(s):
    label = _get_match(_re_label, s)
    legend = _get_match(_re_legend, s, '')
    units = _get_match(_re_units, s, '')
    return label, legend, units

def check_if_multiple_datasets(filename):
    """
    Check if hdf5 or h5 file has multiple datasets.
    Arguments:
        filename    (str): the name of the file to check
    Returns:
                    (bool): whether the file has multiple datasets.
    """
    # open file
    num_datasets = 0
    with h5py.File(filename, 'r') as file_tmp:
        num_datasets = len(file_tmp["datasets"])

    # get number of datasets
    if num_datasets > 1:
        return True
    else:
        return False


## data-url support for storing parameters
DATA_URL_PREFIX = 'data:application/labrad;base64,'


class SessionStore(object):
    """
    Handles session objects.
    Acts as main interface between server and files.
    """
    # todo: ensure repositories can't contain one another

    def __init__(self, datadirs, hub):
        self._sessions = WeakValueDictionary()
        self.hub = hub

        datadirs = [datadirs] if isinstance(datadirs, str) else datadirs

        # self.datadirs holds the root directories and the name to represent them as
        # (e.g. {'labrad': C:\\Users\\EGGS1\\Documents\\.labrad})
        self.datadirs = {os.path.basename(datadir): os.path.dirname(datadir) for datadir in datadirs}

    def get_all(self):
        return self._sessions.values()

    def exists(self, path):
        """
        Check whether a session exists on disk for a given path.

        This does not tell us whether a session object has been
        created for that path.
        """
        return any([os.path.exists(filedir(datadir, path)) for datadir in self.datadirs.values()])

    def get(self, path):
        """
        Get a Session object.
            If a session already exists for the given path, return it.
            Otherwise, create a new session instance.
        Arguments:
            path    list(str): the desired path.
        Returns:
                    class(Session): a Session object representing the desired directory.
        """
        path = tuple(path)

        # return session if it exists
        if path in self._sessions:
            return self._sessions[path]

        session = None

        # return the virtual root directory
        if path == ('',):
            session = VirtualSession(self.datadirs, path, self.hub, self)
        else:
            # redirect the path to the appropriate real directory
            datadir = self.datadirs[path[1]]

            # return a virtual file directory if filepath contains a real hdf5/h5 file
            if ('.hdf5' in path[-1]) or ('.h5' in path[-1]):
                session = VirtualFileSession(datadir, path, self.hub, self)
            # normal case
            else:
                session = Session(datadir, path, self.hub, self)

        # add session to list of sessions
        self._sessions[path] = session
        return session


class Session(object):
    """
    Stores information about a directory on disk.

    One session object is created for each data directory accessed.
    The session object manages reading from and writing to the config
    file, and manages the datasets in this directory.
    # todo: make all functions in Session class that are not used elsewhere begin with "_"
    """

    def __init__(self, datadir, path, hub, session_store):
        """
        Initialization that happens once when session object is created.
        """
        self.path = path
        self.hub = hub
        self.dir = filedir(datadir, path)
        self.infofile = os.path.join(self.dir, 'session.ini')
        self.datasets = WeakValueDictionary()

        # create new directory if it doesn't exist
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

            # notify listeners about this new directory
            parent_session = session_store.get(path[:-1])
            hub.onNewDir(path[-1], parent_session.listeners)

        # load existing infofile (session.ini file) if it exists,
        # otherwise create it
        if os.path.exists(self.infofile):
            self.load()
        else:
            self.counter = 1
            self.created = self.modified = datetime.now()
            self.session_tags = {}
            self.dataset_tags = {}

        # update current access time and save
        self.access()
        self.listeners = set()

    def load(self):
        """
        Load info from the session.ini file.
        """
        S = util.DVSafeConfigParser()
        S.read(self.infofile)

        sec = 'File System'
        self.counter = S.getint(sec, 'Counter')

        sec = 'Information'
        self.created = time_from_str(S.get(sec, 'Created'))
        self.accessed = time_from_str(S.get(sec, 'Accessed'))
        self.modified = time_from_str(S.get(sec, 'Modified'))

        # get tags if they're there
        if S.has_section('Tags'):
            self.session_tags = eval(S.get('Tags', 'sessions', raw=True))
            self.dataset_tags = eval(S.get('Tags', 'datasets', raw=True))
        else:
            self.session_tags = {}
            self.dataset_tags = {}

    def save(self):
        """
        Save info to the session.ini file.
        """
        S = util.DVSafeConfigParser()

        sec = 'File System'
        S.add_section(sec)
        S.set(sec, 'Counter', repr(self.counter))

        sec = 'Information'
        S.add_section(sec)
        S.set(sec, 'Created', time_to_str(self.created))
        S.set(sec, 'Accessed', time_to_str(self.accessed))
        S.set(sec, 'Modified', time_to_str(self.modified))

        sec = 'Tags'
        S.add_section(sec)
        S.set(sec, 'sessions', repr(self.session_tags))
        S.set(sec, 'datasets', repr(self.dataset_tags))

        with open(self.infofile, 'w') as f:
            S.write(f)

    def access(self):
        """
        Update last access time and save.
        """
        self.accessed = datetime.now()
        self.save()

    def listContents(self, tagFilters):
        """
        Get a list of directory names in this directory.
        Arguments:
            tagFilters list(str): todo
        Returns:
            tuple(str), tuple(str): sorted tuples of directories and datasets, respectively.
        """
        # get all names in the directory
        files = os.listdir(self.dir)

        # get directories (objects that end in '.dir' are directories, though we also allow folders that don't end in dir)
        # todo: fix .dir suffix problem, maybe try/except block that does .dir if fails?
        #dirs = [filename_decode(filename.split('.')[0]) for filename in files if os.path.isdir(os.path.join(self.dir, filename))]
        dirs = [filename_decode(filename) for filename in files if os.path.isdir(os.path.join(self.dir, filename))]

        # get only valid dataset files (ignore csv since they're partnered with ini files)
        filetype_suffixes = ('.ini', '.hdf5', '.h5')
        def valid_datafile(filename):
            if filename == "session.ini":
                return False
            # hdf5 files with more than multiple datasets are to be treated as virtual directories
            elif (filename.endswith('.hdf5') or filename.endswith('.h5')):
                multiple_datasets = check_if_multiple_datasets(os.path.join(self.dir, filename))
                # add filename to directories
                if multiple_datasets:
                    dirs.append(filename_decode(filename))
                    return False
                else:
                    return True
            else:
                return any([filename.endswith(filetype) for filetype in filetype_suffixes])

        datasets = sorted([filename_decode(filename.split('.')[0]) for filename in files if valid_datafile(filename)])

        # todo: turn these functions into lambda functions
        # tag filtering functions
        # include = lambda entries, tag, tags: [e for e in entries if (e in tags) and (tag in tags[e])]
        # exclude = lambda entries, tag, tags: [e for e in entries if (e not in tags) or (tag not in tags[e])]
        def include(entries, tag, tags):
            """
            Include only entries that have the specified tag.
            """
            return [e for e in entries
                    if (e in tags) and (tag in tags[e])]

        def exclude(entries, tag, tags):
            """
            Exclude all entries that have the specified tag.
            """
            return [e for e in entries
                    if (e not in tags) or (tag not in tags[e])]

        # iteratively apply tag filters
        for tag in tagFilters:
            # choose filter function
            filter_func = include
            if tag[:1] == '-':
                filter_func = exclude
                tag = tag[1:]

            # filter directories and datasets
            dirs = filter_func(dirs, tag, self.session_tags)
            datasets = filter_func(datasets, tag, self.dataset_tags)

        return sorted(dirs), sorted(datasets)

    def listDatasets(self):
        """
        Get a list of dataset names in this directory.
            Only used by Session.openDataset
        Returns:
            list(str): a list of dataset filenames.
        """
        # get files
        files = os.listdir(self.dir)
        filenames = []

        # separate filenames from extensions
        for s in files:
            base, _, ext = s.rpartition('.')
            if ext in ['csv', 'hdf5', 'h5']:
                filenames.append(filename_decode(base))
        return sorted(filenames)

    def newDataset(self, title, independents, dependents, extended=False):
        """
        todo: document
        Args:
            title:
            independents:
            dependents:
            extended:
        Returns:
            todo
        """
        num = self.counter
        self.counter += 1
        self.modified = datetime.now()

        # todo: this is what makes the datasets have strange numbers in front of it; fix it up
        name = '%05d - %s' % (num, title)
        dataset = Dataset(self, name, title, create=True,
                          independents=independents,
                          dependents=dependents,
                          extended=extended)
        self.datasets[name] = dataset
        self.access()

        # notify listeners about the new dataset
        self.hub.onNewDataset(name, self.listeners)
        return dataset

    def openDataset(self, name):
        """
        Creates and returns a Dataset object from its name.
        Arguments:
            name:
        Returns:
            Dataset: a Dataset object.
        """
        # try to look up dataset by number
        if isinstance(name, (int, int)):
            for oldName in self.listDatasets():
                num = int(oldName[:5])
                if name == num:
                    name = oldName
                    break

        # if it's still a number, we didn't find the dataset
        if isinstance(name, (int, int)):
            raise errors.DatasetNotFoundError(name)

        # try to find dataset file
        filename = filename_encode(name)
        file_base = os.path.join(self.dir, filename)
        if not (os.path.exists(file_base + '.csv') or os.path.exists(file_base + '.hdf5') or os.path.exists(file_base + '.h5')):
        # if not all(map(os.path.exists, [file_base + suffix for suffix in ['.csv', '.hdf5', '.h5']])):
            raise errors.DatasetNotFoundError(name)

        # get dataset wrapper if it already exists
        if name in self.datasets:
            dataset = self.datasets[name]
            dataset.access()
        # otherwise, create new wrapper for dataset
        else:
            dataset = Dataset(self, name)
            self.datasets[name] = dataset
        self.access()

        return dataset

    def updateTags(self, tags, sessions, datasets):
        def updateTagDict(tags, entries, d):
            updates = []
            for entry in entries:
                changed = False
                if entry not in d:
                    d[entry] = set()
                entryTags = d[entry]
                for tag in tags:
                    if tag[:1] == '-':
                        # remove this tag
                        tag = tag[1:]
                        if tag in entryTags:
                            entryTags.remove(tag)
                            changed = True
                    elif tag[:1] == '^':
                        # toggle this tag
                        tag = tag[1:]
                        if tag in entryTags:
                            entryTags.remove(tag)
                        else:
                            entryTags.add(tag)
                        changed = True
                    else:
                        # add this tag
                        if tag not in entryTags:
                            entryTags.add(tag)
                            changed = True
                if changed:
                    updates.append((entry, sorted(entryTags)))
            return updates

        sessUpdates = updateTagDict(tags, sessions, self.session_tags)
        dataUpdates = updateTagDict(tags, datasets, self.dataset_tags)

        self.access()
        if len(sessUpdates) + len(dataUpdates):
            # fire a message about the new tags
            msg = (sessUpdates, dataUpdates)
            self.hub.onTagsUpdated(msg, self.listeners)

    def getTags(self, sessions, datasets):
        sessTags = [(s, sorted(self.session_tags.get(s, []))) for s in sessions]
        dataTags = [(d, sorted(self.dataset_tags.get(d, []))) for d in datasets]
        return sessTags, dataTags


class VirtualSession(object):
    """
    A session object that allows multiple directories in non-contiguous paths
        to be treated as if they were in a single enclosing directory.
    """

    def __init__(self, datadirs, path, hub, session_store):
        """
        Initialization that happens once when session object is created.
        """
        self.path = path
        self.hub = hub
        self.listeners = set()
        self.subdirs = sorted(datadirs.keys())

    def listContents(self, tagFilters):
        """
        Get a list of directory names in this directory.
        """
        return self.subdirs, []

    def newDataset(self, title, independents, dependents, extended=False):
        raise errors.VirtualSessionError("newDataset")

    def openDataset(self, name):
        raise errors.VirtualSessionError("openDataset")

    def updateTags(self, tags, sessions, datasets):
        raise errors.VirtualSessionError("updateTags")

    def getTags(self, sessions, datasets):
        raise errors.VirtualSessionError("getTags")


class VirtualFileSession(VirtualSession):
    """
    A session object that represents a hdf5 file with multiple datasets as a directory.
    """

    def __init__(self, datadir, path, hub, session_store):
        """
        Initialization that happens once when session object is created.
        """
        self.path = path
        self.hub = hub
        self.datasets = WeakValueDictionary()
        self.dataset_filedir = filedir(datadir, path)
        self.dataset_names = None
        self.listeners = set()

        # todo: ensure dataset file exists
        filename = filename_encode(name)
        file_base = os.path.join(self.dir, filename)
        if not (os.path.exists(file_base + '.hdf5') or os.path.exists(file_base + '.h5')):
            raise errors.DatasetNotFoundError(name)

        # get dataset names
        with h5py.File(self.dataset_filedir) as file_tmp:
            datasets = file_tmp["datasets"]
            self.dataset_names = list(map(str, datasets.keys()))

        self.dataset_names = sorted(self.dataset_names)

    def listContents(self, tagFilters):
        """
        Get a list of directory names in this directory.
        """
        return [], self.dataset_names

    def openDataset(self, name):
        """
        Creates and returns a Dataset object from its name.
            Backed by an MultipleHDF5Data.
        Arguments:
            name:
        Returns:
            Dataset: a Dataset object.
        """
        # if it's still a number, we didn't find the dataset
        if isinstance(name, (int, int)):
            raise errors.DatasetNotFoundError(name)

        # todo: need to create and pass filename

        # get dataset wrapper if it already exists
        if dataset_name in self.datasets:
            dataset = self.datasets[dataset_name]
            dataset.access()
        # otherwise, create new wrapper for dataset
        else:
            dataset = Dataset(self, name, create=False, dataset_name=name)
            self.datasets[name] = dataset

        return dataset

    def newDataset(self, title, independents, dependents, extended=False):
        raise errors.VirtualSessionError("newDataset")

    def updateTags(self, tags, sessions, datasets):
        raise errors.VirtualSessionError("updateTags")

    def getTags(self, sessions, datasets):
        raise errors.VirtualSessionError("getTags")


class Dataset(object):
    """
    This object basically takes care of listeners and notifications.
    All the actual data or metadata access is proxied through to a
    backend object.
    """

    def __init__(self, session, name, title=None, create=False, independents=[], dependents=[], extended=False, dataset_name=None):
        self.hub = session.hub
        self.name = name
        file_base = os.path.join(session.dir, filename_encode(name))
        self.listeners = set()  # contexts that want to hear about added data
        self.param_listeners = set()
        self.comment_listeners = set()

        if create:
            indep = [self.makeIndependent(i, extended) for i in independents]
            dep = [self.makeDependent(d, extended) for d in dependents]
            self.data = backend.create_backend(file_base, title, indep, dep, extended)
            self.save()
        else:
            self.data = backend.open_backend(file_base, dataset_name)
            self.load()
            self.access()

    def save(self):
        self.data.save()

    def load(self):
        self.data.load()

    def version(self):
        v = self.data.version
        return '.'.join(str(x) for x in v)

    def access(self):
        """
        Update time of last access for this dataset.
        """
        self.data.access()
        self.save()

    def makeIndependent(self, label, extended):
        """
        Add an independent variable to this dataset.
        """
        if extended:
            return backend.Independent(*label)
        if isinstance(label, tuple):
            label, units = label
        else:
            label, units = parse_independent(label)
        return backend.Independent(label=label, shape=(1,), datatype='v', unit=units)

    def makeDependent(self, label, extended):
        """
        Add a dependent variable to this dataset.
        """
        if extended:
            return backend.Dependent(*label)
        if isinstance(label, tuple):
            label, legend, units = label
        else:
            label, legend, units = parse_dependent(label)
        return backend.Dependent(label=label, legend=legend, shape=(1,), datatype='v', unit=units)

    def getIndependents(self):
        return self.data.getIndependents()

    def getDependents(self):
        return self.data.getDependents()

    def getRowType(self):
        return self.data.getRowType()

    def getTransposeType(self):
        return self.data.getTransposeType()

    def addParameter(self, name, data, saveNow=True):
        self.data.addParam(name, data)
        if saveNow:
            self.save()

        # notify all listening contexts
        self.hub.onNewParameter(None, self.param_listeners)
        self.param_listeners = set()
        return name

    def addParameters(self, params, saveNow=True):
        for name, data in params:
            self.data.addParam(name, data)
        if saveNow:
            self.save()

        # notify all listening contexts
        self.hub.onNewParameter(None, self.param_listeners)
        self.param_listeners = set()

    def getParameter(self, name, case_sensitive=True):
        return self.data.getParameter(name, case_sensitive)

    def getParamNames(self):
        return self.data.getParamNames()

    def addData(self, data):
        # append the data to the file
        self.data.addData(data)

        # notify all listening contexts
        self.hub.onDataAvailable(None, self.listeners)
        self.listeners = set()

    def getData(self, limit, start, transpose=False, simpleOnly=False):
        return self.data.getData(limit, start, transpose, simpleOnly)

    def keepStreaming(self, context, pos):
        # keepStreaming does something a bit odd and has a confusing name (ERJ)
        #
        # The goal is this: a client that is listening for "new data" events should only
        # receive a single notification even if there are multiple writes.  To do this,
        # we do the following:
        #
        # If a client reads to the end of the dataset, it is added to the list to be notified
        # if another context does 'addData'.
        #
        # if a client calls 'addData', all listeners are notified, and then the set of listeners
        # is cleared.
        # 
        # If a client reads, but not to the end of the dataset, it is immediately notified that
        # there is more data for it to read, and then removed from the set of notifiers.
        if self.data.hasMore(pos):
            if context in self.listeners:
                self.listeners.remove(context)
            self.hub.onDataAvailable(None, [context])
        else:
            self.listeners.add(context)

    def addComment(self, user, comment):
        self.data.addComment(user, comment)
        self.save()

        # notify all listening contexts
        self.hub.onCommentsAvailable(None, self.comment_listeners)
        self.comment_listeners = set()

    def getComments(self, limit, start):
        return self.data.getComments(limit, start)

    def keepStreamingComments(self, context, pos):
        if pos < self.data.numComments():
            if context in self.comment_listeners:
                self.comment_listeners.remove(context)
            self.hub.onCommentsAvailable(None, [context])
        else:
            self.comment_listeners.add(context)

    def shape(self):
        return self.data.shape()
