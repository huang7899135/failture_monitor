from flask import Flask, render_template, request
from model.models import Devices, Failure_ticket, User
from model.session import SessionLocal
from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')


@app.route('/device_failure', methods=['GET'])
def index():
    user_id = request.args.get('user_id')

    recipient_name = ""
    recipient_gender = "先生/女士"
    if user_id:
        user_obj = SessionLocal().query(User).filter(User.id == user_id).first()
        recipient_name = user_obj.name
        recipient_gender = "先生" if user_obj.gender == "male" else "女士"
    failure_ticket_id = request.args.get('ticket_id')
    if failure_ticket_id:
        failure_ticket = SessionLocal().query(Failure_ticket).filter(Failure_ticket.id == failure_ticket_id).first()
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
        return render_template('fault.html', device_name=data['device_name'], location=data['location'],
                               ip=data['ip'], port=data['port'], fault_time=data['fault_time']
                               , processors=data['processors'], remark=data['remark'])


@app.route('/device_failure', methods=['POST'])
def index2():
    """
    将故设备故障单的is_accepted字段置为True,并将处理人设置为当前用户
    :return:
    """
    data = request.json
    user_id = data.get('user_id')
    failure_ticket_id = data.get('ticket_id')

    if user_id and failure_ticket_id:
        failure_ticket = SessionLocal().query(Failure_ticket).filter(Failure_ticket.id == failure_ticket_id).first()
        failure_ticket.is_accepted = True
        failure_ticket.handler_id = user_id
        SessionLocal().commit()
        return {"code": 0, "msg": "success"}
    else:
        return {"code": 1, "msg": "参数错误"}


@app.route('/user/<username>')
def show_user_profile(username):
    return 'User %s' % username


@app.route('/search')
def search():
    query = request.args.get('q')
    return 'You searched for: %s' % query


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8090)
