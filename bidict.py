class UniqueBidict:

    def __init__(self, initial: dict):
        self._dict = initial
        self._reverse_dict = dict(
            reversed(item) for item in self._dict.items())

    def __setitem__(self, k, v):
        # Delete existing occurrences of k and v
        if k in self._dict:
            del self._reverse_dict[self._dict[k]]
        if v in self._reverse_dict:
            del self._dict[self._reverse_dict[v]]

        # Set k and v
        self._dict[k] = v
        self._reverse_dict[v] = k

    def __getitem__(self, k):
        # If it's a slice
        if isinstance(k, slice):
            # If we only have the start i.e. [2:]
            if k.start and not (k.stop or k.step):
                return self._dict[k.start]

            # If we only have the stop i.e. [:2]
            elif k.stop and not (k.start or k.step):
                return self._reverse_dict[k.stop]

            # If we have anything else
            else:
                raise TypeError()

        # If it's an integer
        return self._dict[k]

    def __contains__(self, k):
        return k in self.__dict__

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()