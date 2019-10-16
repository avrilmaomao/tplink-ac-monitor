#!/usr/bin/env python
import netifaces
import subprocess
import logging
def get_ping_info(target_host):
    ping_cmd = 'ping -c 100 %s' % target_host
    try:
        output = subprocess.check_output(ping_cmd, shell=True)
    except subprocess.CalledProcessError as error:
        logging.warning("执行ping命令异常 %s" % error)
        output = error.output
    # 获取最后一行
    lines = output.decode("utf-8").strip().split('\n')
    if len(lines) == 0:
        logging.warning("ping命令执行返回为空: %s " % ping_cmd)
        return None
    last_line = lines[len(lines) - 1]
    if '=' not in last_line:
        logging.warning("返回的最后一行不包含= %s" % last_line)
        return None
    last_line_kvs = last_line.split('=')
    last_line_value = last_line_kvs[1].strip()
    last_line_values = last_line_value.split('/')
    if len(last_line_values) < 4:
        logging.warning("最后一行数值缺少:%s" % last_line)
        return None
    return float(last_line_values[1])


def get_local_gateway():
    gateways = netifaces.gateways()
    if 'default' not in gateways:
        logging.warning("未获取到默认网关信息 %s" % gateways)
        return None
    try:
        return gateways['default'][netifaces.AF_INET][0]
    except Exception:
        return None


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    gateway_ip = get_local_gateway()
    logging.info("gateway ip : %s" % gateway_ip)
    avg_ping = get_ping_info(gateway_ip)
    logging.info("平均延迟: %s" % avg_ping)
