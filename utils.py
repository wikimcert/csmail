import base64

from support import SupportSubprocess
from .setup import *
from .models import *

logger = P.logger
ModelSetting = P.ModelSetting


class ScUtils:
    def db_test(command, req):
        ret = {}
        logger.info(f'[db_test] req({req})')
        if command == 'user_db_test':
            server_addr = req['user_db_server_addr']
            user_id = req['user_db_user_id']
            password = req['user_db_password']
            service_name = req['user_db_service_name']
            db_type = req['user_db_type']
        elif command == 'mail_db_test': # 'mail_db_test':
            server_addr = req['mail_db_server_addr']
            user_id = req['mail_db_user_id']
            password = req['mail_db_password']
            service_name = req['mail_db_service_name']
            db_type = req['mail_db_type']

        try:
            if db_type == 'oracle':
                import cx_Oracle
                conn = cx_Oracle.connect(f'{user_id}/{password}@{server_addr}/{service_name}')
                logger.info(f'connection: {conn}')
                if conn:
                    ret['ret'] = 'success'
                    ret['data'] = f'접속성공: {conn.dsn}'
                conn.close()
            elif db_type == 'mysql':
                try:
                    import pymysql
                except ImportError:
                    os.system('pip install pymysql')
                    import pymysql

                host, port = server_addr.split(':')
                port = int(port)
                conn = pymysql.connect(host=host, port=port, user=user_id, password=password, db=service_name, charset='utf8')
                if conn:
                    ret['ret'] = 'success'
                    ret['data'] = f'접속성공: {conn.host}:{conn.port}/{str(conn.db)}'
                conn.close()
            elif db_type == 'mssql':
                try:
                    import pymysql
                except ImportError:
                    os.system('pip install pymssql')
                    import pymysql

                host, port = server_addr.split(':')
                port = int(port)
                conn = pymssql.connect(host=host, port=port, user=user_id, password=password, database=service_name)
                if conn:
                    ret['ret'] = 'success'
                    ret['data'] = f'접속성공: {conn.host}:{conn.port}/{str(conn.db)}'
                conn.close()
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
            ret['data'] = str(e)

        logger.info(f'[user_db_test]: {ret}')
        return ret

    def db_query_test(command, req):
        ret = {}
        logger.info(f'[select_test] req({req})')
        if command == 'user_db_query_test':
            server_addr = req['user_db_server_addr']
            user_id = req['user_db_user_id']
            password = req['user_db_password']
            service_name = req['user_db_service_name']
            db_type = req['user_db_type']
            query_str = req['user_db_query_str']
        elif command == 'mail_db_query_test': # 'mail_db_test':
            server_addr = req['mail_db_server_addr']
            user_id = req['mail_db_user_id']
            password = req['mail_db_password']
            service_name = req['mail_db_service_name']
            db_type = req['mail_db_type']
            query_str = req['mail_db_query_str']
            # for temporary
            dayago = datetime.now() - timedelta(days=1)
            host_addr = ModelSetting.get('host_addr')
            query_str = query_str.format(sender_ip=host_addr,sent_time=dayago.strftime('%Y-%m-%d %H:%M:%S'), sender='test@test.com', title='title')

        try:
            if db_type == 'oracle':
                import cx_Oracle
                conn = cx_Oracle.connect(f'{user_id}/{password}@{server_addr}/{service_name}')
            elif db_type == 'mysql':
                try:
                    import pymysql
                except ImportError:
                    os.system('pip install pymysql')
                    import pymysql

                host, port = server_addr.split(':')
                port = int(port)
                conn = pymysql.connect(host=host, port=port, user=user_id, password=password, db=service_name, charset='utf8')
            elif db_type == 'mssql':
                try:
                    import pymysql
                except ImportError:
                    os.system('pip install pymssql')
                    import pymysql

                host, port = server_addr.split(':')
                port = int(port)

            logger.info(f'try to connect db: {db_type}')
            logger.debug(f'test query: {query_str}')
            cursor = conn.cursor()
            cursor.execute(query_str)

            data = []
            row = cursor.fetchone()
            while row:
                logger.info(f'row: {row}')
                data.append({'emp_code':row[0], 'name':row[1], 'dept':row[2], 'email':row[3]})
                row = cursor.fetchone()

            """
            for emp_code, name, dept_name, email in cursor:
                logger.info(f'{emp_code},{name},{dept_name},{email}')
            """

            ret['ret'] = 'success'
            ret['data'] = data
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
            ret['data'] = str(e)

        logger.info(f'[user_db_test]: {ret}')
        return ret

    def conn_db(target):
        try:
            server_addr = ModelSetting.get(f'{target}_server_addr')
            user_id = ModelSetting.get(f'{target}_user_id')
            password = ModelSetting.get(f'{target}_password')
            service_name = ModelSetting.get(f'{target}_service_name')
            db_type = ModelSetting.get(f'{target}_type')
            conn = None

            if db_type == 'oracle':
                try:
                    import cx_Oracle
                except ImportError:
                    os.system('pip install cx_Oracle')
                    import cx_Oracle

                conn = cx_Oracle.connect(f'{user_id}/{password}@{server_addr}/{service_name}')
            elif db_type == 'mysql':
                try:
                    import pymysql
                except ImportError:
                    os.system('pip install pymysql')
                    import pymysql

                host, port = server_addr.split(':')
                port = int(port)
                conn = pymysql.connect(host=host, port=port, user=user_id, password=password, db=service_name, charset='utf8')
            elif db_type == 'mssql':
                try:
                    import pymssql
                except ImportError:
                    os.system('pip install pymssql')
                    import pymssql

                host, port = server_addr.split(':')
                port = int(port)
                conn = pymssql.connect(host=host, port=port, user=user_id, password=password, db=service_name, charset='utf8')
            return conn
        except Exception as e:
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            return None

    def get_user_list(except_dept_list):
        ret = {}
        query_str = ModelSetting.get('user_db_query_str')
        try:
            conn = ScUtils.conn_db('user_db')
            cursor = conn.cursor()
            cursor.execute(query_str)
            data = []

            for emp_code, name, dept_name, email in cursor:
                logger.info(f'{emp_code},{name},{dept_name},{email}')
                if dept_name in except_dept_list:
                    data.append({'emp_code': emp_code, 'name':name, 'dept_name':dept_name, 'email':email, 'excluded':True})
                else:
                    data.append({'emp_code': emp_code, 'name':name, 'dept_name':dept_name, 'email':email, 'excluded':False})

            conn.close()
            ret['ret'] = 'success'
            ret['data'] = data
        except Exception as e:
            try: conn.close()
            except: pass
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
            ret['data'] = str(e)

        return ret

    def get_report_status(training_id):
        try:
            ret = {}
            tritem = ModelTrainingItem.get_by_id(training_id)

            query_str = ModelSetting.get('mail_db_query_str')
            report_logic = ModelSetting.get('mail_db_report_logic')

            conn = ScUtils.conn_db('mail_db')
            cursor = conn.cursor()

            mitem = ModelMailItem.get_by_id(tritem.mail_id)

            host_addr = ModelSetting.get('host_addr')

            query = query_str.format(sender_ip=host_addr,
                    sender=tritem.sender_email,
                    title=mitem.query_title,
                    sent_time=tritem.started_time)

            logger.debug(f'[mail_db] {query}')
            cursor.execute(query)

            data = []
            targets = {}

            ritems = ModelResultItem.get_all_by_training_id(training_id)
            for ritem in ritems:
                rcpt = ModelRcptItem.get_by_id(ritem.rcpt_id)
                targets[rcpt.email] = {'result':ritem.id}

            rows = cursor.fetchall()
            #logger.debug(f'[rows]: {rows}')
            for row in rows:
                #logger.debug(f'[row]: {row}')

                # row[0] = 신고자(수신자주소), row[1] = 신고시각 고정
                if row[0] in targets:
                    ritem = ModelResultItem.get_by_id(targets[row[0]]['result'])
                    if ritem.status != 'report':
                        ritem.status = 'report'
                        ritem.report_time = row[1]
                        ritem.save()
                        logger.debug(f'[신고내역갱신] 메일DB의 신고내역 존재: {row[0]}, {row[1]}')
                    else:
                        logger.debug(f'[신고내역갱신] SKIP 이미 처리된 사용자: {row[0]}, {row[1]}')

            ret['ret'] = 'success'
            ret['data'] = '갱신완료했음'

        except Exception as e:
            try: conn.close()
            except: pass
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())
            ret['ret'] = 'error'
            ret['data'] = str(e)

        return ret


    def b64encode(text):
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def b64decode(text):
        return base64.b64decode(text.encode('utf-8')).decode('utf-8')

class ResultSummary():
    training_id = None
    created_time = None
    updated_time = None
    name = None
    total_cnt = 0
    read_cnt = 0
    infect_cnt = 0
    report_cnt = 0
    report_read_cnt = 0
    report_infect_cnt = 0

    def __init__(self, training_id):
        self.training_id = training_id
        self.name = None
        self.total_cnt = 0
        self.read_cnt = 0
        self.infect_cnt = 0
        self.report_cnt = 0
        self.report_read_cnt = 0
        self.report_infect_cnt = 0
        self.created_time = None
        self.updated_time = None

class ReportDBItem():
    rcpt_addr = None
    mail_title = None
    report_time = None
    sender_addr = None
    sender_ip = None

    def __init__(self, rcpt_addr):
        self.rcpt_addr = rcpt_addr
        self.mail_title = None
        self.report_time = None
        self.sender_addr = None
        self.sender_ip = None
