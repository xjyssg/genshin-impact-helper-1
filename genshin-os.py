import hashlib
import json
import time
import os

from settings import log, CONFIG, req
from notify import Notify


def hexdigest(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()


class Base(object):
    def __init__(self, cookies: str = None):
        if not isinstance(cookies, str):
            raise TypeError('%s want a %s but got %s' %
                            (self.__class__, type(__name__), type(cookies)))
        self._cookie = cookies

    def get_header(self):
        # header = {
        #     'User-Agent': CONFIG.WB_USER_AGENT,
        #     'Referer': CONFIG.OS_REFERER_URL,
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Cookie': self._cookie
        # }
        header = {'Content-Type': 'application/json;charset=UTF-8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
           'authority':'sg-hk4e-api.hoyolab.com',
           'Accept-Encoding':'gzip, deflate, br',
           'Accept-Language':'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
           'Origin':'https://act.hoyolab.com',
           'Referer':'https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&lang=zh-cn&bbs_theme=light&bbs_theme_device=1',
           'Accept':'application/json, text/plain, */*',
           'X-Rpc-Device_id':'68f9d4a0-93b4-4b1b-88dd-ee68483dcfd2',
           'Sec-Ch-Ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"'
           }
        return header


class Roles(Base):
    def get_awards(self):
        response = {}
        payload = {
            "act_id": "e202102251931481"
        }
        api_url = 'https://sg-hk4e-api.hoyolab.com/event/sol/sign?lang=zh-cn'
        cookies = {'cookie_name': self._cookie}
        header = {'Content-Type': 'application/json;charset=UTF-8',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
           'authority':'sg-hk4e-api.hoyolab.com',
           'Accept-Encoding':'gzip, deflate, br',
           'Accept-Language':'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
           'Origin':'https://act.hoyolab.com',
           'Referer':'https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&lang=zh-cn&bbs_theme=light&bbs_theme_device=1',
           'Accept':'application/json, text/plain, */*',
           'X-Rpc-Device_id':'68f9d4a0-93b4-4b1b-88dd-ee68483dcfd2',
           'Sec-Ch-Ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"'
           }
        try:
            response = req.to_python(req.request(
                'post', api_url, cookies=cookies,headers=header, json=payload).text)
            log.info(self._cookie)
        except json.JSONDecodeError as e:
            raise Exception(e)

        return response


class Sign(Base):
    def __init__(self, cookies: str = None):
        super(Sign, self).__init__(cookies)
        try:
            self.uid = cookies.split('account_id_v2=')[1].split(';')[0]
        except (IndexError, AttributeError):
            self.uid = 'unknown'

    def get_header(self):
        header = super(Sign, self).get_header()
        return header

    def get_info(self):
        log.info('准备获取签到信息...')
        info_url = CONFIG.OS_INFO_URL
        cookies = {'cookie_name': self._cookie}

        try:
            response = req.request(
                'get', info_url, headers=self.get_header(),cookies=cookies).text
        except Exception as e:
            raise Exception(e)

        log.info('签到信息获取完毕')
        return req.to_python(response)

    def run(self):
        info_list = self.get_info()
        log.info(f'info_list: {info_list}')
        message_list = []
        if not info_list or info_list.get('data') is None:
            return "登录失败: " + info_list.get('message', '未知错误')
        if info_list:
            # today = info_list.get('data',{}).get('today')
            today = 'today'
            total_sign_day = info_list.get('data',{}).get('total_sign_day')
            # awards = Roles(self._cookie).get_awards().get('data',{}).get('awards')
            awards = Roles(self._cookie).get_awards()
            uid = str(self.uid).replace(
                str(self.uid)[1:7], '******', 1)

            log.info(f'准备为旅行者 {uid} 签到...')
            time.sleep(1)
            message = {
                'today': today,
                'region_name': '',
                'uid': uid,
                'total_sign_day': total_sign_day,
                'end': '',
            }
            if info_list.get('data',{}).get('is_sign') is True:
                # message['award_name'] = awards[total_sign_day - 1]['name']
                # message['award_cnt'] = awards[total_sign_day - 1]['cnt']
                message['award_name'] = 'xx'
                message['award_cnt'] = 0
                message['status'] = f"👀 Traveler, you've already checked in today"
                message_list.append(self.message.format(**message))
                return ''.join(message_list)
            else:
                # message['award_name'] = awards[total_sign_day]['name']
                # message['award_cnt'] = awards[total_sign_day]['cnt']
                message['award_name'] = 'xx'
                message['award_cnt'] = 0
                log.info('skip')
            if info_list.get('data',{}).get('first_bind') is True:
                message['status'] = f'💪 Please check in manually once'
                message_list.append(self.message.format(**message))
                return ''.join(message_list)

            data = {
                'act_id': CONFIG.OS_ACT_ID
            }

            try:
                api_url = 'https://sg-hk4e-api.hoyolab.com/event/sol/sign?lang=zh-cn'
                cookies = {'cookie_name': self._cookie}
                header = {'Content-Type': 'application/json;charset=UTF-8',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                   'authority':'sg-hk4e-api.hoyolab.com',
                   'Accept-Encoding':'gzip, deflate, br',
                   'Accept-Language':'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                   'Origin':'https://act.hoyolab.com',
                   'Referer':'https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_source=hoyolab&utm_medium=tools&lang=zh-cn&bbs_theme=light&bbs_theme_device=1',
                   'Accept':'application/json, text/plain, */*',
                   'X-Rpc-Device_id':'68f9d4a0-93b4-4b1b-88dd-ee68483dcfd2',
                   'Sec-Ch-Ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"'
                   }
                response = req.to_python(req.request(
                'post', api_url, cookies=cookies,headers=header, json=payload).text)
            except Exception as e:
                raise Exception(e)
            log.info(f'response {response}')
            code = response.get('retcode', 99999)
            log.info(f'response code {code}')
            # 0:      success
            # -5003:  already checked in
            if code != 0:
                message_list.append(response)
                return ''.join(message_list)
            message['total_sign_day'] = total_sign_day + 1
            message['status'] = response['message']
            message_list.append(self.message.format(**message))
        log.info('签到完毕')

        return ''.join(message_list)

    @property
    def message(self):
        return CONFIG.MESSAGE_TEMPLATE


if __name__ == '__main__':
    log.info(f'🌀Genshin Impact Helper v{CONFIG.GIH_VERSION}')
    log.info('If you fail to check in, please try to update!')
    log.info('任务开始')
    notify = Notify()
    msg_list = []
    ret = success_num = fail_num = 0
    """HoYoLAB Community's COOKIE
    :param OS_COOKIE: 米游社国际版的COOKIE.多个账号的COOKIE值之间用 # 号隔开,例如: 1#2#3#4
    """
    # Github Actions用户请到Repo的Settings->Secrets里设置变量,变量名字必须与上述参数变量名字完全一致,否则无效!!!
    # Name=<变量名字>,Value=<获取的值>
    # 从环境变量获取COOKIE
    OS_COOKIE = os.environ.get('OS_COOKIE', '')
    if not OS_COOKIE.strip():
        log.error('未配置有效的COOKIE环境变量(OS_COOKIE)')
        exit(1)

    cookie_list = [c for c in OS_COOKIE.split('#') if c.strip()]
    if not cookie_list:
        log.error('未配置有效的COOKIE，请检查OS_COOKIE设置')
        exit(1)
        
    log.info(f'检测到共配置了 {len(cookie_list)} 个帐号')
    for i in range(len(cookie_list)):
        log.info(f'准备为 NO.{i + 1} 账号签到...')
        try:
            cookie = cookie_list[i]
            log.debug(f'原始COOKIE: {cookie}')
            
            # 提取uid
            try:
                uid = cookie.split('account_id_v2=')[1].split(';')[0]
            except IndexError:
                log.error(f'COOKIE格式错误，缺少account_id_v2: {cookie}')
                uid = 'unknown'
                
            msg = f'	NO.{i + 1} 账号:{Sign(cookie).run()}'
            msg_list.append(msg)
            success_num = success_num + 1
        except Exception as e:
            log.error(f'处理NO.{i + 1}账号时出错:', exc_info=True)
            msg = f'	NO.{i + 1} 账号:\n    错误类型: {type(e).__name__}\n    错误详情: {str(e)}'
            msg_list.append(msg)
            fail_num = fail_num + 1
            log.error(msg)
            ret = -1
        continue
    notify.send(status=f'成功: {success_num} | 失败: {fail_num}', msg=msg_list)
    if ret != 0:
        log.error('异常退出')
        exit(ret)
    log.info('任务结束')
