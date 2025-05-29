from datetime import datetime
import pytz
from flask import Flask, render_template, request, jsonify
from model.models import FailureTicket, User, UserNotifyFrequency
from model.session import SessionLocal
from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE
from utils.logger import setup_logger

logger = setup_logger()
# from celery.utils.log import get_task_logger

# logger = get_task_logger(__name__)
# logger = logging.getLogger(__name__)
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')


@app.route('/device_failure', methods=['GET'])
def get_device_failure():
    """用户故障通知视图"""
    sql_session = SessionLocal()
    user_id = request.args.get('user_id')
    recipient_name = ""
    recipient_gender = "先生/女士"
    if user_id:
        user_obj = sql_session.query(User).filter(User.id == user_id).first()
        recipient_name = user_obj.name
        recipient_gender = "先生" if user_obj.gender == "male" else "女士"
    failure_ticket_id = request.args.get('ticket_id')
    if failure_ticket_id:
        failure_ticket = sql_session.query(FailureTicket).filter(FailureTicket.id == failure_ticket_id).first()
        if not failure_ticket:
            # FIXME:为什么会出现failure_ticket 不存在的情况
            return {"code": 1, "msg": "failure_ticket_id不存在"}
        # 查询是否有将对应的UserNotifyFrequency如果没有则创建,并将message_is_read字段置为True,表示已读
        # 如果有则将message_is_read字段置为True,表示已读
        user_notify_frequency_obj = sql_session.query(UserNotifyFrequency).filter(
            (UserNotifyFrequency.user_id == user_id) & (
                    UserNotifyFrequency.failure_ticket_id == failure_ticket_id)).first()
        if user_notify_frequency_obj:
            user_notify_frequency_obj.message_is_read = True
        else:
            user_notify_frequency_obj = UserNotifyFrequency(user_id=int(user_id), failure_ticket_id=int(failure_ticket_id),
                                                            message_is_read=True)
            sql_session.add(user_notify_frequency_obj)
        sql_session.commit()
        data = {
            "device_name": failure_ticket.device.name,
            "location": failure_ticket.device.location,
            "ip": failure_ticket.device.address,
            "port": failure_ticket.device.port,
            "fault_time": failure_ticket.fault_time,
            # "is_accepted": failure_ticket.is_accepted,
            "processors": failure_ticket.handler.name if failure_ticket.handler else "",
            # TODO: 测试一下,正式环境记得修改
            "remark": DEVICE_FAULT_MESSAGE_TEMPLATE.format(
                recipient_name=recipient_name,
                recipient_gender=recipient_gender,
                location=failure_ticket.device.location,
                name=failure_ticket.device.name,
                device_type=failure_ticket.device.device_type
            )
            # "remark": failure_ticket.description
        }
        sql_session.close()
        return render_template('fault.html', device_name=data['device_name'], location=data['location'],
                               ip=data['ip'], port=data['port'], fault_time=data['fault_time']
                               , processors=data['processors'], remark=data['remark'])


@app.route('/device_failure', methods=['POST'])
def post_device_failure():
    """
    将故设备故障单的is_accepted字段置为True,并将处理人设置为当前用户
    :return:
    """
    data = request.json
    user_id = data.get('user_id')
    failure_ticket_id = data.get('ticket_id')
    sql_session = SessionLocal()
    if user_id and failure_ticket_id:
        failure_ticket = sql_session.query(FailureTicket).filter(FailureTicket.id == failure_ticket_id).first()
        failure_ticket.is_accepted = True
        failure_ticket.handler_id = user_id
        sql_session.commit()
        sql_session.close()
        return {"code": 0, "msg": "success"}
    else:
        sql_session.close()
        return {"code": 1, "msg": "参数错误"}


@app.route('/user_notify_frequency', methods=['POST'])
def user_notify_frequency():
    """
    修改用户通知频率,处理1小时后发送,当日不发送,自定义时间后发送,和不发送
    其他情况设置UserNotifyFrequency的next_notify_time时间,并由UserNotifyFrequencyValidation检测是否符合next_notify_time条件
    :return:
    """
    sql_session = SessionLocal()
    sql_session.expire_all()
    try:
        data = request.json
        # print("recept_data", data)
        user_id = data.get('user_id')
        failure_ticket_id = data.get('ticket_id')
        next_notify_time = data.get('next_notify_time')
        # print(f"next_notify_time:{next_notify_time}")
        # 如果next_notify_time转换成datatime对象,并跟当前日期对比,如果小于now,则返回错误
        if next_notify_time:
            # next_notify_time = datetime.strptime(next_notify_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            next_notify_time = datetime.strptime(next_notify_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            utc_time = next_notify_time.replace(tzinfo=pytz.UTC)
            # next_notify_time = datetime.strptime(next_notify_time, "%Y-%m-%d %H:%M:%S")
            next_notify_time = utc_time.astimezone(pytz.timezone('Asia/Shanghai'))
            current_time = datetime.now().astimezone(pytz.timezone('Asia/Shanghai'))

            # print(f"format_next_notify_time{next_notify_time}")
            # print(f"current_time{current_time}")
            # print(f"next_notify_time < current_time:{next_notify_time < current_time}")
            if next_notify_time < current_time:
                return {"code": 1, "msg": "next_notify_time不能小于当前时间"}

        # 查找是否有对应的user_obj, failure_ticket_obj
        user_obj = sql_session.query(User).filter(User.id == user_id).first()
        failure_ticket_obj = sql_session.query(FailureTicket).filter(FailureTicket.id == failure_ticket_id).first()
        if user_obj and failure_ticket_obj and next_notify_time:
            # 查找是否有对应的UserNotifyFrequency对象
            user_notify_frequency_obj = sql_session.query(UserNotifyFrequency).filter(
                (UserNotifyFrequency.user_id == user_id) & (
                        UserNotifyFrequency.failure_ticket_id == failure_ticket_id)).first()
            if user_notify_frequency_obj:
                user_notify_frequency_obj.next_notify_time = next_notify_time
            else:
                user_notify_frequency_obj = UserNotifyFrequency(user_id=user_id, failure_ticket_id=failure_ticket_id,
                                                                next_notify_time=next_notify_time)
                sql_session.add(user_notify_frequency_obj)
            sql_session.commit()
            # 返回user_notify_frequency_obj的next_notify_time
            return {"code": 0, "msg": "success", "next_notify_time": user_notify_frequency_obj.next_notify_time}
            # return {"code": 0, "msg": "success"}
        else:
            return {"code": 1, "msg": "参数错误"}
    finally:
        sql_session.close()


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        sql_session = SessionLocal()
        sql_session.execute('SELECT 1')
        sql_session.close()

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8090)
