from support import SupportSubprocess, SupportFile
from tool import ToolUtil

from .setup import *
from .utils import *
from .models import *

name = 'base'

class ModuleBase(PluginModuleBase):

    def __init__(self, P):
        super(ModuleBase, self).__init__(P, name='base', first_menu='setting')
        self.db_default = {
            'csmail_db_version' : '1',
            'except_dept_names': '환경,보안,감사',
            'host_addr': '127.0.0.1',
            'smtp_server_addr': '127.0.0.1',
            'smtp_send_sleep_time': '500',
            'web_list_limit': '30',
            'default_rcptlist_json':'[\n{\n  "name":"이름",\n  "dept":"부서명",\n  "emp_code":"사번",\n  "email":"메일주소"\n}\n]',
            # 사용자DB 연동
            'user_db_use' : 'False',
            'user_db_type' : '',
            'user_db_server_addr' : '127.0.0.1:1521',
            'user_db_user_id' : 'user',
            'user_db_password' : 'password',
            'user_db_service_name' : 'servicename',
            'user_db_query_str' : "SELECT name, dept, email, empcode FROM user WHERE [조건문]",

            # 메일DB 연동
            'mail_db_use' : 'False',
            'mail_db_type' : '',
            'mail_db_server_addr' : '127.0.0.1:1521',
            'mail_db_user_id' : 'user',
            'mail_db_password' : 'password',
            'mail_db_service_name' : 'servicename or dbname',
            'mail_db_query_str' : "SELECT * FROM HACK_REPORT WHERE [조건문]",

            # 훈련
            'org_name': '회사명',
            'infect_template_path': '/plugins/csmail/tempaltes/csmail_infect.html',
            'report_template_path': '/plugins/csmail/tempaltes/csmail_report.html',
            'data_path': f'/data/{__package__}',
            'test_default_name': '나보안',
            'test_default_dept': '정보보안팀',
            'test_default_mail': 'cert@wikim.re.kr',
            'test_default_emp_code': '9999',
            'admin_ips': '',
        }
        self.web_listmodel = None
        self.set_page_list([PageSetting, PageTraining, PageDBLink])

    def plugin_load(self):
        if not os.path.exists(os.path.join(ModelSetting.get('data_path'), 'mail')):
            ret = os.makedirs(os.path.join(ModelSetting.get('data_path'), 'mail'))
            logger.info(f'make path: ({ModelSetting.get("mail_path")}), ret({ret})')
        if not os.path.exists(os.path.join(ModelSetting.get('data_path'), 'report')):
            ret = os.makedirs(os.path.join(ModelSetting.get('data_path'), 'report'))
            logger.info(f'make path: ({ModelSetting.get("data_path")}/report), ret({ret})')
        if not os.path.exists(os.path.join(ModelSetting.get('data_path'), 'files')):
            ret = os.makedirs(os.path.join(ModelSetting.get('data_path'), 'files'))
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'files', 'userlist_sample.xlsx'), ToolUtil.make_path(os.path.join(ModelSetting.get('data_path'), 'files', 'userlist_sample.xlsx')))

    def process_api(self, sub, req):
        try:
            st = ['init', 'sent']
            ret = {"success": True, "info": "완료"}
            logger.info(f'[{self.name}] process_api: {sub}, {req}')
            ip_addr = req.headers.get('X-Forwarded-For', req.remote_addr)
            training_id = ScUtils.b64decode(req.args.get('training_id'))
            if training_id == 'preview': return jsonify(ret)
            training_id = int(training_id)
            rcpt_id = int(ScUtils.b64decode(req.args.get('rcpt_id')))
            ritem = ModelResultItem.get_by_rcpt_id_and_training_id(rcpt_id, training_id)
            tritem = ModelTrainingItem.get_by_id(training_id)
            rcpt = ModelRcptItem.get_by_id(rcpt_id)
            emp_code = rcpt.emp_code

            if sub == 'read':
                if ritem.status in st:
                    ritem.status = 'read'
                    ritem.read_time = datetime.now()
                    ritem.read_ip = ip_addr
                    ritem.save()
                else:
                    logger.info(f'[{self.name}] process_api: 이미읽음확인 처리됨')
            elif sub == 'infect':
                if not ritem.click_time:
                    ritem.click_time = datetime.now()
                    if ritem.status != 'report':
                        ritem.status = 'infect'
                        ritem.click_ip = ip_addr
                    logger.info(f'[{self.name}] 감염확인처리: {rcpt.name},{rcpt.dept},{rcpt.email},{emp_code},{ip_addr}')
                else:
                    logger.info(f'[{self.name}] 이미 처리 되어 SKIP: {rcpt.name},{rcpt.dept},{rcpt.email},{emp_code},{ip_addr}')

                if not ritem.read_time:
                    ritem.read_time = ritem.click_time

                ritem.save()
                arg = {}
                arg['action'] = sub
                arg['emp_code'] = emp_code
                arg['rcpt_id'] = rcpt.id
                arg['name'] = rcpt.name
                arg['email'] = rcpt.email
                arg['org_name'] = ModelSetting.get('org_name')

                ddns = F.SystemModelSetting.get('ddns')
                apikey = F.SystemModelSetting.get('apikey')
                report_url = f'{ddns}/{self.P.package_name}/api/base/report?apikey={apikey}'

                arg['report_url'] = report_url
                arg['training_id'] = training_id
                arg['b64_rcpt_id'] = ScUtils.b64encode(str(rcpt.id))
                arg['b64_training_id'] = ScUtils.b64encode(str(training_id))
                arg['title'] = tritem.name
                return render_template(f'{self.P.package_name}_{sub}.html', arg=arg)
            elif sub == 'report':
                if not ritem.report_time:
                    ritem.report_time = datetime.now()
                    if ritem.status != 'report':
                        ritem.status = 'report'
                        ritem.report_ip = ip_addr
                    logger.info(f'[{self.name}] 신고확인처리: {rcpt.name},{rcpt.dept},{rcpt.email},{emp_code},{ip_addr}')
                else:
                    logger.info(f'[{self.name}] 이미신고 처리 되어 SKIP: {rcpt.name},{rcpt.dept},{rcpt.email},{emp_code},{ip_addr}')

                ritem.save()
                arg = {}
                arg['action'] = sub
                arg['emp_code'] = emp_code
                arg['name'] = rcpt.name
                arg['email'] = rcpt.email
                arg['org_name'] = ModelSetting.get('org_name')
                arg['training_id'] = training_id
                arg['b64_rcpt_id'] = ScUtils.b64encode(str(rcpt.id))
                arg['b64_training_id'] = ScUtils.b64encode(str(training_id))
                arg['title'] = tritem.name
                return render_template(f'{self.P.package_name}_{sub}.html', arg=arg)

            return jsonify(ret)

        except Exception as e:
            logger.exception("Exception while processing api requests:")
            return jsonify({"success": False, "log": str(e)})

class PageSetting(PluginPageBase):
    def __init__(self, P, parent):
        super(PageSetting, self).__init__(P, parent, name='setting')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.debug(f'[page_setting] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

class PageTraining(PluginPageBase):
    def __init__(self, P, parent):
        super(PageTraining, self).__init__(P, parent, name='training')

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.debug(f'[page_training] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        logger.info(f'[page_training] command({command}), {arg1}, {arg2}, {arg3}')
        ret = {}
        try:
            if command == 'preview_template':
                ret = self.prepare_preview(arg1)
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            ret = {'ret':'error', 'data':f'{str(e)}'}

        return jsonify(ret)

    def prepare_preview(self, ttype):
        ret = {}
        try:
            if ttype == 'infect': fpath = ModelSetting.get('infect_template_path')
            else: fpath = ModelSetting.get('report_template_path')
            html = SupportFile.read_file(fpath)
            import re
            rx = r"\{%.+%\}"
            data = re.sub(rx, '', html)
            data = data.replace("{{arg['org_name']}}", ModelSetting.get('org_name'))
            data = data.replace("{{arg['title']}}", '악성메일 대응훈련')
            data = data.replace("{{arg['name']}}", ModelSetting.get('test_default_name'))
            data = data.replace("{{arg['emp_code']}}", ModelSetting.get('test_default_emp_code'))
            data = data.replace("{{arg['email']}}", ModelSetting.get('test_default_mail'))
            ret = {'ret':'success', 'data':data}
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            ret = {'ret':'error', 'data':f'{str(e)}'}

        return ret

class PageDBLink(PluginPageBase):
    def __init__(self, P, parent):
        super(PageDBLink, self).__init__(P, parent, name='dblink')

    def my_arg_to_dict(self, arg):
        import html
        import urllib.parse
        ret = {}
        tmp = html.unescape(arg)
        tmp = urllib.parse.unquote(tmp)
        tmp = dict(urllib.parse.parse_qs(tmp, keep_blank_values=True))
        for k, v in tmp.items():
            if k in ret:
                if type(ret[k]) == list: ret[k].append(v)
                else: ret[k] = [ret[k], v]
            else: ret[k] = v if len(v) > 1 else v[0]
        return ret

    def process_menu(self, req):
        arg = P.ModelSetting.to_dict()
        logger.debug(f'[page_dblink] req({req}, {req.args})')
        return render_template(f'{self.P.package_name}_{self.parent.name}_{self.name}.html', arg=arg)

    def process_command(self, command, arg1, arg2, arg3, req):
        logger.info(f'[page_dblink] command({command}), {arg1}, {arg2}, {arg3}')
        ret = {}
        if command == 'user_db_test' or command == 'mail_db_test':
            ret = ScUtils.db_test(command, self.my_arg_to_dict(arg1))
        elif command == 'user_db_query_test' or command == 'mail_db_query_test':
            ret = ScUtils.db_query_test(command, self.my_arg_to_dict(arg1))
        elif command == 'check_pkg':
            if arg1 == 'oracle':
                try:
                    import cx_Oracle as dbpkg
                    ret['data'] = f'이미 설치되어 있음({dbpkg.__name__} {dbpkg.__version__})'
                except ImportError:
                    os.system('pip install cx_Oracle')
                    import cx_Oracle as cx
                    ret['data'] = f'모듈 설치완료({dbpkg.__name__} {dbpkg.__version__})'
            elif arg1 == 'mysql':
                try:
                    import pymysql as dbpkg
                    ret['data'] = f'이미 설치되어 있음({dbpkg.__name__} {dbpkg.__version__})'
                except ImportError:
                    os.system('pip install pymysql')
                    import pymysql as dbpkg
                    ret['data'] = f'모듈 설치완료({dbpkg.__name__} {dbpkg.__version__})'
            elif arg1 == 'mssql':
                try:
                    import pymssql as dbpkg
                    ret['data'] = f'이미 설치되어 있음({dbpkg.__name__} {dbpkg.__version__})'
                except ImportError:
                    os.system('pip install pymysql')
                    import pymssql as dbpkg
                    ret['data'] = f'모듈 설치완료({dbpkg.__name__} {dbpkg.__version__})'
            ret['ret'] = 'success'
        return jsonify(ret)

