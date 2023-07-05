from .setup import *
from sqlalchemy import func, and_

logger = P.logger

# 수신자그룹
class ModelRcptListItem(ModelBase):
    P = P
    __tablename__ = '%s_rcptlist_item' % __package__
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = __package__

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    name = db.Column(db.String) # 수신자목록명
    total_count = db.Column(db.Integer)
    target_count = db.Column(db.Integer)
    except_count = db.Column(db.Integer)

    def __init__(self, name):
        self.created_time = datetime.now()
        self.name = name
        self.total_count = 0
        self.target_count = 0
        self.except_count = 0

    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_all_rcptlist(cls):
        return super().get_list(by_dict=True)

    @classmethod
    def get_all_entities(cls):
        return db.session.query(cls).all()

    @classmethod
    def web_list(cls, req):
        try:
            ret = {}
            page = 1
            page_size = P.ModelSetting.get_int('web_list_limit')
            job_id = ''
            search = ''
            category = ''
            if 'page' in req:
                page = int(req['page'])
            if 'keyword' in req:
                search = req['keyword'].strip()

            query = cls.make_query(search=search)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            return ret
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @classmethod
    def make_query(cls, search='', order='desc'):
        query = db.session.query(cls)
        if search is not None and search != '':
            if search.find('|') != -1:
                tmp = search.split('|')
                conditions = []
                for tt in tmp:
                    if tt != '':
                        conditions.append(cls.name.like('%'+tt.strip()+'%') )
                query = query.filter(or_(*conditions))
            elif search.find(',') != -1:
                tmp = search.split(',')
                for tt in tmp:
                    if tt != '':
                        query = query.filter(cls.name.like('%'+tt.strip()+'%'))
            else:
                query = query.filter(cls.name.like('%'+search+'%'))

        if order == 'desc': query = query.order_by(desc(cls.id))
        else: query = query.order_by(cls.id)
        return query


# 수신자
class ModelRcptItem(ModelBase):
    P = P
    __tablename__ = '%s_rcpt_item' % __package__
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = __package__

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    list_id = db.Column(db.Integer)
    name = db.Column(db.String)
    dept = db.Column(db.String)
    email = db.Column(db.String)
    emp_code = db.Column(db.String)
    excluded = db.Column(db.Boolean)

    def __init__(self, list_id, name, dept, email, emp_code):
        self.created_time = datetime.now()
        self.list_id = list_id
        self.name = name
        self.dept = dept
        self.email = email
        self.emp_code = emp_code
        self.excluded = False

    @classmethod
    def delete_by_list_id(cls, list_id):
        db.session.query(cls).filter(cls.list_id==list_id).delete()
        db.session.commit()

    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_by_email(cls, email):
        return db.session.query(cls).filter_by(email=email).all()

    @classmethod
    def get_by_list_id(cls, list_id):
        return db.session.query(cls).filter_by(list_id=list_id).all()

    @classmethod
    def get_by_email_and_list_id(cls, email, list_id):
        with F.app.app_context():
            return db.session.query(cls).filter_by(email=email).filter_by(list_id=list_id).first()

    @classmethod
    def get_all_entities(cls):
        return db.session.query(cls).all()

    @classmethod
    def get_entity_count(cls, list_id):
        return db.session.query(cls).filter_by(list_id=list_id).count()

    @classmethod
    def get_all_depts(cls):
        query = db.session.query(cls)
        return query.group_by(cls.dept).order_by(func.count(cls.id).desc()).all()

    @classmethod
    def get_all_target_entities(cls):
        query = db.session.query(cls)
        return query.filter(cls.excluded==False).all()

    @classmethod
    def get_all_target_entities_by_list_id(cls, list_id):
        with F.app.app_context():
            query = db.session.query(cls)
            query = query.filter(cls.list_id==list_id)
            return query.filter(cls.excluded==False).all()

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            query = cls.make_query_search(F.db.session.query(cls), search, cls.name)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            if option1 != 'all': query = query.filter(cls.list_id==int(option1))
            if option2 != 'all':
                if option2 == 'included': query = query.filter(cls.excluded==0)
                elif option2 == 'excluded': query = query.filter(cls.excluded==1)
                else: query = query.filter(cls.dept==option2)
            return query

    @classmethod
    def web_list(cls, req):
        try:
            ret = {}
            page = 1
            page_size = P.ModelSetting.get_int('web_list_limit')
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'keyword' in req.form:
                search = req.form['keyword'].strip()
            option1 = req.form.get('option1', 'all')
            option2 = req.form.get('option2', 'all')
            order = req.form['order'] if 'order' in req.form else 'desc'

            query = cls.make_query(req, order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            #F.logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            try:
                if cls.P.ModelSetting is not None and cls.__tablename__ is not None:
                    cls.P.ModelSetting.set(f'{cls.__tablename__}_last_list_option', f'{order}|{page}|{search}|{option1}|{option2}')
            except Exception as e:
                F.logger.error(f"Exception:{str(e)}")
                F.logger.error(traceback.format_exc())
                F.logger.error(f'{cls.__tablename__}_last_list_option ERROR!' )
            return ret
        except Exception as e:
            cls.P.logger.error(f"Exception:{str(e)}")
            cls.P.logger.error(traceback.format_exc())


# 훈련메일
class ModelMailItem(ModelBase):
    P = P
    __tablename__ = '%s_mail_item' % __package__
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = __package__

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    updated_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    name = db.Column(db.String)
    title = db.Column(db.String)
    query_title = db.Column(db.String)
    mime_type = db.Column(db.String)  # text/plain, text/html
    mail_path = db.Column(db.String)

    def __init__(self, name, title, query_title, mime_type):
        self.created_time = datetime.now()
        self.name = name
        self.title = title
        self.query_title = query_title
        self.mime_type = mime_type

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['updated_time'] = self.updated_time.strftime('%m-%d %H:%M:%S') if self.updated_time != None else u'-'
        return ret

    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_all_entities(cls):
        return db.session.query(cls).all()

    @classmethod
    def get_all_target_entities(cls):
        query = db.session.query(cls)
        return query.filter(cls.excluded==False).all()

    @classmethod
    def get_all_items(cls):
        return super().get_list(by_dict=True)

    @classmethod
    def web_list(cls, req):
        try:
            ret = {}
            page = 1
            page_size = P.ModelSetting.get_int('web_list_limit')
            job_id = ''
            search = ''
            rcpt = 'all'
            dept = 'all'
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'keyword' in req.form:
                search = req.form['keyword'].strip()
            order = req.form.get('order', 'desc')
            query = cls.make_query(req, search=search)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            try:
                if cls.P.ModelSetting is not None and cls.__tablename__ is not None:
                    cls.P.ModelSetting.set(f'{cls.__tablename__}_last_list_option', f'{order}|{page}|{search}')
            except Exception as e:
                F.logger.error(f"Exception:{str(e)}")
                F.logger.error(traceback.format_exc())
                F.logger.error(f'{cls.__tablename__}_last_list_option ERROR!' )
            return ret
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return ret

    @classmethod
    def make_query(cls, req, order='desc', search='', option1='all', option2='all'):
        with F.app.app_context():
            query = db.session.query(cls)
            query = cls.make_query_search(F.db.session.query(cls), search, cls.name)
            query = query.order_by(desc(cls.id)) if order == 'desc' else query.order_by(cls.id)
            """
            if option1 != 'all': query = query.filter(cls.list_id==int(option1))
            if option2 != 'all':
                if option2 == 'included': query = query.filter(cls.excluded==0)
                elif option2 == 'excluded': query = query.filter(cls.excluded==1)
                else: query = query.filter(cls.dept==option2)
            """
            return query

# 훈련메일
class ModelTrainingItem(ModelBase):
    P = P
    __tablename__ = '%s_training_item' % __package__
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = __package__

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    started_time = db.Column(db.DateTime)
    finished_time = db.Column(db.DateTime)
    updated_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    name = db.Column(db.String)
    sender_name  = db.Column(db.String)
    sender_email = db.Column(db.String)
    rcptlist_id = db.Column(db.Integer)
    mail_id = db.Column(db.Integer)
    status = db.Column(db.String) # init, running, paused, finished, stopped
    total = db.Column(db.Integer)
    curr = db.Column(db.Integer)

    def __init__(self, name, sender_name, sender_email, rcptlist_id, mail_id, total=0):
        self.created_time = datetime.now()
        self.started_time = None
        self.finished_time = None
        self.updated_time = None
        self.name = name
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.rcptlist_id = rcptlist_id
        self.mail_id = mail_id
        self.status = 'init'
        self.total = total
        self.curr = 0

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['started_time'] = self.started_time.strftime('%m-%d %H:%M:%S') if self.started_time != None else u'-'
        ret['finished_time'] = self.finished_time.strftime('%m-%d %H:%M:%S') if self.finished_time != None else u'-'
        ret['updated_time'] = self.updated_time.strftime('%m-%d %H:%M:%S') if self.updated_time != None else u'-'
        return ret

    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_all_entities(cls):
        return db.session.query(cls).all()

    @classmethod
    def get_all_target_entities(cls):
        query = db.session.query(cls)
        return query.filter(cls.excluded==False).all()

    @classmethod
    def web_list(cls, req):
        try:
            ret = {}
            page = 1
            page_size = P.ModelSetting.get_int('web_list_limit')
            job_id = ''
            search = ''
            rcpt = 'all'
            dept = 'all'
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'keyword' in req.form:
                search = req.form['keyword'].strip()
            order = req.form.get('order', 'desc')
            query = cls.make_query(req, search=search)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            try:
                if cls.P.ModelSetting is not None and cls.__tablename__ is not None:
                    cls.P.ModelSetting.set(f'{cls.__tablename__}_last_list_option', f'{order}|{page}|{search}')
            except Exception as e:
                F.logger.error(f"Exception:{str(e)}")
                F.logger.error(traceback.format_exc())
                F.logger.error(f'{cls.__tablename__}_last_list_option ERROR!' )
            return ret
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return ret

    @classmethod
    def make_query(cls, req, search='', order='desc'):
        query = db.session.query(cls)
        if search is not None and search != '':
            if search.find('|') != -1:
                tmp = search.split('|')
                conditions = []
                for tt in tmp:
                    if tt != '':
                        conditions.append(cls.name.like('%'+tt.strip()+'%') )
                query = query.filter(or_(*conditions))
            elif search.find(',') != -1:
                tmp = search.split(',')
                for tt in tmp:
                    if tt != '':
                        query = query.filter(cls.name.like('%'+tt.strip()+'%'))
            else:
                query = query.filter(or_(cls.name.like('%'+search+'%'), cls.dept.like('%'+search+'%')))

        if order == 'desc': query = query.order_by(desc(cls.id))
        else: query = query.order_by(cls.id)

        return query

class ModelResultItem(ModelBase):
    P = P
    __tablename__ = '%s_result_item' % __package__
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = __package__

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    emp_code = db.Column(db.String)
    rcpt_id = db.Column(db.Integer)
    training_id = db.Column(db.Integer)
    status = db.Column(db.String) # init, sent, read, infect, report
    sent_time = db.Column(db.DateTime)
    read_time = db.Column(db.DateTime)
    click_time = db.Column(db.DateTime)
    report_time = db.Column(db.DateTime)
    read_ip = db.Column(db.String)
    click_ip = db.Column(db.String)
    report_ip = db.Column(db.String)
    is_test = db.Column(db.Boolean)

    def __init__(self, emp_code, rcpt_id, training_id, is_test=False):
        self.created_time = datetime.now()
        self.emp_code = emp_code
        self.rcpt_id = rcpt_id
        self.training_id = training_id
        self.status = 'init'
        self.is_test = is_test
        self.sent_time = None
        self.read_time = None
        self.click_time = None
        self.report_time = None
        self.read_ip = None
        self.click_ip = None
        self.report_ip = None

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['sent_time'] = self.sent_time.strftime('%m-%d %H:%M:%S') if self.sent_time != None else u'-'
        ret['read_time'] = self.read_time.strftime('%m-%d %H:%M:%S') if self.read_time != None else u'-'
        ret['click_time'] = self.click_time.strftime('%m-%d %H:%M:%S') if self.click_time != None else u'-'
        ret['report_time'] = self.report_time.strftime('%m-%d %H:%M:%S') if self.report_time != None else u'-'
        ret['read_ip'] = self.read_ip if self.read_ip != None else u'-'
        ret['click_ip'] = self.click_ip if self.click_ip != None else u'-'
        ret['report_ip'] = self.report_ip if self.report_ip != None else u'-'
        return ret

    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()

    @classmethod
    def get_first_by_training_id(cls, training_id):
        return db.session.query(cls).filter_by(training_id=training_id).order_by(cls.sent_time).first()

    @classmethod
    def get_by_rcpt_id_and_training_id(cls, rcpt_id, training_id):
        with F.app.app_context():
            return db.session.query(cls).filter(and_(cls.rcpt_id==rcpt_id, cls.training_id==training_id)).first()

    @classmethod
    def get_by_emp_code_and_training_id(cls, emp_code, training_id, is_test=False):
        with F.app.app_context():
            query = db.session.query(cls).filter_by(emp_code=emp_code)
            query = query.filter_by(training_id=training_id)
            return query.filter_by(is_test=is_test).first()
        #return db.session.query(cls).filter(and_(cls.emp_code==emp_code, cls.training_id==training_id)).first()

    @classmethod
    def get_all_by_training_id(cls, training_id):
        return db.session.query(cls).filter_by(training_id=training_id).order_by(desc(cls.sent_time)).all()

    @classmethod
    def get_all_entities(cls):
        return db.session.query(cls).all()

    @classmethod
    def get_all_target_entities(cls):
        query = db.session.query(cls)
        return query.filter(cls.excluded==False).all()

    @classmethod
    def web_list(cls, req):
        try:
            logger.info(f'web_list: {req}, {req.form}')
            ret = {}
            page = 1
            page_size = P.ModelSetting.get_int('web_list_limit')
            job_id = ''
            search = ''
            option1 = 'all'
            option2 = 'all'
            if 'keyword' in req.form:
                search = req.form.get('keyword')
            if 'option1' in req.form:
                option1 = req.form.get('option1')
            if 'option2' in req.form:
                option2 = req.form.get('option2')

            query = cls.make_query(search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            return ret
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @classmethod
    def make_query(cls, search='', option1='all', option2='all', order='desc'):
        query = db.session.query(cls)
        if option1 != 'all':
            query = query.filter_by(training_id = option1)
        if option2 != 'all':
            targets = []
            tmps = query.all()
            for tmp in tmps:
                rcpt = ModelRcptItem.get_by_id(tmp.rcpt_id)
                if rcpt.dept == option2:
                    targets.append(cls.rcpt_id == rcpt.id)
            if len(targets) == 0: query = query.filter_by(rcpt_id = -1)
            else: query = query.filter(or_(*targets))
        if search != '':
            targets = []
            tmps = query.all()
            for tmp in tmps:
                rcpt = ModelRcptItem.get_by_id(tmp.rcpt_id)
                if rcpt.name.find(search) != -1:
                    targets.append(cls.rcpt_id == rcpt.id)
            if len(targets) == 0: query = query.filter_by(rcpt_id = -1)
            else: query = query.filter(or_(*targets))

        if order == 'desc':
            query = query.order_by(desc(cls.id))
        else:
            query = query.order_by(cls.id)
        return query
