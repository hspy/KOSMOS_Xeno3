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
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <errno.h>
#include <unistd.h>
#include <netinet/in.h>
#include <limits.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <ctype.h>
#include <sys/time.h>
#include <fcntl.h>

#define PORT_NUMBER  9001

#define PORT 4950 
#define BUFSIZE 2048

#define CMD_READ_ONE_DATA 0x1 
#define CMD_READ_DUMP_DATA 0x2
#define CMD_WRITE_ONE_DATA 0x3 

typedef struct _stDataHeader
{
	long lCodeHead; //0x1 ReadData, 0x2 ReadDataDump, 0x3 WriteData
	long lDataSize; 
}stDataHeader; 

typedef union _uDataValue
{
	double dblV; 
	uint64_t uI64v;
	int64_t i64V;
	struct _lValue32
	{
		long hi;
		long low;
	}lv;
	struct _ulValue32
	{
		unsigned long hi;
		unsigned long low;
	}ulv; 
	struct _fValue32
	{
		float hi;
		float low;
	}fv;
	struct _strValue
	{
		char len;
    		char body[STR_MAX_LEN];
	}strv;
}uDataValue; 

enum _eDataType 
{
	eTypeErr=0,
	eLONG32, 	//SINT , INT , LONG
	eULONG32 ,	//USINT, UINT, ULONG, BOOL, BYTE,DWORD
	eFLOAT32, 	//REAL
	eLONG64,	//LINT, 
	eULONG64,	//ULINT
	eFLOAT64,	//LREAL
	eSTRING
}eDataType; 


extern unsigned int PLC_state;
extern unsigned int PLC_shutdown;

extern long AtomicCompareExchange(long*, long, long);
extern long long AtomicCompareExchange64(long long* , long long , long long);
extern int suspendDebug(int disable);
extern void resumeDebug(void);

pthread_t hmi_thread;
int hmi_thread_id;
int hmi_break;

void *HmiEntry(void);
int ReadValue(unsigned int id , uDataValue *pSetValue);
//int WriteValue(int id, int wValue);
int WriteValue(int id, void* force);

/** 0x1 ReadData Body(ldataSize=4) **
	long dataIndex;   => (4byte)
*****************************************/

/** 0x1 ReadData Return(ldataSize=16) **
	long dataIndex; (4byte)
	long dataType; (4byte)
	uDataValue dataVal; (8byte)
*****************************************/


/** 0x2 readDataDump Body(ldataSize= 4byte + dataCount *4byte) **
	long dataCount; (4byte)
	long [dataCount] ; (4byte * dataCount) =>index list
*****************************************/
/** 0x2 readDataDump Return(ldataSize=16 * dataCount) **
	long dataIndex[1]; (4byte)
	long dataType[1]; (4byte)
	uDataValue dataVal[1]; (8byte)
	long dataIndex[2]; (4byte)
	long dataType[2]; (4byte)
	uDataValue dataVal[2]; (8byte)
	....
	long dataIndex[n]; (4byte)
	long dataType[n]; (4byte)
	uDataValue dataVal[n]; (8byte)
*****************************************/


/** 0x3 WriteData Body(ldataSize=4) **	
long dataIndex;
long dataType; (4byte)
uDataValue dataVal; (8byte)
*****************************************/

/** 0x3 WriteData Body(ldataSize=4) **	
long dataIndex;
long dataType; (4byte)
uDataValue dataVal; (8byte)
*****************************************/



int __init_hmisock(void)
{
	printf("_init_hmisck start..");
	hmi_break = 0;
	//create,start thread
	if((hmi_thread_id = pthread_create(&hmi_thread, NULL, (void *)HmiEntry, NULL)) < 0){
		fprintf(stderr,"OPC thread create error\n");
	}
	fprintf(stderr,"\npthread create\n");
 
	return 0;
}


void send_to_all(int j, int i, int sockfd, int nbytes_recvd, char *recv_buf, fd_set *master) 
{ 
	if (FD_ISSET(j, master))
	{ 
		if (j != sockfd && j != i) 
		{ 
			if (send(j, recv_buf, nbytes_recvd, 0) == -1) 
			{			
				perror("send"); 
			} 
		} 
	} 
} 

/*
	클라이언트에서 요청한 '읽을 변수 index'를 읽어 buffer에 저장한다.
	파라미터
		[IN] id -> 읽을 변수 index
		[OUT] pszBuffer -> 데이터를 저장할 버퍼
	리턴값: pszBuffer에 저장된 크기.
*/
int ReadValueAndSetData(unsigned int id, unsigned char* pszBuffer)
{
	//printf("ReadValueAndSetData start. request index=%iu\n", id);
	uDataValue uSendVal;
	long lRetType;
	long *pTmp =0;
	int nInxPos = 0;
	uDataValue *pDVal=0;
	
	memset(&uSendVal, 0x00, sizeof(uSendVal));
	lRetType = ReadValue(id, &uSendVal);
	
	//printf("lRetType =%ld\n", lRetType);
	
	// ReadIndex
	pTmp = (long*)(pszBuffer + nInxPos);  
	*pTmp = id;
	nInxPos += sizeof(long); //index value (long)
	
	// ReadDataType
	pTmp = (long*)(pszBuffer + nInxPos);  
	*pTmp = lRetType;
	nInxPos += sizeof(long); //data type (long)
	
	if(lRetType == eSTRING)
	{
		pDVal = (uDataValue *)(pszBuffer + nInxPos) ;
		pDVal->strv = uSendVal.strv;
		nInxPos += (uSendVal.strv.len + 1);
	}
	else
	{
		// ReadData Union
		pDVal = (uDataValue *)(pszBuffer + nInxPos) ;
		pDVal->dblV = uSendVal.dblV;
		nInxPos += sizeof(uSendVal.dblV);  //data value (uDataValue)
	}
	
	return nInxPos;	
}

void send_recv(int iSock, fd_set *master, int sockfd, int fdmax) 
{
	int nbytes_recvd; 
	stDataHeader stDH ;  /* get data header */
	
	unsigned int  bytes_read =0;
	unsigned int  total_count =0;
	long *plIdx  =0;
	int nInxPos  = 0 ;
	long *pTmp =0;
	long *pDSizeTmp =0;
	unsigned char pReadData[BUFSIZE] = {0x00, }; 
	unsigned char pSendData[BUFSIZE] = {0x00, } ;

	if ((nbytes_recvd = recv(iSock,  &stDH, sizeof(stDataHeader), 0)) <= 0) 
	{ 
		if (nbytes_recvd == 0) 
		{ 
			//printf("socket %d hung up\n", iSock); 
		}
		else 
		{ 
			perror("recv"); 
		} 
		close(iSock); 
		FD_CLR(iSock, master); 
	}
	else 
	{
		if(stDH.lDataSize > 0)		
		{
			do
			{
				bytes_read = recv(iSock, &pReadData[total_count], stDH.lDataSize -total_count,0 );
				total_count += bytes_read; 

			}while(total_count < stDH.lDataSize);
		
			//printf("==> command=0x%02x. datasize=%li\n", (unsigned int)stDH.lCodeHead, stDH.lDataSize); 
			
			switch (stDH.lCodeHead)
			{
			case CMD_READ_ONE_DATA :	
				nInxPos = 0;
					
				//make header 
				// command
				nInxPos = 0;
				pTmp = (long*)(pSendData +nInxPos) ;  
				*pTmp = CMD_READ_DUMP_DATA;  //command
				nInxPos += sizeof(long); //index value (long)
				
				// datasize
				pDSizeTmp=(long*)(pSendData +nInxPos) ; 
				nInxPos += sizeof(long); //index value (long)				

				//Read  datavalue from Index 
				plIdx = (long *)(pReadData);
				//printf("request index=%ld\n", *plIdx);
				nInxPos += ReadValueAndSetData(*plIdx, pSendData + nInxPos);
				*pDSizeTmp =  nInxPos - sizeof(stDataHeader);
				
				//for(total_count  = 0 ; total_count  < nInxPos ; total_count ++)
				//{
					//if(total_count % 4 == 0) 
					//	fprintf(stderr,"\n");	
					
					//fprintf(stderr,"0x%2x  ",pSendData[total_count]);	
				//}
				
				//fprintf(stderr,"\n");
				
				if( write(iSock,pSendData,nInxPos) ==- 1) 
				{
					perror("send"); 
				}				

				break; 		
			case CMD_READ_DUMP_DATA : 
				{
					nInxPos = 0;
					
					//make header 
					// command
					nInxPos = 0;
					pTmp = (long*)(pSendData +nInxPos) ;  
					*pTmp = CMD_READ_DUMP_DATA;  //command
					nInxPos += sizeof(long); //index value (long)
					
					// datasize
					pDSizeTmp=(long*)(pSendData +nInxPos) ; 
					nInxPos += sizeof(long); //index value (long)
					
					int i = 0;
					for(i = 0; i < stDH.lDataSize/4; i++)
					{
						//Read  datavalue from Index 
						plIdx = (long *)(pReadData + (i * 4));
						//printf("request index=%ld\n", *plIdx);
						nInxPos += ReadValueAndSetData(*plIdx, pSendData + nInxPos);
					}
					*pDSizeTmp =  nInxPos - sizeof(stDataHeader);
					
					//for(total_count  = 0 ; total_count  < nInxPos ; total_count ++)
					//{
					//	if(total_count % 4 == 0) 
					//		fprintf(stderr,"\n");	
						//fprintf(stderr,"0x%2x  ",pSendData[total_count]);	
					//}
					//fprintf(stderr,"\n");
					
					if( write(iSock,pSendData,nInxPos) ==- 1) 
					{
						perror("send"); 
					}
				}
				break; 
			case CMD_WRITE_ONE_DATA : 
				{
					//Read  datavalue from Index 
					plIdx = (long *)(pReadData);
					//printf("request index=%ld\n", *plIdx);
					
					// Read datatype
					long *plDataType = (long *)(pReadData + 4);
					//printf("request datatype=%ld\n", *plDataType);
					
					// Read Data
					uDataValue* writeValue = (uDataValue*)(pReadData + 8);
					switch(*plDataType)
					{
					case eLONG32:
						//printf("writeValue=%ld\n", writeValue->lv.low);
						WriteValue(*plIdx, &writeValue->lv.low);
						break;
					case eULONG32:
						//printf("writeValue=%ld\n", writeValue->ulv.low);
						WriteValue(*plIdx, &writeValue->ulv.low);
						break;
					case eFLOAT32:
						//printf("writeValue=%f\n", writeValue->fv.low);
						WriteValue(*plIdx, &writeValue->fv.low);
						break;
					case eLONG64:
						//printf("writeValue=%lld\n", writeValue->i64V);
						WriteValue(*plIdx, &writeValue->i64V);
						break;
					case eULONG64:
						//printf("writeValue=%llu\n", writeValue->uI64v);
						WriteValue(*plIdx, &writeValue->uI64v);
						break;
					case eFLOAT64:
						//printf("writeValue=%lf\n", writeValue->dblV);
						WriteValue(*plIdx, &writeValue->dblV);
						break;
					case eSTRING:
						////printf("eSTRING not supported......");
						//printf("len=%d. writeValue=%s\n", (int)writeValue->strv.len, writeValue->strv.body);
						WriteValue(*plIdx, &writeValue->strv);
						break;
					}
					
					nInxPos = 0;
					
					//make header 
					// command
					nInxPos = 0;
					pTmp = (long*)(pSendData +nInxPos) ;  
					*pTmp = CMD_READ_DUMP_DATA;  //command
					nInxPos += sizeof(long); //index value (long)
					
					// datasize
					pDSizeTmp=(long*)(pSendData +nInxPos) ; 
					nInxPos += sizeof(long); //index value (long)				
	
					//Read  datavalue from Index 
					plIdx = (long *)(pReadData);
					
					// ReadIndex
					pTmp = (long*)(pSendData +nInxPos);
					*pTmp = *plIdx;
					nInxPos += sizeof(long);
					
					pTmp = (long*)(pSendData +nInxPos);
					*pTmp = 0;	// 0 is OK, other is FAIL.
					nInxPos += sizeof(long);
					
					*pDSizeTmp =  nInxPos - sizeof(stDataHeader);
					
					//for(total_count  = 0 ; total_count  < nInxPos ; total_count ++)
					//{
						//if(total_count % 4 == 0) 
						//	fprintf(stderr,"\n");	
						//fprintf(stderr,"0x%2x  ",pSendData[total_count]);	
					//}
					//fprintf(stderr,"\n");
					
					if( write(iSock,pSendData,nInxPos) ==- 1) 
					{
						perror("send"); 
					}
				}
				break; 
			default : 
				break; 
			}	 
		}
	}     
} 

void connection_accept(fd_set *master, int *fdmax, int sockfd, struct sockaddr_in *client_addr) 
{ 
	socklen_t addrlen; 
	int newsockfd; 

	addrlen = sizeof(struct sockaddr_in); 
	if((newsockfd = accept(sockfd, (struct sockaddr *)client_addr, &addrlen)) == -1) 
	{ 
		perror("accept"); 
		exit(1); 
	}
	else 
	{ 
		FD_SET(newsockfd, master); 
		if(newsockfd > *fdmax)
		{ 
			*fdmax = newsockfd; 
		} 
		//printf("new connection from %s on port %d \n",inet_ntoa(client_addr->sin_addr), ntohs(client_addr->sin_port)); 
	} 
} 

void connect_request(int *sockfd, struct sockaddr_in *my_addr) 
{ 
	int yes = 1; 

	if ((*sockfd = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
	{ 
		perror("Socket"); 
		exit(1); 
	} 

	my_addr->sin_family = AF_INET; 
	my_addr->sin_port = htons(PORT_NUMBER ); 
	my_addr->sin_addr.s_addr = INADDR_ANY; 
	memset(my_addr->sin_zero, '\0', sizeof my_addr->sin_zero); 

	if (setsockopt(*sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) 
	{ 
		perror("setsockopt"); 
		exit(1); 
	} 

	if (bind(*sockfd, (struct sockaddr *)my_addr, sizeof(struct sockaddr)) == -1)
	{ 
		perror("Unable to bind"); 
		exit(1); 
	} 
	if (listen(*sockfd, 10) == -1) 
	{ 
		perror("listen"); 
		exit(1); 
	} 
	//printf("\nTCPServer Waiting for client on port %d\n", PORT_NUMBER ); 
	fflush(stdout); 
} 

void *HmiEntry(void)
{
	fd_set master; 
	fd_set read_fds; 
	int fdmax, i; 
	int readsocks;  
	int sockfd= 0; 
	struct timeval timeout;  /* Timeout for select */     
	struct sockaddr_in my_addr, client_addr; 
	
	FD_ZERO(&master); 
	FD_ZERO(&read_fds); 
	connect_request(&sockfd, &my_addr); 
	FD_SET(sockfd, &master); 

	fdmax = sockfd; 

	timeout.tv_sec = 1; 
	timeout.tv_usec = 0; 

	usleep(10000);
	while (!hmi_break) 
	{
		usleep(100);
		/* Main server loop - forever */
		read_fds = master;

		timeout.tv_sec = 1; 
		timeout.tv_usec = 0;     
		readsocks = select(fdmax+1, &read_fds, NULL, NULL,  &timeout) ; 
		
		if( readsocks ==-1) 
		{ 
			perror("select error"); 
			exit(4); 
		}
		else if(readsocks == 0)
		{
			//printf("timeout\n"); 
			fflush(stdout);
			continue;
		}
		else
		{
			for (i = 0; i <= fdmax; i++) 
			{ 
				if (FD_ISSET(i, &read_fds)) 
				{ 
					if (i == sockfd) 
						connection_accept(&master, &fdmax, sockfd, &client_addr); 
					else 
						send_recv(i, &master, sockfd, fdmax); 
				} 
			}
		}   
	}  

	close(sockfd);		
	fprintf(stderr,"\nHmiThread Exit !! \n");
	return NULL;
}

extern int TryEnterDebugSection(void);
extern __IEC_types_enum __find_variable(unsigned int varindex, void ** varp);
void* UnpackVar(void* varp, __IEC_types_enum vartype, void **real_value_p, char *flags);
extern void resumeDebug(void);
extern int suspendDeubg(int disable);
int ReadValue(unsigned int id , uDataValue *pSetValue)
{
	void *var1;
	void *visible_value_p;
	void *real_value_p = NULL;
	char flags = 0;
	int nReturnType = eTypeErr; 
	__IEC_types_enum iecType ; 

	//printf("Read Value Index = %d \n", id); 
	
	if(TryEnterDebugSection())
	{
		//printf("Read Value Index : %d \n", id); 
		iecType = __find_variable(id, &var1);
		
		visible_value_p = UnpackVar(var1, iecType, &real_value_p, &flags);

	 	//printf(" (int)iecType = %d \n", (int)iecType);
	 	
		switch((int)iecType)
		{
		case  BOOL_ENUM: 
		case  BYTE_ENUM: 
			pSetValue->ulv.low = *((IEC_USINT *) visible_value_p) ;
			nReturnType = eULONG32;
			break;
		
		case  SINT_ENUM: 
		case  USINT_ENUM: 
			//printf(" (R)SINT_ENUM : %d \n", *((IEC_SINT  *) visible_value_p));
			pSetValue->lv.low = *((IEC_SINT  *) visible_value_p) ;
			nReturnType = eLONG32;
			break;

		case  WORD_ENUM:
		case  UINT_ENUM:
			//printf(" (R)UINT_ENUM : %d \n", *((IEC_UINT  *) visible_value_p));
			pSetValue->ulv.low = *((IEC_UINT  *) visible_value_p) ;
			nReturnType = eULONG32;
			break;
		 
		case  INT_ENUM:		
			//printf(" (R)INT_ENUM : %d \n", *((IEC_INT  *) visible_value_p));
			pSetValue->lv.low = *((IEC_INT   *) visible_value_p) ;
			nReturnType = eLONG32;
			break;

		case  DINT_ENUM:
			pSetValue->lv.low = *((IEC_DINT  *) visible_value_p) ;
			nReturnType = eLONG32;
			break;
			break;
		case DWORD_ENUM:
		case  UDINT_ENUM:
			pSetValue->ulv.low = *((IEC_UDINT  *) visible_value_p) ;
			nReturnType = eLONG32;
			break;
		case  REAL_ENUM:
			pSetValue->fv.low = *((IEC_REAL  *) visible_value_p) ;
			nReturnType = eFLOAT32;
			break; 
		case  LINT_ENUM:
		case  ULINT_ENUM:
		case  LREAL_ENUM:
			memcpy( &pSetValue->dblV ,(IEC_LREAL *) visible_value_p,sizeof(IEC_LREAL) );
			if (((int)iecType) == LINT_ENUM )
				nReturnType = eLONG64;
			else if  (((int)iecType) == ULINT_ENUM )
					nReturnType = eULONG64;
			else nReturnType = eFLOAT64;
			break; 
		case 16:
			memcpy(&pSetValue->strv, (IEC_BYTE *)visible_value_p, sizeof(pSetValue->strv));
			nReturnType = eSTRING;
			break;
		default: 
			//printf(" UNKONWN ENUM = %d", (int)iecType);
			break;
		}
	 
		resumeDebug();	
	}
	else
	{
		//fprintf(stderr, "TryEnterDebugSection is false\n");	
	}
		
	return nReturnType;
}

extern void RegisterHMIVariable(int idx, void* force);
int WriteValue(int id, void* force)
{
	//int *value = &wValue;

	if(suspendDebug(0) == 0){
		RegisterHMIVariable(id, (void *)force); 	
		//fprintf(stderr,"\nWriteValue Running 3\n");
		resumeDebug();
	}
	return 0;
}
 
  

void __cleanup_hmisock(void)
{
	hmi_break = 1;
	pthread_join(hmi_thread, NULL); //wait thread exit
}

void __publish_hmisock(void)
{

}

void __retrieve_hmisock(void)
{

}
