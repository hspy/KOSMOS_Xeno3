#include "iec_types_all.h"
#include "POUS.h"
/*for memcpy*/
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
/*for semaphore*/
#include <semaphore.h>
/*for shared memory*/
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <sys/types.h>
/*for xeonamai rt_pipe*/
#include <native/task.h>
#include <native/timer.h>
#include <native/mutex.h>
#include <native/sem.h>
#include <native/pipe.h>
/*for pthread*/
#include <pthread.h>
/*for waitpid*/
#include <sys/types.h>
#include <sys/wait.h>

#define OPC_SERVER_COMMAND				"/usr/lib/opcua/run.sh"
#define WAITOPC_PIPE_DEVICE				"/dev/rtp4"
#define WAITOPC_PIPE_MINOR				4
#ifdef _ENABLE_OPC_UA_CLIENT
#define WAITUACLIENT_PIPE_DEVICE    	"/dev/rtp5"
#define WAITUACLIENT_PIPE_MINOR      	5
#define UACLIENT_PIPE_DEVICE         	"/dev/rtp6"
#define UACLIENT_PIPE_MINOR        		6
#endif
#define OPC_SEMAPHORE_KEY				65786
#define OPC_SHARED_BUFFER_KEY				65787
#define OPC_SHARED_LIST_KEY				65788
#define OPC_SHARED_INFORMATION_KEY			65789
//#define NUM_OPC_VAR					%(variable_num)d
//#define BUFFER_SIZE					%(buffer_size)d
#define PIPE_SIZE					1
#define OPC_SEM_NAME					"opcsem"

#define PLC_STATE_WAITOPC_FILE_OPENED       512
#define PLC_STATE_WAITOPC_PIPE_CREATED      1024
#define PLC_STATE_OPC_TASK_CREATED          2048
#ifdef _ENABLE_OPC_UA_CLIENT
#define PLC_STATE_WAITUACLIENT_FILE_OPENED	   4096
#define PLC_STATE_WAITUACLIENT_PIPE_CREATED    8192
#define PLC_STATE_UACLIENT_FILE_OPENED		   16384
#define PLC_STATE_UACLIENT_PIPE_CREATED		   32768
#define PLC_STATE_UACLIENT_TASK_CREATED		   65536
#endif

typedef struct _plc_opc_variable
{
	unsigned int type;
	unsigned int id;
	char flag;
	char arrayType;
}PLC_OPC_VARIABLE;

typedef enum _plc_variable_type
{
    Type_Null = 0,
    Type_Bool = 1,
    Type_SInt = 2,
    Type_USInt = 3,
    Type_Int = 4,
    Type_UInt = 5,
    Type_DInt = 6,
    Type_UDInt = 7,
    Type_LInt = 8,
    Type_ULInt = 9,
    Type_Real = 10,
    Type_LReal = 11,
    Type_String = 12,
    Type_DT = 13,
    Type_Char = 15
}PLC_VARIABLE_TYPE;

typedef struct _plc_info
{
	int varNumber;
	int bufSize;
	int varWrited;
	int curBufSize;
}OPC_INFO;

union semun
{
	int val;
	struct semid_ds *buf;
	unsigned short int *array;
};


extern unsigned int PLC_state;
extern unsigned int PLC_shutdown;

extern long AtomicCompareExchange(long*, long, long);
extern long long AtomicCompareExchange64(long long* , long long , long long);
extern int suspendDebug(int disable);
extern void resumeDebug(void);

extern int getVarNum(void);

/* OPC rt pipe, thread */
RT_PIPE WaitOPC_pipe;
#ifdef _ENABLE_OPC_UA_CLIENT
RT_PIPE WaitUAClient_pipe;
RT_PIPE UAClient_pipe;
#endif
int WaitOPC_pipe_fd;
#ifdef _ENABLE_OPC_UA_CLIENT
int WaitUAClient_pipe_fd;
int UAClient_pipe_fd;
#endif

pthread_t opc_thread;
#ifdef _ENABLE_OPC_UA_CLIENT
pthread_t uaclient_thread;
#endif
int opc_thread_id;
#ifdef _ENABLE_OPC_UA_CLIENT
int uaclient_thread_id;
#endif

PLC_OPC_VARIABLE *opc_shared_list;
OPC_INFO *opc_shared_information;
char *opc_shared_buffer;

int opc_sem;
struct sembuf opc_sem_lock = {0, -1, IPC_NOWAIT|SEM_UNDO};
struct sembuf opc_sem_unlock = {0, 1, IPC_NOWAIT|SEM_UNDO};


int shared_buffer_id;
int shared_list_id;
int shared_information_id;

pid_t server_pid;
FILE *server_fd;
int opc_break;
int opc_started;

unsigned long __opc_tick;
extern const int buf_size;

#ifdef _ENABLE_OPC_UA_CLIENT
int __init_UAClient();
void __cleanup_UAClient();
#endif
void *OPCEntry(void);
#ifdef _ENABLE_OPC_UA_CLIENT
void *UAClientEntry(void);
#endif
void SetTraceOPCVariable(int idx, void* force);
unsigned int RegisterAndWriteOPCVariable(void);
unsigned int ReadOPCVariable(void);
int GetOPCTypeSize(int type, char *cursor);
void OPCCleanup(void);
#ifdef _ENABLE_OPC_UA_CLIENT
void UAClientIterator(int* result, void** data);
void CallOPCUAFuntion(int* result, void* data);
#endif

int __init_opcua(void)
{
	union semun sem_union;
	
	opc_break = 0;
	opc_started = 0;
	/* create WaitDebug_pipe */
	if(rt_pipe_create(&WaitOPC_pipe, "WaitOPC_pipe", WAITOPC_PIPE_MINOR, PIPE_SIZE)){
		fprintf(stderr,"OPC rt pipe create error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_WAITOPC_PIPE_CREATED;

	/* open WaitDebug_pipe*/
	if((WaitOPC_pipe_fd = open(WAITOPC_PIPE_DEVICE, O_RDWR)) == -1){
		fprintf(stderr,"OPC rt pipe open error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_WAITOPC_FILE_OPENED;
	#ifdef _ENABLE_OPC_UA_CLIENT
	/* create UAClient_pipe */
	if(rt_pipe_create(&UAClient_pipe, "UAClient_pipe", UACLIENT_PIPE_MINOR, PIPE_SIZE)){
		fprintf(stderr,"UAClient rt pipe create error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_UACLIENT_PIPE_CREATED;

	/* open UAClient_pipe*/
	if((UAClient_pipe_fd = open(UACLIENT_PIPE_DEVICE, O_RDWR)) == -1){
		fprintf(stderr,"UAClient rt pipe open error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_UACLIENT_FILE_OPENED;

	/* create WaitUAClient_pipe */
	if(rt_pipe_create(&WaitUAClient_pipe, "WaitUAClient_pipe", WAITUACLIENT_PIPE_MINOR, PIPE_SIZE)){
		fprintf(stderr,"WaitUAClient rt pipe create error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_WAITUACLIENT_PIPE_CREATED;

	/* open WaitUAClient_pipe*/
	if((WaitUAClient_pipe_fd = open(WAITUACLIENT_PIPE_DEVICE, O_RDWR)) == -1){
		fprintf(stderr,"WaitUAClient rt pipe open error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_WAITUACLIENT_FILE_OPENED;

	if(__init_UAClient() == -1)
		goto opcerror;
	#endif

	if((opc_sem = semget((key_t)OPC_SEMAPHORE_KEY, 1, 0666|IPC_CREAT|IPC_EXCL)) == -1){
		fprintf(stderr,"beremiz semget error\n");
		goto opcerror;
	}

	sem_union.val = 1;
	if(semctl(opc_sem, 0, SETVAL, sem_union) == -1){
		fprintf(stderr,"beremiz semctl error\n");
		goto opcerror;
	}

	if((shared_list_id = shmget((key_t)OPC_SHARED_LIST_KEY, sizeof(PLC_OPC_VARIABLE)*getVarNum(), IPC_CREAT|0666)) == -1){
		fprintf(stderr, "list shmget fail\n");
		goto opcerror;
	}

	if((opc_shared_list = (PLC_OPC_VARIABLE *)shmat(shared_list_id, (void *)0, 0)) == NULL){
		fprintf(stderr, "list shmat fail\n");
		goto opcerror;
	}
	memset(opc_shared_list, 0x00, sizeof(PLC_OPC_VARIABLE)*getVarNum());

	if((shared_buffer_id = shmget((key_t)OPC_SHARED_BUFFER_KEY, buf_size, IPC_CREAT|0666)) == -1){
		fprintf(stderr, "buffer shmget fail\n");
		goto opcerror;
	}

	if((opc_shared_buffer = (char *)shmat(shared_buffer_id, (void *)0, 0)) == NULL){
		fprintf(stderr, "buffer shmat fail\n");
		goto opcerror;
	}
	memset(opc_shared_buffer, 0x00, buf_size);

	if((shared_information_id = shmget((key_t)OPC_SHARED_INFORMATION_KEY, sizeof(OPC_INFO), IPC_CREAT|0666)) == -1){
		fprintf(stderr, "size shmget fail\n");
		goto opcerror;
	}

	if((opc_shared_information = (OPC_INFO *)shmat(shared_information_id, (void *)0, 0)) == NULL){
		fprintf(stderr, "size shmat fail\n");
		goto opcerror;
	}
	opc_shared_information->varNumber = getVarNum();
	opc_shared_information->bufSize = buf_size;
	opc_shared_information->varWrited = 0;

	//create,start thread
	if((opc_thread_id = pthread_create(&opc_thread, NULL, (void *)OPCEntry, NULL)) < 0){
		fprintf(stderr,"OPC thread create error\n");
		goto opcerror;
	}
	PLC_state |= PLC_STATE_OPC_TASK_CREATED;

	#ifdef _ENABLE_OPC_UA_CLIENT
	if((uaclient_thread_id = pthread_create(&uaclient_thread, NULL, (void *)UAClientEntry, NULL)) < 0){
		fprintf(stderr,"UA-Client thread create error\n");
		goto opcerror;
		}
	PLC_state |= PLC_STATE_UACLIENT_TASK_CREATED;
	#endif

	if((server_fd = popen(OPC_SERVER_COMMAND, "w")) == NULL){
		fprintf(stderr, "OPC Server start error\n");
		goto opcerror;
	}
	return 0;

	opcerror:

		OPCCleanup();

	return 0;
}

extern void RegisterOPCVariable(int idx, void* force);
extern int suspendDebug(int disable);
extern void resumeDebug(void);
extern void ResetOPCVariables(void);

void *OPCEntry(void)
{
	int res;

	while(!opc_break){
		if((res = semop(opc_sem, &opc_sem_lock, 1)) != -1){
			if(opc_shared_information->varWrited == 1)
				res = RegisterAndWriteOPCVariable();
			if(opc_started)
				res = ReadOPCVariable();
			semop(opc_sem, &opc_sem_unlock, 1);
		}
		usleep(100000);
	}

	return NULL;
}

#ifdef _ENABLE_OPC_UA_CLIENT
void *UAClientEntry(void)
{
	int result = -1;
	void* data = (void*)malloc(sizeof(void));

    while(1)
    {
    	UAClientIterator(&result, &data);
        if(data == NULL)
            break;
    }
	return NULL;
}
#endif

unsigned int RegisterAndWriteOPCVariable(void)
{
	int i;
	char *cur_opc_cursor = opc_shared_buffer;
	ResetOPCVariables();
	for(i = 0; i < getVarNum(); i++){
		if(opc_shared_list[i].flag == 1){
			RegisterOPCVariable(opc_shared_list[i].id, (void *)cur_opc_cursor);
			opc_shared_list[i].flag = 0;
		}
		else{
			RegisterOPCVariable(opc_shared_list[i].id, NULL);
			opc_shared_list[i].flag = 0;
			opc_started = 1;
		}			
		cur_opc_cursor += GetOPCTypeSize(opc_shared_list[i].type, cur_opc_cursor);
	}
	opc_shared_information->varWrited = 0;

	return 0;
}

int GetOPCTypeSize(int type, char *cursor)
{
	char *string_cursor = cursor;

	switch(type)
	{
		case Type_Bool:
			return sizeof(uint8_t);
		case Type_SInt:
			return sizeof(uint8_t);
		/*case OpcUaType_DateTime:
			inputValue->Value.DateTime = *((OpcUa_Boolean *)cur_buffer_cursor);*/
		case Type_LReal:
			return sizeof(double);
		case Type_Real:
			return sizeof(float);
		case Type_Int:
			return sizeof(int16_t);
		case Type_DInt:
			return sizeof(int32_t);
		case Type_LInt:
			return sizeof(int64_t); //占쎈쐻占쎈짗占쎌굲占쏙옙占쎈쐻占쎈뼃占쎈빒�ⓦ끉�굲?
		case Type_UInt:
			return sizeof(uint16_t);
		case Type_UDInt:
			return sizeof(uint32_t);
		case Type_ULInt:
			return sizeof(uint64_t);
		case Type_String:
			return (int)(*((uint8_t *)string_cursor)+1);
		default:
			break;
	}
	return 0;
}

extern void FreeOPCData(void);
extern int GetOPCData(unsigned long *tick, unsigned long *size, void **buffer);
unsigned int ReadOPCVariable(void)
{
	void *tBuffer = NULL;
	unsigned long tTick, tSize;
	if(GetOPCData(&tTick, &tSize, &tBuffer) == 0){
		memset(opc_shared_buffer, 0x00, buf_size);
		memcpy(opc_shared_buffer, tBuffer, (size_t)tSize);
		FreeOPCData();
		return 1;
	}
    return 0;
}

void OPCCleanup(void)
{
	int res;

	fputs("q\n", server_fd);
	pclose(server_fd);

	if (PLC_state & PLC_STATE_OPC_TASK_CREATED) {
		pthread_join(opc_thread, NULL);
		PLC_state &= ~PLC_STATE_OPC_TASK_CREATED;
	}

	#ifdef _ENABLE_OPC_UA_CLIENT
	if (PLC_state & PLC_STATE_UACLIENT_TASK_CREATED) {
		pthread_join(uaclient_thread, NULL);
		PLC_state &= ~PLC_STATE_UACLIENT_TASK_CREATED;
	}
	#endif

	if (PLC_state & PLC_STATE_WAITOPC_PIPE_CREATED) {
		rt_pipe_delete(&WaitOPC_pipe);
		PLC_state &= ~PLC_STATE_WAITOPC_PIPE_CREATED;
	}

	if (PLC_state & PLC_STATE_WAITOPC_FILE_OPENED) {
		close(WaitOPC_pipe_fd);
		PLC_state &= ~PLC_STATE_WAITOPC_FILE_OPENED;
	}

	#ifdef _ENABLE_OPC_UA_CLIENT
	if (PLC_state & PLC_STATE_WAITUACLIENT_PIPE_CREATED) {
		rt_pipe_delete(&WaitUAClient_pipe);
		PLC_state &= ~PLC_STATE_WAITUACLIENT_PIPE_CREATED;
	}

	if (PLC_state & PLC_STATE_WAITUACLIENT_FILE_OPENED) {
		close(WaitUAClient_pipe_fd);
		PLC_state &= ~PLC_STATE_WAITUACLIENT_FILE_OPENED;
	}

	if (PLC_state & PLC_STATE_UACLIENT_PIPE_CREATED) {
		rt_pipe_delete(&UAClient_pipe);
		PLC_state &= ~PLC_STATE_UACLIENT_PIPE_CREATED;
	}

	if (PLC_state & PLC_STATE_UACLIENT_FILE_OPENED) {
		close(UAClient_pipe_fd);
		PLC_state &= ~PLC_STATE_UACLIENT_FILE_OPENED;
	}
	#endif

	//shared memory, shared semaphore detach and clear
	if((res = shmdt(opc_shared_buffer)) == -1)	// detach opc_shared_buffer
		fprintf(stderr,"shared buffer memory detach fail\n");
	if((res = shmdt(opc_shared_list)) == -1)	/// detach opc_shared_list
		fprintf(stderr,"shared list memory detach fail\n");
	if((res = shmdt(opc_shared_information)) == -1)	// detach opc_shared_information
		fprintf(stderr,"shared information memory detach fail\n");
	if((res = shmctl(shared_buffer_id, IPC_RMID, 0)) == -1)
		fprintf(stderr,"shared buffer memory clean fail\n");
	if((res = shmctl(shared_list_id, IPC_RMID, 0)) == -1)
		fprintf(stderr,"shared list memory clean fail\n");
	if((res = shmctl(shared_information_id, IPC_RMID, 0)) == -1)
		fprintf(stderr,"shared information memory clean fail\n");
	if((res = semctl(opc_sem, IPC_RMID, 0)) == -1)
		fprintf(stderr,"OPC semaphore close fail\n");
}

void __cleanup_opcua(void)
{
	opc_break = 1;
	opc_started = 0;
	#ifdef _ENABLE_OPC_UA_CLIENT
	__cleanup_UAClient();
	#endif
	OPCCleanup();
}

#define DEBUG_PENDING_DATA 1
int WaitOPCData(unsigned long *tick)
{
    	char cmd;
    	int res;
    	if (PLC_shutdown) return -1;
    	/* Wait signal from PLC thread */
    	res = read(WaitOPC_pipe_fd, &cmd, sizeof(cmd));
    	if (res == sizeof(cmd) && cmd == DEBUG_PENDING_DATA){
        	*tick = __opc_tick;
        	return 0;
    	}
    	return -1;
}

extern unsigned long __tick;
void InitiateOPCTransfer(void)
{
    	char msg = DEBUG_PENDING_DATA;
    	/* remember tick */
    	__opc_tick = __tick;
    	/* signal debugger thread it can read data */
    	rt_pipe_write(&WaitOPC_pipe, &msg, sizeof(msg), P_NORMAL);
}

#ifdef _ENABLE_OPC_UA_CLIENT

#define UACLIENT_PENDING_COMMAND 1

#define UACLIENT_FREE 0
#define UACLIENT_BUSY 1
static long uaclient_state = UACLIENT_FREE;

int Wait_UAClient_Commands(void)
{
    char cmd;
    if (PLC_shutdown) 
		return -1;
    /* Wait signal from PLC thread */
    if(read(WaitUAClient_pipe_fd, &cmd, sizeof(cmd))==sizeof(cmd) && cmd==UACLIENT_PENDING_COMMAND){
        return 0;
    }
    return -1;
}

/* Called by PLC thread on each new ua_client command*/
void UnBlock_UAClient_Commands(void)
{
    char msg = UACLIENT_PENDING_COMMAND;
    rt_pipe_write(&WaitUAClient_pipe, &msg, sizeof(msg), P_NORMAL);
}

int TryLock_UAClient(void)
{
    return AtomicCompareExchange(
        &uaclient_state,
		UACLIENT_FREE,
		UACLIENT_BUSY) == UACLIENT_FREE;
}

#define UNLOCK_UACLIENT 1
void Lock_UAClient(void)
{
    char cmd = UNLOCK_UACLIENT;
    if (PLC_shutdown) return;
    while(AtomicCompareExchange(
            &uaclient_state,
			UACLIENT_FREE,
			UACLIENT_BUSY) != UACLIENT_FREE &&
            cmd == UNLOCK_UACLIENT){
       read(UAClient_pipe_fd, &cmd, sizeof(cmd));
    }
}

void UnLock_UAClient(void)
{
    if(AtomicCompareExchange(
            &uaclient_state,
			UACLIENT_BUSY,
			UACLIENT_FREE) == UACLIENT_BUSY){
        if(rt_task_self()){/*is that the real time task ?*/
           char cmd = UNLOCK_UACLIENT;
           rt_pipe_write(&UAClient_pipe, &cmd, sizeof(cmd), P_NORMAL);
        }/* otherwise, no signaling from non real time */
    }    /* as plc does not wait for lock. */
}
#endif
