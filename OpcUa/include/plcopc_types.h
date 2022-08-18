/*****************************************************************************
	plcopc_types.h

	Created on: 2017. 4. 19.
	Author: System Software Laboratory
*****************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
* (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
* 3.7. The constant 'maximum elements of array' definitions.
*===========================================================================*/
#define MAX_ELEMENTS_ARRAYDIMENSION		20
#define MAX_ELEMENTS_INDEXRANGE			20
#define MAX_ELEMENTS_NODELIST				20
#define MAX_ELEMENTS_MONITORLIST			20
#define MAX_ELEMENTS_BROWSERESULT			20
#define MAX_ELEMENTS_HISTORYDATA			20
#define MAX_ELEMENTS_EVENTITEMOPERATE		20
#define MAX_ELEMENTS_REGISTER				20
#define MAX_ELEMENTS_RELATIVEPATH			20
#define MAX_ELEMENTS_NAMESPACES			20
#define MAX_ELEMENTS_METHOD					20

/*============================================================================
 * The constant 'maximum length of string' definition.
 *===========================================================================*/
#define MAX_LEN_STR 126

/*============================================================================
 * The constant 'timeout of notification' definitions.
 *===========================================================================*/
#define MAX_INTERVAL_NOTIFICATIONWAIT		1		// seconds
#define MAX_COUNT_NOTIFICATIONWAIT 		5

/*============================================================================
 * The constant 'maximum elements of buffer' definitions.
 *===========================================================================*/
#define MAX_ELEMENTS_MONITORBUFFER			20

/*============================================================================
 * Type definitions for basic data types.
 *===========================================================================*/
typedef int 						PlcOpc_Int;
typedef unsigned int 			PlcOpc_UInt;
typedef void				 		PlcOpc_Void;
typedef void* 					PlcOpc_Handle;
typedef unsigned char 		PlcOpc_Boolean;
typedef char						PlcOpc_SByte;
typedef unsigned char 		PlcOpc_Byte;
typedef short 					PlcOpc_Int16;
typedef unsigned short 		PlcOpc_UInt16;
typedef long 					PlcOpc_Int32;
typedef unsigned long 		PlcOpc_UInt32;
typedef float 					PlcOpc_Float;
typedef double 					PlcOpc_Double;
typedef char 					PlcOpc_CharA;
typedef unsigned char			PlcOpc_UCharA;
typedef PlcOpc_CharA*			PlcOpc_StringA;
typedef unsigned short		PlcOpc_Char;

/*============================================================================
 * Type definitions for status code.
 *===========================================================================*/
typedef PlcOpc_UInt32    PlcOpc_StatusCode;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.1. The UASecurityMsgMode enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UASecurityMsgMode
{
	PlcOpc_UASMM_BestAvailable = 0,
	PlcOpc_UASMM_None,
	PlcOpc_UASMM_Sign,
	PlcOpc_UASMM_SignEncrypt
}PlcOpc_UASecurityMsgMode;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.2. The UASecurityPolicy enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UASecurityPolicy
{
	PlcOpc_UASP_BestAvailable = 0,
	PlcOpc_UASP_None,
	PlcOpc_UASP_Basic128Rsa15,
	PlcOpc_UASP_Basic256,
	PlcOpc_UASP_Basic256Sha256
}PlcOpc_UASecurityPolicy;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.3. The UATransportProfile enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UATransportProfile
{
	PlcOpc_UATP_UATcp = 1,
	PlcOpc_UATP_WSHttpBinary,
	PlcOpc_UATP_WSHttpXmlOrBinary,
	PlcOpc_UATP_WSHttpXml
}PlcOpc_UATransportProfile;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.4. The UAUserIdentityTokenType enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UAUserIdentityTokenType
{
	PlcOpc_UAUITT_Anonymous = 0,
	PlcOpc_UAUITT_Username,
	PlcOpc_UAUITT_x509,
	PlcOpc_UAUITT_IssuedToken
}PlcOpc_UAUserIdentityTokenType;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.5. The UAIdentifierType enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UAIdentifierType
{
	PlcOpc_UAIT_Numeric = 0,
	PlcOpc_UAIT_String,
	PlcOpc_UAIT_GUID,
	PlcOpc_UAIT_Opaque
}PlcOpc_UAIdentifierType;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.6. The UADeadbandType enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UADeadbandType
{
	PlcOpc_UADT_None = 0,
	PlcOpc_UADT_Absolute,
	PlcOpc_UADT_Percent
}PlcOpc_UADeadbandType;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.7. The UAAttribuID enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UAAttributeID
{
	PlcOpc_UAAI_NodeID = 1,
	PlcOpc_UAAI_NodeClass,
	PlcOpc_UAAI_BrowseName,
	PlcOpc_UAAI_DisplayName,
	PlcOpc_UAAI_Description,
	PlcOpc_UAAI_WriteMask,
	PlcOpc_UAAI_UserWriteMask,
	PlcOpc_UAAI_IsAbstract,
	PlcOpc_UAAI_Symmetric,
	PlcOpc_UAAI_InverseName,
	PlcOpc_UAAI_ContainsNoLoops,
	PlcOpc_UAAI_EventNotifier,
	PlcOpc_UAAI_Value,
	PlcOpc_UAAI_DataType,
	PlcOpc_UAAI_ValueRank,
	PlcOpc_UAAI_ArrayDimensions,
	PlcOpc_UAAI_AccessLevel,
	PlcOpc_UAAI_UserAccessLevel,
	PlcOpc_UAAI_MinimumSamplingInterval,
	PlcOpc_UAAI_Historizing,
	PlcOpc_UAAI_Executable,
	PlcOpc_UAAI_UserExecutable
}PlcOpc_UAAttributeID;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.8. The UAConnectionStatus enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UAConnectionStatus
{
	PlcOpc_UACS_Connected = 0,
	PlcOpc_UACS_ConnectionError,
	PlcOpc_UACS_Shutdown
}PlcOpc_UAConnectionStatus;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.3.9. The UAServerState enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UAServerState
{
	PlcOpc_UASS_Running = 0,
	PlcOpc_UASS_Failed ,
	PlcOpc_UASS_NoConfiguration,
	PlcOpc_UASS_Suspended,
	PlcOpc_UASS_Shutdown,
	PlcOpc_UASS_Test,
	PlcOpc_UASS_CommunicationFault,
	PlcOpc_UASS_Unknown
}PlcOpc_UAServerState;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.4.1. The UANodeClassMask enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_UANodeClassMask
{
	PlcOpc_UANCM_None = 0,
	PlcOpc_UANCM_Object = 1,
	PlcOpc_UANCM_Variable = 2,
	PlcOpc_UANCM_Method = 4,
	PlcOpc_UANCM_ObjectType = 8,
	PlcOpc_UANCM_VariableType = 16,
	PlcOpc_UANCM_ReferenceType = 32,
	PlcOpc_UANCM_DataType = 64,
	PlcOpc_UANCM_View = 128,
	PlcOpc_UANCM_All = 255
}PlcOpc_UANodeClassMask;

/*============================================================================
 * The SubscriptionMode enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_SubscriptionMode
{
	PlcOpc_Subscription_init,
	PlcOpc_Subscription_Controller,
	PlcOpc_Subscription_FW
}PlcOpc_SubscriptionMode;

/*============================================================================
 * The VariantType enumeration.
 *===========================================================================*/
typedef enum _PlcOpc_VariantType
{
	PlcOpc_VariantType_Unknown = -1,
	PlcOpc_VariantType_Boolean,
	PlcOpc_VariantType_Byte,
	PlcOpc_VariantType_CharA,
	PlcOpc_VariantType_Int16,
	PlcOpc_VariantType_Int32,
	PlcOpc_VariantType_UInt16,
	PlcOpc_VariantType_UInt32,
	PlcOpc_VariantType_Double,
	PlcOpc_VariantType_Float,
	PlcOpc_VariantType_StringA,
	PlcOpc_VariantType_DateTime,
	PlcOpc_VariantType_QualifiedName
}PlcOpc_VariantType;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.1. The UAUserIdentityToken structure.
 *===========================================================================*/
typedef struct _PlcOpc_UAUserIdentityToken
{
	PlcOpc_UAUserIdentityTokenType		UserIdentityTokenType;
	PlcOpc_StringA						TokenParam1;
	PlcOpc_StringA						TokenParam2;
}PlcOpc_UAUserIdentityToken;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.2. The SessionConnectInfo structure.
 *===========================================================================*/
typedef struct _PlcOpc_SessionConnectInfo
{
	PlcOpc_StringA					SessionName;
	PlcOpc_StringA					ApplicationName;
	PlcOpc_UASecurityMsgMode			SecurityMsgMode;
	PlcOpc_UASecurityPolicy			SecurityPolicy;
	PlcOpc_StringA					CertificateStore;
	PlcOpc_StringA					ClientCertificateName;
	PlcOpc_StringA					ServerUri;
	PlcOpc_Boolean					CheckServerCertificate;
	PlcOpc_UATransportProfile		TransportProfile;
	PlcOpc_UAUserIdentityToken		UserIdentityToken;
	PlcOpc_StringA					VendorSpecificParameter;
	PlcOpc_Double						SessionTimeout;
	PlcOpc_Double						MonitorConnection;
	PlcOpc_StringA					LocaleIDs[5][6];	// ARRAY[1...5] OF STRING[6]
}PlcOpc_SessionConnectInfo;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.3. The UANodeID structure.
 *===========================================================================*/
typedef struct _PlcOpc_UANodeID
{
	PlcOpc_UInt32					NamespaceIndex;
	PlcOpc_CharA					Identifier[MAX_LEN_STR];
	PlcOpc_UAIdentifierType		IdentifierType;
}PlcOpc_UANodeID;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.4. The QualifiedName structure.
 *===========================================================================*/
typedef struct _PlcOpc_QualifiedName
{
	PlcOpc_UInt32		NamespaceIndex;
	PlcOpc_CharA		Name[MAX_LEN_STR];
}PlcOpc_QualifiedName;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.5. The RelativePathElement structure.
 *===========================================================================*/
typedef struct _PlcOpc_RelativePathElement
{
	PlcOpc_UANodeID			ReferenceTypeId;
	PlcOpc_Boolean			IsInverse;
	PlcOpc_Boolean			IncludeSubtypes;
	PlcOpc_QualifiedName		TargetName;
}PlcOpc_RelativePathElement;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.6. The RelativePath structure.
 *===========================================================================*/
typedef struct _PlcOpc_RelativePath
{
	PlcOpc_UInt32					NoOfElements;
	PlcOpc_RelativePathElement	Elements[MAX_ELEMENTS_RELATIVEPATH];
}PlcOpc_RelativePath;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.7. The BrowsePath structure.
 *===========================================================================*/
typedef struct _PlcOpc_BrowsePath
{
	PlcOpc_UANodeID		StartingNode;
	PlcOpc_RelativePath 	RelativePath;
}PlcOpc_BrowsePath;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.8. The UAMonitoringParameter structure.
 *===========================================================================*/
typedef struct _PlcOpc_UAMonitoringParameter
{
	PlcOpc_Double				SamplingInterval;
	PlcOpc_UInt32				QueueSize;
	PlcOpc_Boolean			DiscardOldest;
	PlcOpc_UADeadbandType	UADeadbandType;
	PlcOpc_Double				Deadband;
}PlcOpc_UAMonitoringParameter;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.9. The UALocalizedText structure.
 *===========================================================================*/
typedef struct _PlcOpc_LocalizedText
{
	PlcOpc_CharA		Locale[MAX_LEN_STR];
	PlcOpc_CharA		Text[MAX_LEN_STR];
}PlcOpc_LocalizedText;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.11. The UANodeInformation structure.
 *===========================================================================*/
typedef struct _PlcOpc_UANodeInformation
{
	PlcOpc_Byte				AccessLevel;
	PlcOpc_UInt32				ArrayDimension[MAX_ELEMENTS_ARRAYDIMENSION];
	PlcOpc_QualifiedName		BrowseName;
	PlcOpc_Boolean			ContainsNoLoops;
	PlcOpc_UANodeID			DataType;
	PlcOpc_LocalizedText		Description;
	PlcOpc_LocalizedText		DisplayName;
	PlcOpc_Byte				EventNotifier;
	PlcOpc_Boolean			Executable;
	PlcOpc_Boolean			Historizing;
	PlcOpc_CharA				InverseName[MAX_LEN_STR];
	PlcOpc_Boolean			IsAbstract;
	PlcOpc_Double				MinimumSamplingInterval;
	PlcOpc_UANodeClassMask	NodeClass;
	PlcOpc_Boolean			Symmetric;
	PlcOpc_Byte				UserAccessLevel;
	PlcOpc_Boolean			UserExecutable;
	PlcOpc_UInt32				UserWriteMask;
	PlcOpc_UInt32				ValueRank;
	PlcOpc_UInt32				WriteMask;
}PlcOpc_UANodeInformation;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.12. The UAIndexRange structure.
 *===========================================================================*/
typedef struct _PlcOpc_UAIndexRange
{
	PlcOpc_UInt32		StartIndex;
	PlcOpc_UInt32		EndIndex;
}PlcOpc_UAIndexRange;

/*============================================================================
 * (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
 * 3.5.13. The UANodeAdditionalInfo structure.
 *===========================================================================*/
typedef struct _PlcOpc_UANodeAdditionalInfo
{
	PlcOpc_UAAttributeID		AttributeID;
	PlcOpc_UInt32				IndexRangeCount;
	PlcOpc_UAIndexRange		IndexRange[MAX_ELEMENTS_INDEXRANGE];
}PlcOpc_UANodeAdditionalInfo;

/*============================================================================
 * The MonitoredItem structure.
 *===========================================================================*/
typedef struct _PlcOpc_MonitoredItem
{
	PlcOpc_Handle		MonitoredItemHdl;
	PlcOpc_Byte		preValue[MAX_LEN_STR];
	PlcOpc_Boolean	preValueChanged;
	PlcOpc_UInt32		globalIndex;
	PlcOpc_UInt32		localIndex;
}PlcOpc_MonitoredItem;

typedef PlcOpc_MonitoredItem* PlcOpc_MonitoredItemHdl;

/*============================================================================
 * The Subscription structure.
 *===========================================================================*/
typedef struct _PlcOpc_Subscription
{
	PlcOpc_Handle					SubscriptionHdl;
	PlcOpc_SubscriptionMode		Mode;
	PlcOpc_UInt32					monitoredItemsCount;
	PlcOpc_MonitoredItemHdl*		MonitoredItemHdls;
}PlcOpc_Subscription;

typedef PlcOpc_Subscription* PlcOpc_SubscriptionHdl;

/*============================================================================
 * The DateTime structure.
 *===========================================================================*/
typedef struct _PlcOpc_DateTime
{
    PlcOpc_UInt32		dwLowDateTime;
    PlcOpc_UInt32		dwHighDateTime;
    PlcOpc_CharA		sysTimeStr[32];
}PlcOpc_DateTime;

/*============================================================================
 * The Variant structure.
 *===========================================================================*/
typedef union _PlcOpc_VariantUnion
{
	PlcOpc_Boolean			Boolean;
	PlcOpc_Byte				Byte;
	PlcOpc_CharA				CharA;
	PlcOpc_Int16				Int16;
	PlcOpc_Int32				Int32;
	PlcOpc_UInt16				UInt16;
	PlcOpc_UInt32				UInt32;
	PlcOpc_Double				Double;
	PlcOpc_Float				Float;
	PlcOpc_CharA				StringA[MAX_LEN_STR];
	PlcOpc_DateTime			DateTime;
	PlcOpc_QualifiedName		QualifiedName;
}PlcOpc_VariantUnion;

typedef struct _PlcOpc_Variant
{
	PlcOpc_VariantType		Type;
	PlcOpc_VariantUnion		Value;
}PlcOpc_Variant;

/*============================================================================
 * The DataValue structure.
 *===========================================================================*/
typedef struct _PlcOpc_DataValue
{
    PlcOpc_Variant		Value;
    PlcOpc_UInt32			StatusCode;
    PlcOpc_DateTime 		SourceTimestamp;
    PlcOpc_DateTime		ServerTimestamp;
}PlcOpc_DataValue;

/*============================================================================
 * The MethodHandle structure.
 *===========================================================================*/
typedef struct _PlcOpc_MethodHandle
{
	PlcOpc_UANodeID		ObjectNodeID;
	PlcOpc_UANodeID		MethodNodeID;
}PlcOpc_MethodHandle;

/*============================================================================
 * The MethodParameter structure.
 *===========================================================================*/
typedef struct _PlcOpc_MethodParameter
{
	PlcOpc_UInt32			NoOfArgument;
	PlcOpc_Variant*		Arguments;
}PlcOpc_MethodParameter;

#ifdef __cplusplus
}
#endif
