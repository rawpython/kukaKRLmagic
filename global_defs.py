true = True
false = False

_dollar_VEL = {'CP':0}
_dollar_ACC = {'CP':0}

real = float

class generic_struct():
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    