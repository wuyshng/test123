# Project
TCUA = "TCUA"
VCM  = "VCM"

# Config Variable for loading TC
LIST_TC_NAME            = {}
LIST_TEST_STEP          = {}
LIST_TEST_DESCRIPTION   = {}
LIST_EXPECTED_RESULT    = {}
LIST_TC_POSITION        = {}

MODULE              = "POWER"
TC_NAME             = "TC_Name"
TC_TEST_STEP        = "TEST_STEP"
TC_DESCRIPTON       = "DESCRIPTION"
TC_EXPECTED_RESULT  = "EXPECTED_RESULT"


# DLT config
DLT_DIRECTORY = ""

# CAn bus status
CAN_BUS_UNKOWN = 0
CAN_BUS_ACTIVE = 1
CAN_BUS_SLEEP  = 2
CAN_BUS_READY  = 3

# Common Variable
WAITTING_TIME           = 15  # second
PWMINITIAL_TIMER        = 60  # for testing
PWM_SLEEP_TIMER         = 120 # for testing
PWM_RECEIVE_TIMER       = 120 # for testing
PWM_FIRST_CYCLE_TIMER   = 220 # for testing

# Port
NO_PORT_CONNECTED = "NO_PORT_CONNECTED"

# Device ID
UNKNOWN_ID = -1

VCM_DEVICE_ID = {
    "18728d96" : "BOARD 5G #13 REVB",
    "eaeeb0b7" : "BOARD 5G #14 REVB",
    "9f530770" : "BOARD 5G #11 REVC",
    "50f3cf4"  : "BOARD 5G #15 REVC",
    "146e5691" : "BOARD 5G #17 REVC",
}

VCM_BOARD = {
    "BOARD 5G #13 REVB" : "18728d96",
    "BOARD 5G #14 REVB" : "eaeeb0b7",
    "BOARD 5G #11 REVC" : "9f530770",
    "BOARD 5G #15 REVC" : "50f3cf4",
    "BOARD 5G #17 REVC" : "146e5691",
}

# Device Status
NORMAL           = "Normal"
DISCONNECTED     = "Disconnected"
BOOTING          = "Booting"
NOT_READY        = "Not_ready"

# Power source control
VBAT_ON          = "VBAT_ON"
VBAT_OFF         = "VBAT_OFF"
BUB_ON           = "BUB_ON"
BUB_OFF          = "BUB_OFF"
POWER_RESET      = "POWER_RESET"
CONNECT_ARDUINO  = "CONNECT_ARDUINO"

# Signal thread
SIGNAL_DEVICE_BOOTING             = 101
SIGNAL_DEVICE_BOOT_COMPLETED      = 102
SIGNAL_DEVICE_DISCONNECTED        = 103
SIGNAL_SEND_CAN_NM                = 104
SIGNAL_STOP_CAN_NM                = 105
SIGNAL_RESET_BOARD                = 106
SIGNAL_START_WATCHDOG_TIMER       = 107
SIGNAL_STOP_WATCHDOG_TIMER        = 108
SIGNAL_REMOVE_VBAT                = 119
SIGNAL_VERIFY_LOGS                = 120
SIGNAL_TESTING_STARTED            = 121
SIGNAL_TESTING_COMPLETED          = 122
SIGNAL_SEND_TC10_OFF              = 123
SIGNAL_SEND_TC10_ON               = 124
SIGNAL_VERIFY_ADB_OUTPUT_VALID    = 125
SIGNAL_VERIFY_ADB_OUTPUT_INVALID  = 126


# TimerID
SLEEP_TIMER = 1

# Message ID
ON_SLEEP_TIMER_EXPIRED      = 1000
ON_LISTEN_TIMER_EXPIRED     = 1001


# Test result
PASSED = "PASSED"
FAILED = "FAILED"

# Error code
E_ERROR = -1
E_OK    = 0

# No version
NO_VERSION      = -1
NO_DATA_FOUND   = "NO_DATA_FOUND"

# Wakeup factor
WK_BY_CAN_FROM_SLEEP        = "WK_BY_CAN_FROM_SLEEP"
WK_BY_CAN_FROM_LISTEN       = "WK_BY_CAN_FROM_LISTEN"
WK_BY_AP_RTC                = "WK_BY_AP_RTC"
NO_WAKEUP                   = "NO_WAKEUP"

# Type of command
RESET_BOARD                 = "RESET_BOARD"
SEND_COMMAND                = "SEND_COMMAND"
SEND_CAN_NM                 = "SEND_CAN_NM"
STOP_CAN_NM                 = "STOP_CAN_NM"
WAKEUP                      = "WAKEUP"
VERIFY_LOG                  = "VERIFY_LOG"
START_TO_GET_LOGS           = "START_TO_GET_LOGS"
WAIT_FOR_DEVICE_READY       = "WAIT_FOR_DEVICE_READY"
WAIT_FOR_STATE_TRANSITION   = "WAIT_FOR_STATE_TRANSITION"
ENABLE_BUB                  = "ENABLE_BUB"
REMOVE_VBAT                 = "REMOVE_VBAT"
SEND_TC10_ON                = "SEND_TC10_ON"
SEND_TC10_OFF               = "SEND_TC10_OFF"
VERIFY_ADB_OUTPUT           = "VERIFY_ADB_OUTPUT"

# Test case config
TEST_CASE_START = 1

# Automate QFIL
DOWNLOAD_IMAGE_ONLY         = "DOWNLOAD_IMAGE_ONLY"
FLASH_IMAGE_ONLY            = "FLASH_IMAGE_ONLY"
DOWNLOAD_FLASH_IMAGE        = "DOWNLOAD_FLASH_IMAGE"
NO_IMAGE_URL                = ""
DEFAULT_DOWNLOAD_IMAGE_URL  = ""
VCM_ARTIFACTORY_BASE_URL    = "http://vbas.lge.com:8082/artifactory/vcm/DAILY"  
TCUA_ARTIFACTORY_BASE_URL   = "http://vbas.lge.com:8082/artifactory/tcua/DAILY"  