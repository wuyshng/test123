import os
import sys

# Choose project path depending on whether the application is a frozen exe or a script
if getattr(sys, 'frozen', False):
    PROJECT_PATH = os.path.dirname(sys.executable)
elif __file__:
    PROJECT_PATH = os.path.dirname(os.path.abspath(__file__)) + r"\.."

# Config
CONFIG_PATH = os.path.join(PROJECT_PATH, r'conf\conf.ini')

# Settings
USERSETTING_PATH = os.path.join(PROJECT_PATH, r'conf\usersetting.ini')
PROJECTSETTING_PATH = os.path.join(PROJECT_PATH, r'conf\projectsetting.ini')

# Log
LOG_DIR_PATH = os.path.join(PROJECT_PATH, 'log')
TOOL_LOG_PATH = os.path.join(LOG_DIR_PATH, 'tool.log')
QFIL_LOG_PATH = os.path.join(LOG_DIR_PATH, 'qfil.log')
BUILD_LOG_PATH = os.path.join(LOG_DIR_PATH, 'bee-build.log')
BUILD_SCRIPT_PATH = os.path.join(LOG_DIR_PATH, 'build.sh')

# DB
DB_PATH = os.path.join(PROJECT_PATH, 'db')
IMAGE_DB_PATH = os.path.join(DB_PATH, 'image.csv')
CACHE_DB_PATH = os.path.join(DB_PATH, 'cache.ini')

# Temporary data
TEMP_DIR_PATH = os.path.join(PROJECT_PATH, 'tmp')
TEMP_GIT_LOG_PATH = os.path.join(TEMP_DIR_PATH, 'git-log.log')
TEMP_GIT_DIFF_PATH = os.path.join(TEMP_DIR_PATH, 'git-diff.patch')

# Package
ARIA_EXE_PATH = os.path.join(PROJECT_PATH, r'package\aria2-1.37.0\aria2c.exe')

# Get/set device log
LOG_RUNTIME_DIR_NAME = 'log_runtime'
SCRIPT_DIR_PATH = os.path.join(PROJECT_PATH, r'conf\scripts')
GET_LOG_SCRIPT = os.path.join(SCRIPT_DIR_PATH, 'get_log.ps1')
SET_LOG_SCRIPT = os.path.join(SCRIPT_DIR_PATH, 'set_log.ps1')
DOWNLOAD_V2X_LIBS_SCRIPT = os.path.join(SCRIPT_DIR_PATH, 'download_cmf_service_libs.ps1')

TOOL_VERSION = '1.0'

class COMMAND:
    BUILD = 'build'
    DOWNLOAD = 'download'
    FLASH = 'flash'
    BUILD_DOWNLOAD = 'build-download'
    DOWNLOAD_FLASH = 'download-flash'
    BUILD_DOWNLOAD_FLASH = 'build-download-flash'
    ALL = 'all'    # Same as BUILD_DOWNLOAD_FLASH
    IMAGE = 'image'
    LOG = 'log'
    SCRIPT = 'script'
    LGVF = 'lgvf'

class SUBCOMMAND_IMAGE:
    LIST = 'list'
    DESC = 'desc'
    SHARE = 'share'

class SUBCOMMAND_LOG:
    SET = 'set'
    GET = 'get'
    DIAG = 'diag'

class SUBCOMMAND_SCRIPT:
    LIST = 'list'
    RUN = 'run'

ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

class VBEE_COMMAND:
    BOOST_START = 'bee-boost-start'
    BOOST_STOP = 'bee-boost-stop'
    BOOST_STATUS = 'bee-boost-status'
    NOTIF_MARK = 'Notify AutoTool that building is finished'

class VBEE_STATUS:
    RUNNING_IN_NONBOOST = 'Not in boost mode'
    RUNNING_IN_BOOST = ''

class VBEE_FILE_PATH:
    BUILD_SCRIPT = '/home/worker/bee_build/build.sh'
    BUILD_LOG = '/home/worker/bee_build/bee_build.log'

class CHIPSET_NAME:
    SA515M = 'SA515M'
    SA2150P = 'SA2150P'
