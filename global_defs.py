import sys

true = True
false = False

DOLLAR__vel = {'CP':0}
DOLLAR__acc = {'CP':0}

real = float
char = str

def _not(value):
    if type(value) is bool:
        return not value
    return ~value

class generic_struct():
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        #in the case where a structure (inheriting a generic_struct) gets as parameter a generic_struct
        # DECL JERK_STRUC DEF_JERK_STRUC={CP 500.000,ORI 50000.0,AX {A1 1000.00,A2 1000.00,A3 1000.00,A4 1000.00,A5 1000.00,A6 1000.00,E1 1000.00,E2 1000.00,E3 1000.00,E4 1000.00,E5 1000.00,E6 1000.00}} ; jerk value for the spline. CP: [m/Sec3], ORI: [[GRAD/Sec3], AX: [[GRAD/Sec3] (rotatory) resp. [m/Sec3] (linear)
        # def_jerk_struc = jerk_struc(generic_struct(cp=500.000,ori=50000.0,ax=generic_struct(a1=1000.00,a2=1000.00,a3=1000.00,a4=1000.00,a5=1000.00,a6=1000.00,e1=1000.00,e2=1000.00,e3=1000.00,e4=1000.00,e5=1000.00,e6=1000.00)))
        if not args is None and len(args) > 0:
            if type(args[0]) == type(self):
                self.__dict__.update(args[0].__dict__)
    

class enum():
    enum_name = ''
    values_dict = None
    actual_value = None
    def __init__(self, value=None): #args contains values
        if not value is None:
            self.actual_value = self.values_dict[value]

    def __call__(self, value = None):
        ret = self.__class__()
        if not arg is None:
            self.actual_value = self.values_dict[value]
            ret.actual_value = self.actual_value
        return ret


class multi_dimensional_array():
    values = None
    size = None
    _type = None
    data = None

    def __init__(self, _type, size):
        self.size = size
        self._type = _type
        self.data = [_type]
        for s in size:
            self.data = self.data * s
        
    def __getitem__(self, key):
        #key is a tuple
        # if accessed by my_multidimensional_array[1,1]
        #   key=(1,1)
        # if accessed by my_multidimensional_array[5,]
        #   key=(5,) #the key is a tuple with len==1
        if type(key) == int:
            return self.data[key-1]

        value = self.data
        for i in key:
            value = value[i]
        return value

    def __setitem__(self, key, value):
        if type(key) == int:
            self.data[key-1] = self._type(value)
            return

        if len(key) == 1:
            self.data[key[0]] = self._type(value)
        if len(key) == 2:
            self.data[key[0]][key[1]] = self._type(value)
        if len(key) == 3:
            self.data[key[0]][key[1]][key[2]] = self._type(value)

    def __delitem__(key):
        pass
    

def _geometric_addition_operator(left_operant, right_operand):
    return

def fake_func():
    pass
interrupt_flags = {}
interrupts = {} #this contains function pointers to interrupt subprograms, these have to be called by thread
for i in range(1, 129):
    interrupt_flags[i] = False #activated by interrupt on
    interrupts[i] = fake_func 

DOLLAR__timer = {}
DOLLAR__timer_stop = {}
for i in range(1, 129):
    DOLLAR__timer_stop[i] = True #activated by interrupt on
    DOLLAR__timer[i] = 0 

DOLLAR__inputs = {}
DOLLAR__outputs = {}
for i in range(1, 4097):
    DOLLAR__inputs[i] = False
    DOLLAR__outputs[i] = False

def signal(io, io_end_range=None):
    return 0

#circ_type = int

jerk_struc = generic_struct

#this is referenced in $operate.dat, I don't know the right definition
call_stack = int


class Robot():
    _do_not_stop_ADVANCE_on_next_IO = False

    def __init__(self, *args, **kwargs):
        pass

    def do_not_stop_ADVANCE_on_next_IO(self):
        self._do_not_stop_ADVANCE_on_next_IO = True

    def ptp(self, position, apo=None):
        print("PTP %s %s"%(position, apo))

    def lin(self, position, apo=None):
        print("LIN %s %s"%(position, apo))

    def ptp_rel(self, position, apo=None):
        print("PTP_REL %s %s"%(position, apo))

    def lin_rel(self, position, apo=None):
        print("LIN_REL %s %s"%(position, apo))

    def circ(self, position, apo=None):
        print("CIRC %s %s"%(position, apo))

robot = Robot()
