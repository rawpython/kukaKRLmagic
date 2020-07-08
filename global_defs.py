true = True
false = False

_dollar_VEL = {'CP':0}
_dollar_ACC = {'CP':0}

real = float

class generic_struct():
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        #in the case where a structure (inheriting a generic_struct) gets as parameter a generic_struct
        # DECL JERK_STRUC DEF_JERK_STRUC={CP 500.000,ORI 50000.0,AX {A1 1000.00,A2 1000.00,A3 1000.00,A4 1000.00,A5 1000.00,A6 1000.00,E1 1000.00,E2 1000.00,E3 1000.00,E4 1000.00,E5 1000.00,E6 1000.00}} ; jerk value for the spline. CP: [m/Sec3], ORI: [[GRAD/Sec3], AX: [[GRAD/Sec3] (rotatory) resp. [m/Sec3] (linear)
        # def_jerk_struc = jerk_struc(generic_struct(cp=500.000,ori=50000.0,ax=generic_struct(a1=1000.00,a2=1000.00,a3=1000.00,a4=1000.00,a5=1000.00,a6=1000.00,e1=1000.00,e2=1000.00,e3=1000.00,e4=1000.00,e5=1000.00,e6=1000.00)))
        if not args is None:
            if type(args[0]) == type(self):
                self.__dict__.update(args[0].__dict__)
    
enum = generic_struct

class multi_dimensional_array():
    values = None
    size = None
    _type = None
    
    def __init__(size, _type):
        self.size = size
        self._type = _type
        
    def __getitem__(self, key):
        #key is a tuple
        # if accessed by my_multidimensional_array[1,1]
        #   key=(1,1)
        # if accessed by my_multidimensional_array[5,]
        #   key=(5,) #the key is a tuple with len==1
		return key #@todo should return values[key[0], key[1]]

    """
    def __setitem__(@todo):
        pass
    
    def __delitem__(@todo):
        pass
    """

def ptp(_pos, _apo):
    #_pos : position
    #_apo : c_dis, c_ptp, c_ori
    pass

def lin(_pos, _apo):
    #_pos : position
    #_apo : c_dis, c_ptp, c_ori
    pass


def fake_func():
    pass
interrupt_flags = {}
interrupts = {} #this contains function pointers to interrupt subprograms, these have to be called by thread
for i in range(1, 129):
    interrupt_flags[i] = False #activated by interrupt on
    interrupts[i] = fake_func 