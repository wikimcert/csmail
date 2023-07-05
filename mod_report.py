from support import SupportSubprocess
from .setup import *
from .utils import *
from .models import *

from urllib.parse import parse_qsl

name = 'report'


@app.route('/csmail_download_report', methods=['GET'])
def download_report():
    from flask import send_file
    logger.debug(f'[download_report] {request.args}')
    fpath = request.args.get('path');
    fname = request.args.get('name');
    excel = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(fpath, mimetype=excel, download_name=fname, as_attachment=True)

class ModuleReport(PluginModuleBase):

    def __init__(self, P):
        super(ModuleReport, self).__init__(P, name='report', first_menu='summary')
        self.web_list_model = ModelResultItem

    def process_menu(self, page, req):
        logger.info(f'[{self.name}] req({req}, {req.args})')
        arg = P.ModelSetting.to_dict()
        traininglist = ModelTrainingItem.get_list(by_dict=True)
        rcptlist = ModelRcptItem.get_list(by_dict=True)
        deptlist = []
        for e in rcptlist:
            if e['dept'] not in deptlist:
                deptlist.append(e['dept'])

        start_training_id = req.args.get('training_id', None);
        if start_training_id: arg['start_training_id'] = start_training_id;
        return render_template(f'{self.P.package_name}_{self.name}_{page}.html', arg=arg, deptlist=deptlist, traininglist=traininglist, rcptlist=rcptlist)

    def process_command(self, command, arg1, arg2, arg3, req):
        ret = {'ret':'success'}
        logger.info(f'[{self.name}] process_command: cmd({command}), req({req}), {arg1}, {arg2}, {arg3}')

        if command == 'resend_mail':
            ritem = ModelResultItem.get_by_id(int(arg1))
            req = {'req_type': 'test' if ritem.is_test else 'training', 'training_id':ritem.training_id, 'rcpt_id':ritem.rcpt_id}
            thread = threading.Thread(target=self.get_module('training').sendmail_thread_function, args=(req,))
            thread.daemon = True
            thread.start()
            ret = {'ret':'success', 'data':'훈련메일 발송 요청 완료'}
        elif command == 'summary':
            training_ids = {}
            summary_list = []

            args = dict(parse_qsl(arg1))
            logger.debug(f'[args] {args}')
            training_id = args['option_tr'] if ('option_tr' in args  and args['option_tr'] != 'all') else None
            if training_id: entities = ModelResultItem.get_all_by_training_id(int(training_id))
            else: entities = ModelResultItem.get_all_entities()

            for e in entities:
                if e.is_test: continue
                if str(e.training_id) not in training_ids:
                    s = ResultSummary(e.training_id)
                    titem = ModelTrainingItem.get_by_id(e.training_id)
                    s.name = titem.name
                    # 훈련명 검색 처리
                    if 'keyword' in args and args['keyword'] != '':
                        if s.name.find(args['keyword']) == -1: continue
                    s.created_time = titem.created_time.strftime('%m-%d %H:%M:%S')
                    #s.updated_time = titem.updated_time.strftime('%m-%d %H:%M:%S')
                    summary_list.append(s)
                    idx = summary_list.index(s)
                    training_ids[str(e.training_id)] = idx

                s = summary_list[training_ids[str(e.training_id)]]

                # 부서가 지정된 경우 처리
                if 'option_dept' in args and args['option_dept'] != 'all':
                    rcpt = ModelRcptItem.get_by_id(e.rcpt_id)
                    if rcpt.dept.find(args['option_dept']) == -1: continue

                s.total_cnt += 1
                if e.read_time: s.read_cnt += 1
                if e.click_time: s.infect_cnt += 1
                if e.report_time:
                    s.report_cnt += 1
                    if e.read_time: s.report_read_cnt += 1
                    if e.click_time: s.report_infect_cnt += 1

            logger.debug(f'[summary] {summary_list}')
            ret['list'] = [x.__dict__ for x in summary_list]
        elif command == 'download_report':
            training_id = int(arg1)
            ret = self.gen_report(training_id)
        elif command == 'get_report_status':
            training_id = int(arg1)
            ret = ScUtils.get_report_status(training_id)

        return jsonify(ret)


    def gen_report(self, training_id):
        try:
            import os
            try:
                import xlsxwriter
            except ImportError:
                os.system('pip install xlsxwriter')
                import xlsxwriter

            ret = {}
            str_today = datetime.now().strftime("%Y%m%d")
            tritem = ModelTrainingItem.get_by_id(training_id)
            title = tritem.name

            report_path = os.path.join(ModelSetting.get('data_path'), 'report')
            fpath = os.path.join(report_path, f'악성메일대응훈련_{title}_결과리포트_{str_today}.xlsx')
            logger.info(f'[gen_report] fpath: {fpath}')

            columns = ['부서', '성명','사번', '메일주소', '상태', '읽음여부', '감염여부','신고여부','발송시각', '읽음시각', '감염시각', '신고시각']
            entities = ModelResultItem.get_all_by_training_id(training_id)

            contents = []
            contents.append(columns)
            for e in entities:
                if e.is_test: continue

                rcpt    = ModelRcptItem.get_by_id(e.rcpt_id)
                tritem  = ModelTrainingItem.get_by_id(e.training_id)

                dept = rcpt.dept
                name = rcpt.name
                emp_code = rcpt.emp_code
                email = rcpt.email
                if e.status == 'init':
                    status = '초기상태'
                elif e.status == 'sent':
                    status = '메일발송됨'
                elif e.status == 'read':
                    status = '메일읽음'
                elif e.status == 'infect':
                    status = '감염됨'
                elif e.status == 'report':
                    status = '신고완료'

                read = 'Y' if e.read_time else 'N'
                infect = 'Y' if e.click_time else 'N'
                report = 'Y' if e.report_time else 'N'

                stime = e.sent_time.strftime('%Y-%m-%d %H:%M:%S') if e.sent_time else '-'
                rtime = e.read_time.strftime('%Y-%m-%d %H:%M:%S') if e.read_time else '-'
                ctime = e.click_time.strftime('%Y-%m-%d %H:%M:%S') if e.click_time else '-'
                ptime = e.report_time.strftime('%Y-%m-%d %H:%M:%S') if e.report_time else '-'

                contents.append([dept, name, emp_code, email, status, read, infect, report, stime, rtime, ctime, ptime])

            # 엑셀 기록 하기
            book = xlsxwriter.Workbook(fpath)
            bold = book.add_format({"bold": True})
            ws1 = book.add_worksheet(f'훈련 결과({title}_{str_today})')

            rows = 0
            for row in contents:
                for i in range(0, len(row)):
                    if rows == 0: ws1.write(rows, i, row[i], bold)
                    else: ws1.write(rows, i, row[i])
                rows += 1

            ws1.autofilter(f'A1:L{rows}')
            ws1.autofit()
            book.close()
            ret = {'ret':'success', 'data':{'path':fpath, 'name':os.path.basename(fpath)}}
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
            ret ={'ret':'error', 'data':f'{str(e)}'}
        return ret


