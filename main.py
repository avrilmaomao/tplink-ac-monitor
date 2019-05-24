#!/usr/bin/env python
import os
from ap import APApi
import notification
import logging
import schedule
import time

def main(arguments):
    print("os name: %s" % os.uname()[0])


def monitor_ap_status():
    expected_ap_list = ['TL-AP1750C-PoE-0000', 'TL-AP1750C-PoE-0001', 'TL-AP1750C-PoE-0002', 'TL-AP1750C-PoE-0004', 'TL-AP1750C-PoE-0005', 'TL-AP1750C-PoE-0006']
    ap_api = APApi()
    login_succ = ap_api.login()
    if not login_succ:
        notification.show('AC登录失败', "请检查网络")
        return False
    ap_list = ap_api.get_ap_list()
    if not ap_list:
        notification.show('获取AP列表失败','请登录页面查看')
        return False
    ap_name_list = []
    for item in ap_list:
        ap_name_list.append(item['ap_name'])
    missing_ap_names = []
    for item in expected_ap_list:
        if not item in ap_name_list:
            missing_ap_names.append(item)
            logging.warning("%s不在线" % item)
    if len(missing_ap_names) > 0:
        notification.show('有AP离线，请检查', ','.join(missing_ap_names))
    else:
        logging.info('AP状态正常')


def monitor_client_status():
    """
    1. 总终端数量监控
    2. office弱信号 监控 不超过5个
    3. office 单个ap、ssid不超过20个设备
    4。 单个ap不超过50个设备
    """
    weak_signal_threshold = -65
    weak_signal_device_number_threshold = 5
    max_client_number_per_ap_ssid = 20
    max_client_number_per_ap = 40
    max_clients = 150
    office_ssid_keyword = 'OFFICE'
    guest_ssid_keyword = 'GUEST'

    ap_api = APApi()
    login_succ = ap_api.login()
    if not login_succ:
        notification.show('AC登录失败', "请检查网络")
        return False

    client_list = ap_api.get_client_list()
    if len(client_list) > max_clients:
        logging.warning('too many clients:%d' % len(client_list))
        notification.show("客户端过多", '终端数量:%d' % len(client_list))
        return False
    weak_signal_list = []
    ap_ssid_data = {}
    ap_clients_number = {}
    for item in client_list:

        if item['ssid'] not in ap_ssid_data:
            ap_ssid_data[item['ssid']] = {}
        if item['ap_name'] not in ap_ssid_data[item['ssid']]:
            ap_ssid_data[item['ssid']][item['ap_name']] = 0
        ap_ssid_data[item['ssid']][item['ap_name']] += 1

        if item['ap_name'] not in ap_clients_number:
            ap_clients_number[item['ap_name']] = 0
        ap_clients_number[item['ap_name']] += 1

        if office_ssid_keyword in item['ssid'] and int(item['rssi']) < weak_signal_threshold:
            weak_signal_list.append("%s,%s,%s,%s" % (item['ssid'], item['ap_name'], item['mac'], item['rssi']))
            logging.warning('发现弱信号设备:%s,%s' % (item['mac'], item['rssi']))

    # 弱信号
    if len(weak_signal_list) > weak_signal_device_number_threshold:
        logging.warning("弱信号设备过多:%d" % len(weak_signal_list))
        notification.show("弱信号设备过多:%d" % len(weak_signal_list), "\r\n".join(weak_signal_list))

    # 单ap、ssid设备过多
    too_many_clients_ap_ssid_list = []
    for k_ssid, v_ssid_data in ap_ssid_data.items():
        for k_ap_name, v_client_number in v_ssid_data.items():
            if v_client_number > max_client_number_per_ap_ssid:
                logging.warning("单个ap下SSID设备过多:%s,%s,%d" % (k_ap_name, k_ssid,v_client_number) )
                too_many_clients_ap_ssid_list.append("单个ap下SSID设备过多:%s,%s,%d" % (k_ap_name, k_ssid,v_client_number))
    if len(too_many_clients_ap_ssid_list) > 0:
        notification.show("单个ap下SSID设备过多", "\r\n".join(too_many_clients_ap_ssid_list))

    # 单ap设备过多
    for k_ap_name, v_client_number in ap_clients_number.items():
        if v_client_number > max_client_number_per_ap:
            logging.warning('单个ap设备过多:%s,%d' % (k_ap_name, v_client_number))
            notification.show('单个ap设备过多', '%s:%d' % (k_ap_name, v_client_number))


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    schedule.every().hours.do(monitor_client_status)
    schedule.every(3).hours.do(monitor_ap_status)
    while True:
        schedule.run_pending()
        time.sleep(300)



