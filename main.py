#!/usr/bin/env python
import os
from ap import APApi
import notification
import logging
import schedule
import time
from datetime import  datetime
import network


def main(arguments):
    print("os name: %s" % os.uname()[0])


def monitor_ap_status():
    expected_ap_list = ['TL-AP1750C-PoE-INSIDE', 'TL-AP1750C-PoE-OUTSIDE','TL-AP1750C-PoE-MIDDLE']
    ap_api = APApi()
    login_succ = ap_api.login()
    if not login_succ:
        notification.show('AC登录失败', "请检查网络")
        return False
    ap_list = ap_api.get_ap_list()
    if not ap_list:
        notification.show('获取AP列表失败', '请登录页面查看')
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
    weak_signal_device_number_threshold = 3
    max_client_number_per_ap_ssid = 35
    max_client_number_per_ap = 50
    max_clients = 100
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


def monitor_sys_time():
    ap_api = APApi()
    login_succ = ap_api.login()
    if not login_succ:
        notification.show('AC登录失败', "请检查网络")
        return False
    sys_time_info = ap_api.get_sys_time()
    ap_sys_time = datetime.strptime(sys_time_info['date'] + sys_time_info['time'], '%m/%d/%Y%H:%M:%S')
    local_time = datetime.now()
    diff_seconds = (local_time - ap_sys_time).total_seconds()
    if abs(diff_seconds) > 3600:
        logging.warning("ap时间差别太大:%s %s" % (ap_sys_time, local_time))
        notification.show("ap时差过大", ap_sys_time.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        logging.info("ap时差正常")


def monitor_gateway_ping():
    gateway_ip = network.get_local_gateway()
    if gateway_ip is None:
        logging.warning("获取网关ip失败")
        return None
    logging.info("gateway ip :%s" % gateway_ip)
    ping_info = network.get_ping_info(gateway_ip)
    if ping_info is None:
        logging.warning("获取ping延迟异常")
        return None
    if ping_info > 100:
        logging.warning("ping延迟过高: %s" % ping_info)
        notification.show("网关ping值延迟过高:%s" % ping_info, gateway_ip)
    else:
        logging.info("ping延迟正常: %s" % ping_info)


if __name__ == '__main__':
    logging.basicConfig(level='INFO', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    schedule.every().hours.do(monitor_client_status)
    schedule.every(30).minutes.do(monitor_ap_status)
    schedule.every(120).minutes.do(monitor_sys_time)
    schedule.every(15).minutes.do(monitor_gateway_ping)
    schedule.run_all()
    while True:
        schedule.run_pending()
        time.sleep(300)



