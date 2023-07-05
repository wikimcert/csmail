import time

from support import SupportSubprocess, SupportFile
from .setup import *
from .utils import *
from .models import *

name = 'training'
modal = 'command_modal_add_text'

class ModuleTraining(PluginModuleBase):

    def __init__(self, P):
        super(ModuleTraining, self).__init__(P, name='training', first_menu='list')
        self.web_list_model = ModelTrainingItem

    def process_menu(self, page, req):
        arg = P.ModelSetting.to_dict()
        rcptlist = ModelRcptListItem.get_all_rcptlist()
        maillist = ModelMailItem.get_all_items()
        logger.info(f'[{self.name}] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.name}_{page}.html', arg=arg, rcptlist=rcptlist, maillist=maillist)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {}
        data = None
        logger.info(f'[{self.name}] process_command: {command}, {arg1}, {req}')
        if command == 'register_training':
            _ = P.logic.arg_to_dict(arg1)
            rcptlist = ModelRcptListItem.get_by_id(int(_['rcptlist_id']))
            tritem = ModelTrainingItem(_['name'], _['sender_name'], _['sender_email'], int(_['rcptlist_id']), int(_['mail_id']), rcptlist.total_count)
            tritem.save()
            ret = {'ret':'success', 'data':f'훈련({tritem.name}) 등록 완료'}
        elif command == 'modify_training':
            _ = P.logic.arg_to_dict(arg1)
            tritem = ModelTrainingItem.get_by_id(int(_['training_id']))
            tritem.name = _['m_name']
            tritem.sender_name = _['m_sender_name']
            tritem.sender_email = _['m_sender_email']
            tritem.rcptlist_id = _['m_rcptlist_id']
            tritem.mail_id = _['m_mail_id']
            tritem.status = 'init'
            rcptlist = ModelRcptListItem.get_by_id(tritem.rcptlist_id)
            tritem.total = rcptlist.target_count
            tritem.curr = 0
            tritem.save()
            ret = {'ret':'success', 'data':f'훈련정보({tritem.name}) 수정 완료'}
        elif command == 'test_training':
            req = {'req_type':'test', 'training_id':int(arg1)}
            thread = threading.Thread(target=self.sendmail_thread_function, args=(req,))
            thread.daemon = True
            thread.start()
            ret = {'ret':'success', 'data':'훈련메일 테스트 발송 요청 완료'}
        elif command == 'execute_training':
            req = {'req_type':'training', 'training_id':int(arg1)}
            thread = threading.Thread(target=self.sendmail_thread_function, args=(req,))
            thread.daemon = True
            thread.start()
            ret = {'ret':'success', 'data':'훈련메일 발송 요청 완료'}
        elif command == 'remove_rcpt':
            try:
                rcpt = ModelRcptItem.get_by_id(arg1)
                rcptlist = ModelRcptListItem.get_by_id(rcpt.list_id)
                rcptlist.total_count -= 1
                if rcpt.excluded: rcptlist.except_count -= 1
                else: rcptlist.target_count -= 1
                ModelRcptItem.delete_by_id(arg1)
                ret = {'ret':'success', 'data':f'삭제 완료(ID:{arg1})'}
            except Exception as e:
                ret = {'ret':'error', 'data':f'삭제 실패(ID:{arg1})'}
        return jsonify(ret)

    def sendmail_thread_function(self, req):
        logger.debug(f'[sendmail] 메일전송 요청 수신: {req}')
        req_type = req['req_type']
        training_id = req['training_id']

        tritem = ModelTrainingItem.get_by_id(training_id)
        mitem = ModelMailItem.get_by_id(tritem.mail_id)
        mail_data = SupportFile.read_file(mitem.mail_path)

        # 수신자가1명인 경우: 테스트 발송 혹은 재발송의 경우 처리
        if req_type == 'test' or 'rcpt_id' in req:
            socketio.emit(modal, '0.훈련메일 테스트(재발송) 발송을 시작합니다.\n\n', namespace='/framework', broadcast=True)
            msg = '1. 발송대상 메일: 테스트 발송\n\
              메일이름: {}\n\
              메일제목: {}\n\
              메일경로: {}\n\n'.format(mitem.name, mitem.title, mitem.mail_path)
            socketio.emit(modal, msg, namespace='/framework', broadcase=True)

            if req_type == 'test':
                name = ModelSetting.get('test_default_name')
                dept = ModelSetting.get('test_default_dept')
                email = ModelSetting.get('test_default_mail')
                emp_code = ModelSetting.get('test_default_emp_code')
                rcpt = None
                rcpt = ModelRcptItem.get_by_email_and_list_id(email, -1)
                if not rcpt: rcpt = ModelRcptItem(-1, name, dept, email, emp_code)
            else: # 재발송
                rcpt = ModelRcptItem.get_by_id(req['rcpt_id'])

            rcpt.save()
            msg = '2. 수신자 정보: {},{},{},{}\n\n'.format(rcpt.name, rcpt.dept, rcpt.email, rcpt.emp_code)
            socketio.emit(modal, msg, namespace='/framework', broadcase=True)

            is_test = True if req_type == 'test' else False
            ritem = None
            ritem = ModelResultItem.get_by_rcpt_id_and_training_id(rcpt.id, tritem.id)
            if not ritem:
                ritem = ModelResultItem(rcpt.emp_code, rcpt.id, tritem.id, is_test=is_test)
            else: # 최초가 아닌 경우 값 초기화
                ritem.status = 'init'
                ritem.sent_time = None
                ritem.read_time = None
                ritem.click_time = None
                ritem.report_time = None
                ritem.read_ip = None
                ritem.click_ip = None
                ritem.report_ip = None
                ritem.is_test = is_test
            ritem.save()
            mime = self.get_module('mail').set_mime(mail_data, tritem, mitem, rcpt)
            ret = self.get_module('mail').send_mail(tritem, rcpt, mime)
            return ret
        # 훈련 실행 처리
        elif req_type == 'training':
            sleep_time = ModelSetting.get_int('smtp_send_sleep_time')/1000
            socketio.emit(modal, '0.훈련메일 발송을 시작합니다.\n\n', namespace='/framework', broadcast=True)
            msg = '1. 발송대상 메일: 훈련 발송\n\
              메일이름: {}\n\
              메일제목: {}\n\
              메일경로: {}\n\n'.format(mitem.name, mitem.title, mitem.mail_path)
            socketio.emit(modal, msg, namespace='/framework', broadcase=True)

            rcptlist = ModelRcptItem.get_all_target_entities_by_list_id(tritem.rcptlist_id)
            total = len(rcptlist)

            tritem.status = 'running'
            tritem.total = total
            tritem.started_time = datetime.now()
            tritem.save()

            i = 1
            msg = '2. 훈련대상자 정보 로드: {}명'.format(total)
            socketio.emit(modal, msg, namespace='/framework', broadcase=True)
            for rcpt in rcptlist:
                # TODO: 중단/실패된 경우 중간부서 전송할 수 있도록 체크 로직 추가
                msg = '- {}/{}: {},{},{},{}\n\n'.format(i,total,rcpt.name, rcpt.dept, rcpt.email, rcpt.emp_code)
                socketio.emit(modal, msg, namespace='/framework', broadcase=True)

                tritem.curr = i

                ritem = None
                ritem = ModelResultItem.get_by_rcpt_id_and_training_id(rcpt.emp_code, tritem.id)
                if not ritem:
                    ritem = ModelResultItem(rcpt.emp_code, rcpt.id, tritem.id, is_test=False)
                else: # 최초가 아닌 경우 값 초기화
                    ritem.status = 'init'
                    ritem.sent_time = None
                    ritem.read_time = None
                    ritem.click_time = None
                    ritem.report_time = None
                    ritem.read_ip = None
                    ritem.click_ip = None
                    ritem.report_ip = None
                    ritem.is_test = False
                ritem.save()
                msg = '- 메일데이터 구성 완료\n\n'
                socketio.emit(modal, msg, namespace='/framework', broadcase=True)
                mime = self.get_module('mail').set_mime(mail_data, tritem, mitem, rcpt)
                ret = self.get_module('mail').send_mail(tritem, rcpt, mime)

                if ret['ret'] != 'success':
                    logger.error(f'훈련메일 발송 실패: {ret["data"]}')
                else:
                    ritem.sent_time = datetime.now()
                    ritem.status = 'sent'
                    ritem.save()

                i += 1
                tritem.save()
                time.sleep(sleep_time)
                # TODO: break 처리
                # TODO: 상태 업데이트 처리

            if ret['ret'] == 'success':
                tritem.status = 'finished'
                tritem.finished_time = datetime.now()
                tritem.save()
            return ret

        return {'ret':'success'}
