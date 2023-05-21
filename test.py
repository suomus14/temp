#!/usr/bin/env python3
# coding: euc_jp

# ================================================================================
# File Name                  : xxx
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
# 0.0.1.000    2023/04/15    Canon Inc.    New
# ================================================================================

import os
import re
import glob
import json
import subprocess
from ftplib import FTP, all_errors
from datetime import datetime

# xxx
ESPRITSET_PATH = './'
ESPRITSET_NAME = '*.espritset'
ESPRITSET_NAME_KEY = 'NAME'
ESPRITSET_TYPE_KEY = 'TYPE'
ESPRITSET_IP_KEY = 'ADDRESS'
ESPRITSET_SN_KEY = 'SN'

# xxx
DATA_PUSH_JSON = 'data_push.json'
LDB_FAB_KEY = 'fab_name'
LDB_IP_KEY = 'ip_address'

# Equip. user/password
EQUIP_USER = 'suomus'
EQUIP_PASS = '1018'
EQUIP_PORT = 21

# LDB user/password
LDB_USER = 'suomus'
LDB_PASS = '1018'

# xxx
searchTargetListEquip = [
    {
        'path': '/hestia/web/work',
        'file': '*.sh',
    },
    {
        'path': '/hestia/web/a',
        'file': '*.sh',
    },
]

# xxx
searchTargetListLdb = [
    {
        'path': '/hestia/web/work',
        'file': '*.sh',
    },
]

"""
@class   PriorConfirmation
@details xxx
"""
class PriorConfirmation():

    def __init__(self):
        self.equipList = []
        self.ldbInfo = {}

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
        #self.runConnectivityTest()

        self.getFileInfoOnAnotherServer()





    """
    @fn      getEquipInfo()
    @details MachineList内にあるespritsetを検索して、装置名、装置S/N、モデル、IPアドレスを取得する
    @param   None
    @return  None
    """
    def getEquipInfo(self):
        print('[INFO] ==================== Read the espritset files      ====================')

        fileList = self.getFileListInMdas(ESPRITSET_PATH, ESPRITSET_NAME)
        print('[INFO] Number of espritset files = ' + str(len(fileList)))
        if len(fileList) == 0:
            print('[ERROR] Espritset file not found')

        for file in fileList:
            equipName = ''
            equipType = ''
            equipIP = ''
            equipSN = ''

            f = open(file, 'r')
            dataList = f.readlines()
            for data in dataList:
                if 0:
                    pass
                elif ESPRITSET_NAME_KEY in data: # ex) equip1
                    equipName = re.findall('[a-zA-Z0-9_]+$', data)[0]
                elif ESPRITSET_TYPE_KEY in data: # ex) 63xxx
                    equipType = re.findall('[a-zA-Z0-9_]+$', data)[0]
                elif ESPRITSET_IP_KEY in data: # ex) 192.168.1.10
                    equipIP = re.findall('[0-9.]+$', data)[0]
                elif ESPRITSET_SN_KEY in data: # ex) 1234567
                    equipSN = re.findall('[0-9]+$', data)[0]
            f.close()

            print('[INFO] ----- ' + os.path.basename(file) + ' -----')
            print('[INFO] Name: ' + equipName)
            print('[INFO] Type: ' + equipType)
            print('[INFO] IP  : ' + equipIP)
            print('[INFO] S/N : ' + equipSN)

            equipInfo = {
                ESPRITSET_NAME_KEY: equipName,
                ESPRITSET_TYPE_KEY: equipType,
                ESPRITSET_IP_KEY: equipIP,
                ESPRITSET_SN_KEY: equipSN,
            }
            self.equipList.append(equipInfo)

    """
    @fn      getDataPushJson()
    @details data_push.jsonを参照して、FAB名、LiplusDBのIPアドレスを取得する
    @param   None
    @return  None
    """
    def getDataPushJson(self):
        print('[INFO] ==================== Read the data_push.json       ====================')

        jsonFile = open(DATA_PUSH_JSON, 'r')
        jsonData = json.load(jsonFile)
        self.ldbInfo = {
            LDB_FAB_KEY: jsonData[LDB_FAB_KEY],
            LDB_IP_KEY: jsonData[LDB_IP_KEY],
        }
        print('[INFO] ----- LiplusDB -----')
        print('[INFO] FAB : ' + self.ldbInfo[LDB_FAB_KEY])
        print('[INFO] IP  : ' + self.ldbInfo[LDB_IP_KEY])

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
        return fileList

    """
    @fn      runConnectivityTest()
    @details MDASに接続されているサーバーに対して疎通確認を実行する
    @param   None
    @return  None
    """
    def runConnectivityTest(self):
        print('[INFO] ==================== Run Connectivity Test         ====================')

        for equipInfo in self.equipList:
            print('[INFO] ----- Name: ' + equipInfo[ESPRITSET_NAME_KEY] + ' / IP: ' + equipInfo[ESPRITSET_IP_KEY] + ' -----')
            self.runPing(equipInfo[ESPRITSET_IP_KEY])

        print('[INFO] ----- Name: LiplusDB / IP: ' + self.ldbInfo[LDB_IP_KEY] + ' -----')
        self.runPing(self.ldbInfo[LDB_IP_KEY])

        # LDB

    """
    @fn      runPing()
    @details 指定されたIPアドレスに対してpingを実行する
    @param   ip   IPアドレス
    @return  None
    """
    def runPing(self, ip):
        res = subprocess.run(['ping', ip, '-c', '4', '-w', '100'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        print(res.stdout.decode())
        if res.returncode == 0:
            print('[INFO] Check -> OK!\n')
        else:
            print('[INFO] Check -> NG!\n')

    """
    @fn      getFileInfoOnAnotherServer()
    @details xxx
    @param   None
    @return  None
    """
    def getFileInfoOnAnotherServer(self):
        print('[INFO] ==================== Check file existence in equip ====================')

        for equipInfo in self.equipList:
            print('[INFO] ----- ' + 'Name: ' + equipInfo[ESPRITSET_NAME_KEY] + ' / ' + 'IP: ' + equipInfo[ESPRITSET_IP_KEY] + ' -----')

            try:
                ftp = FTP()
                ftp.connect(host = equipInfo[ESPRITSET_IP_KEY], port = EQUIP_PORT, timeout = 5)
                ftp.login(user = EQUIP_USER, passwd = EQUIP_PASS)
            except all_errors as e:
                print('[ERROR] FTP connection error: xxx')
                continue

            for searchTarget in searchTargetListEquip:
                print('[INFO] --- Search target path: ' + searchTarget['path'] + ' ---')

                try:
                    ftp.cwd(searchTarget['path'])
                except all_errors as e:
                    print('[ERROR] FTP cwd (' + searchTarget['path'] + ') error: xxx')
                    continue

                latestFileName = ''
                latestModTime = datetime(1900, 1, 1, 0, 0, 0)
                lines = []
                try:
                    # 対象パスでFTP DIRコマンドを実行する
                    ftp.dir(lines.append)
                except all_errors as e:
                    print('[ERROR] FTP dir (' + searchTarget['path'] + ') error: xxx')
                    continue
                for line in lines:
                    # 下記の形式で取得できるため、分割する
                    # -rwxr-xr-x 1   1000 1000 1100 Apr 1   10:00 test.dat
                    # [0]        [1] [2]  [3]  [4]  [5] [6] [7]   [8]
                    fileInfo = line.split()
                    fileName = fileInfo[-1]
                    try:
                        modTime = datetime.strptime("{} {}".format(datetime.utcnow().year, " ".join(fileInfo[5:8])), "%Y %b %d %H:%M")
                        if modTime > latestModTime:
                            latestFileName = fileName
                            latestModTime = modTime
                    except:
                        print('[WARN] Failed to parse timestamp' + line)

                if latestFileName != '':
                    print('[INFO] Latest file: file = ' + fileName + ' / time = ' + str(latestModTime))
                else:
                    print('[ERROR] Could not find latest file')

            ftp.close()







if __name__ == "__main__":
    obj = PriorConfirmation()
    obj.main()
