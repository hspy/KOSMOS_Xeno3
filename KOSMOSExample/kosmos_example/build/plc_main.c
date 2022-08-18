/**
 * Head of code common to all C targets
 **/

#include "beremiz.h"
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <stdlib.h>
#include <native/timer.h>


/*
 * Prototypes of functions provided by generated C softPLC
 **/
void config_run__(unsigned long tick);
void config_init__(void);

/*
 * Prototypes of functions provided by generated target C code
 * */
void __init_debug(void);
void __cleanup_debug(void);
/*void __retrieve_debug(void);*/
void __publish_debug(void);
FILE *ethercat_test;


/*
 *  Variables used by generated C softPLC and plugins
 **/
IEC_TIME __CURRENT_TIME;
IEC_BOOL __DEBUG = 0;
unsigned long __tick = 0;

/*
 *  Variable generated by C softPLC and plugins
 **/
extern unsigned long greatest_tick_count__;

/* Effective tick time with 1ms default value */
static long long Ttick = 1000000;

/* Help to quit cleanly when init fail at a certain level */
static int init_level = 0;

/*
 * Prototypes of functions exported by plugins
 **/
int __init_py_ext(int argc,char **argv);
void __cleanup_py_ext(void);
void __retrieve_py_ext(void);
void __publish_py_ext(void);

/*
 * Retrieve input variables, run PLC and publish output variables
 **/

double ethercat_time;
void __run(void)
{
    __tick++;
    if (greatest_tick_count__)
        __tick %= greatest_tick_count__;
	
	ethercat_time = rt_timer_read();

    __retrieve_py_ext();

    /*__retrieve_debug();*/

    config_run__(__tick);

    __publish_debug();

    __publish_py_ext();

}

/*
 * Initialize variables according to PLC's default values,
 * and then init plugins with that values
 **/
int __init(int argc,char **argv)
{
    int res = 0;
    init_level = 0;
    
	ethercat_test = fopen("./ethercat_cycle.csv", "w");

    if(common_ticktime__)
        Ttick = common_ticktime__;

    config_init__();
    __init_debug();
    init_level=1; if((res = __init_py_ext(argc,argv))){return res;}
    return res;
}
/*
 * Calls plugin cleanup proc.
 **/
void __cleanup(void)
{
    if(init_level >= 1) __cleanup_py_ext();
    __cleanup_debug();
}

void PLC_GetTime(IEC_TIME *CURRENT_TIME);
void PLC_SetTimer(unsigned long long next, unsigned long long period);



/**
 * Xenomai Linux specific code
 **/

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/fcntl.h>

#include <native/task.h>
#include <native/timer.h>
#include <native/mutex.h>
#include <native/sem.h>
#include <native/pipe.h>

unsigned int PLC_state = 0;
#define PLC_STATE_TASK_CREATED                 1
#define PLC_STATE_DEBUG_FILE_OPENED            2 
#define PLC_STATE_DEBUG_PIPE_CREATED           4 
#define PLC_STATE_PYTHON_FILE_OPENED           8 
#define PLC_STATE_PYTHON_PIPE_CREATED          16   
#define PLC_STATE_WAITDEBUG_FILE_OPENED        32   
#define PLC_STATE_WAITDEBUG_PIPE_CREATED       64
#define PLC_STATE_WAITPYTHON_FILE_OPENED       128
#define PLC_STATE_WAITPYTHON_PIPE_CREATED      256

#define WAITDEBUG_PIPE_DEVICE        "/dev/rtp0"
#define WAITDEBUG_PIPE_MINOR         0
#define DEBUG_PIPE_DEVICE            "/dev/rtp1"
#define DEBUG_PIPE_MINOR             1
#define WAITPYTHON_PIPE_DEVICE       "/dev/rtp2"
#define WAITPYTHON_PIPE_MINOR        2
#define PYTHON_PIPE_DEVICE           "/dev/rtp3"
#define PYTHON_PIPE_MINOR            3
#define PIPE_SIZE                    1 


long AtomicCompareExchange(long* atomicvar,long compared, long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}
long long AtomicCompareExchange64(long long* atomicvar, long long compared, long long exchange)
{
    return __sync_val_compare_and_swap(atomicvar, compared, exchange);
}

void PLC_GetTime(IEC_TIME *CURRENT_TIME)
{
    RTIME current_time = rt_timer_read();
    CURRENT_TIME->tv_sec = current_time / 1000000000;
    CURRENT_TIME->tv_nsec = current_time % 1000000000;
}

RT_TASK PLC_task;
RT_PIPE WaitDebug_pipe;
RT_PIPE WaitPython_pipe;
RT_PIPE Debug_pipe;
RT_PIPE Python_pipe;
int WaitDebug_pipe_fd;
int WaitPython_pipe_fd;
int Debug_pipe_fd;
int Python_pipe_fd;

int PLC_shutdown = 0;

void PLC_SetTimer(unsigned long long next, unsigned long long period)
{
  RTIME current_time = rt_timer_read();
  rt_task_set_periodic(&PLC_task, current_time + next, rt_timer_ns2ticks(period));
}

void PLC_task_proc(void *arg)
{
    PLC_SetTimer(Ttick, Ttick);

    while (!PLC_shutdown) {
        PLC_GetTime(&__CURRENT_TIME);
        __run();
        if (PLC_shutdown) break;
        rt_task_wait_period(NULL);
    }
}

static unsigned long __debug_tick;

void PLC_cleanup_all(void)
{
    if (PLC_state & PLC_STATE_TASK_CREATED) {
        rt_task_delete(&PLC_task);
        PLC_state &= ~PLC_STATE_TASK_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITDEBUG_PIPE_CREATED) {
        rt_pipe_delete(&WaitDebug_pipe);
        PLC_state &= ~PLC_STATE_WAITDEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITDEBUG_FILE_OPENED) {
        close(WaitDebug_pipe_fd);
        PLC_state &= ~PLC_STATE_WAITDEBUG_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_WAITPYTHON_PIPE_CREATED) {
        rt_pipe_delete(&WaitPython_pipe);
        PLC_state &= ~PLC_STATE_WAITPYTHON_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_WAITPYTHON_FILE_OPENED) {
        close(WaitPython_pipe_fd);
        PLC_state &= ~PLC_STATE_WAITPYTHON_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_DEBUG_PIPE_CREATED) {
        rt_pipe_delete(&Debug_pipe);
        PLC_state &= ~PLC_STATE_DEBUG_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_DEBUG_FILE_OPENED) {
        close(Debug_pipe_fd);
        PLC_state &= ~PLC_STATE_DEBUG_FILE_OPENED;
    }

    if (PLC_state & PLC_STATE_PYTHON_PIPE_CREATED) {
        rt_pipe_delete(&Python_pipe);
        PLC_state &= ~PLC_STATE_PYTHON_PIPE_CREATED;
    }

    if (PLC_state & PLC_STATE_PYTHON_FILE_OPENED) {
        close(Python_pipe_fd);
        PLC_state &= ~PLC_STATE_PYTHON_FILE_OPENED;
    }

}

int stopPLC()
{
    /* Stop the PLC */
    PLC_shutdown = 1;

    /* Wait until PLC task stops */
    rt_task_join(&PLC_task);

    PLC_cleanup_all();
    __cleanup();
    __debug_tick = -1;
    return 0;
}

//
void catch_signal(int sig)
{
    stopPLC();
//  signal(SIGTERM, catch_signal);
    signal(SIGINT, catch_signal);
    printf("Got Signal %d\n",sig);
    exit(0);
}

#define max_val(a,b) ((a>b)?a:b)
int startPLC(int argc,char **argv)
{
    signal(SIGINT, catch_signal);

    /* no memory swapping for that process */
    mlockall(MCL_CURRENT | MCL_FUTURE);

    PLC_shutdown = 0;

    /*** RT Pipes creation and opening ***/
    /* create Debug_pipe */
    if(rt_pipe_create(&Debug_pipe, "Debug_pipe", DEBUG_PIPE_MINOR, PIPE_SIZE)) 
        goto error;
    PLC_state |= PLC_STATE_DEBUG_PIPE_CREATED;

    /* open Debug_pipe*/
    if((Debug_pipe_fd = open(DEBUG_PIPE_DEVICE, O_RDWR)) == -1) goto error;
    PLC_state |= PLC_STATE_DEBUG_FILE_OPENED;

    /* create Python_pipe */
    if(rt_pipe_create(&Python_pipe, "Python_pipe", PYTHON_PIPE_MINOR, PIPE_SIZE)) 
        goto error;
    PLC_state |= PLC_STATE_PYTHON_PIPE_CREATED;

    /* open Python_pipe*/
    if((Python_pipe_fd = open(PYTHON_PIPE_DEVICE, O_RDWR)) == -1) goto error;
    PLC_state |= PLC_STATE_PYTHON_FILE_OPENED;

    /* create WaitDebug_pipe */
    if(rt_pipe_create(&WaitDebug_pipe, "WaitDebug_pipe", WAITDEBUG_PIPE_MINOR, PIPE_SIZE))
        goto error;
    PLC_state |= PLC_STATE_WAITDEBUG_PIPE_CREATED;

    /* open WaitDebug_pipe*/
    if((WaitDebug_pipe_fd = open(WAITDEBUG_PIPE_DEVICE, O_RDWR)) == -1) goto error;
    PLC_state |= PLC_STATE_WAITDEBUG_FILE_OPENED;

    /* create WaitPython_pipe */
    if(rt_pipe_create(&WaitPython_pipe, "WaitPython_pipe", WAITPYTHON_PIPE_MINOR, PIPE_SIZE))
        goto error;
    PLC_state |= PLC_STATE_WAITPYTHON_PIPE_CREATED;

    /* open WaitPython_pipe*/
    if((WaitPython_pipe_fd = open(WAITPYTHON_PIPE_DEVICE, O_RDWR)) == -1) goto error;
    PLC_state |= PLC_STATE_WAITPYTHON_FILE_OPENED;

    /*** create PLC task ***/
    if(rt_task_create(&PLC_task, "PLC_task", 0, 50, T_JOINABLE)) goto error;
    PLC_state |= PLC_STATE_TASK_CREATED;

    if(__init(argc,argv)) goto error;

    /* start PLC task */
    if(rt_task_start(&PLC_task, &PLC_task_proc, NULL)) goto error;

    return 0;

error:

    PLC_cleanup_all();
    return 1;
}

#define DEBUG_FREE 0
#define DEBUG_BUSY 1
static long debug_state = DEBUG_FREE;

int TryEnterDebugSection(void)
{
    if(AtomicCompareExchange(
        &debug_state,
        DEBUG_FREE,
        DEBUG_BUSY) == DEBUG_FREE){
        if(__DEBUG){
            return 1;
        }
        AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
    }
    return 0;
}

#define DEBUG_UNLOCK 1
void LeaveDebugSection(void)
{
    if(AtomicCompareExchange( &debug_state, 
        DEBUG_BUSY, DEBUG_FREE) == DEBUG_BUSY){
        char msg = DEBUG_UNLOCK;
        /* signal to NRT for wakeup */
        rt_pipe_write(&Debug_pipe, &msg, sizeof(msg), P_NORMAL);
    }
}

extern unsigned long __tick;

#define DEBUG_PENDING_DATA 1
int WaitDebugData(unsigned long *tick)
{
    char cmd;
    int res;
    if (PLC_shutdown) return -1;
    /* Wait signal from PLC thread */
    res = read(WaitDebug_pipe_fd, &cmd, sizeof(cmd));
    if (res == sizeof(cmd) && cmd == DEBUG_PENDING_DATA){
        *tick = __debug_tick;
        return 0;
    }
    return -1;
}

/* Called by PLC thread when debug_publish finished
 * This is supposed to unlock debugger thread in WaitDebugData*/
void InitiateDebugTransfer()
{
    char msg = DEBUG_PENDING_DATA;
    /* remember tick */
    __debug_tick = __tick;
    /* signal debugger thread it can read data */
    rt_pipe_write(&WaitDebug_pipe, &msg, sizeof(msg), P_NORMAL);
}

int suspendDebug(int disable)
{
    char cmd = DEBUG_UNLOCK;
    if (PLC_shutdown) return -1;
    while(AtomicCompareExchange(
            &debug_state,
            DEBUG_FREE,
            DEBUG_BUSY) != DEBUG_FREE &&
            cmd == DEBUG_UNLOCK){
       if(read(Debug_pipe_fd, &cmd, sizeof(cmd)) != sizeof(cmd)){
           return -1;
       }
    }
    __DEBUG = !disable;
    if (disable)
        AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
    return 0;
}

void resumeDebug(void)
{
    AtomicCompareExchange( &debug_state, DEBUG_BUSY, DEBUG_FREE);
}

#define PYTHON_PENDING_COMMAND 1

#define PYTHON_FREE 0
#define PYTHON_BUSY 1
static long python_state = PYTHON_FREE;

int WaitPythonCommands(void)
{ 
    char cmd;
    if (PLC_shutdown) return -1;
    /* Wait signal from PLC thread */
    if(read(WaitPython_pipe_fd, &cmd, sizeof(cmd))==sizeof(cmd) && cmd==PYTHON_PENDING_COMMAND){
        return 0;
    }
    return -1;
}

/* Called by PLC thread on each new python command*/
void UnBlockPythonCommands(void)
{
    char msg = PYTHON_PENDING_COMMAND;
    rt_pipe_write(&WaitPython_pipe, &msg, sizeof(msg), P_NORMAL);
}

int TryLockPython(void)
{
    return AtomicCompareExchange(
        &python_state,
        PYTHON_FREE,
        PYTHON_BUSY) == PYTHON_FREE;
}

#define UNLOCK_PYTHON 1
void LockPython(void)
{
    char cmd = UNLOCK_PYTHON;
    if (PLC_shutdown) return;
    while(AtomicCompareExchange(
            &python_state,
            PYTHON_FREE,
            PYTHON_BUSY) != PYTHON_FREE &&
            cmd == UNLOCK_PYTHON){
       read(Python_pipe_fd, &cmd, sizeof(cmd));
    }
}

void UnLockPython(void)
{
    if(AtomicCompareExchange(
            &python_state,
            PYTHON_BUSY,
            PYTHON_FREE) == PYTHON_BUSY){
        if(rt_task_self()){/*is that the real time task ?*/
           char cmd = UNLOCK_PYTHON;
           rt_pipe_write(&Python_pipe, &cmd, sizeof(cmd), P_NORMAL);
        }/* otherwise, no signaling from non real time */
    }    /* as plc does not wait for lock. */
}

int CheckRetainBuffer(void)
{
	return 1;
}

void ValidateRetainBuffer(void)
{
}

void InValidateRetainBuffer(void)
{
}

void Retain(unsigned int offset, unsigned int count, void *p)
{
}

void Remind(unsigned int offset, unsigned int count, void *p)
{
}
/**
 * Tail of code common to all C targets
 **/

/** 
 * LOGGING
 **/

#ifndef LOG_BUFFER_SIZE
#define LOG_BUFFER_SIZE (1<<14) /*16Ko*/
#endif
#ifndef LOG_BUFFER_ATTRS
#define LOG_BUFFER_ATTRS
#endif

#define LOG_BUFFER_MASK (LOG_BUFFER_SIZE-1)

static char LogBuff[LOG_LEVELS][LOG_BUFFER_SIZE] LOG_BUFFER_ATTRS;
void inline copy_to_log(uint8_t level, uint32_t buffpos, void* buf, uint32_t size){
    if(buffpos + size < LOG_BUFFER_SIZE){
        memcpy(&LogBuff[level][buffpos], buf, size);
    }else{
        uint32_t remaining = LOG_BUFFER_SIZE - buffpos; 
        memcpy(&LogBuff[level][buffpos], buf, remaining);
        memcpy(LogBuff[level], (char*)buf + remaining, size - remaining);
    }
}
void inline copy_from_log(uint8_t level, uint32_t buffpos, void* buf, uint32_t size){
    if(buffpos + size < LOG_BUFFER_SIZE){
        memcpy(buf, &LogBuff[level][buffpos], size);
    }else{
        uint32_t remaining = LOG_BUFFER_SIZE - buffpos; 
        memcpy(buf, &LogBuff[level][buffpos], remaining);
        memcpy((char*)buf + remaining, LogBuff[level], size - remaining);
    }
}

/* Log buffer structure

 |<-Tail1.msgsize->|<-sizeof(mTail)->|<--Tail2.msgsize-->|<-sizeof(mTail)->|...
 |  Message1 Body  |      Tail1      |   Message2 Body   |      Tail2      |

*/
typedef struct {
    uint32_t msgidx;
    uint32_t msgsize;
    unsigned long tick;
    IEC_TIME time;
} mTail;

/* Log cursor : 64b
   |63 ... 32|31 ... 0|
   | Message | Buffer |
   | counter | Index  | */
static uint64_t LogCursor[LOG_LEVELS] LOG_BUFFER_ATTRS = {0x0,0x0,0x0,0x0};

void ResetLogCount(void) {
	uint8_t level;
	for(level=0;level<LOG_LEVELS;level++){
		LogCursor[level] = 0;
	}
}

/* Store one log message of give size */
int LogMessage(uint8_t level, char* buf, uint32_t size){
    if(size < LOG_BUFFER_SIZE - sizeof(mTail)){
        uint32_t buffpos;
        uint64_t new_cursor, old_cursor;

        mTail tail;
        tail.msgsize = size;
        tail.tick = __tick;
        PLC_GetTime(&tail.time);

        /* We cannot increment both msg index and string pointer 
           in a single atomic operation but we can detect having been interrupted.
           So we can try with atomic compare and swap in a loop until operation
           succeeds non interrupted */
        do{
            old_cursor = LogCursor[level];
            buffpos = (uint32_t)old_cursor;
            tail.msgidx = (old_cursor >> 32); 
            new_cursor = ((uint64_t)(tail.msgidx + 1)<<32) 
                         | (uint64_t)((buffpos + size + sizeof(mTail)) & LOG_BUFFER_MASK);
        }while(AtomicCompareExchange64(
            (long long*)&LogCursor[level],
            (long long)old_cursor,
            (long long)new_cursor)!=(long long)old_cursor);

        copy_to_log(level, buffpos, buf, size);
        copy_to_log(level, (buffpos + size) & LOG_BUFFER_MASK, &tail, sizeof(mTail));

        return 1; /* Success */
    }else{
    	char mstr[] = "Logging error : message too big";
        LogMessage(LOG_CRITICAL, mstr, sizeof(mstr));
    }
    return 0;
}

uint32_t GetLogCount(uint8_t level){
    return (uint64_t)LogCursor[level] >> 32;
}

/* Return message size and content */
uint32_t GetLogMessage(uint8_t level, uint32_t msgidx, char* buf, uint32_t max_size, uint32_t* tick, uint32_t* tv_sec, uint32_t* tv_nsec){
    uint64_t cursor = LogCursor[level];
    if(cursor){
        /* seach cursor */
        uint32_t stailpos = (uint32_t)cursor; 
        uint32_t smsgidx;
        mTail tail;
        tail.msgidx = cursor >> 32;
        tail.msgsize = 0;

        /* Message search loop */
        do {
            smsgidx = tail.msgidx;
            stailpos = (stailpos - sizeof(mTail) - tail.msgsize ) & LOG_BUFFER_MASK;
            copy_from_log(level, stailpos, &tail, sizeof(mTail));
        }while((tail.msgidx == smsgidx - 1) && (tail.msgidx > msgidx));

        if(tail.msgidx == msgidx){
            uint32_t sbuffpos = (stailpos - tail.msgsize ) & LOG_BUFFER_MASK; 
            uint32_t totalsize = tail.msgsize;
            *tick = tail.tick; 
            *tv_sec = tail.time.tv_sec; 
            *tv_nsec = tail.time.tv_nsec; 
            copy_from_log(level, sbuffpos, buf, 
                          totalsize > max_size ? max_size : totalsize);
            return totalsize;
        }
    }
    return 0;
}

#define CALIBRATED -2
#define NOT_CALIBRATED -1
static int calibration_count = NOT_CALIBRATED;
static IEC_TIME cal_begin;
static long long Tsync = 0;
static long long FreqCorr = 0;
static int Nticks = 0;
static unsigned long last_tick = 0;

/*
 * Called on each external periodic sync event
 * make PLC tick synchronous with external sync
 * ratio defines when PLC tick occurs between two external sync
 * @param sync_align_ratio 
 *          0->100 : align ratio
 *          < 0 : no align, calibrate period
 **/
void align_tick(int sync_align_ratio)
{
	/*
	printf("align_tick(%d)\n", calibrate);
	*/
	if(sync_align_ratio < 0){ /* Calibration */
		if(calibration_count == CALIBRATED)
			/* Re-calibration*/
			calibration_count = NOT_CALIBRATED;
		if(calibration_count == NOT_CALIBRATED)
			/* Calibration start, get time*/
			PLC_GetTime(&cal_begin);
		calibration_count++;
	}else{ /* do alignment (if possible) */
		if(calibration_count >= 0){
			/* End of calibration */
			/* Get final time */
			IEC_TIME cal_end;
			PLC_GetTime(&cal_end);
			/*adjust calibration_count*/
			calibration_count++;
			/* compute mean of Tsync, over calibration period */
			Tsync = ((long long)(cal_end.tv_sec - cal_begin.tv_sec) * (long long)1000000000 +
					(cal_end.tv_nsec - cal_begin.tv_nsec)) / calibration_count;
			if( (Nticks = (Tsync / Ttick)) > 0){
				FreqCorr = (Tsync % Ttick); /* to be divided by Nticks */
			}else{
				FreqCorr = Tsync - (Ttick % Tsync);
			}
			/*
			printf("Tsync = %ld\n", Tsync);
			printf("calibration_count = %d\n", calibration_count);
			printf("Nticks = %d\n", Nticks);
			*/
			calibration_count = CALIBRATED;
		}
		if(calibration_count == CALIBRATED){
			/* Get Elapsed time since last PLC tick (__CURRENT_TIME) */
			IEC_TIME now;
			long long elapsed;
			long long Tcorr;
			long long PhaseCorr;
			long long PeriodicTcorr;
			PLC_GetTime(&now);
			elapsed = (now.tv_sec - __CURRENT_TIME.tv_sec) * 1000000000 + now.tv_nsec - __CURRENT_TIME.tv_nsec;
			if(Nticks > 0){
				PhaseCorr = elapsed - (Ttick + FreqCorr/Nticks)*sync_align_ratio/100; /* to be divided by Nticks */
				Tcorr = Ttick + (PhaseCorr + FreqCorr) / Nticks;
				if(Nticks < 2){
					/* When Sync source period is near Tick time */
					/* PhaseCorr may not be applied to Periodic time given to timer */
					PeriodicTcorr = Ttick + FreqCorr / Nticks;
				}else{
					PeriodicTcorr = Tcorr;
				}
			}else if(__tick > last_tick){
				last_tick = __tick;
				PhaseCorr = elapsed - (Tsync*sync_align_ratio/100);
				PeriodicTcorr = Tcorr = Ttick + PhaseCorr + FreqCorr;
			}else{
				/*PLC did not run meanwhile. Nothing to do*/
				return;
			}
			/* DO ALIGNEMENT */
			PLC_SetTimer(Tcorr - elapsed, PeriodicTcorr);
		}
	}
}
