#include "beremiz.h"
#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"

__DECLARE_ENUMERATED_TYPE(LOGLEVEL,
  LOGLEVEL__CRITICAL,
  LOGLEVEL__WARNING,
  LOGLEVEL__INFO,
  LOGLEVEL__DEBUG
)

// FUNCTION_BLOCK R_TRIG
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CLK)
  __DECLARE_VAR(BOOL,Q)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,M)

} R_TRIG;

// FUNCTION_BLOCK F_TRIG
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CLK)
  __DECLARE_VAR(BOOL,Q)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,M)

} F_TRIG;

// FUNCTION_BLOCK SR
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,S1)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,Q1)

  // FB private variables - TEMP, private and located variables

} SR;

// FUNCTION_BLOCK RS
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,S)
  __DECLARE_VAR(BOOL,R1)
  __DECLARE_VAR(BOOL,Q1)

  // FB private variables - TEMP, private and located variables

} RS;

// FUNCTION_BLOCK CTU
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(INT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(INT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CU_T;

} CTU;

// FUNCTION_BLOCK CTU_DINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(DINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(DINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CU_T;

} CTU_DINT;

// FUNCTION_BLOCK CTU_LINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(LINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(LINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CU_T;

} CTU_LINT;

// FUNCTION_BLOCK CTU_UDINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(UDINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(UDINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CU_T;

} CTU_UDINT;

// FUNCTION_BLOCK CTU_ULINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(ULINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(ULINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CU_T;

} CTU_ULINT;

// FUNCTION_BLOCK CTD
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(INT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(INT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;

} CTD;

// FUNCTION_BLOCK CTD_DINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(DINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(DINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;

} CTD_DINT;

// FUNCTION_BLOCK CTD_LINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(LINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(LINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;

} CTD_LINT;

// FUNCTION_BLOCK CTD_UDINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(UDINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(UDINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;

} CTD_UDINT;

// FUNCTION_BLOCK CTD_ULINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(ULINT,PV)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(ULINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;

} CTD_ULINT;

// FUNCTION_BLOCK CTUD
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(INT,PV)
  __DECLARE_VAR(BOOL,QU)
  __DECLARE_VAR(BOOL,QD)
  __DECLARE_VAR(INT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;
  R_TRIG CU_T;

} CTUD;

// FUNCTION_BLOCK CTUD_DINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(DINT,PV)
  __DECLARE_VAR(BOOL,QU)
  __DECLARE_VAR(BOOL,QD)
  __DECLARE_VAR(DINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;
  R_TRIG CU_T;

} CTUD_DINT;

// FUNCTION_BLOCK CTUD_LINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(LINT,PV)
  __DECLARE_VAR(BOOL,QU)
  __DECLARE_VAR(BOOL,QD)
  __DECLARE_VAR(LINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;
  R_TRIG CU_T;

} CTUD_LINT;

// FUNCTION_BLOCK CTUD_UDINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(UDINT,PV)
  __DECLARE_VAR(BOOL,QU)
  __DECLARE_VAR(BOOL,QD)
  __DECLARE_VAR(UDINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;
  R_TRIG CU_T;

} CTUD_UDINT;

// FUNCTION_BLOCK CTUD_ULINT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CU)
  __DECLARE_VAR(BOOL,CD)
  __DECLARE_VAR(BOOL,R)
  __DECLARE_VAR(BOOL,LD)
  __DECLARE_VAR(ULINT,PV)
  __DECLARE_VAR(BOOL,QU)
  __DECLARE_VAR(BOOL,QD)
  __DECLARE_VAR(ULINT,CV)

  // FB private variables - TEMP, private and located variables
  R_TRIG CD_T;
  R_TRIG CU_T;

} CTUD_ULINT;

// FUNCTION_BLOCK TP
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,IN)
  __DECLARE_VAR(TIME,PT)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(TIME,ET)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,STATE)
  __DECLARE_VAR(BOOL,PREV_IN)
  __DECLARE_VAR(TIME,CURRENT_TIME)
  __DECLARE_VAR(TIME,START_TIME)

} TP;

// FUNCTION_BLOCK TON
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,IN)
  __DECLARE_VAR(TIME,PT)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(TIME,ET)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,STATE)
  __DECLARE_VAR(BOOL,PREV_IN)
  __DECLARE_VAR(TIME,CURRENT_TIME)
  __DECLARE_VAR(TIME,START_TIME)

} TON;

// FUNCTION_BLOCK TOF
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,IN)
  __DECLARE_VAR(TIME,PT)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(TIME,ET)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,STATE)
  __DECLARE_VAR(BOOL,PREV_IN)
  __DECLARE_VAR(TIME,CURRENT_TIME)
  __DECLARE_VAR(TIME,START_TIME)

} TOF;

// FUNCTION_BLOCK DERIVATIVE
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,RUN)
  __DECLARE_VAR(REAL,XIN)
  __DECLARE_VAR(TIME,CYCLE)
  __DECLARE_VAR(REAL,XOUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,X1)
  __DECLARE_VAR(REAL,X2)
  __DECLARE_VAR(REAL,X3)

} DERIVATIVE;

// FUNCTION_BLOCK HYSTERESIS
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(REAL,XIN1)
  __DECLARE_VAR(REAL,XIN2)
  __DECLARE_VAR(REAL,EPS)
  __DECLARE_VAR(BOOL,Q)

  // FB private variables - TEMP, private and located variables

} HYSTERESIS;

// FUNCTION_BLOCK INTEGRAL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,RUN)
  __DECLARE_VAR(BOOL,R1)
  __DECLARE_VAR(REAL,XIN)
  __DECLARE_VAR(REAL,X0)
  __DECLARE_VAR(TIME,CYCLE)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(REAL,XOUT)

  // FB private variables - TEMP, private and located variables

} INTEGRAL;

// FUNCTION_BLOCK PID
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,AUTO)
  __DECLARE_VAR(REAL,PV)
  __DECLARE_VAR(REAL,SP)
  __DECLARE_VAR(REAL,X0)
  __DECLARE_VAR(REAL,KP)
  __DECLARE_VAR(REAL,TR)
  __DECLARE_VAR(REAL,TD)
  __DECLARE_VAR(TIME,CYCLE)
  __DECLARE_VAR(REAL,XOUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,ERROR)
  INTEGRAL ITERM;
  DERIVATIVE DTERM;

} PID;

// FUNCTION_BLOCK RAMP
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,RUN)
  __DECLARE_VAR(REAL,X0)
  __DECLARE_VAR(REAL,X1)
  __DECLARE_VAR(TIME,TR)
  __DECLARE_VAR(TIME,CYCLE)
  __DECLARE_VAR(BOOL,BUSY)
  __DECLARE_VAR(REAL,XOUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(REAL,XI)
  __DECLARE_VAR(TIME,T)

} RAMP;

// FUNCTION_BLOCK RTC
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,IN)
  __DECLARE_VAR(DT,PDT)
  __DECLARE_VAR(BOOL,Q)
  __DECLARE_VAR(DT,CDT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,PREV_IN)
  __DECLARE_VAR(TIME,OFFSET)
  __DECLARE_VAR(DT,CURRENT_TIME)

} RTC;

// FUNCTION_BLOCK SEMA
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CLAIM)
  __DECLARE_VAR(BOOL,RELEASE)
  __DECLARE_VAR(BOOL,BUSY)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,Q_INTERNAL)

} SEMA;

// FUNCTION_BLOCK LOGGER
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,TRIG)
  __DECLARE_VAR(STRING,MSG)
  __DECLARE_VAR(LOGLEVEL,LEVEL)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,TRIG0)

} LOGGER;

// FUNCTION_BLOCK PYTHON_EVAL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,TRIG)
  __DECLARE_VAR(STRING,CODE)
  __DECLARE_VAR(BOOL,ACK)
  __DECLARE_VAR(STRING,RESULT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(DWORD,STATE)
  __DECLARE_VAR(STRING,BUFFER)
  __DECLARE_VAR(STRING,PREBUFFER)
  __DECLARE_VAR(BOOL,TRIGM1)
  __DECLARE_VAR(BOOL,TRIGGED)

} PYTHON_EVAL;

// FUNCTION_BLOCK PYTHON_POLL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,TRIG)
  __DECLARE_VAR(STRING,CODE)
  __DECLARE_VAR(BOOL,ACK)
  __DECLARE_VAR(STRING,RESULT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(DWORD,STATE)
  __DECLARE_VAR(STRING,BUFFER)
  __DECLARE_VAR(STRING,PREBUFFER)
  __DECLARE_VAR(BOOL,TRIGM1)
  __DECLARE_VAR(BOOL,TRIGGED)

} PYTHON_POLL;

// FUNCTION_BLOCK PYTHON_GEAR
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(USINT,N)
  __DECLARE_VAR(BOOL,TRIG)
  __DECLARE_VAR(STRING,CODE)
  __DECLARE_VAR(BOOL,ACK)
  __DECLARE_VAR(STRING,RESULT)

  // FB private variables - TEMP, private and located variables
  PYTHON_EVAL PY_EVAL;
  __DECLARE_VAR(USINT,COUNTER)
  __DECLARE_VAR(USINT,ADD10_OUT)
  __DECLARE_VAR(BOOL,EQ13_OUT)
  __DECLARE_VAR(USINT,SEL15_OUT)
  __DECLARE_VAR(BOOL,AND7_OUT)

} PYTHON_GEAR;

// FUNCTION_BLOCK GETBOOLSTRING
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,VALUE)
  __DECLARE_VAR(STRING,CODE)

  // FB private variables - TEMP, private and located variables

} GETBOOLSTRING;

// FUNCTION_BLOCK BUTTON
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,BACK_ID)
  __DECLARE_VAR(STRING,SELE_ID)
  __DECLARE_VAR(BOOL,TOGGLE)
  __DECLARE_VAR(BOOL,SET_STATE)
  __DECLARE_VAR(BOOL,STATE_IN)
  __DECLARE_VAR(BOOL,STATE_OUT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(STRING,ID)
  PYTHON_EVAL INIT_COMMAND;
  GETBOOLSTRING GETBUTTONSTATE;
  PYTHON_EVAL SETSTATE_COMMAND;
  PYTHON_POLL GETSTATE_COMMAND;
  GETBOOLSTRING GETBUTTONTOGGLE;
  __DECLARE_VAR(STRING,CONCAT2_OUT)
  __DECLARE_VAR(STRING,CONCAT22_OUT)
  __DECLARE_VAR(INT,STRING_TO_INT25_OUT)
  __DECLARE_VAR(BOOL,INT_TO_BOOL26_OUT)
  __DECLARE_VAR(BOOL,AND31_OUT)
  __DECLARE_VAR(STRING,CONCAT7_OUT)

} BUTTON;

// FUNCTION_BLOCK LED
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,BACK_ID)
  __DECLARE_VAR(STRING,SELE_ID)
  __DECLARE_VAR(BOOL,STATE_IN)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(STRING,ID)
  PYTHON_EVAL INIT_COMMAND;
  PYTHON_POLL SETSTATE_COMMAND;
  GETBOOLSTRING GETLEDSTATE;
  __DECLARE_VAR(STRING,CONCAT2_OUT)
  __DECLARE_VAR(STRING,CONCAT7_OUT)

} LED;

// FUNCTION_BLOCK TEXTCTRL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,BACK_ID)
  __DECLARE_VAR(BOOL,SET_TEXT)
  __DECLARE_VAR(STRING,TEXT)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(STRING,ID)
  PYTHON_EVAL SVGUI_TEXTCTRL;
  PYTHON_EVAL SETSTATE_COMMAND;
  __DECLARE_VAR(STRING,CONCAT1_OUT)
  __DECLARE_VAR(BOOL,AND31_OUT)
  __DECLARE_VAR(STRING,CONCAT12_OUT)

} TEXTCTRL;

// PROGRAM PROGRAM0
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_VAR(INT,LOCALVAR0)
  __DECLARE_VAR(INT,ADD1_OUT)

} PROGRAM0;

#endif //__POUS_H
