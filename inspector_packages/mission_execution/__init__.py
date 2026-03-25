from inspector_packages import np

DATABASE_CHUNK_SIZE = 1000

COMM_DATA_TABLE = "comm_data"

# SHARED COLUMNS
class SharedColumns:
   EVENT_ID = "Event_ID"
   ISO_DATE = "ISODate"
   HMS_TIME = "HMSTime"
   SIMULATION_TIME = "SimulationTime"
   EVENT_TYPE = "Event_Type"

# COMMS DATA COLUMNS
class CommDataColumns:
   MESSAGE_SERIALNUMBER = "Message_SerialNumber"
   MESSAGE_ORIGINATOR = "Message_Originator"
   MESSAGE_TYPE = "Message_Type"
   MESSAGE_SIZE = "Message_Size"
   MESSAGE_PRIORITY = "Message_Priority"
   MESSAGE_DATATAG = "Message_DataTag"
   OLDMESSAGE_SERIALNUMBER = "OldMessage_SerialNumber"
   OLDMESSAGE_ORIGINATOR = "OldMessage_Originator"
   OLDMESSAGE_TYPE = "OldMessage_Type"
   OLDMESSAGE_SIZE = "OldMessage_Size"
   OLDMESSAGE_PRIORITY = "OldMessage_Priority"
   OLDMESSAGE_DATATAG = "OldMessage_DataTag"
   SENDER_NAME = "Sender_Name"
   SENDER_SIDE = "Sender_Side"
   SENDER_TYPE = "Sender_Type"
   SENDER_BASETYPE = "Sender_BaseType"
   SENDERLOCATION_X = "SenderLocation_X"
   SENDERLOCATION_Y = "SenderLocation_Y"
   SENDERLOCATION_Z = "SenderLocation_Z"
   SENDER_LATITUDE = "Sender_Latitude"
   SENDER_LONGITUDE = "Sender_Longitude"
   SENDER_ALTITUDE = "Sender_Altitude"
   SENDERPART_NAME = "SenderPart_Name"
   SENDERPART_TYPE = "SenderPart_Type"
   SENDERPART_BASETYPE = "SenderPart_BaseType"
   RECEIVER_NAME = "Receiver_Name"
   RECEIVER_SIDE = "Receiver_Side"
   RECEIVER_TYPE = "Receiver_Type"
   RECEIVER_BASETYPE = "Receiver_BaseType"
   RECEIVERLOCATION_X = "ReceiverLocation_X"
   RECEIVERLOCATION_Y = "ReceiverLocation_Y"
   RECEIVERLOCATION_Z = "ReceiverLocation_Z"
   RECEIVER_LATITUDE = "Receiver_Latitude"
   RECEIVER_LONGITUDE = "Receiver_Longitude"
   RECEIVER_ALTITUDE = "Receiver_Altitude"
   RECEIVERPART_NAME = "ReceiverPart_Name"
   RECEIVERPART_TYPE = "ReceiverPart_Type"
   RECEIVERPART_BASETYPE = "ReceiverPart_BaseType"
   SENDERTORCVR_RANGE = "SenderToRcvr_Range"
   COMMINTERACTION_SUCCEEDED = "CommInteraction_Succeeded"
   COMMINTERACTION_FAILED = "CommInteraction_Failed"
   COMMINTERACTION_FAILEDSTATUS = "CommInteraction_FailedStatus"
   QUEUE_SIZE = "Queue_Size"

COMM_SUBSTITUTIONS = {
   CommDataColumns.MESSAGE_ORIGINATOR: 'unknown',
   CommDataColumns.OLDMESSAGE_ORIGINATOR: 'unknown',
   CommDataColumns.OLDMESSAGE_TYPE: 'Does Not Exist',
   CommDataColumns.SENDER_SIDE: 'unknown',
   CommDataColumns.SENDER_TYPE: 'unknown',
   CommDataColumns.SENDER_BASETYPE: 'unknown',
   CommDataColumns.SENDERPART_TYPE: 'unknown',
   CommDataColumns.SENDERPART_BASETYPE: 'unknown',
   CommDataColumns.RECEIVER_NAME: 'Does Not Exist',
   CommDataColumns.RECEIVER_SIDE: 'unknown',
   CommDataColumns.RECEIVER_TYPE: 'unknown',
   CommDataColumns.RECEIVER_BASETYPE: 'unknown',
   CommDataColumns.RECEIVERPART_NAME: 'Does Not Exist',
   CommDataColumns.RECEIVERPART_TYPE: 'unknown',
   CommDataColumns.RECEIVERPART_BASETYPE: 'unknown',
   CommDataColumns.COMMINTERACTION_FAILEDSTATUS: 'Does Not Exist',
}

SQLITE_COMM_DATA_TYPES = {
   SharedColumns.EVENT_ID: "INTEGER PRIMARY KEY",
   SharedColumns.ISO_DATE: "TEXT",
   SharedColumns.HMS_TIME: "TEXT",
   SharedColumns.SIMULATION_TIME: "REAL",
   SharedColumns.EVENT_TYPE: "TEXT",
   CommDataColumns.MESSAGE_SERIALNUMBER: "INTEGER",
   CommDataColumns.MESSAGE_ORIGINATOR: "TEXT",
   CommDataColumns.MESSAGE_TYPE: "TEXT",
   CommDataColumns.MESSAGE_SIZE: "INTEGER",
   CommDataColumns.MESSAGE_PRIORITY: "INTEGER",
   CommDataColumns.MESSAGE_DATATAG: "REAL",
   CommDataColumns.OLDMESSAGE_SERIALNUMBER: "INTEGER",
   CommDataColumns.OLDMESSAGE_ORIGINATOR: "TEXT",
   CommDataColumns.OLDMESSAGE_TYPE: "TEXT",
   CommDataColumns.OLDMESSAGE_SIZE: "INTEGER",
   CommDataColumns.OLDMESSAGE_PRIORITY: "INTEGER",
   CommDataColumns.OLDMESSAGE_DATATAG: "REAL",
   CommDataColumns.SENDER_NAME: "TEXT",
   CommDataColumns.SENDER_SIDE: "TEXT",
   CommDataColumns.SENDER_TYPE: "TEXT",
   CommDataColumns.SENDER_BASETYPE: "TEXT",
   CommDataColumns.SENDERLOCATION_X: "REAL",
   CommDataColumns.SENDERLOCATION_Y: "REAL",
   CommDataColumns.SENDERLOCATION_Z: "REAL",
   CommDataColumns.SENDER_LATITUDE: "REAL",
   CommDataColumns.SENDER_LONGITUDE: "REAL",
   CommDataColumns.SENDER_ALTITUDE: "REAL",
   CommDataColumns.SENDERPART_NAME: "TEXT",
   CommDataColumns.SENDERPART_TYPE: "TEXT",
   CommDataColumns.SENDERPART_BASETYPE: "TEXT",
   CommDataColumns.RECEIVER_NAME: "TEXT",
   CommDataColumns.RECEIVER_SIDE: "TEXT",
   CommDataColumns.RECEIVER_TYPE: "TEXT",
   CommDataColumns.RECEIVER_BASETYPE: "TEXT",
   CommDataColumns.RECEIVERLOCATION_X: "REAL",
   CommDataColumns.RECEIVERLOCATION_Y: "REAL",
   CommDataColumns.RECEIVERLOCATION_Z: "REAL",
   CommDataColumns.RECEIVER_LATITUDE: "REAL",
   CommDataColumns.RECEIVER_LONGITUDE: "REAL",
   CommDataColumns.RECEIVER_ALTITUDE: "REAL",
   CommDataColumns.RECEIVERPART_NAME: "TEXT",
   CommDataColumns.RECEIVERPART_TYPE: "TEXT",
   CommDataColumns.RECEIVERPART_BASETYPE: "TEXT",
   CommDataColumns.SENDERTORCVR_RANGE: "REAL",
   CommDataColumns.COMMINTERACTION_SUCCEEDED: "INTEGER",
   CommDataColumns.COMMINTERACTION_FAILED: "INTEGER",
   CommDataColumns.COMMINTERACTION_FAILEDSTATUS: "TEXT",
   CommDataColumns.QUEUE_SIZE: "INTEGER"   
}


PANDAS_COMM_DATA_TYPES = {
   SharedColumns.ISO_DATE: str,
   SharedColumns.HMS_TIME: str,
   SharedColumns.SIMULATION_TIME: np.float64,
   SharedColumns.EVENT_TYPE: str,
   CommDataColumns.MESSAGE_SERIALNUMBER: np.int32,
   CommDataColumns.MESSAGE_ORIGINATOR: str,
   CommDataColumns.MESSAGE_TYPE: str,
   CommDataColumns.MESSAGE_SIZE: np.int32,
   CommDataColumns.MESSAGE_PRIORITY: np.int16,
   CommDataColumns.MESSAGE_DATATAG: np.float64,
   CommDataColumns.OLDMESSAGE_SERIALNUMBER: np.int32,
   CommDataColumns.OLDMESSAGE_ORIGINATOR: str,
   CommDataColumns.OLDMESSAGE_TYPE: str,
   CommDataColumns.OLDMESSAGE_SIZE: np.int32,
   CommDataColumns.OLDMESSAGE_PRIORITY: np.int16,
   CommDataColumns.OLDMESSAGE_DATATAG: np.float64,
   CommDataColumns.SENDER_NAME: str,
   CommDataColumns.SENDER_SIDE: str,
   CommDataColumns.SENDER_TYPE: str,
   CommDataColumns.SENDER_BASETYPE: str,
   CommDataColumns.SENDERLOCATION_X: np.float64,
   CommDataColumns.SENDERLOCATION_Y: np.float64,
   CommDataColumns.SENDERLOCATION_Z: np.float64,
   CommDataColumns.SENDER_LATITUDE: np.float64,
   CommDataColumns.SENDER_LONGITUDE: np.float64,
   CommDataColumns.SENDER_ALTITUDE: np.float64,
   CommDataColumns.SENDERPART_NAME: str,
   CommDataColumns.SENDERPART_TYPE: str,
   CommDataColumns.SENDERPART_BASETYPE: str,
   CommDataColumns.RECEIVER_NAME: str,
   CommDataColumns.RECEIVER_SIDE: str,
   CommDataColumns.RECEIVER_TYPE: str,
   CommDataColumns.RECEIVER_BASETYPE: str,
   CommDataColumns.RECEIVERLOCATION_X: np.float64,
   CommDataColumns.RECEIVERLOCATION_Y: np.float64,
   CommDataColumns.RECEIVERLOCATION_Z: np.float64,
   CommDataColumns.RECEIVER_LATITUDE: np.float64,
   CommDataColumns.RECEIVER_LONGITUDE: np.float64,
   CommDataColumns.RECEIVER_ALTITUDE: np.float64,
   CommDataColumns.RECEIVERPART_NAME: str,
   CommDataColumns.RECEIVERPART_TYPE: str,
   CommDataColumns.RECEIVERPART_BASETYPE: str,
   CommDataColumns.SENDERTORCVR_RANGE: np.float64,
   CommDataColumns.COMMINTERACTION_SUCCEEDED: np.int8,
   CommDataColumns.COMMINTERACTION_FAILED: np.int8,
   CommDataColumns.COMMINTERACTION_FAILEDSTATUS: str,
   CommDataColumns.QUEUE_SIZE: np.int16
}

__all__ = [
   "DATABASE_CHUNK_SIZE",
   "COMM_DATA_TABLE",
   "COMM_SUBSTITUTIONS",
   "SQLITE_COMM_DATA_TYPES",
   "PANDAS_COMM_DATA_TYPES",
   "SharedColumns",
   "CommDataColumns",
]