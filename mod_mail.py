from support import SupportSubprocess, SupportFile
from .setup import *
from .utils import *
from .models import *

name = 'mail'

class ModuleMail(PluginModuleBase):

    def __init__(self, P):
        super(ModuleMail, self).__init__(P, name='mail', first_menu='list')
        self.web_list_model = ModelMailItem
        self.ddns = F.SystemModelSetting.get('ddns')
        self.apikey = F.SystemModelSetting.get('apikey')


        self.base_url = f'{self.ddns}'+'/csmail/api/base'
        self.read_url = f'{self.base_url}'+f'/read?apikey={self.apikey}'+'&rcpt_id={b64_rcpt_id}&training_id={b64_training_id}'
        self.infect_url = f'{self.base_url}'+f'/infect?apikey={self.apikey}'+'&rcpt_id={b64_rcpt_id}&training_id={b64_training_id}'
        self.report_url = f'{self.base_url}'+f'/report?apikey={self.apikey}'+'&rcpt_id={b64_rcpt_id}&training_id={b64_training_id}'

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        data = None
        logger.info(f'[{self.name}] process_command: {command}, {arg1}, {req}')

        if command == 'register_mail':
            ret = self.register_mail(P.logic.arg_to_dict(arg1))
        elif command == 'modify_mail':
            ret = self.modify_mail(P.logic.arg_to_dict(arg1))
        elif command == 'preview_mail':
            ret = self.preview_mail(arg1)
        elif command == 'remove_mail':
            if ModelMailItem.delete_by_id(int(arg1)):
                ret = {'ret':'success', 'data':f'삭제 완료(ID:{arg1})'}
            else:
                ret = {'ret':'success', 'data':f'삭제 실패(ID:{arg1})'}

        return jsonify(ret)

    def process_menu(self, page, req):
        arg = P.ModelSetting.to_dict()
        logger.info(f'[{self.name}] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.name}_{page}.html', arg=arg)

    def register_mail(self, req):
        try:
            mail_dir = os.path.join(ModelSetting.get('data_path'), 'mail')
            name = req['name']
            title = req['title']
            query_title = req['query_title']
            mime_type = req['mime_type']
            body = req['mail_text']
            logger.info(f'body: {body}')

            ext = '.html' if mime_type == 'text/html' else '.txt'
            mitem = ModelMailItem(name, title, query_title, mime_type)
            mitem.save()
            fname = '{mail_id:>03d}_{name}{ext}'.format(mail_id=mitem.id, name=name, ext=ext)
            mail_path = os.path.join(mail_dir, fname)
            SupportFile.write_file(mail_path, body)
            mitem.mail_path = mail_path
            mitem.save()
            return {'ret':'success', 'data':f'메일등록 완료: {title}({mitem.id})'}

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            return {'ret':'error', 'data':f'{str(e)}'}

    def modify_mail(self, req):
        try:
            mail_dir = os.path.join(ModelSetting.get('data_path'), 'mail')
            mail_id = int(req['mail_id'])
            mitem = ModelMailItem.get_by_id(mail_id)
            name = req['m_name']
            title = req['m_title']
            query_title = req['m_query_title']
            mime_type = req['m_mime_type']

            ext = '.html' if mime_type == 'text/html' else '.txt'
            fname = f'{mitem.id:>03d}_{req["m_name"]}{ext}'
            mail_path = os.path.join(mail_dir, fname)
            if mail_path != mitem.mail_path:
                SupportFile.file_move(mitem.mail_path, mail_dir, fname)
            mitem.name = name
            mitem.title = title
            mitem.query_title = query_title
            mitem.mime_type = mime_type
            mitem.mail_path = mail_path
            mitem.updated_time = datetime.now()
            mitem.save()
            return {'ret':'success', 'data':f'메일정보수정 완료: {title}({mitem.id})'}

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            return {'ret':'error', 'data':f'{str(e)}'}

    def preview_mail(self, mail_id):
        try:
            ret = {}
            data = {}
            mitem = ModelMailItem.get_by_id(int(mail_id))
            name = ModelSetting.get('test_default_name')
            dept = ModelSetting.get('test_default_dept')
            email = ModelSetting.get('test_default_mail')
            emp_code = ModelSetting.get('test_default_emp_code')
            html = SupportFile.read_file(mitem.mail_path)

            b64_rcpt_id = ScUtils.b64encode(emp_code)
            b64_training_id = ScUtils.b64encode('preview')
            read_url = self.read_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)
            read_tag = f'<img src="{read_url}" hidden>'
            infect_url = self.infect_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)
            report_url = self.report_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)

            data['body'] = html.format(read=read_tag, infect=infect_url, report=report_url, name=name, dept=dept, email=email, emp_code=emp_code)
            data['title'] = mitem.title.format(name=name,emp_code=emp_code,dept=dept,email=email)
            return {'ret':'success', 'data':data}

        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            return {'ret':'error', 'data':f'{str(e)}'}


    def send_mail(self, tritem, rcpt, mime):
        try:
            import smtplib
            from email import utils

            modal = 'command_modal_add_text'
            b64_sender = ScUtils.b64encode(tritem.sender_name)
            sender_name = f'=?UTF-8?B?{b64_sender}?='

            mime['From'] = f'{sender_name} <{tritem.sender_email}>'
            mime['To'] = f'{rcpt.email}'
            mime['Date'] = utils.formatdate(localtime = 1)

            msg = f'3. 발신자 정보: {sender_name}\n\n'
            msg = msg + f'From: {mime["From"]}, To: {mime["To"]}, Date: {mime["Date"]}\n\n'
            socketio.emit(modal, msg, namespace='/framework')

            server_addr = ModelSetting.get('smtp_server_addr')
            port = 25
            if server_addr.find(':') != -1:
                server_addr, port = server_addr.split(':')
                port = int(port)

            s = smtplib.SMTP()
            if ModelSetting.get_bool('smtp_set_debug'): s.set_debuglevel(1)
            s.connect(server_addr, port)
            s.sendmail(tritem.sender_email, rcpt.email, mime.as_string())
            socketio.emit(modal, '메일 발송 완료\n\n', namespace='/framework')
            s.quit()
            logger.debug(f'[sendmail] 메일 발송 완료: 수신자({rcpt.email}), 메일제목({mime["subject"]})')

            ritem = None
            ritem = ModelResultItem.get_by_rcpt_id_and_training_id(rcpt.id, tritem.id)
            is_test = True if rcpt.list_id == -1 else False
            if not ritem:
                ritem = ModelResultItem(rcpt.emp_code, rcpt.id, tritem.id, is_test=is_test)
            ritem.sent_time = datetime.now()
            ritem.status = 'sent'
            ritem.save()
            return {'ret':'success'}
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return {'ret':'error', 'data':f'{str(e)}'}

    def set_mime(self, mail_data, tritem, mitem, rcpt):
        try:
            from email.mime.text import MIMEText

            subject = mitem.title.format(name=rcpt.name,dept=rcpt.dept,emp_code=rcpt.emp_code,email=rcpt.email)
            b64_subject = ScUtils.b64encode(subject)
            subject_str = f'=?UTF-8?B?{b64_subject}?='

            emp_code = rcpt.emp_code
            email_id = rcpt.email.split('@')[0]

            b64_rcpt_id = ScUtils.b64encode(str(rcpt.id))
            b64_training_id = ScUtils.b64encode(str(tritem.id))
            read_url = self.read_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)
            read_tag = f'<img src="{read_url}" hidden>'
            infect_url = self.infect_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)
            report_url = self.report_url.format(b64_rcpt_id=b64_rcpt_id, b64_training_id=b64_training_id)

            msg = mail_data.format(name=rcpt.name, emp_code=emp_code, email=rcpt.email, dept=rcpt.dept, read=read_tag, infect=infect_url, report=report_url, email_id=email_id)

            mime = MIMEText(msg, "html", _charset='utf-8')
            mime['subject'] = subject_str
            assert mime['Content-Transfer-Encoding'] == 'base64'
            return mime

        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return {'ret':'error', 'data':f'{str(e)}'}

