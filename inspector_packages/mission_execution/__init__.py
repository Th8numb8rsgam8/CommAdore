from inspector_packages import np

DATABASE_CHUNK_SIZE = 1000

COMM_DATA_TABLE = "comm_data"
TRACK_DATA_TABLE = "track_data"
PLATFORM_DATA_TABLE = "platform_data"
QUEUE_DATA_TABLE = "queue_data"

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

# TRACK DATA COLUMNS
class TrackDataColumns:
   TIME_SINCE_STARTED = "Time_Since_Started"
   TIME_SINCE_UPDATED = "Time_Since_Updated"
   TRACK_ID = "Track_ID"
   OWNING_PLATFORM = "Owning_Platform"
   PLATFORM_TYPE = "Platform_Type"
   NONLOCAL_TRACK_ID = "NonLocal_Track_ID"
   TRACK_LIST_COUNT = "Track_List_Count"
   RAW_TRACK_COUNT = "Raw_Track_Count"
   MASTER_TRACK_LIST = "Master_Track_List"
   RAW_TRACKS = "Raw_Tracks"
   ALTITUDE_KNOWN = "Altitude_Known"
   IS_STALE = "Is_Stale"
   PLATFORMLOCATION_X = "PlatformLocation_X"
   PLATFORMLOCATION_Y = "PlatformLocation_Y"
   PLATFORMLOCATION_Z = "PlatformLocation_Z"
   TARGETLOCATION_X = "TargetLocation_X"
   TARGETLOCATION_Y = "TargetLocation_Y"
   TARGETLOCATION_Z = "TargetLocation_Z"

# PLATFORM DATA COLUMNS
class PlatformDataColumns:
   PLATFORM_NAME = "Platform_Name"
   LOCATION_X = "Location_X"
   LOCATION_Y = "Location_Y"
   LOCATION_Z = "Location_Z"

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

TRACK_SUBSTITUTIONS = {
   TrackDataColumns.NONLOCAL_TRACK_ID: "no_track",
   TrackDataColumns.RAW_TRACKS: "no_tracks"
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

SQLITE_TRACK_DATA_TYPES = {
   SharedColumns.EVENT_ID: "INTEGER PRIMARY KEY",
   SharedColumns.ISO_DATE: "TEXT",
   SharedColumns.HMS_TIME: "TEXT",
   SharedColumns.SIMULATION_TIME: "REAL",
   SharedColumns.EVENT_TYPE: "TEXT",
   TrackDataColumns.TIME_SINCE_STARTED: "REAL",
   TrackDataColumns.TIME_SINCE_UPDATED: "REAL",
   TrackDataColumns.TRACK_ID: "TEXT",
   TrackDataColumns.OWNING_PLATFORM: "TEXT",
   TrackDataColumns.PLATFORM_TYPE: "TEXT",
   TrackDataColumns.NONLOCAL_TRACK_ID: "TEXT",
   TrackDataColumns.TRACK_LIST_COUNT: "INTEGER",
   TrackDataColumns.RAW_TRACK_COUNT: "INTEGER",
   TrackDataColumns.MASTER_TRACK_LIST: "TEXT",
   TrackDataColumns.RAW_TRACKS: "TEXT",
   TrackDataColumns.ALTITUDE_KNOWN: "INTEGER",
   TrackDataColumns.IS_STALE: "INTEGER",
   TrackDataColumns.PLATFORMLOCATION_X: "REAL",
   TrackDataColumns.PLATFORMLOCATION_Y: "REAL",
   TrackDataColumns.PLATFORMLOCATION_Z: "REAL",
   TrackDataColumns.TARGETLOCATION_X: "REAL",
   TrackDataColumns.TARGETLOCATION_Y: "REAL",
   TrackDataColumns.TARGETLOCATION_Z: "REAL"
}

SQLITE_PLATFORM_DATA_TYPES = {
   SharedColumns.EVENT_ID: "INTEGER PRIMARY KEY",
   SharedColumns.ISO_DATE: "TEXT",
   SharedColumns.HMS_TIME: "TEXT",
   SharedColumns.SIMULATION_TIME: "REAL",
   PlatformDataColumns.PLATFORM_NAME: "TEXT",
   TrackDataColumns.PLATFORM_TYPE: "TEXT",
   PlatformDataColumns.LOCATION_X: "REAL",
   PlatformDataColumns.LOCATION_Y: "REAL",
   PlatformDataColumns.LOCATION_Z: "REAL"
}

SQLITE_QUEUE_DATA_TYPES = {
   SharedColumns.SIMULATION_TIME: "REAL",
   CommDataColumns.SENDER_NAME: "TEXT",
   CommDataColumns.SENDERPART_NAME: "TEXT",
   CommDataColumns.MESSAGE_SERIALNUMBER: "INTEGER",
   CommDataColumns.MESSAGE_TYPE: "TEXT",
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

PANDAS_TRACK_DATA_TYPES = {
   SharedColumns.ISO_DATE: str,
   SharedColumns.HMS_TIME: str,
   SharedColumns.SIMULATION_TIME: np.float64,
   SharedColumns.EVENT_TYPE: str,
   TrackDataColumns.TIME_SINCE_STARTED: np.float64,
   TrackDataColumns.TIME_SINCE_UPDATED: np.float64,
   TrackDataColumns.TRACK_ID: str,
   TrackDataColumns.OWNING_PLATFORM: str,
   TrackDataColumns.PLATFORM_TYPE: str,
   TrackDataColumns.NONLOCAL_TRACK_ID: str,
   TrackDataColumns.TRACK_LIST_COUNT: np.uint16,
   TrackDataColumns.RAW_TRACK_COUNT: np.uint16,
   TrackDataColumns.MASTER_TRACK_LIST: str,
   TrackDataColumns.RAW_TRACKS: str,
   TrackDataColumns.ALTITUDE_KNOWN: bool,
   TrackDataColumns.IS_STALE: bool,
   TrackDataColumns.PLATFORMLOCATION_X: np.float64,
   TrackDataColumns.PLATFORMLOCATION_Y: np.float64,
   TrackDataColumns.PLATFORMLOCATION_Z: np.float64,
   TrackDataColumns.TARGETLOCATION_X: np.float64,
   TrackDataColumns.TARGETLOCATION_Y: np.float64,
   TrackDataColumns.TARGETLOCATION_Z: np.float64
}

PANDAS_PLATFORM_DATA_TYPES = {
   SharedColumns.ISO_DATE: str,
   SharedColumns.HMS_TIME: str,
   SharedColumns.SIMULATION_TIME: np.float64,
   # PlatformDataColumns.PLATFORM_NAME: str,
   TrackDataColumns.PLATFORM_TYPE: str,
   PlatformDataColumns.LOCATION_X: np.float64,
   PlatformDataColumns.LOCATION_Y: np.float64,
   PlatformDataColumns.LOCATION_Z: np.float64
}

__all__ = [
   "DATABASE_CHUNK_SIZE",
   "COMM_DATA_TABLE",
   "TRACK_DATA_TABLE",
   "PLATFORM_DATA_TABLE",
   "QUEUE_DATA_TABLE",
   "COMM_SUBSTITUTIONS",
   "TRACK_SUBSTITUTIONS",
   "SQLITE_COMM_DATA_TYPES",
   "SQLITE_TRACK_DATA_TYPES",
   "SQLITE_PLATFORM_DATA_TYPES",
   "SQLITE_QUEUE_DATA_TYPES",
   "PANDAS_COMM_DATA_TYPES",
   "PANDAS_TRACK_DATA_TYPES",
   "PANDAS_PLATFORM_DATA_TYPES",
   "SharedColumns",
   "CommDataColumns",
   "TrackDataColumns",
   "PlatformDataColumns"
]