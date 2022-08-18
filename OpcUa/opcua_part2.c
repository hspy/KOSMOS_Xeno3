#ifdef _ENABLE_OPC_UA_CLIENT
/* The fifo (fixed size, as number of FB is fixed) */

#include "PlcOpcClientLib.h"
#include <stdbool.h>	// for support bool type

enum UAClientType
{
	UA_Connect = 0,
	UA_Disconnect,
	UA_NamespaceGetIndexList,
	UA_NodeGetHandleList,
	UA_NodeReleaseHandleList,
	UA_NodeGetInformation,
	UA_SubscriptionCreate,
	UA_SubscriptionDelete,
	UA_SubscriptionProcessed,
	UA_MonitoredItemAddList,
	UA_MonitoredItemRemoveList,
	UA_MonitoredItemOperateList,
	UA_ReadList,
	UA_WriteList,
	UA_MethodGetHandleList,
	UA_MethodReleaseHandleList,
	UA_MethodCall,
	UA_ConnectionGetStatus,
	_UA_GetMonitoredItemVariableValueFB
};

typedef struct
{
	enum UAClientType FBTYPE;
	void* FBPOINTER;
}UAClient;
static UAClient* UAClientFBs[%(UAClientFBCounts)d];

/* Producer and consumer cursors */
static int Current_PLC_UAClientFB;
static int Current_UAClient_UAClientFB;

/* A global state, for use inside UA-client FBs*/
static int UAClient_State;
#define UACLIENT_LOCKED_BY_UACLIENT 0
#define UACLIENT_LOCKED_BY_PLC 1
#define UACLIENT_MUSTWAKEUP 2
#define UACLIENT_FINISHED 4

/* Each UA-client FunctionBlock have it own state */
#define UACLIENT_FB_FREE 0
#define UACLIENT_FB_REQUESTED 1
#define UACLIENT_FB_PROCESSING 2
#define UACLIENT_FB_ANSWERED 3

int Wait_UAClient_Commands(void);
void UnBlock_UAClient_Commands(void);
int TryLock_UAClient(void);
void UnLock_UAClient(void);
void Lock_UAClient(void);

PlcOpc_Handle hApplication = NULL;
PlcOpc_Handle szCertificateStore = NULL;

unsigned char** variables[20] = {NULL, };
bool*	valuesChanged[20] = {NULL, };
bool*	valuesUpdate[20] = {NULL, };
unsigned int Current_PLC_MonitoredItemsIndex = 0;

int __init_UAClient()
{
	int i;
	
	/* Initialize cursors */
	Current_UAClient_UAClientFB = 0;
	Current_PLC_UAClientFB = 0;
	UAClient_State = UACLIENT_LOCKED_BY_UACLIENT;

	for(i = 0; i < %(UAClientFBCounts)d; i++)
		UAClientFBs[i] = NULL;

	if(PlcOpc_UA_Initialize("PlcOpcUaClient", "CertificateStore_Client_", &hApplication, &szCertificateStore) != 0)
		return -1;

	return 0;
}

void __cleanup_UAClient()
{
	int i;
	UAClient_State = UACLIENT_FINISHED;
	UnBlock_UAClient_Commands();
	for(i = 0; i < %(UAClientFBCounts)d; i++)
	{
		free(UAClientFBs[i]);
		UAClientFBs[i] = NULL;
	}
	PlcOpc_UA_Shutdown(hApplication, &szCertificateStore);
}
#endif
void __retrieve_opcua(void)
{
#ifdef _ENABLE_OPC_UA_CLIENT
	/* Check UA-client thread is not being
	 * modifying internal UA-ClientFBs data */
	UAClient_State = TryLock_UAClient() ?
					UACLIENT_LOCKED_BY_PLC :
					UACLIENT_LOCKED_BY_UACLIENT;
	/* If UA-client thread _is_ in, then UAClient_State remains UACLIENT_LOCKED_BY_UACLIENT
	 * and ClientFBs will no do anything */
#endif
}

void __publish_opcua(void)
{
#ifdef _ENABLE_OPC_UA_CLIENT
	if(UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* If runnig PLC did push something in the fifo*/
		if(UAClient_State & UACLIENT_MUSTWAKEUP){
			/* WakeUp ua-client thread */
			UnBlock_UAClient_Commands();
		}
		UnLock_UAClient();
	}
#endif
}
#ifdef _ENABLE_OPC_UA_CLIENT
/**
 * Called by the PLC, each time a UA-client
 * FB instance is executed
 */
void __UA_ConnectFB(UA_CONNECT* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_SERVERENDPOINTURL, __GET_VAR(data__->SERVERENDPOINTURL));
		__SET_VAR(data__->, PRE_SESSIONCONNECTINFO, __GET_VAR(data__->SESSIONCONNECTINFO));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}

	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, CONNECTIONHDL, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_Connect;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SERVERENDPOINTURL0, __GET_VAR(data__->PRE_SERVERENDPOINTURL));
			__SET_VAR(data__->, PRE_SESSIONCONNECTINFO0, __GET_VAR(data__->PRE_SESSIONCONNECTINFO));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_DisconnectFB(UA_DISCONNECT* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_Disconnect;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_NamespaceGetIndexListFB(UA_NAMESPACEGETINDEXLIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NAMESPACEURISCOUNT, __GET_VAR(data__->NAMESPACEURISCOUNT));
		__SET_VAR(data__->, PRE_NAMESPACEURIS, __GET_VAR(data__->NAMESPACEURIS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NAMESPACEINDEXES, __GET_VAR(data__->PRE_NAMESPACEINDEXES));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_NamespaceGetIndexList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NAMESPACEURISCOUNT0, __GET_VAR(data__->PRE_NAMESPACEURISCOUNT));
			__SET_VAR(data__->, PRE_NAMESPACEURIS0, __GET_VAR(data__->PRE_NAMESPACEURIS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_NodeGetHandleListFB(UA_NODEGETHANDLELIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEIDCOUNT, __GET_VAR(data__->NODEIDCOUNT));
		__SET_VAR(data__->, PRE_NODEIDS, __GET_VAR(data__->NODEIDS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, NODEHDLS, __GET_VAR(data__->PRE_NODEHDLS));
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_NodeGetHandleList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEIDCOUNT0, __GET_VAR(data__->PRE_NODEIDCOUNT));
			__SET_VAR(data__->, PRE_NODEIDS0, __GET_VAR(data__->PRE_NODEIDS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_NodeReleaseHandleListFB(UA_NODERELEASEHANDLELIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEHDLCOUNT, __GET_VAR(data__->NODEHDLCOUNT));
		__SET_VAR(data__->, PRE_NODEHDLS, __GET_VAR(data__->NODEHDLS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_NodeReleaseHandleList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEHDLCOUNT0, __GET_VAR(data__->PRE_NODEHDLCOUNT));
			__SET_VAR(data__->, PRE_NODEHDLS0, __GET_VAR(data__->PRE_NODEHDLS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_NodeGetInformationFB(UA_NODEGETINFORMATION* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEID, __GET_VAR(data__->NODEID));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, NODEGETINFOERRORIDS, __GET_VAR(data__->PRE_NODEGETINFOERRORIDS));
			__SET_VAR(data__->, NODEINFO, __GET_VAR(data__->PRE_NODEINFO));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_NodeGetInformation ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEID0, __GET_VAR(data__->PRE_NODEID));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_SubscriptionCreateFB(UA_SUBSCRIPTIONCREATE* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_PUBLISHINGENABLE, __GET_VAR(data__->PUBLISHINGENABLE));
		__SET_VAR(data__->, PRE_PRIORITY, __GET_VAR(data__->PRIORITY));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
		__SET_VAR(data__->, PRE_PUBLISHINGINTERVAL, __GET_VAR(data__->PUBLISHINGINTERVAL));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, SUBSCRIPTIONHDL, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PUBLISHINGINTERVAL, __GET_VAR(data__->PRE_PUBLISHINGINTERVAL1));
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_SubscriptionCreate ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_PUBLISHINGENABLE0, __GET_VAR(data__->PRE_PUBLISHINGENABLE));
			__SET_VAR(data__->, PRE_PRIORITY0, __GET_VAR(data__->PRE_PRIORITY));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			__SET_VAR(data__->, PRE_PUBLISHINGINTERVAL0, __GET_VAR(data__->PRE_PUBLISHINGINTERVAL));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_SubscriptionDeleteFB(UA_SUBSCRIPTIONDELETE* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL, __GET_VAR(data__->SUBSCRIPTIONHDL));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_SubscriptionDelete ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL0, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_SubscriptionProcessedFB(UA_SUBSCRIPTIONPROCESSED* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL, __GET_VAR(data__->SUBSCRIPTIONHDL));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, PUBLISHED, __GET_VAR(data__->PRE_PUBLISHED));
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_SubscriptionProcessed ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL0, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MonitoredItemAddListFB(UA_MONITOREDITEMADDLIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
	    __SET_VAR(data__->, PRE_SUBSCRIPTIONHDL, __GET_VAR(data__->SUBSCRIPTIONHDL));
		__SET_VAR(data__->, PRE_NODEHDLCOUNT, __GET_VAR(data__->NODEHDLCOUNT));
		__SET_VAR(data__->, PRE_NODEHDLS, __GET_VAR(data__->NODEHDLS));
		__SET_VAR(data__->, PRE_NODEADDINFOS, __GET_VAR(data__->NODEADDINFOS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
		__SET_VAR(data__->, PRE_VARIABLES, __GET_VAR(data__->VARIABLES));
		__SET_VAR(data__->, PRE_MONITORINGSETTINGS, __GET_VAR(data__->MONITORINGSETTINGS));
		__SET_VAR(data__->, PRE_VALUESCHANGED, __GET_VAR(data__->VALUESCHANGED));
		__SET_VAR(data__->, PRE_REMAININGVALUECOUNT, __GET_VAR(data__->REMAININGVALUECOUNT));
		__SET_VAR(data__->, PRE_TIMESTAMPS, __GET_VAR(data__->TIMESTAMPS));
		__SET_VAR(data__->, PRE_NODEQUALITYIDS, __GET_VAR(data__->NODEQUALITYIDS));

	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			__SET_VAR(data__->, MONITOREDITEMHDLS, __GET_VAR(data__->PRE_MONITOREDITEMHDLS));
			__SET_VAR(data__->, VARIABLES, __GET_VAR(data__->PRE_VARIABLES1));
			__SET_VAR(data__->, MONITORINGSETTINGS, __GET_VAR(data__->PRE_MONITORINGSETTINGS1));
			__SET_VAR(data__->, VALUESCHANGED, __GET_VAR(data__->PRE_VALUESCHANGED1));
			__SET_VAR(data__->, REMAININGVALUECOUNT, __GET_VAR(data__->PRE_REMAININGVALUECOUNT1));
			__SET_VAR(data__->, TIMESTAMPS, __GET_VAR(data__->PRE_TIMESTAMPS1));
			__SET_VAR(data__->, NODEQUALITYIDS, __GET_VAR(data__->PRE_NODEQUALITYIDS1));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MonitoredItemAddList ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL0, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PRE_NODEHDLCOUNT0, __GET_VAR(data__->PRE_NODEHDLCOUNT));
			__SET_VAR(data__->, PRE_NODEHDLS0, __GET_VAR(data__->PRE_NODEHDLS));
			__SET_VAR(data__->, PRE_NODEADDINFOS0, __GET_VAR(data__->PRE_NODEADDINFOS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			__SET_VAR(data__->, PRE_VARIABLES0, __GET_VAR(data__->PRE_VARIABLES));
			__SET_VAR(data__->, PRE_MONITORINGSETTINGS0, __GET_VAR(data__->PRE_MONITORINGSETTINGS));
			__SET_VAR(data__->, PRE_VALUESCHANGED0, __GET_VAR(data__->PRE_VALUESCHANGED));
			__SET_VAR(data__->, PRE_REMAININGVALUECOUNT0, __GET_VAR(data__->PRE_REMAININGVALUECOUNT));
			__SET_VAR(data__->, PRE_TIMESTAMPS0, __GET_VAR(data__->PRE_TIMESTAMPS));
			__SET_VAR(data__->, PRE_NODEQUALITYIDS0, __GET_VAR(data__->PRE_NODEQUALITYIDS));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MonitoredItemRemoveListFB(UA_MONITOREDITEMREMOVELIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL, __GET_VAR(data__->SUBSCRIPTIONHDL));
		__SET_VAR(data__->, PRE_MONITOREDITEMHDLCOUNT, __GET_VAR(data__->MONITOREDITEMHDLCOUNT));
		__SET_VAR(data__->, PRE_MONITOREDITEMHDLS, __GET_VAR(data__->MONITOREDITEMHDLS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MonitoredItemRemoveList ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL0, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PRE_MONITOREDITEMHDLCOUNT0, __GET_VAR(data__->PRE_MONITOREDITEMHDLCOUNT));
			__SET_VAR(data__->, PRE_MONITOREDITEMHDLS0, __GET_VAR(data__->PRE_MONITOREDITEMHDLS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MonitoredItemOperateListFB(UA_MONITOREDITEMOPERATELIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->ENABLE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

	if(__GET_VAR(data__->ENABLE) && __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL, __GET_VAR(data__->SUBSCRIPTIONHDL));
		__SET_VAR(data__->, PRE_MONITOREDITEMHDLCOUNT, __GET_VAR(data__->MONITOREDITEMHDLCOUNT));
		__SET_VAR(data__->, PRE_MONITOREDITEMHDLS, __GET_VAR(data__->MONITOREDITEMHDLS));
	}

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, PUBLISHED, __GET_VAR(data__->PRE_PUBLISHED));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MonitoredItemOperateList ;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_SUBSCRIPTIONHDL0, __GET_VAR(data__->PRE_SUBSCRIPTIONHDL));
			__SET_VAR(data__->, PRE_MONITOREDITEMHDLCOUNT0, __GET_VAR(data__->PRE_MONITOREDITEMHDLCOUNT));
			__SET_VAR(data__->, PRE_MONITOREDITEMHDLS0, __GET_VAR(data__->PRE_MONITOREDITEMHDLS));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_ReadListFB(UA_READLIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

  	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEHDLCOUNT, __GET_VAR(data__->NODEHDLCOUNT));
		__SET_VAR(data__->, PRE_NODEHDLS, __GET_VAR(data__->NODEHDLS));
		__SET_VAR(data__->, PRE_NODEADDINFOS, __GET_VAR(data__->NODEADDINFOS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
		__SET_VAR(data__->, PRE_VARIABLES, __GET_VAR(data__->VARIABLES));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			__SET_VAR(data__->, TIMESTAMPS, __GET_VAR(data__->PRE_TIMESTAMPS));
			__SET_VAR(data__->, VARIABLES, __GET_VAR(data__->PRE_VARIABLES));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_ReadList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEHDLCOUNT0, __GET_VAR(data__->PRE_NODEHDLCOUNT));
			__SET_VAR(data__->, PRE_NODEHDLS0, __GET_VAR(data__->PRE_NODEHDLS));
			__SET_VAR(data__->, PRE_NODEADDINFOS0, __GET_VAR(data__->PRE_NODEADDINFOS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_WriteListFB(UA_WRITELIST* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

  	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEHDLCOUNT, __GET_VAR(data__->NODEHDLCOUNT));
		__SET_VAR(data__->, PRE_NODEHDLS, __GET_VAR(data__->NODEHDLS));
		__SET_VAR(data__->, PRE_NODEADDINFOS, __GET_VAR(data__->NODEADDINFOS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
		__SET_VAR(data__->, PRE_VARIABLES, __GET_VAR(data__->VARIABLES));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, NODEERRORIDS, __GET_VAR(data__->PRE_NODEERRORIDS));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_WriteList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEHDLCOUNT0, __GET_VAR(data__->PRE_NODEHDLCOUNT));
			__SET_VAR(data__->, PRE_NODEHDLS0, __GET_VAR(data__->PRE_NODEHDLS));
			__SET_VAR(data__->, PRE_NODEADDINFOS0, __GET_VAR(data__->PRE_NODEADDINFOS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			__SET_VAR(data__->, PRE_VARIABLES0, __GET_VAR(data__->PRE_VARIABLES));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MethodGetHandleListFB(UA_METHODGETHANDLELIST* data__)
{
	int index=0, error = 0;

	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
	}

  	// detect rising edge on TRIG to trigger evaluation
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    // trig only if not already trigged
	    __GET_VAR(data__->TRIGGED) == 0){
		// mark as trigged
	    __SET_VAR(data__->, TRIGGED, 1);
		// make a safe copy of the code
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_NODEIDCOUNT, __GET_VAR(data__->NODEIDCOUNT));
		__SET_VAR(data__->, PRE_OBJECTNODEIDS, __GET_VAR(data__->OBJECTNODEIDS));
		__SET_VAR(data__->, PRE_METHODNODEIDS, __GET_VAR(data__->METHODNODEIDS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	// retain value for next rising edge detection
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	// python thread is not in ?
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		// if some answer are waiting, publish
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			// Copy buffer content into result
			__SET_VAR(data__->, ERRORIDS, __GET_VAR(data__->PRE_ERRORIDS));
			__SET_VAR(data__->, METHODHDLS, __GET_VAR(data__->PRE_METHODHDLS));
			// signal result presece to PLC
			for(index=0; index<__GET_VAR(data__->PRE_NODEIDCOUNT); index++)
			{
				if(__GET_VAR(data__->ERRORIDS, .ELEMENTS.table[index]) != 0)
				{
					error = 1;
					break;
				}
			}
			if(error == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			// Mark as free
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			// printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
		}
		// got the order to act ?
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   // and not already being processed
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			// Enter the block in the fifo
			// * Don't have to check if fifo cell is free
			// * as fifo size == FB count, and a FB cannot
			// * be requested twice
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MethodGetHandleList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_NODEIDCOUNT0, __GET_VAR(data__->PRE_NODEIDCOUNT));
			__SET_VAR(data__->, PRE_OBJECTNODEIDS0, __GET_VAR(data__->PRE_OBJECTNODEIDS));
			__SET_VAR(data__->, PRE_METHODNODEIDS0, __GET_VAR(data__->PRE_METHODNODEIDS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			// Set ACK pin to low so that we can set a rising edge on result
			// when not polling, a new answer imply reseting ack
			__SET_VAR(data__->, DONE, 0);
			// Mark FB busy
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			// Have to wakeup uaclient thread in case he was asleep
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			// printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
			// Get a new line
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MethodReleaseHandleListFB(UA_METHODRELEASEHANDLELIST* data__)
{
	int index=0, error=0;

	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
	}

  	// detect rising edge on TRIG to trigger evaluation
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    // trig only if not already trigged
	    __GET_VAR(data__->TRIGGED) == 0){
		// mark as trigged
	    __SET_VAR(data__->, TRIGGED, 1);
		// make a safe copy of the code
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_METHODHDLCOUNT, __GET_VAR(data__->METHODHDLCOUNT));
		__SET_VAR(data__->, PRE_METHODHDLS, __GET_VAR(data__->METHODHDLS));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	// retain value for next rising edge detection
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	// python thread is not in ?
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		// if some answer are waiting, publish
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			// Copy buffer content into result
			__SET_VAR(data__->, ERRORIDS, __GET_VAR(data__->PRE_ERRORIDS));
			// signal result presece to PLC
			for(index=0; index<__GET_VAR(data__->PRE_METHODHDLCOUNT); index++)
			{
				if(__GET_VAR(data__->ERRORIDS, .ELEMENTS.table[index]) != 0)
				{
					error = 1;
					break;
				}
			}
			if(error == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			// Mark as free
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			// printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
		}
		// got the order to act ?
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   // and not already being processed
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			// Enter the block in the fifo
			// * Don't have to check if fifo cell is free
			// * as fifo size == FB count, and a FB cannot
			// * be requested twice
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MethodReleaseHandleList;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_METHODHDLCOUNT0, __GET_VAR(data__->PRE_METHODHDLCOUNT));
			__SET_VAR(data__->, PRE_METHODHDLS0, __GET_VAR(data__->PRE_METHODHDLS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			// Set ACK pin to low so that we can set a rising edge on result
			// when not polling, a new answer imply reseting ack
			__SET_VAR(data__->, DONE, 0);
			// Mark FB busy
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			// Have to wakeup uaclient thread in case he was asleep
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			// printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
			// Get a new line
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_MethodCallFB(UA_METHODCALL* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

  	// detect rising edge on TRIG to trigger evaluation
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    // trig only if not already trigged
	    __GET_VAR(data__->TRIGGED) == 0){
		// mark as trigged
	    __SET_VAR(data__->, TRIGGED, 1);
		// make a safe copy of the code
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_METHODHDL, __GET_VAR(data__->METHODHDL));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
		__SET_VAR(data__->, PRE_INPUTARGUMENTS, __GET_VAR(data__->INPUTARGUMENTS));
		__SET_VAR(data__->, PRE_OUTPUTARGUMENTS, __GET_VAR(data__->OUTPUTARGUMENTS));
	}
	// retain value for next rising edge detection
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	// python thread is not in ?
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		// if some answer are waiting, publish
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			// Copy buffer content into result
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			__SET_VAR(data__->, INPUTARGUMENTS, __GET_VAR(data__->PRE_INPUTARGUMENTS1));
			__SET_VAR(data__->, OUTPUTARGUMENTS, __GET_VAR(data__->PRE_OUTPUTARGUMENTS1));
			// signal result presece to PLC
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			// Mark as free
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			// printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
		}
		// got the order to act ?
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   // and not already being processed
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			// Enter the block in the fifo
			// * Don't have to check if fifo cell is free
			// * as fifo size == FB count, and a FB cannot
			// * be requested twice
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_MethodCall;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			__SET_VAR(data__->, PRE_METHODHDL0, __GET_VAR(data__->PRE_METHODHDL));
			__SET_VAR(data__->, PRE_INPUTARGUMENTS0, __GET_VAR(data__->PRE_INPUTARGUMENTS));
			__SET_VAR(data__->, PRE_OUTPUTARGUMENTS0, __GET_VAR(data__->PRE_OUTPUTARGUMENTS));
			__SET_VAR(data__->, PRE_TIMEOUT0, __GET_VAR(data__->PRE_TIMEOUT));
			// Set ACK pin to low so that we can set a rising edge on result
			// when not polling, a new answer imply reseting ack
			__SET_VAR(data__->, DONE, 0);
			// Mark FB busy
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			// Have to wakeup uaclient thread in case he was asleep
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			// printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);
			// Get a new line
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void __UA_ConnectionGetStatusFB(UA_CONNECTIONGETSTATUS* data__)
{
	/* reset */
	if(!__GET_VAR(data__->EXECUTE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
		__SET_VAR(data__->, ERROR, 0);
		__SET_VAR(data__->, ERRORID, 0);
	}

  	/* detect rising edge on TRIG to trigger evaluation */
	if(((__GET_VAR(data__->EXECUTE) && !__GET_VAR(data__->TRIGM1))) &&
	    /* trig only if not already trigged */
	    __GET_VAR(data__->TRIGGED) == 0){
		/* mark as trigged */
	    __SET_VAR(data__->, TRIGGED, 1);
		/* make a safe copy of the code */
	    __SET_VAR(data__->, BUSY, 1);
		__SET_VAR(data__->, PRE_CONNECTIONHDL, __GET_VAR(data__->CONNECTIONHDL));
		__SET_VAR(data__->, PRE_TIMEOUT, __GET_VAR(data__->TIMEOUT));
	}
	/* retain value for next rising edge detection */
	__SET_VAR(data__->, TRIGM1, __GET_VAR(data__->EXECUTE));

	/* python thread is not in ? */
	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		/* if some answer are waiting, publish*/
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			/* Copy buffer content into result*/
			__SET_VAR(data__->, CONNECTIONSTATUS, __GET_VAR(data__->PRE_CONNECTIONSTATUS));
			__SET_VAR(data__->, SERVERSTATE, __GET_VAR(data__->PRE_SERVERSTATE));
			__SET_VAR(data__->, SERVICELEVEL, __GET_VAR(data__->PRE_SERVICELEVEL));
			__SET_VAR(data__->, ERRORID, __GET_VAR(data__->PRE_ERRORID));
			/* signal result presece to PLC*/
			if(__GET_VAR(data__->ERRORID) == 0)
			{
				__SET_VAR(data__->, ERROR, 0);
				__SET_VAR(data__->, BUSY, 0);
				__SET_VAR(data__->, DONE, 1);
			}
			else
			{
				__SET_VAR(data__->, ERROR, 1);
			}

			/* Mark as free */
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
			/*printf("__PythonEvalFB pop %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
		}
		/* got the order to act ?*/
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   /* and not already being processed */
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			/* Enter the block in the fifo
			 * Don't have to check if fifo cell is free
			 * as fifo size == FB count, and a FB cannot
			 * be requested twice */
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = UA_ConnectionGetStatus;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, PRE_CONNECTIONHDL0, __GET_VAR(data__->PRE_CONNECTIONHDL));
			/* Set ACK pin to low so that we can set a rising edge on result */
			/* when not polling, a new answer imply reseting ack*/
			__SET_VAR(data__->, DONE, 0);
			/* Mark FB busy */
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			/* Have to wakeup uaclient thread in case he was asleep */
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			/*printf("__PythonEvalFB push %%d - %%*s\n",Current_PLC_EvalFB, data__->BUFFER.len, data__->BUFFER.body);*/
			/* Get a new line */
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void ___UA_GetMonitoredItemVariableValueFB(_UA_GETMONITOREDITEMVARIABLEVALUE* data__)
{
	static int globalIndex = 0;
	static int localIndex = 0;

	if(!__GET_VAR(data__->ENABLE))
	{
		__SET_VAR(data__->, BUSY, 0);
		__SET_VAR(data__->, DONE, 0);
	}

	if((__GET_VAR(data__->ENABLE)) &&
	    __GET_VAR(data__->TRIGGED) == 0){
		globalIndex = __GET_VAR(data__->GLOBALINDEX);
		if(globalIndex < Current_PLC_MonitoredItemsIndex)
		{
			localIndex = __GET_VAR(data__->LOCALINDEX) - 1;
			if( (valuesUpdate[globalIndex])[localIndex] )
			{
			    __SET_VAR(data__->, TRIGGED, 1);
			    __SET_VAR(data__->, BUSY, 1);
			}
		}
	}

	if( UAClient_State & UACLIENT_LOCKED_BY_PLC){
		if(__GET_VAR(data__->STATE) == UACLIENT_FB_ANSWERED){
			__SET_VAR(data__->, BUSY, 0);
			__SET_VAR(data__->, DONE, 1);
			__SET_VAR(data__->, STATE, UACLIENT_FB_FREE);
			__SET_VAR(data__->, TRIGGED, 0);
		}
		if(__GET_VAR(data__->TRIGGED) == 1 &&
		   __GET_VAR(data__->STATE) == UACLIENT_FB_FREE)
		{
			UAClient* temp = (UAClient*)malloc(sizeof(UAClient*));
			temp->FBPOINTER = data__;
			temp->FBTYPE = _UA_GetMonitoredItemVariableValueFB;
			UAClientFBs[Current_PLC_UAClientFB] = temp;
			__SET_VAR(data__->, DONE, 0);
			__SET_VAR(data__->, STATE, UACLIENT_FB_REQUESTED);
			UAClient_State |= UACLIENT_MUSTWAKEUP;
			Current_PLC_UAClientFB = (Current_PLC_UAClientFB + 1) %% %(UAClientFBCounts)d;
		}
	}
}

void ___UA_GetMonitoredItemValuesChangedValueFB(_UA_GETMONITOREDITEMVALUESCHANGEDVALUE* data__)
{
	static int globalIndex = 0;
	static int localIndex = 0;
	/* reset */
	if(!__GET_VAR(data__->ENABLE))
	{
		__SET_VAR(data__->, DONE, 0);
	}

  	/* detect rising edge on TRIG to trigger evaluation */
	if(__GET_VAR(data__->ENABLE))
	{
		globalIndex = __GET_VAR(data__->GLOBALINDEX);
		if(globalIndex < Current_PLC_MonitoredItemsIndex)
		{
			localIndex = __GET_VAR(data__->LOCALINDEX) - 1;
			__SET_VAR(data__->, VALUECHANGED, (valuesChanged[globalIndex])[localIndex]);
			__SET_VAR(data__->, DONE, 1);
		}
	}
}

int _state_UAClient(UAClient* data, int write, int value)	// helper function
{
	int returnValue = -1;
	void* UAPointer = NULL;

	if(data==NULL)
		return returnValue;

	switch(data->FBTYPE)
	{
		case UA_Connect :
			UAPointer = (UA_CONNECT*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_CONNECT*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_CONNECT*)UAPointer)->STATE);
			}

			break;

		case UA_Disconnect :
			UAPointer = (UA_DISCONNECT*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_DISCONNECT*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_DISCONNECT*)UAPointer)->STATE);
			}

			break;

		case UA_NamespaceGetIndexList :
			UAPointer = (UA_DISCONNECT*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_NAMESPACEGETINDEXLIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_NAMESPACEGETINDEXLIST*)UAPointer)->STATE);
			}

			break;

		case UA_NodeGetHandleList :
			UAPointer = (UA_NODEGETHANDLELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_NODEGETHANDLELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_NODEGETHANDLELIST*)UAPointer)->STATE);
			}

			break;

		case UA_NodeReleaseHandleList :
			UAPointer = (UA_NODERELEASEHANDLELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_NODERELEASEHANDLELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_NODERELEASEHANDLELIST*)UAPointer)->STATE);
			}

			break;

		case UA_NodeGetInformation :
			UAPointer = (UA_NODEGETINFORMATION*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_NODEGETINFORMATION*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_NODEGETINFORMATION*)UAPointer)->STATE);
			}

			break;

		case UA_SubscriptionCreate :
			UAPointer = (UA_SUBSCRIPTIONCREATE*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_SUBSCRIPTIONCREATE*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_SUBSCRIPTIONCREATE*)UAPointer)->STATE);
			}

			break;

		case UA_SubscriptionDelete :
			UAPointer = (UA_SUBSCRIPTIONDELETE*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_SUBSCRIPTIONDELETE*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_SUBSCRIPTIONDELETE*)UAPointer)->STATE);
			}

			break;

		case UA_SubscriptionProcessed :
			UAPointer = (UA_SUBSCRIPTIONPROCESSED*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_SUBSCRIPTIONPROCESSED*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_SUBSCRIPTIONPROCESSED*)UAPointer)->STATE);
			}

			break;

		case UA_MonitoredItemAddList :
			UAPointer = (UA_MONITOREDITEMADDLIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_MONITOREDITEMADDLIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_MONITOREDITEMADDLIST*)UAPointer)->STATE);
			}

			break;

		case UA_MonitoredItemRemoveList :
			UAPointer = (UA_MONITOREDITEMREMOVELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_MONITOREDITEMREMOVELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_MONITOREDITEMREMOVELIST*)UAPointer)->STATE);
			}

			break;

		case UA_MonitoredItemOperateList :
			UAPointer = (UA_MONITOREDITEMOPERATELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_MONITOREDITEMOPERATELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_MONITOREDITEMOPERATELIST*)UAPointer)->STATE);
			}

			break;

		case UA_ReadList :
			UAPointer = (UA_READLIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_READLIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_READLIST*)UAPointer)->STATE);
			}

			break;

		case UA_WriteList :
			UAPointer = (UA_WRITELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_WRITELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_WRITELIST*)UAPointer)->STATE);
			}

			break;

		case UA_MethodGetHandleList :
			UAPointer = (UA_METHODGETHANDLELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_METHODGETHANDLELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_METHODGETHANDLELIST*)UAPointer)->STATE);
			}

			break;

		case UA_MethodReleaseHandleList :
			UAPointer = (UA_METHODRELEASEHANDLELIST*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_METHODRELEASEHANDLELIST*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_METHODRELEASEHANDLELIST*)UAPointer)->STATE);
			}

			break;

		case UA_MethodCall :
			UAPointer = (UA_METHODCALL*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_METHODCALL*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_METHODCALL*)UAPointer)->STATE);
			}

			break;

		case UA_ConnectionGetStatus :
			UAPointer = (UA_CONNECTIONGETSTATUS*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((UA_CONNECTIONGETSTATUS*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((UA_CONNECTIONGETSTATUS*)UAPointer)->STATE);
			}

			break;

		case _UA_GetMonitoredItemVariableValueFB :
			UAPointer = (_UA_GETMONITOREDITEMVARIABLEVALUE*)(data->FBPOINTER);

			if(write)
			{
				__SET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)UAPointer)->, STATE, value);
			}
			else
			{
				returnValue = __GET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)UAPointer)->STATE);
			}

			break;

		default :
			break;
	}

	return returnValue;
}

void UAClientIterator(int* result, void** data)
{
	UAClient* data__;
    /*emergency exit*/
    if(UAClient_State & UACLIENT_FINISHED)
	{
    	free(*data);
    	*data = NULL;
    	return;
	}
	/* take ua-client mutex to prevent changing PLC data while PLC running */
	Lock_UAClient();
	/* Get current FB */
	data__ = UAClientFBs[Current_UAClient_UAClientFB];

	if(data__ && /* may be null at first run */
			_state_UAClient(data__, 0, -1) == UACLIENT_FB_PROCESSING){ /* some answer awaited*/
	   	/* If result not None */
	   	if(*result){
		/* copy results */
		/* remove block from fifo*/
	   	*result = 0;
		/* Mark block as answered */
	   	_state_UAClient(data__, 1, UACLIENT_FB_ANSWERED);
	   	free(UAClientFBs[Current_UAClient_UAClientFB]);
	   	UAClientFBs[Current_UAClient_UAClientFB] = NULL;
		/* Get a new line */
		Current_UAClient_UAClientFB = (Current_UAClient_UAClientFB + 1) %% %(UAClientFBCounts)d;
	   	}
	}
	/* while next slot is empty */
	while(((data__ = UAClientFBs[Current_UAClient_UAClientFB]) == NULL) ||
	 	  /* or doesn't contain command */
			_state_UAClient(data__, 0, -1) != UACLIENT_FB_REQUESTED)
	{
		UnLock_UAClient();
		/* wait next FB */
		if(Wait_UAClient_Commands())
		{
			free(*data);
	    	*data = NULL;
	    	return;
		}
		/*emergency exit*/
		if(UAClient_State & UACLIENT_FINISHED)
		{
			free(*data);
	    	*data = NULL;
	    	return;
		}
		Lock_UAClient();
	}
	/* Mark block as processing */
	_state_UAClient(data__, 1, UACLIENT_FB_PROCESSING);
	/* next command is BUFFER */
	CallOPCUAFuntion(result, data__);
	/* free python mutex */
	UnLock_UAClient();
	/* return the next command to compute */
}

int _SecurityMSG(UASECURITYMSGMODE mode)	// helper function
{
	switch(mode)
	{
		case UASECURITYMSGMODE__UASMM_BESTAVAILABLE :
			return PlcOpc_UASMM_BestAvailable;
		case UASECURITYMSGMODE__UASMM_NONE :
			return PlcOpc_UASMM_None;
		case UASECURITYMSGMODE__UASMM_SIGN :
			return PlcOpc_UASMM_Sign;
		case UASECURITYMSGMODE__UASMM_SIGNENCRYPT :
			return PlcOpc_UASMM_SignEncrypt;
		default :
			return PlcOpc_UASMM_None;
	}
}

int _SecurityPolicy(UASECURITYPOLICY mode)	// helper function
{
	switch(mode)
	{
		case UASECURITYPOLICY__UASP_BESTAVAILABLE :
			return PlcOpc_UASP_BestAvailable;
		case UASECURITYPOLICY__UASP_NONE :
			return PlcOpc_UASP_None;
		case UASECURITYPOLICY__UASP_BASIC128RSA15 :
			return PlcOpc_UASP_Basic128Rsa15;
		case UASECURITYPOLICY__UASP_BASIC256 :
			return PlcOpc_UASP_Basic256;
		case UASECURITYPOLICY__UASP_BASIC256SHA256 :
			return PlcOpc_UASP_Basic256Sha256;
		default :
			return PlcOpc_UASP_None;
	}
}

int _TransportProfile(UATRANSPORTPROFILE mode)	// helper function
{
	switch(mode)
	{
		case UATRANSPORTPROFILE__UATP_UATCP :
			return PlcOpc_UATP_UATcp;
		case UATRANSPORTPROFILE__UATP_WSHTTPBINARY :
			return PlcOpc_UATP_WSHttpBinary;
		case UATRANSPORTPROFILE__UATP_WSHTTPXMLORBINARY :
			return PlcOpc_UATP_WSHttpXmlOrBinary;
		case UATRANSPORTPROFILE__UATP_WSHTTPXML :
			return PlcOpc_UATP_WSHttpXml;
		default :
			return PlcOpc_UATP_UATcp;
	}
}

int _UserIdentityTokenType(UAUSERIDENTITYTOKENTYPE mode)	// helper function
{
	switch(mode)
	{
		case UAUSERIDENTITYTOKENTYPE__UAUITT_ANONYMOUS :
			return PlcOpc_UAUITT_Anonymous;
		case UAUSERIDENTITYTOKENTYPE__UAUITT_USERNAME :
			return PlcOpc_UAUITT_Username;
		case UAUSERIDENTITYTOKENTYPE__UAUITT_X509 :
			return PlcOpc_UAUITT_x509;
		case UAUSERIDENTITYTOKENTYPE__UAUITT_ISSUEDTOKEN :
			return PlcOpc_UAUITT_IssuedToken;
		default :
			return PlcOpc_UAUITT_Anonymous;
	}
}

void _UAConnectionStatus(PlcOpc_Int32 mode, void* pointer)	// helper function
{
	switch(mode)
	{
		case PlcOpc_UACS_Connected :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_CONNECTIONSTATUS, UACONNECTIONSTATUS__UACS_CONNECTED);
			break;
		case PlcOpc_UACS_ConnectionError :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_CONNECTIONSTATUS, UACONNECTIONSTATUS__UACS_CONNECTIONERROR);
			break;
		case PlcOpc_UACS_Shutdown :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_CONNECTIONSTATUS, UACONNECTIONSTATUS__UACS_SHUTDOWN);
			break;
		default :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_CONNECTIONSTATUS, UACONNECTIONSTATUS__UACS_CONNECTIONERROR);
			break;
	}
	return;
}

void _UAServerState(PlcOpc_Int32 mode, void* pointer)	// helper function
{
	switch(mode)
	{
		case PlcOpc_UASS_Running :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_RUNNING);
			break;
		case PlcOpc_UASS_Failed :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_FAILED);
			break;
		case PlcOpc_UASS_NoConfiguration :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_NOCONFIGURATION);
			break;
		case PlcOpc_UASS_Suspended :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_SUSPENDED);
			break;
		case PlcOpc_UASS_Shutdown :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_SHUTDOWN);
			break;
		case PlcOpc_UASS_Test :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_TEST);
			break;
		case PlcOpc_UASS_CommunicationFault :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_COMMUNICATIONFAULT);
			break;
		case PlcOpc_UASS_Unknown :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_UNKNOWN);
			break;
		default :
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVERSTATE, UASERVERSTATE__UASS_UNKNOWN);
			break;
	}
	return;
}

void _UANodeID(UAClient* pointer, PlcOpc_UInt32 NodeIDCount, PlcOpc_UANodeID* NodeIDs)
{
	PlcOpc_UInt32 index=0, index2 = 0;
	UANODEID temp;
	int checkType = -1;

	for(index = 0; index < NodeIDCount; index ++)
	{
		switch(pointer->FBTYPE)
		{
			case UA_NodeGetHandleList :
				temp = __GET_VAR(((UA_NODEGETHANDLELIST*)(pointer->FBPOINTER))->PRE_NODEIDS0, .ELEMENTS.table[index]);
				checkType = 1;
			break;
			case UA_NodeGetInformation :
				temp = __GET_VAR(((UA_NODEGETINFORMATION*)(pointer->FBPOINTER))->PRE_NODEID0);
				checkType = 1;
			break;
			case UA_MethodGetHandleList :
				if(index < NodeIDCount/2)
					temp = __GET_VAR(((UA_METHODGETHANDLELIST*)(pointer->FBPOINTER))->PRE_OBJECTNODEIDS0, .ELEMENTS.table[index]);
				else
					temp = __GET_VAR(((UA_METHODGETHANDLELIST*)(pointer->FBPOINTER))->PRE_METHODNODEIDS0, .ELEMENTS.table[index - (NodeIDCount/2)]);
				checkType = 1;
			break;
			default :
				printf("Unknown Type\n");
			break;
		}

		if(checkType == -1)
			return;

		NodeIDs[index].IdentifierType = temp.IDENTIFIERTYPE;
		NodeIDs[index].NamespaceIndex = temp.NAMESPACEINDEX;

		switch(NodeIDs[index].IdentifierType)
		{
			case UAIDENTIFIERTYPE__UAIT_NUMERIC :
			case UAIDENTIFIERTYPE__UAIT_STRING :
				for(index2 = 0; index2 < temp.IDENTIFIER.len; index2 ++)
				{
					if(index2==STR_MAX_LEN)
					{
						NodeIDs[index].Identifier[index2] = '\0' ;
						break;
					}
					NodeIDs[index].Identifier[index2] = temp.IDENTIFIER.body[index2];
				}
				if(temp.IDENTIFIER.len < STR_MAX_LEN)
					NodeIDs[index].Identifier[index2] = '\0' ;
				break;
			default :
				printf("Unknown data\n");
		}
	}
}

void __UANodeHdl(PlcOpc_Handle* NodeHdls, PlcOpc_UInt32 NodeIDCount, UA_NODEGETHANDLELIST* nodegethandlelist_point)
{
	PlcOpc_UInt32 index = 0;

	for(index = 0; index < NodeIDCount; index ++)
		__SET_VAR(nodegethandlelist_point->, PRE_NODEHDLS, (int)NodeHdls[index], .ELEMENTS.table[index]);
}

void __UAVariable(PlcOpc_DataValue* Variables, PlcOpc_UInt32 NodeHdlCount, UA_READLIST* nodereadlist_point)
{
	int index = 0;
	PlcOpc_CharA result[STR_MAX_LEN];
	memset(result, 0, STR_MAX_LEN);
	STRING temp;

	for(index=0; index<NodeHdlCount; index++)
	{
		PlcOpc_UA_GetPlcValueString(Variables+index, result, STR_MAX_LEN);
		strncpy((char*)temp.body, result, strlen(result));
		temp.len = strlen(result);
		__SET_VAR(nodereadlist_point->, PRE_VARIABLES, temp, .ELEMENTS.table[index]);
	}
}

int __UAVariable_(PlcOpc_DataValue* Variables, PlcOpc_UInt32 NodeHdlCount, UA_WRITELIST* pointer)
{
	int index = 0;
	PlcOpc_UInt32 uStatus = -1;
	PlcOpc_Handle* NodeHdls = (PlcOpc_Handle*)malloc(NodeHdlCount*sizeof(PlcOpc_Handle));
	PlcOpc_DataValue* Read_Result = (PlcOpc_DataValue*)malloc(NodeHdlCount*sizeof(PlcOpc_DataValue));
	PlcOpc_UANodeAdditionalInfo* NodeAddInfo = (PlcOpc_UANodeAdditionalInfo*)malloc(NodeHdlCount*sizeof(PlcOpc_UANodeAdditionalInfo));
	PlcOpc_Handle ConnectionHdl = (PlcOpc_Handle)__GET_VAR(pointer->PRE_CONNECTIONHDL0);
	STRING value_string;
	char* str = NULL;

	if((NodeHdls == NULL) || (Read_Result == NULL) || (NodeAddInfo == NULL))
	{
		printf("Memory allocation failed at __UAVariable_\n");
		goto error;
	}

	for(index = 0; index<NodeHdlCount; index++)
	{
		NodeHdls[index] = (PlcOpc_Handle)(__GET_VAR(pointer->PRE_NODEHDLS, .ELEMENTS.table[index]));
		NodeAddInfo[index].AttributeID = PlcOpc_UAAI_Value;
		NodeAddInfo[index].IndexRange[0].StartIndex = 0;
		NodeAddInfo[index].IndexRange[0].EndIndex = 0;
	}

	uStatus = PlcOpc_UA_ReadList(hApplication, ConnectionHdl, NodeHdlCount, NodeHdls, NodeAddInfo, 0, Read_Result);

	if(uStatus != 0)
	{
		printf("Readint Data type failed at __UAVariable_ : %%x\n", ((unsigned int)uStatus));
		goto error;
	}

	for(index = 0; index<NodeHdlCount; index++)
	{
		value_string = __GET_VAR(pointer->PRE_VARIABLES, .ELEMENTS.table[index]);
		str = (char*)malloc(value_string.len * sizeof(char));
		strcpy(str, (char*)(value_string.body));
		Variables[index].Value.Type = Read_Result[index].Value.Type;
		switch(Variables[index].Value.Type)
		{
			case PlcOpc_VariantType_Boolean :
				if(!strcasecmp(str, "true"))
					Variables[index].Value.Value.Boolean = true;
				else if(!strcasecmp(str, "false"))
					Variables[index].Value.Value.Boolean = false;
				else
					printf("%%d : Not Supported dataType(Boolean)\n", index);
				break;
			case PlcOpc_VariantType_Byte :
				Variables[index].Value.Value.Byte = atoi(str);
				break;
			case PlcOpc_VariantType_Int16 :
				Variables[index].Value.Value.Int16 = atoi(str);
				break;
			case PlcOpc_VariantType_Int32 :
				Variables[index].Value.Value.Int32 = atoi(str);
				break;
			case PlcOpc_VariantType_UInt16 :
				Variables[index].Value.Value.UInt16 = atoi(str);
				break;
			case PlcOpc_VariantType_UInt32 :
				Variables[index].Value.Value.UInt32 = atoi(str);
				break;
			case PlcOpc_VariantType_Double :
				Variables[index].Value.Value.Double = atof(str);
				break;
			case PlcOpc_VariantType_StringA :
				strncpy(Variables[index].Value.Value.StringA, str, strlen(str));
				break;
			case PlcOpc_VariantType_Float :
				Variables[index].Value.Value.Float = atof(str);
				break;
			default :
				printf("%%d : Not Supported dataType (%%d)\n", index, Variables[index].Value.Type);
				uStatus = 1;
				free(str);
				str=NULL;
				goto error;
				break;
		}
		free(str);
		str=NULL;
	}
	uStatus = 0;

	error :
		free(NodeHdls);
		NodeHdls = NULL;
		free(Read_Result);
		Read_Result = NULL;
		free(NodeAddInfo);
		NodeAddInfo = NULL;
		return uStatus;
}

void _UANodeInformation(UA_NODEGETINFORMATION* pointer, PlcOpc_UANodeInformation NodeInfo, PlcOpc_UInt32* NodeErrorIDs)
{
	// node class
	int index = PlcOpc_UAAI_NodeClass - 1;
	if(NodeErrorIDs[index] != 0)
	{
		printf("uStatus : %%x\n", ((unsigned int)NodeErrorIDs[index]));
		printf("can not find valid node class\n");
		return;
	}
    switch(NodeInfo.NodeClass)
    {
    case PlcOpc_UANCM_None :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_NONE, .NODECLASS);
        break;
    case PlcOpc_UANCM_Object :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_OBJECT, .NODECLASS);
        break;
    case PlcOpc_UANCM_Variable :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_VARIABLE, .NODECLASS);
    	break;
    case PlcOpc_UANCM_Method :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_METHOD, .NODECLASS);
        break;
    case PlcOpc_UANCM_ObjectType :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_OBJECTTYPE, .NODECLASS);
        break;
    case PlcOpc_UANCM_VariableType :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_VARIABLETYPE, .NODECLASS);
        break;
    case PlcOpc_UANCM_ReferenceType :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_REFERENCETYPE, .NODECLASS);
        break;
    case PlcOpc_UANCM_DataType :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_DATATYPE, .NODECLASS);
        break;
    case PlcOpc_UANCM_View :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_VIEW, .NODECLASS);
        break;
    case PlcOpc_UANCM_All :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_ALL, .NODECLASS);
        break;
    default :
    	__SET_VAR(pointer->, PRE_NODEINFO, UANODECLASSMASK__UANCM_NONE, .NODECLASS);
        break;
    }

	// BrowseName
	index = PlcOpc_UAAI_BrowseName - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.BrowseName.NamespaceIndex, .BROWSENAME.NAMESPACEINDEX);
		if(NodeInfo.BrowseName.Name != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .BROWSENAME.NAME.body)), NodeInfo.BrowseName.Name);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.BrowseName.Name), .BROWSENAME.NAME.len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .BROWSENAME.NAME.len);
	}

	// DisplayName
	index = PlcOpc_UAAI_DisplayName - 1;
	if(NodeErrorIDs[index] == 0)
	{
		if(NodeInfo.DisplayName.Locale != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .DISPLAYNAME.LOCALE.LOCALE.table[0].body)), NodeInfo.DisplayName.Locale);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.DisplayName.Locale), .DISPLAYNAME.LOCALE.LOCALE.table[0].len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .DISPLAYNAME.LOCALE.LOCALE.table[0].len);
		if(NodeInfo.DisplayName.Text != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .DISPLAYNAME.TEXT.body)), NodeInfo.DisplayName.Text);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.DisplayName.Text), .DISPLAYNAME.TEXT.len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .DISPLAYNAME.TEXT.len);
	}

	// Description
	index = PlcOpc_UAAI_Description - 1;
	if(NodeErrorIDs[index] == 0)
	{
		if(NodeInfo.Description.Locale != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .DESCRIPTION.LOCALE.LOCALE.table[0].body)), NodeInfo.Description.Locale);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.Description.Locale), .DESCRIPTION.LOCALE.LOCALE.table[0].len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .DESCRIPTION.LOCALE.LOCALE.table[0].len);
		if(NodeInfo.Description.Text != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .DESCRIPTION.TEXT.body)), NodeInfo.Description.Text);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.Description.Text), .DESCRIPTION.TEXT.len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .DESCRIPTION.TEXT.len);
	}

	// WriteMask
	index = PlcOpc_UAAI_WriteMask - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.WriteMask, .WRITEMASK);
	}

	// UserWriteMask
	index = PlcOpc_UAAI_UserWriteMask;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.UserWriteMask, .USERWRITEMASK);
	}

	// IsAbstract
	index = PlcOpc_UAAI_IsAbstract - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.IsAbstract, .ISABSTRACT);
	}

	// Symmetric
	index = PlcOpc_UAAI_Symmetric - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.Symmetric, .SYMMETRIC);
	}

	// InverseName
	index = PlcOpc_UAAI_InverseName - 1;
	if(NodeErrorIDs[index] == 0)
	{
		if(NodeInfo.InverseName != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .INVERSENAME.body)), NodeInfo.InverseName);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.InverseName), .INVERSENAME.len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .INVERSENAME.len);
	}

	// ContainsNoLoops -> not supported

	// EventNotifier
	index = PlcOpc_UAAI_EventNotifier - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.EventNotifier, .EVENTNOTIFIER);
	}

	// DataType
	index = PlcOpc_UAAI_DataType - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.DataType.NamespaceIndex, .DATATYPE.NAMESPACEINDEX);
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.DataType.IdentifierType, .DATATYPE.IDENTIFIERTYPE);
		if(NodeInfo.DataType.Identifier != NULL)
		{
			strcpy(((char*)__GET_VAR(pointer->PRE_NODEINFO, .DATATYPE.IDENTIFIER.body)), NodeInfo.DataType.Identifier);
			__SET_VAR(pointer->, PRE_NODEINFO, strlen(NodeInfo.DataType.Identifier), .DATATYPE.IDENTIFIER.len);
		}
		else
			__SET_VAR(pointer->, PRE_NODEINFO, 0, .DATATYPE.IDENTIFIER.len);
	}

	// ValueRank
	index = PlcOpc_UAAI_ValueRank - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.ValueRank, .VALUERANK);
	}

	// ArrayDimension
	index = PlcOpc_UAAI_ArrayDimensions - 1;
	if(NodeErrorIDs[index] == 0)
	{
		for(index=0; index<NodeInfo.ValueRank; index++)
		{
			__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.ArrayDimension[index], .ARRAYDIMENSION.ELEMENTS.table[index]);
		}
	}

	// AccessLevel
	index = PlcOpc_UAAI_AccessLevel - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.AccessLevel, .ACCESSLEVEL);
	}

	// UserAccessLevel
	index = PlcOpc_UAAI_UserAccessLevel - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.UserAccessLevel, .USERACCESSLEVEL);
	}

	// MinimumSamplingInterval, TODO : convert PlcOpc_StringA to TIME
//	index = PlcOpc_UAAI_MinimumSamplingInterval - 1;
//	if(NodeErrorIDs[index] == 0)
//	{
//		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.MinimumSamplingInterval, .MINIMUMSAMPLINGINTERVAL);
//	}

	// Historizing
	index = PlcOpc_UAAI_Historizing - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.Historizing, .HISTORIZING);
	}

	// Executable
	index = PlcOpc_UAAI_Executable - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.Executable, .EXECUTABLE);
	}

	// UserExecutable
	index = PlcOpc_UAAI_UserExecutable - 1;
	if(NodeErrorIDs[index] == 0)
	{
		__SET_VAR(pointer->, PRE_NODEINFO, NodeInfo.UserExecutable, .USEREXECUTABLE);
	}
}

void _UA_MethodInputArguments(UA_METHODCALL* pointer, PlcOpc_MethodParameter** PlcOpc_variable)
{
	int index = 0;

	PlcOpc_variable[0]->NoOfArgument = __GET_VAR(pointer->PRE_INPUTARGUMENTS0, .NOOFARGUMENT);
	if( PlcOpc_variable[0]->NoOfArgument == 0 )
		PlcOpc_variable[0]->Arguments = NULL;
	else
		PlcOpc_variable[0]->Arguments = (PlcOpc_Variant*)malloc( sizeof(PlcOpc_Variant) * (PlcOpc_variable[0]->NoOfArgument) );

	for(index=0; index < PlcOpc_variable[0]->NoOfArgument; index++)
	{
		PlcOpc_variable[0]->Arguments[index].Type = __GET_VAR(pointer->PRE_INPUTARGUMENTS0, .ARGUMENTS.ELEMENTS.table[index].VARIANTTYPE);
		switch(PlcOpc_variable[0]->Arguments[index].Type)
		{
			case _UA_VARIANTTYPE__PLCOPEN_VARIANTTYPE_DOUBLE :
				PlcOpc_variable[0]->Arguments[index].Value.Double = atof( ((char*)__GET_VAR(pointer->PRE_INPUTARGUMENTS0, .ARGUMENTS.ELEMENTS.table[index].VALUE.body)) );
				break;
			default :
				break;
		}
	}
}

void _UA_MethodOutputArguments(UA_METHODCALL* pointer, PlcOpc_MethodParameter** PlcOpc_variable)
{
	int index = 0;
	int* dec = (int*)malloc(sizeof(int));
	int* sign = (int*)malloc(sizeof(int));

	__SET_VAR(pointer->, PRE_OUTPUTARGUMENTS1, PlcOpc_variable[1]->NoOfArgument, .NOOFARGUMENT);

	for(index=0; index < (PlcOpc_variable[1]->NoOfArgument); index++)
	{
		switch(PlcOpc_variable[1]->Arguments[index].Type)
		{
			case PlcOpc_VariantType_Double :
				snprintf((char*)(__GET_VAR(pointer->PRE_OUTPUTARGUMENTS1, .ARGUMENTS.ELEMENTS.table[index].VALUE.body)), STR_MAX_LEN, "%%lf", PlcOpc_variable[1]->Arguments[index].Value.Double);
				__SET_VAR(pointer->, PRE_OUTPUTARGUMENTS1, strlen((char*)(__GET_VAR(pointer->PRE_OUTPUTARGUMENTS1, .ARGUMENTS.ELEMENTS.table[index].VALUE.body))), .ARGUMENTS.ELEMENTS.table[index].VALUE.len);
				break;
			default :
				break;
		}
	}

	free(dec);
	dec = NULL;
	free(sign);
	sign = NULL;
}

void CallOPCUAFuntion(int* result, void* data)
{
	// TODO : call OpenOpcUa client Functions.

	void* pointer = ((UAClient*)data)->FBPOINTER;
	int index = 0;

	PlcOpc_UInt32 count = 0;
	void* PlcOpc_output = NULL;
	void* PlcOpc_output2 = NULL;
	void* PlcOpc_variable = NULL;
	void* PlcOpc_errorID = NULL;

	PlcOpc_Handle ConnectionHdl;
	PlcOpc_StringA ServerEndpointUrl = NULL;
	PlcOpc_StringA* NamespaceUris = NULL;
	PlcOpc_UInt32 uStatus = -1;
	PlcOpc_Double Timeout = 0;
	PlcOpc_UANodeID NodeIDs[20];
	PlcOpc_Handle NodeHdls[20];
	PlcOpc_UInt32 NodeErrorIDs[20];
	PlcOpc_UANodeAdditionalInfo NodeAddInfos[20];
	PlcOpc_DataValue Variables[20];
	PlcOpc_UAMonitoringParameter MonitoringSettings[20];
	PlcOpc_UInt32 RemainingValueCount[20];
	PlcOpc_DateTime TimeStamps[20];
	PlcOpc_Handle NodeQualityIDs[20];
	int globalIndex = 0;
	int localIndex = 0;

	switch(((UAClient*)data)->FBTYPE)
	{
		case UA_Connect :	//TODO : TIMEOUT conversion and check input variables unused.
			ServerEndpointUrl = (PlcOpc_StringA)__GET_VAR(((UA_CONNECT*)pointer)->PRE_SERVERENDPOINTURL0, .body);
			PlcOpc_SessionConnectInfo SessionConnectInfo;
			SessionConnectInfo.SessionName = (PlcOpc_StringA)__GET_VAR(((UA_CONNECT*)pointer)->PRE_SESSIONCONNECTINFO0, .SESSIONNAME.body);
			SessionConnectInfo.ApplicationName = "\0";
			SessionConnectInfo.SecurityMsgMode = _SecurityMSG(__GET_VAR(((UA_CONNECT*)pointer)->PRE_SESSIONCONNECTINFO0, .SECURITYMSGMODE));
			SessionConnectInfo.SecurityPolicy = _SecurityPolicy(__GET_VAR(((UA_CONNECT*)pointer)->PRE_SESSIONCONNECTINFO0, .SECURITYPOLICY));
			SessionConnectInfo.TransportProfile = _TransportProfile(__GET_VAR(((UA_CONNECT*)pointer)->PRE_SESSIONCONNECTINFO0, .TRANSPORTPROFILE));
			SessionConnectInfo.UserIdentityToken.UserIdentityTokenType = _UserIdentityTokenType(__GET_VAR(((UA_CONNECT*)pointer)->PRE_SESSIONCONNECTINFO0, .USERIDENTITYTOKEN.USERIDENTITYTOKENTYPE));
			SessionConnectInfo.SessionTimeout = 1000000.0;
			uStatus = PlcOpc_UA_Connect(hApplication, ServerEndpointUrl, SessionConnectInfo, SessionConnectInfo.SessionTimeout , &ConnectionHdl);
			__SET_VAR(((UA_CONNECT*)pointer)->, PRE_CONNECTIONHDL, (int)ConnectionHdl);
			__SET_VAR(((UA_CONNECT*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_Disconnect :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_DISCONNECT*)pointer)->PRE_CONNECTIONHDL0);
			uStatus = PlcOpc_UA_Disconnect(hApplication, ConnectionHdl, Timeout);
			__SET_VAR(((UA_DISCONNECT*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_NamespaceGetIndexList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->PRE_CONNECTIONHDL0);
			count = (PlcOpc_UInt32)__GET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->PRE_NAMESPACEURISCOUNT);
			PlcOpc_output = (PlcOpc_Int*)malloc(count*sizeof(PlcOpc_Int32));
			NamespaceUris = (PlcOpc_StringA*)malloc(count*sizeof(PlcOpc_StringA));
			for(index = 0; index<count; index++)
				NamespaceUris[index] = (PlcOpc_StringA)malloc(100*sizeof(PlcOpc_CharA));
			PlcOpc_errorID = (PlcOpc_UInt32*)malloc(count*sizeof(PlcOpc_UInt32));
			if ( (PlcOpc_output != NULL) && (NamespaceUris!=NULL) && (PlcOpc_errorID!=NULL) )
			{
				for(index = 0; index<count; index++)
				{
					strcpy(NamespaceUris[index], (char*)(__GET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->PRE_NAMESPACEURIS, .ELEMENTS.table[index].body)));
					NamespaceUris[index][__GET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->PRE_NAMESPACEURIS, .ELEMENTS.table[index].len)] = '\0';
				}
				uStatus = PlcOpc_UA_NamespaceGetIndexList(hApplication, ConnectionHdl, count, NamespaceUris, Timeout, (PlcOpc_Int32*)PlcOpc_output, PlcOpc_errorID);
				for(index = 0; index<count; index++)
					__SET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->, PRE_NAMESPACEINDEXES, ((PlcOpc_Int32*)PlcOpc_output)[index], .ELEMENTS.table[index]);
				__SET_VAR(((UA_NAMESPACEGETINDEXLIST*)pointer)->, PRE_ERRORID, uStatus);
			}
			else
				printf("Memory allocation failed at UA_NamespaceGetIndexList\n");
			for(index=0; index<count; index++)
			{
				free(NamespaceUris[index]);	NamespaceUris[index] = NULL;
			}
			free(NamespaceUris);				NamespaceUris = NULL;
			free(PlcOpc_output);				PlcOpc_output = NULL;
			free(PlcOpc_errorID);				PlcOpc_errorID = NULL;
			*result = 1;
			break;
		case UA_NodeGetHandleList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_NODEGETHANDLELIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_NODEGETHANDLELIST*)pointer)->PRE_NODEIDCOUNT0);
			_UANodeID(((UAClient*)(data)), count, NodeIDs);
			uStatus = PlcOpc_UA_NodeGetHandleList(hApplication, ConnectionHdl, count, NodeIDs, Timeout, NodeHdls, NodeErrorIDs);
			__UANodeHdl(NodeHdls, count, ((UA_NODEGETHANDLELIST*)pointer));
			__SET_VAR(((UA_NODEGETHANDLELIST*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_NodeReleaseHandleList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_NODERELEASEHANDLELIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_NODERELEASEHANDLELIST*)pointer)->PRE_NODEHDLCOUNT0);
			for(index=0; index<count; index++)
				NodeHdls[index] = (PlcOpc_Handle)(__GET_VAR(((UA_NODERELEASEHANDLELIST*)pointer)->PRE_NODEHDLS, .ELEMENTS.table[index]));
			uStatus = PlcOpc_UA_NodeReleaseHandleList(hApplication, ConnectionHdl, count, NodeHdls, Timeout, NodeErrorIDs);
			__SET_VAR(((UA_NODERELEASEHANDLELIST*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_NodeGetInformation :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_NODEGETINFORMATION*)pointer)->PRE_CONNECTIONHDL0);
			_UANodeID(((UAClient*)(data)), 1, NodeIDs);
			PlcOpc_output = (PlcOpc_UANodeInformation*)malloc(sizeof(PlcOpc_UANodeInformation));
			PlcOpc_errorID = (PlcOpc_UInt32*)malloc(22*sizeof(PlcOpc_UInt32));
			if( (PlcOpc_output != NULL) && (PlcOpc_errorID != NULL) )
			{
				uStatus = PlcOpc_UA_NodeGetInformation(hApplication, ConnectionHdl, NodeIDs[0], Timeout, PlcOpc_output, PlcOpc_errorID);
				_UANodeInformation(((UA_NODEGETINFORMATION*)(pointer)), *((PlcOpc_UANodeInformation*)(PlcOpc_output)), ((PlcOpc_UInt32*)(PlcOpc_errorID)));
				__SET_VAR(((UA_NODEGETINFORMATION*)pointer)->, ERRORID, uStatus);
			}
			else
				printf("Memory allocation failed at UA_NodeGetInformation\n");
			free(PlcOpc_output);		PlcOpc_output = NULL;
			free(PlcOpc_errorID);		PlcOpc_errorID = NULL;
			*result = 1;
			break;
		case UA_SubscriptionCreate :	//TODO : Publishing Interval read / write.
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_SUBSCRIPTIONCREATE*)pointer)->PRE_CONNECTIONHDL0);
			PlcOpc_output = NULL;
			PlcOpc_output2 = (PlcOpc_Double*)malloc(sizeof(PlcOpc_Double));
			if( (PlcOpc_output2 != NULL) )
			{
				*((PlcOpc_Double*)PlcOpc_output2) = (PlcOpc_Double)0;
				uStatus = PlcOpc_UA_SubscriptionCreate(hApplication, ConnectionHdl, ((PlcOpc_Boolean)__GET_VAR(((UA_SUBSCRIPTIONCREATE*)pointer)->PRE_PUBLISHINGENABLE0)),
														((PlcOpc_Byte)__GET_VAR(((UA_SUBSCRIPTIONCREATE*)pointer)->PRE_PRIORITY0)), Timeout,
														(PlcOpc_SubscriptionHdl*)(&PlcOpc_output), ((PlcOpc_Double*)PlcOpc_output2));
				__SET_VAR(((UA_SUBSCRIPTIONCREATE*)pointer)->, PRE_ERRORID, uStatus);
				__SET_VAR(((UA_SUBSCRIPTIONCREATE*)pointer)->, PRE_SUBSCRIPTIONHDL, ((PlcOpc_UInt32)((PlcOpc_SubscriptionHdl)PlcOpc_output)));
			}
			else
				printf("Memory allocation failed at UA_SubscriptionCreate\n");
			PlcOpc_output = NULL;
			free(PlcOpc_output2);		PlcOpc_output2 = NULL;
			*result = 1;
			break;
		case UA_SubscriptionDelete :
			uStatus = PlcOpc_UA_SubscriptionDelete(hApplication, (PlcOpc_SubscriptionHdl)__GET_VAR(((UA_SUBSCRIPTIONDELETE*)pointer)->PRE_SUBSCRIPTIONHDL0), Timeout);
			__SET_VAR(((UA_SUBSCRIPTIONDELETE*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_SubscriptionProcessed :
			PlcOpc_output = (PlcOpc_Boolean*)malloc(sizeof(PlcOpc_Boolean));
			uStatus = PlcOpc_UA_SubscriptionProcessed(hApplication, ((PlcOpc_SubscriptionHdl)__GET_VAR(((UA_SUBSCRIPTIONPROCESSED*)pointer)->PRE_SUBSCRIPTIONHDL0)), Timeout,
															PlcOpc_output);
			__SET_VAR(((UA_SUBSCRIPTIONPROCESSED*)pointer)->, PRE_PUBLISHED, *((PlcOpc_Boolean*)PlcOpc_output));
			free(PlcOpc_output);
			PlcOpc_output = NULL;
			*result = 1;
			break;
		case UA_MonitoredItemAddList :
			PlcOpc_output = NULL; // MonitoredItemHdls

			if(Current_PLC_MonitoredItemsIndex > 20)
			{
				__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_ERRORID, 3);
				*result = 1;
				break;
			}

			for(index=0; index<((PlcOpc_UInt32)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0)); index++)
			{
				NodeAddInfos[index].AttributeID = PlcOpc_UAAI_Value;
				NodeAddInfos[index].IndexRange[0].StartIndex = 0;
				NodeAddInfos[index].IndexRange[0].EndIndex = 0;

				// MonitoringSettings
				MonitoringSettings[index].Deadband = 0;
				MonitoringSettings[index].DiscardOldest = 0;
				MonitoringSettings[index].QueueSize = __GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_MONITORINGSETTINGS0, .ELEMENTS.table[index].QUEUESIZE);
				MonitoringSettings[index].SamplingInterval = 0;
				MonitoringSettings[index].UADeadbandType = 0;
				// NodeHdls
				NodeHdls[index] = ((PlcOpc_Handle)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLS0, .ELEMENTS.table[index]));
			}
			if( ((PlcOpc_SubscriptionHdl*)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_SUBSCRIPTIONHDL0)) != NULL )
			{
				variables[Current_PLC_MonitoredItemsIndex] = (unsigned char**)malloc(sizeof(unsigned char*)
																						*__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0));
				for(index=0; index<__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0); index++)
					variables[Current_PLC_MonitoredItemsIndex][index] = (unsigned char*)malloc(sizeof(unsigned char)*STR_MAX_LEN);
				valuesChanged[Current_PLC_MonitoredItemsIndex] = (bool*)malloc(sizeof(bool)*__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0));
				valuesUpdate[Current_PLC_MonitoredItemsIndex] = (bool*)malloc(sizeof(bool)*__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0));
				if( (variables[Current_PLC_MonitoredItemsIndex] != NULL) && (valuesChanged[Current_PLC_MonitoredItemsIndex] != NULL) )
				{
					uStatus = PlcOpc_UA_MonitoredItemAddList(hApplication, (PlcOpc_SubscriptionHdl)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_SUBSCRIPTIONHDL0),
																(PlcOpc_UInt32)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0), NodeHdls, NodeAddInfos,
																Timeout, NodeErrorIDs, (PlcOpc_MonitoredItemHdl**)(&PlcOpc_output), Current_PLC_MonitoredItemsIndex,
																MonitoringSettings, Current_PLC_MonitoredItemsIndex, RemainingValueCount, TimeStamps, NodeQualityIDs);
					if(uStatus == 0)
					{
						for(index=0; index<((PlcOpc_UInt32)__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0)); index++)
						{
							__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_MONITOREDITEMHDLS,
										((PlcOpc_UInt32)(((PlcOpc_MonitoredItemHdl*)PlcOpc_output)[index])), .ELEMENTS.table[index]);
						}
						__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_VARIABLES1, Current_PLC_MonitoredItemsIndex);
						__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_VALUESCHANGED1, Current_PLC_MonitoredItemsIndex);
						Current_PLC_MonitoredItemsIndex = Current_PLC_MonitoredItemsIndex + 1;
					}
					else
					{
						for(index=0; index<__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0); index++)
							free(variables[Current_PLC_MonitoredItemsIndex][index]);
						free(variables[Current_PLC_MonitoredItemsIndex]);
						variables[Current_PLC_MonitoredItemsIndex] = NULL;
						free(valuesChanged[Current_PLC_MonitoredItemsIndex]);
						valuesChanged[Current_PLC_MonitoredItemsIndex] = NULL;
					}
					__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_ERRORID, uStatus);
				}
				else
				{
					for(index=0; index<__GET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->PRE_NODEHDLCOUNT0); index++)
						free(variables[Current_PLC_MonitoredItemsIndex][index]);
					free(variables[Current_PLC_MonitoredItemsIndex]);
					variables[Current_PLC_MonitoredItemsIndex] = NULL;
					free(valuesChanged[Current_PLC_MonitoredItemsIndex]);
					valuesChanged[Current_PLC_MonitoredItemsIndex] = NULL;
					free(valuesUpdate[Current_PLC_MonitoredItemsIndex]);
					valuesUpdate[Current_PLC_MonitoredItemsIndex] = NULL;
					__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_ERRORID, 2);
				}
			}
			else
			{
				__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_ERRORID, 1);
			}
			*result = 1;
			break;
		case UA_MonitoredItemRemoveList :	//TODO : free pointer "PlcOpc_output" at MonitoredItemAddList
			if(Current_PLC_MonitoredItemsIndex < 1)
			{
				__SET_VAR(((UA_MONITOREDITEMADDLIST*)pointer)->, PRE_ERRORID, 1);
				*result = 1;
				break;
			}
			PlcOpc_variable = (PlcOpc_MonitoredItemHdl*)malloc(sizeof(PlcOpc_MonitoredItemHdl) * __GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0));
			for(index=0; index<__GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0); index++)
			{
				((PlcOpc_MonitoredItemHdl*)PlcOpc_variable)[index] = ((PlcOpc_MonitoredItemHdl)
																		__GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_MONITOREDITEMHDLS0, .ELEMENTS.table[index]));
			}
			uStatus = PlcOpc_UA_MonitoredItemRemoveList(hApplication, (PlcOpc_SubscriptionHdl)__GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_SUBSCRIPTIONHDL0),
															((PlcOpc_UInt32)__GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0)),
															(PlcOpc_MonitoredItemHdl*)(PlcOpc_variable), Timeout,
															NodeErrorIDs);
			if(uStatus == 0)
			{
				Current_PLC_MonitoredItemsIndex = Current_PLC_MonitoredItemsIndex - 1;
				for(index=0; index<__GET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0); index++)
					free(variables[Current_PLC_MonitoredItemsIndex+1][index]);
				free(variables[Current_PLC_MonitoredItemsIndex+1]);
				variables[Current_PLC_MonitoredItemsIndex+1] = NULL;
				free(valuesChanged[Current_PLC_MonitoredItemsIndex+1]);
				valuesChanged[Current_PLC_MonitoredItemsIndex+1] = NULL;
				free(valuesUpdate[Current_PLC_MonitoredItemsIndex+1]);
				valuesUpdate[Current_PLC_MonitoredItemsIndex+1] = NULL;
			}
			free(PlcOpc_variable);
			PlcOpc_variable = NULL;
			__SET_VAR(((UA_MONITOREDITEMREMOVELIST*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_MonitoredItemOperateList :
			PlcOpc_output = (PlcOpc_Boolean*)malloc(sizeof(PlcOpc_Boolean));
			PlcOpc_variable = (PlcOpc_MonitoredItemHdl*)malloc(sizeof(PlcOpc_MonitoredItemHdl)*__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0));
			for(index=0; index<__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0);index++)
			{
				((PlcOpc_MonitoredItemHdl*)PlcOpc_variable)[index] =
						((PlcOpc_MonitoredItemHdl)__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)-> PRE_MONITOREDITEMHDLS, .ELEMENTS.table[index]));
			}
			if( ((PlcOpc_SubscriptionHdl)__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->PRE_SUBSCRIPTIONHDL0)) != NULL )
			{
				uStatus = PlcOpc_UA_MonitoredItemOperateList(hApplication, ((PlcOpc_SubscriptionHdl)__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->PRE_SUBSCRIPTIONHDL0)),
																((PlcOpc_UInt32)__GET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->PRE_MONITOREDITEMHDLCOUNT0)),
																((PlcOpc_MonitoredItemHdl*)PlcOpc_variable), PlcOpc_output);
				__SET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->, PRE_PUBLISHED, *((PlcOpc_Boolean*)PlcOpc_output));
				__SET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->, PRE_ERRORID, uStatus);
			}
			else
			{
				__SET_VAR(((UA_MONITOREDITEMOPERATELIST*)pointer)->, PRE_ERRORID, 1);
			}
			free(PlcOpc_variable);
			PlcOpc_variable = NULL;
			free(PlcOpc_output);
			PlcOpc_output = NULL;
			*result = 1;
			break;
		case UA_ReadList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_READLIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_READLIST*)pointer)->PRE_NODEHDLCOUNT0);
			for(index=0; index<count; index++)
			{
				NodeHdls[index] = (PlcOpc_Handle)(__GET_VAR(((UA_READLIST*)pointer)->PRE_NODEHDLS, .ELEMENTS.table[index]));
				NodeAddInfos[index].AttributeID = PlcOpc_UAAI_Value;
				NodeAddInfos[index].IndexRange[0].EndIndex = 0;
				NodeAddInfos[index].IndexRange[0].StartIndex = 0;
			}
			uStatus = PlcOpc_UA_ReadList(hApplication, ConnectionHdl, count, NodeHdls, NodeAddInfos, Timeout, Variables);
			__SET_VAR(((UA_READLIST*)pointer)->, PRE_ERRORID, uStatus);
			__UAVariable(Variables, count, ((UA_READLIST*)pointer));
			*result = 1;
			break;
		case UA_WriteList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_WRITELIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_WRITELIST*)pointer)->PRE_NODEHDLCOUNT0);
			for(index=0; index<count; index++)
			{
				NodeHdls[index] = (PlcOpc_Handle)(__GET_VAR(((UA_WRITELIST*)pointer)->PRE_NODEHDLS, .ELEMENTS.table[index]));
				NodeAddInfos[index].AttributeID = PlcOpc_UAAI_Value;
				NodeAddInfos[index].IndexRange[0].EndIndex = 0;
				NodeAddInfos[index].IndexRange[0].StartIndex = 0;
			}
			if(__UAVariable_(Variables, count, ((UA_WRITELIST*)pointer)) == 0)
				uStatus = PlcOpc_UA_WriteList(hApplication, ConnectionHdl, count, NodeHdls, NodeAddInfos, Timeout, Variables);
			else
				uStatus = 1;
			__SET_VAR(((UA_WRITELIST*)pointer)->, PRE_ERRORID, uStatus);
			*result = 1;
			break;
		case UA_MethodGetHandleList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_METHODGETHANDLELIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_METHODGETHANDLELIST*)pointer)->PRE_NODEIDCOUNT0);
			PlcOpc_output = (PlcOpc_Handle*)malloc(sizeof(PlcOpc_Handle)*count);
			PlcOpc_variable = (PlcOpc_UANodeID*)malloc(sizeof(PlcOpc_UANodeID)*count*2);
			_UANodeID(((UAClient*)(data)), count*2, ((PlcOpc_UANodeID*)(PlcOpc_variable)));
			uStatus = PlcOpc_UA_MethodGetHandleList(hApplication, ConnectionHdl, count, ((PlcOpc_UANodeID*)PlcOpc_variable), ((PlcOpc_UANodeID*)PlcOpc_variable) + count,
														Timeout, ((PlcOpc_Handle*)PlcOpc_output));
			if(uStatus == 0)
			{
				for(index=0; index<count; index++)
					__SET_VAR(((UA_METHODGETHANDLELIST*)pointer)->, PRE_METHODHDLS, ((int)((PlcOpc_Handle*)PlcOpc_output)[index]), .ELEMENTS.table[index]);
			}
			for(index=0; index<count; index++)
			{
				__SET_VAR(((UA_METHODGETHANDLELIST*)pointer)->, PRE_ERRORIDS, uStatus, .ELEMENTS.table[index]);
			}
			free(PlcOpc_output);
			PlcOpc_output = NULL;
			free(PlcOpc_variable);
			PlcOpc_variable = NULL;
			*result = 1;
			break;
		case UA_MethodReleaseHandleList :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_METHODRELEASEHANDLELIST*)pointer)->PRE_CONNECTIONHDL0);
			count = __GET_VAR(((UA_METHODRELEASEHANDLELIST*)pointer)->PRE_METHODHDLCOUNT0);
			PlcOpc_variable = (PlcOpc_Handle*)malloc(sizeof(PlcOpc_Handle)*count);
			for(index=0; index<count; index++)
				((PlcOpc_Handle*)PlcOpc_variable)[index] = (PlcOpc_Handle)__GET_VAR(((UA_METHODRELEASEHANDLELIST*)pointer)->PRE_METHODHDLS0, .ELEMENTS.table[index]);
			uStatus = PlcOpc_UA_MethodReleaseHandleList(hApplication, ConnectionHdl, count, ((PlcOpc_Handle*)PlcOpc_variable), Timeout);
			for(index=0; index<count; index++)
			{
				__SET_VAR(((UA_METHODRELEASEHANDLELIST*)pointer)->, PRE_ERRORIDS, uStatus, .ELEMENTS.table[index]);
			}
			free(PlcOpc_variable);
			PlcOpc_variable = NULL;
			*result = 1;
			break;
		case UA_MethodCall :
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_METHODCALL*)pointer)->PRE_CONNECTIONHDL0);
			PlcOpc_variable = (PlcOpc_MethodParameter**)malloc(sizeof(PlcOpc_MethodParameter*)*2);	// 0 : InputArguments, 1 : OutputArguments
			((PlcOpc_MethodParameter**)PlcOpc_variable)[0] = (PlcOpc_MethodParameter*)malloc(sizeof(PlcOpc_MethodParameter));
			_UA_MethodInputArguments(((UA_METHODCALL*)pointer), ((PlcOpc_MethodParameter**)PlcOpc_variable));
			((PlcOpc_MethodParameter**)PlcOpc_variable)[1] = (PlcOpc_MethodParameter*)malloc(sizeof(PlcOpc_MethodParameter));
			uStatus = PlcOpc_UA_MethodCall(hApplication, ConnectionHdl, ((PlcOpc_Handle)__GET_VAR(((UA_METHODCALL*)pointer)->PRE_METHODHDL0)), Timeout,
												((PlcOpc_MethodParameter**)PlcOpc_variable)[0],
												((PlcOpc_MethodParameter**)PlcOpc_variable)[1]);
			__SET_VAR(((UA_METHODCALL*)pointer)->, PRE_ERRORID, uStatus);
			if(uStatus == 0)
				_UA_MethodOutputArguments(((UA_METHODCALL*)pointer), ((PlcOpc_MethodParameter**)PlcOpc_variable));
			free(((PlcOpc_MethodParameter**)PlcOpc_variable)[0]->Arguments);
			((PlcOpc_MethodParameter**)PlcOpc_variable)[0]->Arguments = NULL;
			((PlcOpc_MethodParameter**)PlcOpc_variable)[0] = NULL;
			free(((PlcOpc_MethodParameter**)PlcOpc_variable)[0]);
			((PlcOpc_MethodParameter**)PlcOpc_variable)[0] = NULL;
			free(((PlcOpc_MethodParameter**)PlcOpc_variable)[1]);
			((PlcOpc_MethodParameter**)PlcOpc_variable)[1] = NULL;
			free(PlcOpc_variable);
			PlcOpc_variable = NULL;
			*result = 1;
			break;
		case UA_ConnectionGetStatus :
			PlcOpc_output = (PlcOpc_Int32*)malloc(2*sizeof(PlcOpc_Int32));
			PlcOpc_output2 = (PlcOpc_Byte*)malloc(sizeof(PlcOpc_Byte));
			ConnectionHdl = (PlcOpc_Handle)__GET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->PRE_CONNECTIONHDL0);
			uStatus = PlcOpc_UA_ConnectionGetStatus(hApplication, ConnectionHdl, ((PlcOpc_Int32*)PlcOpc_output),
												((PlcOpc_Int32*)PlcOpc_output)+1, ((PlcOpc_Byte*)PlcOpc_output2));
			__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_ERRORID, uStatus);
			if(uStatus == 0)
			{
				_UAConnectionStatus(*((PlcOpc_Int32*)PlcOpc_output), pointer);
				_UAServerState(*(((PlcOpc_Int32*)PlcOpc_output)+1), pointer);
				__SET_VAR(((UA_CONNECTIONGETSTATUS*)pointer)->, PRE_SERVICELEVEL, *((PlcOpc_Int32*)PlcOpc_output2));
			}
			free(PlcOpc_output); 	PlcOpc_output = NULL;
			free(PlcOpc_output2);	PlcOpc_output2 = NULL;
			*result = 1;
			break;
		case _UA_GetMonitoredItemVariableValueFB :
			globalIndex = __GET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)pointer)->GLOBALINDEX);
			if(globalIndex < Current_PLC_MonitoredItemsIndex)
			{
				localIndex = __GET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)pointer)->LOCALINDEX) - 1;
				__SET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)pointer)->, VALUE, strlen((char*)((variables[globalIndex][localIndex]))), .len);
				strcpy((char*)__GET_VAR(((_UA_GETMONITOREDITEMVARIABLEVALUE*)pointer)->VALUE, .body), (char*)((variables[globalIndex][localIndex])));
				(valuesUpdate[globalIndex])[localIndex] = false;
			}
			*result = 1;
			break;
		default :
			printf("default\n");
			break;
	}
}
#endif
