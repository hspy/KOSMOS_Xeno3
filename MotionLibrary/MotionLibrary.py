import os
import shutil
from POULibrary import POULibrary

def GetLocalPath(filename):
    return os.path.join(os.path.split(__file__)[0], filename) 

Headers="""
    int __MK_Init();
    void __MK_Cleanup();
    void __MK_Retrieve();
    void __MK_Publish();
    void __MK_ComputeAxis(int);
    
    typedef enum {
        mc_mode_none, // No motion mode
        mc_mode_csp,  // Continuous Synchronous Positionning mode
        mc_mode_csv,  // Continuous Synchronous Velocity mode
        mc_mode_cst,  // Continuous Synchronous Torque mode
    } mc_axismotionmode_enum;
    
    typedef struct {
       IEC_BOOL Power;
       IEC_BOOL CommunicationReady;
       IEC_UINT NetworkPosition;
       IEC_BOOL ReadyForPowerOn;
       IEC_BOOL PowerFeedback;
       IEC_BOOL HomingCompleted;
       IEC_UINT ErrorCode;
       IEC_DWORD DigitalInputs;
       IEC_DWORD DigitalOutputs;
       IEC_WORD TouchProbeFunction;
       IEC_WORD TouchProbeStatus;
       IEC_DINT TouchProbePos1PosValue;
       IEC_DINT TouchProbePos1NegValue;
       IEC_DINT ActualRawPosition;
       IEC_DINT ActualRawVelocity;
       IEC_DINT ActualRawTorque;
       IEC_DINT RawPositionSetPoint;
       IEC_DINT RawVelocitySetPoint;
       IEC_DINT RawTorqueSetPoint;
       mc_axismotionmode_enum AxisMotionMode;
       /*PLCopen TC2 parameters (MC_{Read,Write}{,Bool}Parameter)*/
       IEC_LREAL CommandedPosition; /*Commanded position (#1,R)*/
       IEC_LREAL SWLimitPos; /*Positive Software limit switch position (#2,R/W)*/
       IEC_LREAL SWLimitNeg; /*Negative Software limit switch position (#3,R/W)*/
       IEC_BOOL EnableLimitPos; /*Enable positive software limit switch (#4,R/W)*/
       IEC_BOOL EnableLimitNeg; /*Enable negative software limit switch (#5,R/W)*/
       IEC_BOOL EnablePosLagMonitoring; /*Enable monitoring of position lag (#6,R/W)*/
       IEC_LREAL MaxPositionLag; /*Maximal position lag (#7,R/W)*/
       IEC_LREAL MaxVelocitySystem; /*Maximal allowed velocity of the axis in the motion system (#8,R)*/
       IEC_LREAL MaxVelocityAppl; /*Maximal allowed velocity of the axis in the application (#9,R/W)*/
       IEC_LREAL ActualVelocity; /*Actual velocity (#10,R)*/
       IEC_LREAL CommandedVelocity; /*Commanded velocity (#11,R)*/
       IEC_LREAL MaxAccelerationSystem; /*Maximal allowed acceleration of the axis in themotion system (#12,R)*/
       IEC_LREAL MaxAccelerationAppl; /*Maximal allowed acceleration of the axis in theapplication (#13,R/W)*/
       IEC_LREAL MaxDecelerationSystem; /*Maximal allowed deceleration of the axis in themotion system (#14,R)*/
       IEC_LREAL MaxDecelerationAppl; /*Maximal allowed deceleration of the axis in theapplication (#15,R/W)*/
       IEC_LREAL MaxJerkSystem; /*Maximum allowed jerk of the axis in the motionsystem (#16,R)*/
       IEC_LREAL MaxJerkAppl; /*Maximum allowed jerk of the axis in the application (#17,R/W)*/
       IEC_BOOL Simulation; /*Simulation Mode (#1000,R/W)*/
       IEC_LREAL PositionSetPoint; /*Position SetPoint (#1001,R)*/
       IEC_LREAL VelocitySetPoint; /*Velocity SetPoint (#1002,R)*/
       IEC_LREAL RatioNumerator; /*Drive_Unit = PLCopen_Unit * RatioNumerator / RatioDenominator (#1003,R/W)*/
       IEC_LREAL RatioDenominator; /*Drive_Unit = PLCopen_Unit * RatioNumerator / RatioDenominator (#1004,R/W)*/
       IEC_LREAL PositionOffset; /*SentPosition = (PositionSepoint + PosotionOffset) * RatioNumerator / RatioDenominator (#1005,R/W)*/
       IEC_BOOL LimitSwitchNC; /*Set if limit switches are normaly closed (#1006,R/W)*/
       IEC_LREAL ActualPosition; /*Position from drive, scaled but without offset. (#1008,R)*/
       IEC_LREAL HomingLimitWindow; /*Distance at which soft limit is alredy valid during homing (#1009,R/W)*/
       IEC_LREAL HomingVelocity; /*Velocity applied on drive while homing (#1010,R/W)*/
       IEC_LREAL TorqueSetPoint; /*Torque SetPoint (#1011,R)*/
       IEC_LREAL ActualTorque; /*Torque from drive scaled (#1012,R)*/
       IEC_LREAL TorqueRatioNumerator; /*Drive_Unit = PLCopen_Unit * TorqueRatioNumerator / TorqueRatioDenominator (#1013,R/W)*/
       IEC_LREAL TorqueRatioDenominator; /*Drive_Unit = PLCopen_Unit * TorqueRatioNumerator / TorqueRatioDenominator (#1014,R/W)*/
       void (*__mcl_func_MC_GetTorqueLimit)(MC_GETTORQUELIMIT *data__);
       void (*__mcl_func_MC_SetTorqueLimit)(MC_SETTORQUELIMIT *data__);
    }axis_s;
    
    typedef struct {
      double x;
      double y;
    } point2d_s;
    
    typedef struct {
      int count;
      point2d_s *points;
    } array2d_s;
    #define __LINKAGE_TYPE_TCP 0
    #define __LINKAGE_TYPE_REVOLUTE 1
    #define __LINKAGE_TYPE_PRISMATIC 2
    
    typedef struct {
      double Tx;
      double Ty;
      double Tz;
      double Rx;
      double Ry;
      double Rz;
      int type;
    } linkage_s;
    
    typedef struct {
      int count;
      linkage_s *linkages;
    } kinematic_chain_s;
    
    typedef double mc_matrix_s[9];
    
    typedef struct {
       MC_REAL_ARRAY transform;
       mc_matrix_s forward_rotation;
       mc_matrix_s backward_rotation;
    } cartesian_transform_s;
    
    typedef struct {
       kinematic_chain_s KinTransform;
       cartesian_transform_s CartesianTransform;
    } group_s;
    
    
    int __MK_Alloc_AXIS_REF();
    axis_s* __MK_GetPublic_AXIS_REF(int index);
    int __MK_CheckPublicValid_AXIS_REF(int index);
    void __MK_Set_AXIS_REF_Pos(int index, int pos);
    int __MK_Get_AXIS_REF_Pos(int index);
    int __MK_Alloc_MC_TP_REF();
    array2d_s* __MK_GetPublic_MC_TP_REF(int index);
    int __MK_CheckPublicValid_MC_TP_REF(int index);
    int __MK_Alloc_MC_TV_REF();
    array2d_s* __MK_GetPublic_MC_TV_REF(int index);
    int __MK_CheckPublicValid_MC_TV_REF(int index);
    int __MK_Alloc_MC_TA_REF();
    array2d_s* __MK_GetPublic_MC_TA_REF(int index);
    int __MK_CheckPublicValid_MC_TA_REF(int index);
    int __MK_Alloc_MC_CAMSWITCH_REF();
    int __MK_Alloc_MC_TRACK_REF();
    int __MK_Alloc_MC_TRIGGER_REF();
    uint8_t* __MK_GetPublic_MC_TRIGGER_REF(int index);
    int __MK_CheckPublicValid_MC_TRIGGER_REF(int index);
    int __MK_Alloc_MC_CAM_REF();
    array2d_s* __MK_GetPublic_MC_CAM_REF(int index);
    int __MK_CheckPublicValid_MC_CAM_REF(int index);
    int __MK_Alloc_MC_CAM_ID();
    int __MK_Alloc_AXES_GROUP_REF();
    group_s* __MK_GetPublic_AXES_GROUP_REF(int index);
    int __MK_CheckPublicValid_AXES_GROUP_REF(int index);
    int __MK_Alloc_IDENT_IN_GROUP_REF();
    int* __MK_GetPublic_IDENT_IN_GROUP_REF(int index);
    int __MK_CheckPublicValid_IDENT_IN_GROUP_REF(int index);
    int __MK_Alloc_MC_KIN_REF();
    kinematic_chain_s* __MK_GetPublic_MC_KIN_REF(int index);
    int __MK_CheckPublicValid_MC_KIN_REF(int index);
    int __MK_Alloc_MC_COORD_REF();
    MC_REAL_ARRAY* __MK_GetPublic_MC_COORD_REF(int index);
    int __MK_CheckPublicValid_MC_COORD_REF(int index);
    int __MK_Alloc_MC_PATH_DATA_REF();
    int __MK_Alloc_MC_PATH_REF();
"""

AxisXSD="""
 <!-- Positive Software limit switch position (#2,R/W) -->
 <xsd:attribute name="SWLimitPos" type="xsd:float" use="optional" />
 <!-- Negative Software limit switch position (#3,R/W) -->
 <xsd:attribute name="SWLimitNeg" type="xsd:float" use="optional" />
 <!-- Enable positive software limit switch (#4,R/W) -->
 <xsd:attribute name="EnableLimitPos" type="xsd:boolean" use="optional" />
 <!-- Enable negative software limit switch (#5,R/W) -->
 <xsd:attribute name="EnableLimitNeg" type="xsd:boolean" use="optional" />
 <!-- Enable monitoring of position lag (#6,R/W) -->
 <xsd:attribute name="EnablePosLagMonitoring" type="xsd:boolean" use="optional" />
 <!-- Maximal position lag (#7,R/W) -->
 <xsd:attribute name="MaxPositionLag" type="xsd:float" use="optional" />
 <!-- Maximal allowed velocity of the axis in the application (#9,R/W) -->
 <xsd:attribute name="MaxVelocityAppl" type="xsd:float" use="optional" />
 <!-- Maximal allowed acceleration of the axis in theapplication (#13,R/W) -->
 <xsd:attribute name="MaxAccelerationAppl" type="xsd:float" use="optional" />
 <!-- Maximal allowed deceleration of the axis in theapplication (#15,R/W) -->
 <xsd:attribute name="MaxDecelerationAppl" type="xsd:float" use="optional" />
 <!-- Maximum allowed jerk of the axis in the application (#17,R/W) -->
 <xsd:attribute name="MaxJerkAppl" type="xsd:float" use="optional" />
 <!-- Simulation Mode (#1000,R/W) -->
 <xsd:attribute name="Simulation" type="xsd:boolean" use="optional" />
 <!-- Drive_Unit = PLCopen_Unit * RatioNumerator / RatioDenominator (#1003,R/W) -->
 <xsd:attribute name="RatioNumerator" type="xsd:float" use="optional" default="65536.0"/>
 <!-- Drive_Unit = PLCopen_Unit * RatioNumerator / RatioDenominator (#1004,R/W) -->
 <xsd:attribute name="RatioDenominator" type="xsd:float" use="optional" default="360.0"/>
 <!-- SentPosition = (PositionSepoint + PosotionOffset) * RatioNumerator / RatioDenominator (#1005,R/W) -->
 <xsd:attribute name="PositionOffset" type="xsd:float" use="optional" default="0.0"/>
 <!-- Set if limit switches are normaly closed (#1006,R/W) -->
 <xsd:attribute name="LimitSwitchNC" type="xsd:boolean" use="optional" default="0"/>
 <!-- Distance at which soft limit is alredy valid during homing (#1009,R/W) -->
 <xsd:attribute name="HomingLimitWindow" type="xsd:float" use="optional" default="10.0"/>
 <!-- Velocity applied on drive while homing (#1010,R/W) -->
 <xsd:attribute name="HomingVelocity" type="xsd:float" use="optional" default="360.0"/>
 <!-- Drive_Unit = PLCopen_Unit * TorqueRatioNumerator / TorqueRatioDenominator (#1013,R/W) -->
 <xsd:attribute name="TorqueRatioNumerator" type="xsd:float" use="optional" default="10.0"/>
 <!-- Drive_Unit = PLCopen_Unit * TorqueRatioNumerator / TorqueRatioDenominator (#1014,R/W) -->
 <xsd:attribute name="TorqueRatioDenominator" type="xsd:float" use="optional" default="1.0"/>
"""

class MotionLibrary(POULibrary):

    def GetLibraryPath(self):
        return GetLocalPath("pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        targetname = self.GetCTR().GetTarget().getcontent()["name"]
        kernel_file = "MotionKernel"+targetname+".o"
        kernel_file_path = os.path.join(os.path.split(__file__)[0], kernel_file)
        c_file_path = os.path.join(os.path.split(__file__)[0], "motion.c")
        c_file = open(c_file_path, 'r')
        c_code = c_file.read()
        c_file.close()

        c_code = c_code % {"headers": Headers}

        gen_c_file_path = os.path.join(buildpath, "motion.c")
        gen_c_file = open(gen_c_file_path,'w')
        gen_c_file.write(c_code)
        gen_c_file.close()

        return ((["motion"], [(gen_c_file_path, IECCFLAGS),(kernel_file_path, "")], True), "-lm",
            ("runtime_motion.py", file(GetLocalPath("MotionHelpers.py"))))
