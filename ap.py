#!/usr/bin/env python
import json
import requests
import logging
import notification


class APApi:
    HOST = 'http://192.168.0.253'
    LOGIN_URL = HOST + '/cgi-bin/luci/;stok=/login?form=login'
    LOGIN_USERNAME = 'hr'
    LOGIN_PASSWORD = '9ad1f5fc61a2aed76258004219af3efb6465eed68e9ac3b71fa034bc1e19d3d8a9eebd3ea661ff54d82ed4f13bb0bfa73f51d60262711e0553f5ad8d62779b8b496ff534d7676fd87242d4468d97b6e0fc9401dc3ea663ff95b25068e688dbe5ccb4883c1d81c21fca01a423acddcb01a773b87180ba07fb7dff0dd08ba8a335'

    def __init__(self):
        self.cookies = {}
        self.stok = ""
        self.headers = {'Referer': self.HOST}

    def login(self):
        data_param = {'method': 'login', 'params': {'username': self.LOGIN_USERNAME, 'password': self.LOGIN_PASSWORD}}
        try:
            res = self.send_post_request(self.LOGIN_URL, data_param)
            res_data = res.json()
            if res_data['result']['stok'] is None:
                logging.warning('登录返回错误:', res)
                return False
            self.stok = res_data['result']['stok']
            self.cookies['sysauth'] = res.cookies['sysauth']
            logging.info('登录成功')
            return True
        except Exception:
            logging.warning("登录请求异常:")
            return False

    def get_ap_list(self):
        ap_status_url = '%s/cgi-bin/luci/;stok=%s/admin/ap_status?form=ap_list' % (self.HOST, self.stok)
        res = self.send_post_request(ap_status_url, {"method": "get", "params": {"group_id": 0}})
        if not res:
            return res
        res_data = res.json()
        return res_data['result']

    def get_client_list(self):
        client_status_url = '%s/cgi-bin/luci/;stok=%s/admin/ac_wstation?form=wsta_list' % (self.HOST, self.stok)
        res = self.send_post_request(client_status_url, {"method": "get", "params": {"pageNo": 0, "group_id": "0"}})
        if not res:
            return res
        res_data = res.json()
        return res_data['result']

    def get_sys_time(self):
        sys_time_url = '%s/cgi-bin/luci/;stok=%s/admin/time?form=settings' % (self.HOST, self.stok)
        res = self.send_post_request(sys_time_url, {"method": "get"})
        if not res:
            return res
        res_data = res.json()
        return res_data['result']

    def send_post_request(self, url, data_param):
        post_data = {'data': json.dumps(data_param)}
        try:
            res = requests.post(url, data=post_data, headers=self.headers, cookies=self.cookies, timeout=5)
        except Exception as e:
            logging.warning("请求发送异常:", e)
            notification.show("请求发送异常", url)
            return False
        return res


def main():
    ap_api = APApi()
    ap_api.login()
    print(ap_api.get_client_list())


if __name__ == '__main__':
    main()
