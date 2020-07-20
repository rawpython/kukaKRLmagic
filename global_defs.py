import sys
import collections
import functools
import threading
import traceback
import sys

true = True
false = False


"""
class real():
    value = 0.0
    def __init__(self, value = 0.0):
        self.set_value(value)

    def set_value(self, v):
        if type(v) == real:
            self.value = v.value
        else:
            self.value = float(v)

class krl_int(int):
    value = 0
    def __init__(self, value = 0):
        self.value = value

    def set_value(self, value):
        self.value = value

    def __index__(self):
        return self.value
    
    def __int__(self):
        return self.value
"""


real = float
char = str

class krl_list(collections.deque):
    def __init__(self, *args, **kwargs):
        collections.deque.__init__(self, *args, **kwargs)

    def set_value(self, value):
        for i in range(0, len(value)):
            self[i] = value[i]
"""
class char():
    value = ''
    def __init__(self, value = ''):
        self.value = value

    def set_value(self, value):
        self.value = value

"""

def _not(value):
    if type(value) is bool:
        return not value
    return ~value

class generic_struct():
    def __init__(self, *args, **kwargs):
        for k,v in kwargs.items():
            if type(v) == float:
                kwargs[k] = real(v)

        self.__dict__.update(kwargs)
        #in the case where a structure (inheriting a generic_struct) gets as parameter a generic_struct
        # DECL JERK_STRUC DEF_JERK_STRUC={CP 500.000,ORI 50000.0,AX {A1 1000.00,A2 1000.00,A3 1000.00,A4 1000.00,A5 1000.00,A6 1000.00,E1 1000.00,E2 1000.00,E3 1000.00,E4 1000.00,E5 1000.00,E6 1000.00}} ; jerk value for the spline. CP: [m/Sec3], ORI: [[GRAD/Sec3], AX: [[GRAD/Sec3] (rotatory) resp. [m/Sec3] (linear)
        # def_jerk_struc = jerk_struc(generic_struct(cp=500.000,ori=50000.0,ax=generic_struct(a1=1000.00,a2=1000.00,a3=1000.00,a4=1000.00,a5=1000.00,a6=1000.00,e1=1000.00,e2=1000.00,e3=1000.00,e4=1000.00,e5=1000.00,e6=1000.00)))
        if not args is None and len(args) > 0:
            if issubclass(type(args[0]),generic_struct):
                self.__dict__.update(args[0].__dict__)
    
    def set_value(self, value):
        self.__dict__.update(value.__dict__)
    

DOLLAR__vel = generic_struct(cp=0, ori1=0, ori2=0)
DOLLAR__acc = generic_struct(cp=0, ori1=0, ori2=0)


class enum():
    enum_name = ''
    values_dict = None
    actual_value = None
    def __init__(self, value=None): #args contains values
        if not value is None:
            #self.actual_value = self.values_dict[value]
            self.actual_value = value

    def __call__(self, value = None):
        ret = self.__class__()
        if not arg is None:
            #self.actual_value = self.values_dict[value]
            self.actual_value = value
            ret.actual_value = self.actual_value
        return ret

    def __eq__(self, other):
        if self.actual_value==other:
            return True
        else:
            return False

    def __repr__(self):
        return self.actual_value

    def set_value(self, value):
        self.actual_value = value


class multi_dimensional_array():
    values = None
    size = None
    _type = None
    data = None

    def __init__(self, _type, size):
        self.size = size[0]
        self._type = _type

        if len(size)>1:
            self.data = krl_list([multi_dimensional_array(_type, size[1:]) for x in range(0, size[0])])
        else:
            self.data = krl_list([_type()]*size[0])
        
    def __getitem__(self, indexes):
        if not (type(indexes) == int) and len(indexes) == 1:
            indexes = indexes[0]
        if type(indexes) == int:
            return self.data[indexes-1]
        if len(indexes)>1:
            return self.data[indexes[0]-1].__getitem__(indexes[1:])
        
    def __setitem__(self, indexes, value):
        if not (type(indexes) == int) and len(indexes) == 1:
            #self.data[indexes[0]-1].set_value(value)
            self.data[indexes[0]-1] = value
        elif type(indexes) == int:
            self.data[indexes-1] = self._type(value)
        else:
            self.data[indexes[0]-1].__setitem__(indexes[1:], value)

    def __delitem__(key):
        pass

    def set_value(self, value):
        if type(value) == generic_struct:
            self.data.set_value(value)
            return
        for i in range(0, len(value)):
            self.data[i] = value[i]
    

def _geometric_addition_operator(left_operant, right_operand):
    return

def fake_func():
    pass

interrupt_flags = {}
interrupts = {} #this contains function pointers to interrupt subprograms, these have to be called by thread
for i in range(1, 129):
    interrupt_flags[i] = False #activated by interrupt on
    interrupts[i] = fake_func 

""" defined in operate.dat
DOLLAR__timer = {}
DOLLAR__timer_stop = {}

for i in range(1, global_timers_count+1):
    DOLLAR__timer_stop[i] = True #activated by interrupt on
    DOLLAR__timer[i] = 0 
"""
global_timers_count = 64

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

    internal_stop_flag = False
    
    def __init__(self, *args, **kwargs):
        self.clock()
        self.check_interrupts()
    
    def clock(self):
        global global_timers_count
        try:
            import operate
            for i in range(1, global_timers_count+1):
                if not operate.DOLLAR__timer_stop[i]:
                    operate.DOLLAR__timer[i] = operate.DOLLAR__timer[i] + 1
        except:
            #timers are defined later in operate.dat
            traceback.print_exc()
        if not self.internal_stop_flag:
            threading.Timer(0.001, self.clock).start()

    def check_interrupts(self):
        global interrupts
        for iterrupt_number, interrupt_function in interrupts.items():
            interrupt_function()
        if not self.internal_stop_flag:
            threading.Timer(0.001, self.check_interrupts).start()

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

    def __del__(self):
        self.internal_stop_flag = True

robot = Robot()
