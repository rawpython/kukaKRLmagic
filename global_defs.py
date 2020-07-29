import sys
import collections
import functools
import threading
import traceback
import sys
import _thread

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
    
    #geometric addition
    def __add__(self, other):
        """ Tests on robot
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
            LOG(PTOS({X 10, Y 20, Z 30, A 90, B 0, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 90, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 90}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
            LOG(PTOS({X 10, Y 20, Z 30, A 90, B 90, C 90}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
            result
            {X 11.000000, Y 22.000000, Z 33.000000, A 0.000000, B 0.000000, C 0.000000} 
            {X 8.000000, Y 21.000000, Z 33.000000, A 90.000000, B 0.000000, C 0.000000} 
            {X 13.000000, Y 22.000000, Z 29.000000, A 0.000000, B 90.000000, C 0.000000} 
            {X 11.000000, Y 17.000000, Z 32.000000, A 0.000000, B 0.000000, C 90.000000} 
            {X 13.000000, Y 22.000000, Z 29.000000, A 0.000000, B 90.000000, C 0.000000} 
        """
        import math
        ret = generic_struct(self)
        a = ret.a
        x = math.cos(a*math.pi/180.0 + math.atan2(other.y, other.x))*math.sqrt(other.x**2 + other.y**2)
        y = math.sin(a*math.pi/180.0 + math.atan2(other.y, other.x))*math.sqrt(other.x**2 + other.y**2)
        other.x = x
        other.y = y

        b = math.cos(-ret.a*math.pi/180.0 + math.atan2(ret.c, ret.b))*math.sqrt(ret.b**2 + ret.c**2)
        c = math.sin(-ret.a*math.pi/180.0 + math.atan2(ret.c, ret.b))*math.sqrt(ret.b**2 + ret.c**2)

        x = math.cos(-b*math.pi/180.0 + math.atan2(other.z, other.x))*math.sqrt(other.x**2 + other.z**2)
        z = math.sin(-b*math.pi/180.0 + math.atan2(other.z, other.x))*math.sqrt(other.x**2 + other.z**2)
        other.x = x
        other.z = z

        #c = math.sin(b*math.pi/180.0 + math.atan2(ret.c, ret.b))*math.sqrt(ret.b**2 + ret.c**2)

        y = math.cos(c*math.pi/180.0 + math.atan2(other.z, other.y))*math.sqrt(other.y**2 + other.z**2)
        z = math.sin(c*math.pi/180.0 + math.atan2(other.z, other.y))*math.sqrt(other.y**2 + other.z**2)
        other.y = y
        other.z = z

        """
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
            LOG(PTOS({X 10, Y 20, Z 30, A 90, B 0, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 90, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
            LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 90}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
            LOG(PTOS({X 10, Y 20, Z 30, A 90, B 90, C 90}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
            result
            {X 11.000000, Y 22.000000, Z 33.000000, A 10.000000, B 20.000000, C 30.000000} 
            {X 8.000000, Y 21.000000, Z 33.000000, A 100.000000, B 20.000000, C 30.000000} 
            {X 13.000000, Y 22.000000, Z 29.000000, A 154.000000, B 67.7312, C -177.273000} 
            {X 11.000000, Y 17.000000, Z 32.000000, A 20.283, B -9.3912, C 116.548} 
            {X 13.000000, Y 22.000000, Z 29.000000, A 154.494, B 67.7312, C -177.273} 
        """
        from scipy.spatial.transform import Rotation as R
        r1 = R.from_euler('xyz', [self.a,self.b,self.c], True)
        r2 = R.from_euler('xyz', [other.a,other.b,other.c], True)
        r3 = r2*r1
        _a, _b, _c = [(x * 180.0/math.pi) for x in  r3.as_euler('xyz')]
        #print( "%s, %s, %s"%(_a, _b, _c) )
        ret.x = ret.x + other.x
        ret.y = ret.y + other.y
        ret.z = ret.z + other.z
        ret.a = _a
        ret.b = _b
        ret.c = _c
        return ret

    def __repr__(self):
        return "{%s}"%( ', '.join(["%s:%s"%(k, v) for k, v in self.__dict__.items()]) )

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
    

def fake_func():
    pass


def interruptable_function_decorator(func):
    """ A decorator to handle interrupts 
        robot functions have to be decorated with this decorator to make it possible trace the calling stack and
        properly handle interrupts
    """
    def interruptable_function(*args, **kwargs):
        try:
            threads_callstack[threading.currentThread].append(func)
            func(*args, **kwargs)
            mem = threads_callstack[threading.currentThread].pop()
        except KeyboardInterrupt:
            mem = threads_callstack[threading.currentThread].pop()
            #the resume makes it the interpreter to move up to the interrupt declaration level
            # if the level does not correspont to the interrupt level, raise again the Exception to move upper
            if len(threads_callstack[threading.currentThread]) == 0:
                print("Program structure inadmissible for RESUME")
            if not threads_callstack[threading.currentThread][-1] == robot.interrupt_actually_triggered.function_in_which_it_is_defined:
                raise(KeyboardInterrupt('asd'))
            
    return interruptable_function


interrupt_flags = {}
interrupt_rising_edge_flags = {} #TODO for each interrupt, here is stored if the condition is already triggered
interrupts = {} #this contains function pointers to interrupt subprograms, these have to be called by thread
class InterruptData():
    function_to_call = None
    function_in_which_it_is_defined = None
    function_to_get_condition_status = None
    condition_status_mem = False
    def __init__(self, fcall, fdef, fcond):
        self.function_to_call = fcall
        self.function_in_which_it_is_defined = fdef
        self.function_to_get_condition_status = fcond
        self.condition_status_mem = False
    def probe_interrupt(self):
        s = self.function_to_get_condition_status()
        if s and not self.condition_status_mem:
            robot.interrupt_actually_triggered = self
            self.function_to_call()
        self.condition_status_mem = s

for i in range(1, 129):
    interrupt_flags[i] = False #activated by interrupt on
    interrupts[i] = InterruptData(fake_func, fake_func, fake_func)


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

#to implement kinematics refer to https://ros-planning.github.io/moveit_tutorials/doc/getting_started/getting_started.html
# or https://github.com/siddikui/Kuka-KR210-Kinematics
# or https://github.com/Peroulis/6DOF-KUKA
class Robot():
    _do_not_stop_ADVANCE_on_next_IO = False

    internal_stop_flag = False
    
    interrupt_actually_triggered = None

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
        for iterrupt_number, interrupt_def in interrupts.items():
            interrupt_def.probe_interrupt()
        if not self.internal_stop_flag:
            threading.Timer(0.001, self.check_interrupts).start()
    def resume_interrupt(self): 
        #this generate a KeyboardInterrupt to the main thread (the one that executes the robot program)
        # the KeyboardInterrupt is correctly handled in interruptable_function_decorator
        # to make it possible resume the thread at the correct point WOOOOW
        _thread.interrupt_main()

    def wait_sec(self, t):
        time.sleep(t)

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

"""
STRUC PRO_IP CHAR NAME[32],INT SNR,CHAR NAME_C[32],INT SNR_C,CHAR NAME_C_TRL[32],INT SNR_C_TRL,BOOL I_EXECUTED,INT P_ARRIVED,CHAR P_NAME[24],CALL_STACK SI01,SI02,SI03,SI04,SI05,SI06,SI07,SI08,SI09,SI10

name[]      Name of the module in which the interpreter is in the advance run
snr         Number of the block in which the interpreter is in the advance run (usually not equal to the line number of the program)
name_c[]    Name of the module in which the interpolator is in the main run
snr_c       Number of the block in which the interpolator is in the main run
i_executed  Indicates whether the block has already been executed by the interpreter (= TRUE) 
p_arrived   Indicates where the robot is located on the path (only relevant for motion instructions)
 0: Arrived at the target or auxiliary point of the motion
 1: Target point not reached, i.e. robot is somewhere on the path
 2: Not relevant
 3: Arrived at the auxiliary point of a CIRC or SCIRC motion
 4: On the move in the section between the start and the auxiliary point
p_name[]    Name or aggregate of the target or auxiliary point at which the robot is located
SI01 … SI10 Caller stack in which the interpreter is situated
"""

#STRUC PROG_INFO CHAR SEL_NAME[32],PRO_STATE P_STATE,PRO_MODE P_MODE,CHAR PRO_IP_NAME[32],INT PRO_IP_SNR
# SEL_NAME name of the selected program
# PRO_IP_NAME[] name of the current module
# PRO_IP_SNR current block in the current module

submit_interpreter_thread = None
robot_interpreter_thread = None

threads_callstack = {} #thread:functionpointer[]
threads_callstack[threading.currentThread] = []
#def get_current_pro_ip():
#    if threading.currentThread == submit_interpreter_thread:
#        return DOLLAR_pro_ip0
#    return DOLLAR_pro_ip1




