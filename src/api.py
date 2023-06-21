import re

from config import ROOT_ID,SELF_ID
from native_api import send_msg,RECALL_FLAG,get_msg
from utils import openai_chat, weather, rand_pic,timing,real_dora,logger

BASE_URL = 'http://127.0.0.1:5700/'

INSTR_LIST  = [
    '~help        - 显示指令集',
    '~wea         - 天气预报',
    '~setu        - 随机图片',
    '~chat        - 聊天'
]

ROOT_ID = ROOT_ID
SELF_ID = SELF_ID

# bot指令集
# def msg_handlers(message,uid,gid=None,role=None,message_id=None):
def msg_handlers(data_dict):

    message_id = data_dict.get('message_id')
    message = data_dict.get('raw_message')
    uid = data_dict.get('user_id')
    gid = data_dict.get('group_id',None)
    sender = data_dict.get('sender')
    role = sender.get('role','member')

    repeat_msg_dict = {}  # 复读辅助集合

    try:
        # 处理普通消息
        if message[0] != '~' and message[0] != '～':
            return handle_common_msg(message,uid,gid,role,repeat_msg_dict)
        
        errMsg = "抱歉,不存在 " + message + " 指令哦!"
        # 返回所有指令
        if message[1:5]=='help':
            tmpMes = '\n'.join(INSTR_LIST )
            # print(message)
            send_msg(tmpMes,uid,gid)
        # 返回指定内容
        elif message[1:7]=='return':
            tmpMes = message.replace('~return','').lstrip()
            send_msg(tmpMes,uid,gid)
        # 防撤回开关
        elif message[1:3]=='wd':
            if gid == None:
                return send_msg("抱歉,该指令仅对群聊有效😭",uid,gid)
            if role == 'member':
                return send_msg("Sorry,你没有该指令权限.",uid,gid)
            if message[4:6]=='on':
                send_msg("该群聊已开启防撤回功能",uid,gid)
                RECALL_FLAG[gid] = 1
            elif message[4:7]=='off':
                if RECALL_FLAG.__contains__(gid):
                    del RECALL_FLAG[gid]
                send_msg("防撤回功能已关闭",uid,gid)
            else:
                send_msg(errMsg,uid,gid)
        # ai对话相关
        elif message[1:5]=='chat':
            tmpMes = message[5:].lstrip();
            if message_id == None:
                chatReply = openai_chat.chat(tmpMes,uid,gid)
            else:
                chatReply = '[CQ:reply,id={0}][CQ:at,qq={1}] '.format(message_id,uid) +openai_chat.chat(tmpMes,uid,gid)
            send_msg(chatReply,uid,gid)
        elif message[1:6]=='clear':
            openai_chat.clear(uid,gid)
            send_msg('已重置对话🥰',uid,gid)
        elif message[1:4]=='get':
            tmpMes = openai_chat.get(uid,gid)
            send_msg(repr(tmpMes),uid,gid)
        elif message[1:7]=='preset':
            tmpMes = message[7:].lstrip()
            openai_chat.preset(tmpMes,uid,gid)
            send_msg('预设成功🏃',uid,gid)
        # 随机图片相关 api接口挂了,暂时关闭
        # elif message[1:4]=='pic':
        #     tmpMes = randPic.normal()
        #     send_msg(tmpMes,uid,gid) 
        elif message[1:5]=='setu':
            tmpMes = '[CQ:reply,id={0}][CQ:at,qq={1}] '.format(message_id,uid) + rand_pic.setu(message)
            send_msg(tmpMes,uid,gid)
        # 功能信息
        elif message[1:7]=='status':
            all_sta(uid,gid,repeat_msg_dict)
        # 天气相关
        elif message =='~briefForecast':
            tmpMes = weather.briefForecast()
            warning = weather.warning()
            send_msg(tmpMes,uid,gid)
            if warning!='No Warning':
                send_msg(warning,uid,gid)
        elif message[1:4]=='wea':
            pos = message[4:].lstrip();
            tmpMes = weather.detailForecast(pos)
            send_msg(tmpMes,uid,gid)
        elif message[1:6]=='clock':
            tmpMes = set_clock(message,"weather")
            send_msg(tmpMes,uid,gid)
        elif message[1:5]=='warn':
            tmpMes = weather.warning()
            send_msg(tmpMes,uid,gid)
        # 约球
        elif message[1:7]=="soccer":
            if uid == ROOT_ID:
                tmpMes = set_clock(message,"soccer",15)
                send_msg(tmpMes,uid,gid)
            else:
                send_msg("Sorry~没有权限哦",uid,gid)
        elif message[1:5]=="moyu":
            tmpMes = rand_pic.moyuPic()
            send_msg(tmpMes,uid,gid)
        else:
            return send_msg(errMsg,uid,gid)
    except Exception as err:
        send_msg(str(err),uid,gid)

def handle_common_msg(message,uid,gid,role,repeat_msg_dict={},):
    """
    处理非指令形式的普通信息: 1.复读 2.违禁词处理 3.随机发言

    Args:
        message (str): 消息内容。
        uid (str): 用户ID。
        gid (str, optional): 群组ID，默认为None。若为None，则不处理消息。
        role (str): 用户在群聊中的身份,默认为成员
        repeat_msg_dict (dict, optional): 重复消息字典，默认为空字典。该字典用于存储每个群组的重复消息信息。
    """

    # 私聊消息 或 消息为空 或 复读成功
    if gid is None or message == "" or handle_repeat(message,uid,gid,repeat_msg_dict):
        return
    
    # 违禁词设置
    regex = r"\[CQ:reply,id=([\-0-9]*)\]\[CQ:at,qq={}\] \[CQ:at,qq={}\] 不可以".format(SELF_ID, SELF_ID)
    res = re.match(regex,message)
    if res:
        # 用户没有执行权限
        if role == 'member' and uid!=ROOT_ID:
            return send_msg("Sorry,你没有该指令权限.",uid,gid)
        
        msg_id = res.group(1)
        rawmsg = get_msg(msg_id).get("data").get("message")
        if rawmsg:
            real_dora.shutUp(rawmsg)
            send_msg(f"[CQ:reply,id={msg_id}] banned",uid,gid)
        return

    # 随机发言
    tmpMes = real_dora.Mewo(message,uid,gid)
    if tmpMes != "SILENT":
        send_msg(tmpMes,uid,gid)
    return

def handle_repeat(message, uid, gid=None,repeat_msg_dict={}):
    """
    处理重复的群组消息，当同一群组中的三个用户发送相同的消息时，自动发送该消息一次。

    Args:
        message (str): 消息内容。
        uid (str): 用户ID。
        gid (str, optional): 群组ID，默认为None。若为None，则不处理消息。
        repeat_msg_dict (dict, optional): 重复消息字典，默认为空字典。该字典用于存储每个群组的重复消息信息。

    Returns:
        bool: 是否进行复读。
    """
    if gid is None:
        return False

    if gid in repeat_msg_dict:
        repeat_info = repeat_msg_dict[gid]
        if message == repeat_info['message'] and uid not in repeat_info['users']:
            repeat_info['users'].add(uid)
            if len(repeat_info['users']) == 3 and not repeat_info['repeated']:
                send_msg(repeat_info['message'], uid, gid)
                repeat_info['repeated'] = True
                return True
        else:
            repeat_msg_dict[gid] = {'message': message, 'users': {uid}, 'repeated': False}
    else:
        repeat_msg_dict[gid] = {'message': message, 'users': {uid}, 'repeated': False}
    return False

def all_sta(uid,gid=None,repeat_msg_dict={}):
    """
    获取群组状态信息

    Args:
        uid: int, 指定用户的id
        gid: int, 群组id，默认为None
        repeat_msg_dict: dict, 群组复读信息字典，默认为None
    """
    if gid is not None:
        withdraw_status = 'On' if gid in RECALL_FLAG else 'off'
        repeat_status = repeat_msg_dict.get(gid, 'None') if repeat_msg_dict else 'None'
        weaTime = '{:0>2}:{:0>2}'.format(timing.weaCof["hour"],timing.weaCof["minus"])
        
        tmpMes = f"防撤回状态: {withdraw_status}\n复读信息: {repeat_status}\n预报时间: {weaTime}"
        send_msg(tmpMes,uid,gid)

def set_clock(message,type,offset=0):
    """
    设置定时播报的时间

    Args:
        message: str, 指令原始内容
        type: str, 播报消息的类别
        offset: int, 时间偏移量
    Returns:
        str,回显信息
    """
    try:
        pos = message.find(' ')
        arr = message[pos+1:].split(' ')
        a = int(arr[0])
        b = int(arr[1])
        if b-offset<0:
            a = (a-1)%24
            b = (b-offset)%60
        else:
            b = b-offset
        if (a < 0 or a >= 24 or b < 0 or b >= 60 or offset>=60):
            return '格式错误！'

        tmpa = f"0{a}" if a < 10 else str(a)
        tmpb = f"0{b}" if b < 10 else str(b)

        if type in timing.TIMING_COF:
            timing.TIMING_COF[type].update({
                "enable":True,
                "hour":a,
                "minus":b
            })
            return f"{type} updated: {tmpa}:{tmpb}"
        else:
            return "type not exist"
    except Exception as exc:
        logger.error(f"定时未知错误:{str(exc)}")
        return '未知错误:' + str(exc)
    