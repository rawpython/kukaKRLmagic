#include "operate.h"
#include "operate_r1.h"

#include <thread>
#include <functional>
#include <vector>
using namespace std;

typedef float real;

template <class T>
class krl_list : public vector<T>{

};

bool _not(bool value){return !value;}

struct e6pos {

	float	X;
	float	Y;
	float	Z;

	float	A;
	float	B;
	float	C;

    e6pos operator+(const e6pos& other){
        e6pos res;
        return res;
    }
};

struct E6AXIS {

	float	A1;
	float	A2;
	float	A3;
	float	A4;
	float	A5;
	float	A6;

};

class signal{
    bool* start_address;
    bool* end_address;
    signal(bool* pstart, bool* pend){
        start_address = pstart;
        end_address = pend;
    }

    signal(bool* pstart){
        start_address = pstart;
        end_address = pstart;
    }

    void operator = (int value){
        bool* address = start_address;
        while(address <= end_address){
            address = value & 1;
            address++;
        }
    }

    int operator = (){
        int res = 0;
        int index = 0;
        bool* address = start_address;
        while(address <= end_address){
            res = res | ((*address) << index);
            address++;
            index++;
        }
        return res;
    }

    void operator = (bool value){
        *start_address = value;
    }

    bool operator = (){
        return *start_address;
    }
};

/*
class generic_struct{
    def __init__(self, *args, **kwargs):
        for k,v in kwargs.items():
            if type(v) == float:
                kwargs[k] = real(v)

        self.__dict__.update(kwargs)
        
        //in the case where a structure (inheriting a generic_struct) gets as parameter a generic_struct
        // DECL JERK_STRUC DEF_JERK_STRUC={CP 500.000,ORI 50000.0,AX {A1 1000.00,A2 1000.00,A3 1000.00,A4 1000.00,A5 1000.00,A6 1000.00,E1 1000.00,E2 1000.00,E3 1000.00,E4 1000.00,E5 1000.00,E6 1000.00}} ; jerk value for the spline. CP: [m/Sec3], ORI: [[GRAD/Sec3], AX: [[GRAD/Sec3] (rotatory) resp. [m/Sec3] (linear)
        // def_jerk_struc = jerk_struc(generic_struct(cp=500.000,ori=50000.0,ax=generic_struct(a1=1000.00,a2=1000.00,a3=1000.00,a4=1000.00,a5=1000.00,a6=1000.00,e1=1000.00,e2=1000.00,e3=1000.00,e4=1000.00,e5=1000.00,e6=1000.00)))
        
        if not args is None and len(args) > 0:
            if issubclass(type(args[0]),generic_struct):
                self.__dict__.update(args[0].__dict__)
    
    //geometric addition
    def __add__(self, other):
        // Tests on robot
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 90, B 0, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 90, C 0}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 90}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 90, B 90, C 90}:{X 1, Y 2, Z 3, A 0, B 0, C 0}))
        //    result
        //    {X 11.000000, Y 22.000000, Z 33.000000, A 0.000000, B 0.000000, C 0.000000} 
        //    {X 8.000000, Y 21.000000, Z 33.000000, A 90.000000, B 0.000000, C 0.000000} 
        //    {X 13.000000, Y 22.000000, Z 29.000000, A 0.000000, B 90.000000, C 0.000000} 
        //    {X 11.000000, Y 17.000000, Z 32.000000, A 0.000000, B 0.000000, C 90.000000} 
        //    {X 13.000000, Y 22.000000, Z 29.000000, A 0.000000, B 90.000000, C 0.000000} 
        
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

        
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 90, B 0, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 90, C 0}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 0, B 0, C 90}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
        //    LOG(PTOS({X 10, Y 20, Z 30, A 90, B 90, C 90}:{X 1, Y 2, Z 3, A 10, B 20, C 30}))
        //    result
        //    {X 11.000000, Y 22.000000, Z 33.000000, A 10.000000, B 20.000000, C 30.000000} 
        //    {X 8.000000, Y 21.000000, Z 33.000000, A 100.000000, B 20.000000, C 30.000000} 
        //    {X 13.000000, Y 22.000000, Z 29.000000, A 154.000000, B 67.7312, C -177.273000} 
        //    {X 11.000000, Y 17.000000, Z 32.000000, A 20.283, B -9.3912, C 116.548} 
        //    {X 13.000000, Y 22.000000, Z 29.000000, A 154.494, B 67.7312, C -177.273} 
        
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
}
*/
/*
template <class T>
class multi_dimensional_array{
    T* values;
    int size;
    
    multi_dimensional_array(self, size):
        self.size = size[0]
        self._type = _type

        if len(size)>1:
            #self.data = krl_list([multi_dimensional_array(_type, size[1:]) for x in range(0, size[0])])
            self.data = []
            for i in range(0, size[0]):
                self.data.append(multi_dimensional_array(_type, size[1:]))
        else:
            #self.data = krl_list([_type()]*size[0])
            self.data = []
            for i in range(0, size[0]):
                self.data.append(_type())
        
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
        if issubclass(type(value), generic_struct):
            self.data.set_value(value)
            return
        for i in range(0, len(value)):
            self.data[i] = value[i]
    
*/


int global_timers_count = 64;

bool DOLLAR__inputs[4096] = {false};
bool DOLLAR__outputs[4096] = {false};


//this is referenced in $operate.dat, I don't know the right definition
typedef int call_stack;


bool interrupt_flags[128] = {false};
class InterruptData{
    typedef std::function<bool()> callback;
    callback fcond;
    callback fcall;

    InterruptData(callback cond, callback call){
        fcond = cond;
        fcall = call;
    }
};

InterruptData interrupts[128];

//to implement kinematics refer to https://ros-planning.github.io/moveit_tutorials/doc/getting_started/getting_started.html
// or https://github.com/siddikui/Kuka-KR210-Kinematics
// or https://github.com/Peroulis/6DOF-KUKA

class Robot(){
    bool _do_not_stop_ADVANCE_on_next_IO;

    bool internal_stop_flag;
    
    int interrupt_actually_triggered;

    thread clock_thread;
    /*
    RDK = None
    rdk_available = False
    rdk_robot = None
    */

    //module_operate_r1 = None

    Robot(){
        internal_stop_flag = false;
        clock_thread = thread(this->clock);
        /*
        try:
            self.RDK = Robolink()
            self.rdk_robot = self.RDK.ItemUserPick('Select a robot',ITEM_TYPE_ROBOT)
            self.rdk_available = self.rdk_robot.Valid()
            if not self.rdk_robot.Valid():
                print("RoboDK not available. Robot not selected or not valid")
            else:
                pose = self.rdk_robot.Pose()
                pos = Pose_2_KUKA(pose)
                DOLLAR__pos_act.x=pos[0]
                DOLLAR__pos_act.y=pos[1]
                DOLLAR__pos_act.z=pos[2]
                DOLLAR__pos_act.a=pos[3]
                DOLLAR__pos_act.b=pos[4]
                DOLLAR__pos_act.c=pos[5]

                DOLLAR__axis_act.a1 = self.rdk_robot.Joints().tolist()[0]
                DOLLAR__axis_act.a2 = self.rdk_robot.Joints().tolist()[1]
                DOLLAR__axis_act.a3 = self.rdk_robot.Joints().tolist()[2]
                DOLLAR__axis_act.a4 = self.rdk_robot.Joints().tolist()[3]
                DOLLAR__axis_act.a5 = self.rdk_robot.Joints().tolist()[4]
                DOLLAR__axis_act.a6 = self.rdk_robot.Joints().tolist()[5]
                print("POS_ACT: " + str(DOLLAR__pos_act))
                print("AXIS_ACT: " + str(DOLLAR__axis_act))
        except:
            print("RoboDK API not installed for the current python version")
            traceback.print_exc()
        */
    }

    ~Robot(){
        internal_stop_flag = true;
        clock_thread.join();
    }

    void clock(){
        while( !this->internal_stop_flag ){
            for(int i = 0; i < global_timers_count; i++){
                if( !DOLLAR__timer_stop[i] ){
                    DOLLAR__timer[i] = DOLLAR__timer[i] + 1;
                }
            }
            sleep(0.001);
        }    
    }

    void resume_interrupt(){
        //this generate a KeyboardInterrupt to the main thread (the one that executes the robot program)
        // the KeyboardInterrupt is correctly handled in interruptable_function_decorator
        // to make it possible resume the thread at the correct point WOOOOW
        _thread.interrupt_main();
    }

    void wait_sec(flaot t){
        sleep(t);
    }

    void do_not_stop_ADVANCE_on_next_IO(){
        _do_not_stop_ADVANCE_on_next_IO = true;
    }

    void ptp(e6pos position, bool apo=false){
        /*
        if( self.rdk_available ){
            self.rdk_robot.setSpeedJoints(DOLLAR__vel_axis[0])
            self.rdk_robot.setAccelerationJoints(DOLLAR__acc_axis[0])
            self.rdk_robot.MoveJ([position.a1, position.a2, position.a3, position.a4, position.a5, position.a6])
        }
        */
        printf("PTP \n"); //%s %s"%(position, apo))
    }

    void lin(e6pos position, bool apo=false){
        /*
        if self.rdk_available:
            self.rdk_robot.setSpeed(speed_linear=DOLLAR__vel.cp*1000, accel_linear=DOLLAR__acc.cp*1000)
            self.rdk_robot.setPoseFrame(KUKA_2_Pose([DOLLAR__base.x, DOLLAR__base.y, DOLLAR__base.z, DOLLAR__base.a, DOLLAR__base.b, DOLLAR__base.c]))
            print(">>>>>>setPoseFrame:" + str(DOLLAR__base))
            self.rdk_robot.setPoseTool(KUKA_2_Pose([DOLLAR__tool.x, DOLLAR__tool.y, DOLLAR__tool.z, DOLLAR__tool.a, DOLLAR__tool.b, DOLLAR__tool.c]))
            print(">>>>>>setPoseTool:" + str(DOLLAR__tool))
            self.rdk_robot.MoveL(KUKA_2_Pose([position.x, position.y, position.z, position.a, position.b, position.c]))
        */
        printf("LIN \n"); //%s %s"%(position, apo))
    }

    void ptp_rel(e6pos position, bool apo=false){
        printf("PTP_REL \n");//%s %s"%(position, apo))
    }

    void lin_rel(e6pos position, bool apo=false){
        printf("LIN_REL \n"); //%s %s"%(position, apo))
    }

    void circ(e6pos position, bool apo=false){
        printf("CIRC \n"); //%s %s"%(position, apo))
    }
};

Robot robot();


/*
"""
STRUC PRO_IP CHAR NAME[32],INT SNR,CHAR NAME_C[32],INT SNR_C,CHAR NAME_C_TRL[32],INT SNR_C_TRL,BOOL I_EXECUTED,INT P_ARRIVED,CHAR P_NAME[24],CALL_STACK SI01,SI02,SI03,SI04,SI05,SI06,SI07,SI08,SI09,SI10

name[]      Name of the module in which the interpreter is in the advance run
snr         Number of the block in which the interpreter is in the advance run (usually not equal to the line number of the program)
name_c[]    Name of the module in which the interpolator is in the main run
snr_c       Number of the block in which the interpolator is in the main run
i_executed  Indicates whether the block has already been executed by the interpreter (= TRUE) 
p_arrived   Indicates where the robot is located on the path (only relevant for motion instructions)
# 0: Arrived at the target or auxiliary point of the motion
# 1: Target point not reached, i.e. robot is somewhere on the path
# 2: Not relevant
# 3: Arrived at the auxiliary point of a CIRC or SCIRC motion
# 4: On the move in the section between the start and the auxiliary point
p_name[]    Name or aggregate of the target or auxiliary point at which the robot is located
SI01 … SI10 Caller stack in which the interpreter is situated
"""

#STRUC PROG_INFO CHAR SEL_NAME[32],PRO_STATE P_STATE,PRO_MODE P_MODE,CHAR PRO_IP_NAME[32],INT PRO_IP_SNR
# SEL_NAME name of the selected program
# PRO_IP_NAME[] name of the current module
# PRO_IP_SNR current block in the current module
*/

/*
submit_interpreter_thread = None
robot_interpreter_thread = None
*/

/*
threads_callstack = {} #thread:functionpointer[]
threads_callstack[threading.currentThread] = []
#def get_current_pro_ip():
#    if threading.currentThread == submit_interpreter_thread:
#        return DOLLAR_pro_ip0
#    return DOLLAR_pro_ip1
*/
