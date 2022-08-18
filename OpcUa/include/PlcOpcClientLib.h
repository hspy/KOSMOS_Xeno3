/*****************************************************************************
	PlcOpcClientLib.h

	Created on: 2016. 4. 19.
	Author: System Software Laboratory
*****************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include "plcopc_types.h"

/////////////////////////////////////////////////////////////////////////////
// (OPC-UA Client FUNCTIONBLOCKS for IEC61131-3 Version 1.1)
// 5.1. UA_Connect : Connect to server
PlcOpc_StatusCode PlcOpc_UA_Connect(PlcOpc_Handle hApplication, // OutOfSpec param
								PlcOpc_StringA ServerEndpointUrl,
								PlcOpc_SessionConnectInfo SessionConnectInfo,
								PlcOpc_Double Timeout,
								PlcOpc_Handle* ConnectionHdl);
// 5.2. UA_Disconnect : Disconnect from server
PlcOpc_StatusCode PlcOpc_UA_Disconnect(PlcOpc_Handle hApplication, // OutOfSpec param
									PlcOpc_Handle ConnectionHdl,
									PlcOpc_Double Timeout);
// 5.3. UA_NamespaceGetIndexList : Get list of namespaceIndex from list of namespaceUri
PlcOpc_StatusCode PlcOpc_UA_NamespaceGetIndexList(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_Handle ConnectionHdl,
												PlcOpc_UInt32 NamespaceUrisCount,
												PlcOpc_StringA* NamespaceUris,
												PlcOpc_Double Timeout,
												PlcOpc_Int32* NamespaceIndexs,
												PlcOpc_UInt32* ErrorIDs);
// 5.4. UA_ServerGetUriByIndex : Get serverUri from serverIndex
PlcOpc_StatusCode PlcOpc_UA_ServerGetUriByIndex(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_Handle ConnectionHdl,
												PlcOpc_UInt32 ServerIndex,
												PlcOpc_Double Timeout,
												PlcOpc_StringA* ServerUri);
// 5.5. UA_ServerGetIndexByUriList : Get list of serverIndex from list of serverUri
PlcOpc_StatusCode PlcOpc_UA_ServerGetIndexByUriList(PlcOpc_Handle hApplication, // OutOfSpec param
													PlcOpc_Handle ConnectionHdl,
													PlcOpc_UInt32 ServerUrisCount,
													PlcOpc_StringA* ServerUris,
													PlcOpc_Double Timeout,
													PlcOpc_Int32* ServerIndexes,
													PlcOpc_UInt32* ErrorIDs);
// 5.7. UA_NodeGetHandleList : Get list of nodeHdl from list of nodeID
PlcOpc_StatusCode PlcOpc_UA_NodeGetHandleList(PlcOpc_Handle hApplication, // OutOfSpec param
											PlcOpc_Handle ConnectionHdl,
											PlcOpc_UInt32 NodeIDCount,
											PlcOpc_UANodeID* NodeIDs,
											PlcOpc_Double Timeout,
											PlcOpc_Handle* NodeHdls,
											PlcOpc_UInt32* NodeErrorIDs);
// 5.8. UA_NodeReleaseHandleList : Release list of nodeHdl
PlcOpc_StatusCode PlcOpc_UA_NodeReleaseHandleList(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_Handle ConnectionHdl,
												PlcOpc_UInt32 NodeHdlCount,
												PlcOpc_Handle* NodeHdls,
												PlcOpc_Double Timeout,
												PlcOpc_UInt32* NodeErrorIDs);
// 5.9. UA_NodeGetInformation : Get informations of node
PlcOpc_StatusCode PlcOpc_UA_NodeGetInformation(PlcOpc_Handle hApplication, // OutOfSpec param
											PlcOpc_Handle ConnectionHdl,
											PlcOpc_UANodeID NodeID,
											PlcOpc_Double Timeout,
											PlcOpc_UANodeInformation* NodeInfo,
											PlcOpc_UInt32* NodeGetInfoErrorIDs);
// 5.10. UA_SubscriptionCreate : Create subscription
PlcOpc_StatusCode PlcOpc_UA_SubscriptionCreate(PlcOpc_Handle hApplication, // OutOfSpec param
											PlcOpc_Handle ConnectionHdl,
											PlcOpc_Boolean PublishingEnable,
											PlcOpc_Byte Priority,
											PlcOpc_Double Timeout,
											PlcOpc_SubscriptionHdl* SubscriptionHdl,
											PlcOpc_Double* PublishingInterval); // In/Out param
// 5.11. UA_SubscriptionDelete : Delete Subscription
PlcOpc_StatusCode PlcOpc_UA_SubscriptionDelete(PlcOpc_Handle hApplication, // OutOfSpec param
											PlcOpc_SubscriptionHdl SubscriptionHdl,
											PlcOpc_Double Timeout);

// 5.13. UA_SubscriptionProcessed : Check change of items value in subscription
PlcOpc_StatusCode PlcOpc_UA_SubscriptionProcessed(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_SubscriptionHdl SubscriptionHdl,
												PlcOpc_Double Timeout,
												PlcOpc_Boolean* Published);
// 5.14. UA_MonitoredItemAddList : Add list of item to subscription
PlcOpc_StatusCode PlcOpc_UA_MonitoredItemAddList(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_SubscriptionHdl SubscriptionHdl,
												PlcOpc_UInt32 NodeHdlCount,
												PlcOpc_Handle* NodeHdls,
												PlcOpc_UANodeAdditionalInfo* NodeAddInfos,
												PlcOpc_Double Timeout,
												PlcOpc_UInt32* NodeErrorIDs,
												PlcOpc_MonitoredItemHdl** MonitoredItemHdls,
												PlcOpc_UInt32 variablesIndex, // In/Out param
												PlcOpc_UAMonitoringParameter* MonitoringSettings, // In/Out param
												PlcOpc_UInt32 valuesChangedIndex, // In/Out param
												PlcOpc_UInt32* RemainingValueCount, // In/Out param
												PlcOpc_DateTime* TimeStamps, // In/Out param
												PlcOpc_Handle* NodeQualityIDs); // In/Out param
// 5.15. UA_MonitoredItemRemoveList : Remove list of item from subscription
PlcOpc_StatusCode PlcOpc_UA_MonitoredItemRemoveList(PlcOpc_Handle hApplication, // OutOfSpec param
														PlcOpc_SubscriptionHdl SubscriptionHdl,
														PlcOpc_UInt32 MonitoredItemHdlCount,
														PlcOpc_MonitoredItemHdl* MonitoredItemHdls,
														PlcOpc_Double Timeout,
														PlcOpc_UInt32* NodeErrorIDs);
// 5.17.UA_MonitoredItemOperateList : Check change of items value, and update
PlcOpc_StatusCode PlcOpc_UA_MonitoredItemOperateList(PlcOpc_Handle hApplication, // OutOfSpec param
														PlcOpc_SubscriptionHdl SubscriptionHdl,
														PlcOpc_UInt32 MonitoredItemHdlCount,
														PlcOpc_MonitoredItemHdl* MonitoredItemHdls,
														PlcOpc_Boolean* Published);
// 5.18. UA_ReadList : Read value of nodes
PlcOpc_StatusCode PlcOpc_UA_ReadList(PlcOpc_Handle hApplication, // OutOfSpec param
									PlcOpc_Handle ConnectionHdl,
									PlcOpc_UInt32 NodeHdlCount,
									PlcOpc_Handle* NodeHdls,
									PlcOpc_UANodeAdditionalInfo* NodeAddInfos,
									PlcOpc_Double Timeout,
									PlcOpc_DataValue* Variables); // In/Out param
									// ErrorID handling with uStatus return
// 5.19. UA_WriteList : Write value of nodes
PlcOpc_StatusCode PlcOpc_UA_WriteList(PlcOpc_Handle hApplication, // OutOfSpec param
										PlcOpc_Handle ConnectionHdl,
										PlcOpc_UInt32 NodeHdlCount,
										PlcOpc_Handle* NodeHdls,
										PlcOpc_UANodeAdditionalInfo* NodeAddInfos,
										PlcOpc_Double Timeout,
										PlcOpc_DataValue* Variable2); // In/Out param
										// ErrorID handling with uStatus return
// 5.20. UA_MethodGetHandleList : Get list of methodHdl from list of methodNodeId
PlcOpc_StatusCode PlcOpc_UA_MethodGetHandleList(PlcOpc_Handle hApplication, // OutOfSpec param
													PlcOpc_Handle ConnectionHdl,
													PlcOpc_UInt32 NodeIDCount,
													PlcOpc_UANodeID* ObjectNodeIDs,
													PlcOpc_UANodeID* MethodNodeIDs,
													PlcOpc_Double Timeout,
													PlcOpc_Handle* MethodHdls);
													// ErrorID handling with uStatus return
// 5.21. UA_MethodReleaseHandleList : Release list of methodHdl
PlcOpc_StatusCode PlcOpc_UA_MethodReleaseHandleList(PlcOpc_Handle hApplication, // OutOfSpec param
														PlcOpc_Handle ConnectionHdl,
														PlcOpc_UInt32 MethodHdlCount,
														PlcOpc_Handle* MethodHdls,
														PlcOpc_Double Timeout);
														// ErrorID handling with uStatus return
// 5.22. UA_MethodCall : Call method
PlcOpc_StatusCode PlcOpc_UA_MethodCall(PlcOpc_Handle hApplication, // OutOfSpec param
										PlcOpc_Handle ConnectionHdl,
										PlcOpc_Handle MethodHdl,
										PlcOpc_Double Timeout,
										PlcOpc_Handle InputArguments, // In/Out param
										PlcOpc_Handle OutputArguments); // In/Out param
// 6.1. UA_ConnectionGetStatus : Get status of connection with server
PlcOpc_StatusCode PlcOpc_UA_ConnectionGetStatus(PlcOpc_Handle hApplication, // OutOfSpec param
													PlcOpc_Handle ConnectionHdl,
													PlcOpc_Int32* ConnectionStatus,
													PlcOpc_Int32* ServerState,
													PlcOpc_Byte* ServiceLevel);

/////////////////////////////////////////////////////////////////////////////
// OufOfSpec functions
// Initialize client
PlcOpc_StatusCode PlcOpc_UA_Initialize(PlcOpc_StringA appName,
										PlcOpc_StringA appCerPath,
										PlcOpc_Handle* hApp,
										PlcOpc_Handle* szcertificateStore);
// Shutdown client
PlcOpc_StatusCode PlcOpc_UA_Shutdown(PlcOpc_Handle hApp, PlcOpc_Handle szcertificateStore);
// Get endPoint index from sessionConnectInfo
PlcOpc_StatusCode PlcOpc_UA_GetEndpointIndex(PlcOpc_Handle hApplication, // OutOfSpec param
								PlcOpc_UInt32 numOfEndpointDescription,
								PlcOpc_Handle pEndpointDescription,
								PlcOpc_SessionConnectInfo SessionConnectInfo,
								PlcOpc_UInt32* index);
// Get list of namespace index from server
PlcOpc_StatusCode PlcOpc_UA_GetNamespaceIndex(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_Handle ConnectionHdl,
												PlcOpc_StringA NamespaceUri,
												PlcOpc_Double Timeout,
												PlcOpc_Int32* NamespaceIndex);
// Get stringTable from array node
PlcOpc_StatusCode PlcOpc_UA_GetNodeStringTable(PlcOpc_Handle hApplication, // OutOfSpec param
												PlcOpc_Handle ConnectionHdl,
												PlcOpc_Handle ArrayNode,
												PlcOpc_Double Timeout,
												PlcOpc_UInt32* ArrayLength,
												PlcOpc_Handle StringTable);
// Get stringTable index
PlcOpc_StatusCode PlcOpc_UA_GetStringTableIndex(PlcOpc_Handle stringTable, PlcOpc_Handle string, PlcOpc_Int32* index);
// convert stack dataValue to nodeInformation
PlcOpc_StatusCode PlcOpc_UA_StackDataValueToNodeInformation(PlcOpc_Handle inputDataValue,
																PlcOpc_UANodeInformation* outputNodeInformation,
																PlcOpc_UInt32* ErrorIDs);
// Get string about data value
PlcOpc_Void PlcOpc_UA_GetPlcValueString(PlcOpc_DataValue* dataValue, PlcOpc_StringA valueString, PlcOpc_UInt32 size);
// Get value about data value
PlcOpc_UInt32 PlcOpc_UA_GetStackValueString(PlcOpc_StringA valueString, PlcOpc_Handle inputDataValue);
// Notification function in subscription
PlcOpc_StatusCode PlcOpc_UA_OnNotificationMessage(PlcOpc_Handle hSubscription,
													PlcOpc_Int32 noOfMonitoredItems,
													PlcOpc_Handle MonitoredItems,
													void* pParam);
// Convert identifier type form from PlcOpc to stack
PlcOpc_UInt16 PlcOpc_UA_IdentifierType_PlcOpcToStack (PlcOpc_UAIdentifierType identifierType);
// Convert identifier type form from stack to PlcOpc
PlcOpc_UAIdentifierType PlcOpc_UA_IdentifierType_StackToPlcOpc (PlcOpc_Int identifierType);
// Convert messageSecurityMode form from PlcOpc to stack
PlcOpc_Int PlcOpc_UA_MessageSecurityMode_PlcOpcToStack(PlcOpc_UASecurityMsgMode messageSecurityMode);
// Convert messageSecurityMode form from stack to PlcOpc
PlcOpc_UASecurityMsgMode PlcOpc_UA_MessageSecurityMode_StackToPlcOpc(PlcOpc_Int messageSecurityMode);
// Convert userTokenType form from PlcOpc to stack
PlcOpc_Int PlcOpc_UA_UserTokenType_PlcOpcToStack(PlcOpc_UAUserIdentityTokenType userIdentityTokenType);
// Convert userTokenType form from stack to PlcOpc
PlcOpc_UAUserIdentityTokenType PlcOpc_UA_UserTokenType_StackToPlcOpc(PlcOpc_Int userIdentityTokenType);
// Convert nodeId form from PlcOpc to stack
PlcOpc_Void PlcOpc_UA_NodeId_PlcOpcToStack(PlcOpc_UANodeID inputNodeId, PlcOpc_Handle outputNodeId);
// Convert nodeId form from stack to PlcOpc
PlcOpc_Void PlcOpc_UA_NodeId_StackToPlcOpc(PlcOpc_Handle inputNodeId, PlcOpc_UANodeID* outputNodeId);
// Convert variant form from PlcOpc to stack
PlcOpc_Void PlcOpc_UA_Variant_PlcOpcToStack(PlcOpc_Variant inputVariant, PlcOpc_Handle outputVariant);
// Convert variant form from stack to PlcOpc
PlcOpc_Void PlcOpc_UA_Variant_StackToPlcOpc(PlcOpc_Handle inputVariant, PlcOpc_Variant* outputVariant);
// Convert dataValue form from PlcOpc to stack
PlcOpc_Void PlcOpc_UA_DataValue_PlcOpcToStack(PlcOpc_DataValue inputDataValue, PlcOpc_Handle outputDataValue);
// Convert dataValue form from stack to PlcOpc
PlcOpc_Void PlcOpc_UA_DataValue_StackToPlcOpc(PlcOpc_Handle inputDataValue, PlcOpc_DataValue* outputDataValue);
// Convert qualifiedName form from PlcOpc to stack

#ifdef __cplusplus
}
#endif
