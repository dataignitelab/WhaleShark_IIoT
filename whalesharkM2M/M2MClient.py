import binascii
import json
import socket
import time
import minimalmodbus
import serial

from datetime import datetime

from whalesharkM2M.config.info_reader import read_controller
from whalesharkM2M.datautil.hexconversion import str2hex, int2hex

client_socket = socket.socket()
host = 'localhost'
port = 1233


def get_serialinterface(port, slaveaddr, mode, baudrate):
    '''
    시스템과 연결될 직렬포트에 대한 정보를 할당하여 리턴한다.
    '''
    instrument = minimalmodbus.Instrument(port, slaveaddr)
    instrument.serial.baudrate = baudrate  # Baud
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 2
    instrument.serial.timeout = 1  # seconds
    instrument.mode = mode
    return instrument
    
if __name__ == '__main__':
    '''
    서버와 연결될 소켓을 열고 설비 정보를 읽어 정보를 메모리에 저장한 후 설비로 부터 측정값, 상태값 등을 읽어봐 서버로 전송한다. 
    '''
    try:
        client_socket.connect((host, port))
    except Exception as e:
        print(e)
    instrument_list = []
    accessinfo_df = read_controller(filepath='config/controllerinfo.csv')
    try:
        fun_length = accessinfo_df.shape[0]
        for index, row in accessinfo_df.iterrows():
            conn = get_serialinterface(port='/dev/tty.usbserial-AQ00WOQH',
                                       slaveaddr=row['STATIONID'],
                                       mode=row['MODE'],
                                       baudrate=row['BAUDRATE'])
            acces_info ={'conn':conn,'address':row['ADDRESS']}
            instrument_list.append(acces_info)

    except Exception as e:
        print("Serial Device connection failed")
        print("Run on simulation mode")

    while True:
        if len(instrument_list) == 0:
            try:
                for index, row in accessinfo_df.iterrows():
                    sensor_id = '%04d'%(row['SENSOR_CODE'])
                    station_class = 'HM'
                    station_id = '%04d' % (1)

                    fun_cd = row['FUNCTION']
                    now = datetime.now()
                    str_time = '%d%d%d%d%d%d%d' % (
                        now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond / 1000)
                    int_time = int(str_time)
                    now_time = hex(int_time).replace('0x', '')
                    status_dict = {}
                    status_dict['sensor_cd'] = str2hex(sensor_id)
                    status_dict['fun_cd'] = str2hex(fun_cd)
                    status_dict['sensor_value'] = int2hex(202)
                    status_dict['decimal_point'] = int2hex(1)
                    status_dict['pub_time'] = now_time
                    measured_dict = {
                        'equipmentid': str2hex(station_class)+str2hex(station_id),
                        'meta': status_dict
                    }
                    data = hex(2)+json.dumps(measured_dict) + hex(3)
                    print(data)
                    client_socket.sendall(bytes(data, encoding='utf-8'))
                    time.sleep(1)
            except Exception as e:
                print(e)
                break
        else:
            for instrument in instrument_list:
                try:
                    conn = instrument['conn']
                    address = instrument['address']
                    print(address)
                    print(conn.read_register(int(address, 16), 0, functioncode=int('0x04', 16)))
                    time.sleep(1)
                except IOError:
                    print("Failed to read from instrument")