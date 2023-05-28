#!/usr/bin/env python3
# coding: euc_jp

# ================================================================================
# File Name                  : init_check_tool.py
#
# Copyright(C) Canon Inc.
# All rights reserved.
# Confidential
#
# --------------------------------------------------------------------------------
# Function                   : xxx
# --------------------------------------------------------------------------------
# Designer                   : Canon Inc.
# --------------------------------------------------------------------------------
# History      Date          Designer      Contents
# 0.0.1.000    2023/06/01    Canon Inc.    New
# ================================================================================

import os
import re
import glob
import json
import subprocess
from ftplib import FTP, all_errors
from datetime import datetime, timedelta
from telnetlib import Telnet

# xxx
ESPRITSET_PATH     = '/console/mdas/MachineList'
ESPRITSET_NAME     = '*.espritset'
ESPRITSET_NAME_KEY = 'setenv TOOL_ID'
ESPRITSET_TYPE_KEY = 'setenv ESPRIT_MACHINE_TYPE'
ESPRITSET_EIP_KEY  = 'setenv EPC_IPADDR'
ESPRITSET_LIP_KEY  = 'setenv LOGPC_IPADDR'
ESPRITSET_SN_KEY   = 'setenv SERIAL_NUM'

# xxx
DATA_PUSH_PATH = '/console/mdas/etc'
DATA_PUSH_FILE = 'data_push.json'
LDB_FAB_KEY    = 'CustomerName'
LDB_IP_KEY     = 'IPAddress'

# Equip. user/password
EQUIP_USER = 'ifour'
EQUIP_PASS = 'ifour22'
EQUIP_PORT = 21

# LDB user/password
LDB_USER = 'lpsuser'
LDB_PASS = 'lpspass2'

TELNET_PORT = 23
TIME_OUT = 5

# xxx
searchTargetListEquip = [
    {
        'path': '/home/suomus/Documents/check_tool',
        'file': '*.espritset',
    },
]

# xxx
LDB_ORIGINAL_PATH = '/liplus/original'
LDB_RECOVERY_PATH = '/liplus/recovery'

"""
@class   PriorConfirmation
@details xxx
"""
class PriorConfirmation():

    def __init__(self):
        self._ftp = FTP()

        self._equipList = []
        self._ldbInfo = {}

        self._logFile = open('mdas_log.txt', 'w')

    def __del__(self):
        self._logFile.close()

    def log_info(self, msg, flag = True):
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        if flag:
            print(now + ' [INFO ] ' + msg)
        self._logFile.write(now + ' [INFO ] ' + msg + '\n')

    def log_warn(self, msg, flag = True):
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        if flag:
            print(now + ' [WARN ] ' + msg)
        self._logFile.write(now + ' [WARN ] ' + msg + '\n')

    def log_error(self, msg, flag = True):
        now = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        if flag:
            print(now + ' [ERROR] ' + msg)
        self._logFile.write(now + ' [ERROR] ' + msg + '\n')

    """
    @fn      main()
    @details xxx
    @param   None
    @return  None
    """
    def main(self):

        # MachineList内にあるespritsetを検索して、装置名、装置S/N、モデル、IPアドレスを取得する
        self.getEquipInfo()
        # data_push.jsonを参照して、FAB名、LiplusDBのIPアドレスを取得する
        self.getDataPushJson()

        # MDASに接続されているサーバーに対して疎通確認を実行する
        self.runConnectivityTest()

        # FTP接続を行いファイルの存在確認と最新ファイルの時刻情報を取得する
        # Equip.
        # 装置が出力するtopomap/finfoなど
        # ライセンスなど
        # LiplusDB
        # 転送先ディレクトリ
        self.getFileInfoOnAnotherServer()

        # サーバーとの時刻差を検出する
        self.compareSystemTime()

    """
    @fn      getEquipInfo()
    @details MachineList内にあるespritsetを検索して、装置名、装置S/N、モデル、IPアドレスを取得する
    @param   None
    @return  None
    """
    def getEquipInfo(self):
        self.log_info('==================== Read the espritset files ===========================')

        fileList = self.getFileListInMdas(ESPRITSET_PATH, ESPRITSET_NAME)
        self.log_info('Number of espritset files = ' + str(len(fileList)))
        if len(fileList) == 0:
            self.log_error('Espritset file not found')

        for file in fileList:
            equipSN = ''
            equipEIP = ''
            equipLIP = ''
            equipName = ''
            equipType = ''

            f = open(file, 'r')
            dataList = f.readlines()
            for data in dataList:
                if ESPRITSET_SN_KEY in data: # ex) 1234567
                    equipSN = re.findall('[0-9]+$', data)[0]
                elif ESPRITSET_EIP_KEY in data: # ex) 192.168.1.10
                    equipEIP = re.findall('[0-9.]+$', data)[0]
                elif ESPRITSET_LIP_KEY in data: # ex) 192.168.1.10
                    equipLIP = re.findall('[0-9.]+$', data)[0]
                elif ESPRITSET_NAME_KEY in data: # ex) equip1
                    equipName = re.findall('[a-zA-Z0-9_]+$', data)[0]
                elif ESPRITSET_TYPE_KEY in data: # ex) 63xxx
                    equipType = re.findall('[a-zA-Z0-9_]+$', data)[0]
            f.close()

            self.log_info('-- ' + os.path.basename(file))
            self.log_info('  Name: ' + equipName)
            self.log_info('  Type: ' + equipType)
            self.log_info('  EIP : ' + equipEIP)
            self.log_info('  LIP : ' + equipLIP)
            self.log_info('  S/N : ' + equipSN)

            if (equipSN != '') and (equipEIP != '') and (equipLIP != '') and \
                (equipName != '') and (equipType != ''):
                equipInfo = {
                    ESPRITSET_NAME_KEY: equipName,
                    ESPRITSET_TYPE_KEY: equipType,
                    ESPRITSET_EIP_KEY: equipEIP,
                    ESPRITSET_LIP_KEY: equipLIP,
                    ESPRITSET_SN_KEY: equipSN,
                }
                self._equipList.append(equipInfo)
            else:
                self.log_error('There was a problem with espritset file')

    """
    @fn      getDataPushJson()
    @details data_push.jsonを参照して、FAB名、LiplusDBのIPアドレスを取得する
    @param   None
    @return  None
    """
    def getDataPushJson(self):
        self.log_info('==================== Read the data_push.json ============================')

        path = os.path.join(DATA_PUSH_PATH, DATA_PUSH_FILE)
        if os.path.exists(path):
            jsonFile = open(path, 'r')
            jsonData = json.load(jsonFile)
            self._ldbInfo = {
                LDB_FAB_KEY: jsonData[LDB_FAB_KEY],
                LDB_IP_KEY: jsonData[LDB_IP_KEY],
            }
            self.log_info('-- data_push.json')
            self.log_info('  FAB : ' + self._ldbInfo[LDB_FAB_KEY])
            self.log_info('  IP  : ' + self._ldbInfo[LDB_IP_KEY])
        else:
            self.log_error('Path does not exist: ' + path)

    """
    @fn      getFileListInMdas()
    @details MDASの対象パス内にある対象ファイル名のファイルを検索してリスト形式で返す
    @param   path      対象パス
    @param   extension 対象ファイル名
    @return            ファイルリスト
    """
    def getFileListInMdas(self, path, extension = '*'):
        fileList = ''
        if os.path.exists(path):
            fileList = glob.glob(os.path.join(path, extension))
        else:
            self.log_error('Path does not exist: ' + path)
        return fileList

    """
    @fn      runConnectivityTest()
    @details MDASに接続されているサーバーに対して疎通確認を実行する
    @param   None
    @return  None
    """
    def runConnectivityTest(self):
        self.log_info('==================== Run Connectivity Test ==============================')

        for equipInfo in self._equipList:
            self.log_info('-- Name: ' + equipInfo[ESPRITSET_NAME_KEY] + ' / IP: ' + equipInfo[ESPRITSET_EIP_KEY])
            self.runPing(equipInfo[ESPRITSET_EIP_KEY])

        self.log_info('-- Name: LiplusDB / IP: ' + self._ldbInfo[LDB_IP_KEY])
        self.runPing(self._ldbInfo[LDB_IP_KEY])

    """
    @fn      runPing()
    @details 指定されたIPアドレスに対してpingを実行する
    @param   ip   IPアドレス
    @return  None
    """
    def runPing(self, ip):
        cmd = ['ping', ip, '-c', '4', '-w', '100']
        self.log_info('  ' + ' '.join(cmd))
        res = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        #self.log_info(res.stdout.decode(), False)
        if res.returncode == 0:
            self.log_info('  Check -> OK!')
        else:
            self.log_error('  Check -> NG!')

    """
    @fn      getFileInfoOnAnotherServer()
    @details FTP接続を行いファイルの存在確認と最新ファイルの時刻情報を取得する
    @param   None
    @return  None
    """
    def getFileInfoOnAnotherServer(self):
        self.log_info('==================== Check file existence in equip ======================')

        for equipInfo in self._equipList:
            self.log_info('-- ' + 'Name: ' + equipInfo[ESPRITSET_NAME_KEY] + ' / ' + 'IP: ' + equipInfo[ESPRITSET_EIP_KEY])
            self.log_info('---- Equip')

            try:
                self._ftp = FTP()
                self._ftp.connect(host = equipInfo[ESPRITSET_EIP_KEY], port = EQUIP_PORT, timeout = TIME_OUT)
                self._ftp.login(user = EQUIP_USER, passwd = EQUIP_PASS)
            except all_errors as e:
                self.log_error('FTP connection error: ' + str(e))
                continue

            # Equip.
            # 装置が出力するtopomap/finfoなど
            # ライセンスなど
            self.getFileInfoOnEquipServer()

            self.log_info('---- LiplusDB')

            # LiplusDB
            # 転送先ディレクトリ
            self.getFileInfoOnLDBServer(equipInfo)

            self._ftp.close()

    """
    @fn      getFileInfoOnEquipServer()
    @details FTP接続を行いファイルの存在確認と最新ファイルの時刻情報を取得する
    @param   None
    @return  None
    """
    def getFileInfoOnEquipServer(self):
        for searchTarget in searchTargetListEquip:
            self.log_info('------ Search target path: ' + searchTarget['path'] + '/' + searchTarget['file'])

            try:
                self._ftp.cwd(searchTarget['path'])
            except all_errors as e:
                self.log_error('FTP cwd (' + searchTarget['path'] + ') error: ' + str(e))
                continue

            latestFileName = ''
            latestModTime = datetime(1900, 1, 1, 0, 0, 0)
            lines = []
            try:
                # 対象パスでFTP DIRコマンドを実行する
                self._ftp.dir(lines.append)
            except all_errors as e:
                self.log_error('FTP dir (' + searchTarget['path'] + ') error: ' + str(e))
                continue

            for line in lines:
                # 下記の形式で取得できるため、分割する
                # -rwxr-xr-x 1   1000 1000 1100 Apr 1   10:00 test.dat
                # [0]        [1] [2]  [3]  [4]  [5] [6] [7]   [8]
                fileInfo = line.split()
                fileName = fileInfo[-1]
                try:
                    modTime = latestModTime
                    if re.match('\d{2}:\d{2}', fileInfo[7]):
                        modTime = datetime.strptime('{} {}'.format(datetime.utcnow().year, ' '.join(fileInfo[5:8])), '%Y %b %d %H:%M')
                    elif re.match('\d{4}', fileInfo[7]):
                        year = fileInfo[7]
                        fileInfo[7] = '00:00'
                        modTime = datetime.strptime('{} {}'.format(year, ' '.join(fileInfo[5:8])), '%Y %b %d %H:%M')
                    if modTime > latestModTime:
                        latestFileName = fileName
                        latestModTime = modTime
                except all_errors as e:
                    self.log_warn('Failed to parse timestamp: ' + line)
                    self.log_warn('Failed to parse timestamp: ' + str(e))

            if latestFileName != '':
                self.log_info('  Latest file: file = ' + fileName + ' / time = ' + str(latestModTime))
            else:
                self.log_error('Could not find latest file')

    """
    @fn      getFileInfoOnLDBServer()
    @details FTP接続を行いファイルの存在確認と最新ファイルの時刻情報を取得する
    @param   equipInfo 装置情報
    @return  None
    """
    def getFileInfoOnLDBServer(self, equipInfo):
        path = os.path.join(LDB_ORIGINAL_PATH, self._ldbInfo[LDB_FAB_KEY], equipInfo[ESPRITSET_SN_KEY])
        self.log_info('------ Search target path: ' + path)
        try:
            self._ftp.cwd(path)
            self.log_info('  Check -> OK!')
        except all_errors as e:
            self.log_error('FTP cwd (' + path + ') error: ' + str(e))
            self.log_error('  Check -> NG!')

    """
    @fn      compareSystemTime()
    @details xxx
    @param   None
    @return  None
    """
    def compareSystemTime(self):
        self.log_info('==================== Get time difference ================================')

        cmd = 'date \'+%Y/%m/%d %H:%M:%S\''

        for equipInfo in self._equipList:
            self.log_info('-- ' + 'Name: ' + equipInfo[ESPRITSET_NAME_KEY] + ' / ' + 'IP: ' + equipInfo[ESPRITSET_EIP_KEY])
            self.log_info('---- Equip')

            # 'date'コマンドを実行する
            res = self.runTelnetCmd(equipInfo[ESPRITSET_EIP_KEY], EQUIP_USER, EQUIP_PASS, cmd)
            if res:
                self.checkTimeDifference(res.decode('utf-8'))

        self.log_info('---- LiplusDB')

        # 'date'コマンドを実行する
        res = self.runTelnetCmd(self._ldbInfo[LDB_IP_KEY], LDB_USER, LDB_PASS, cmd)
        if res:
            self.checkTimeDifference(res.decode('utf-8'))

    """
    @fn      checkTimeDifference()
    @details xxx
    @param   None
    @return  None
    """
    def checkTimeDifference(self, res):
        # 接続先サーバーの時刻情報を取得する
        match = re.search('\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', res)
        if match:
            destTime = datetime.strptime(match.group(), '%Y/%m/%d %H:%M:%S')
            mdasTime = datetime.now()
            self.log_info('  dest: ' + str(destTime))
            self.log_info('  mdas: ' + str(mdasTime.strftime('%Y-%m-%d %H:%M:%S')))

            diff = abs(destTime - mdasTime)
            self.log_info('  diff: ' + str(diff))
            if diff > timedelta(seconds = 120):
                if destTime > mdasTime:
                    self.log_info('  Check -> OK!')
                else:
                    self.log_error('  Check -> NG!')

    """
    @fn      runTelnetCmd()
    @details xxx
    @param   None
    @return  None
    """
    def runTelnetCmd(self, ip, user, passwd, cmd):
        try:
            # Telnetで接続を行う
            tn = Telnet(ip, TELNET_PORT, TIME_OUT)
            # ユーザー名の入力
            tn.read_until(b'login: ')
            tn.write(user.encode() + b'\n')
            # パスワードの入力
            tn.read_until(b'Password: ')
            tn.write(passwd.encode() + b'\n')
            # ログインの実行完了待ち
            output = tn.read_until(b'$')

        except:
            self.log_error('Telnet connection error')
            return
            
        try:
            # コマンドを実行する
            tn.write(cmd.encode() + b'\n')
            # コマンドの実行完了待ち
            output = tn.read_until(b'$')
            # Telnetを切断する            
            tn.write(b'exit\n')

        except:
            self.log_error('Command error via telnet')
            return

        return output

if __name__ == '__main__':
    obj = PriorConfirmation()
    obj.main()
    del obj
