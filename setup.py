setting = {
    'filepath' : __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': None,
    'menu': {
        'uri': __package__,
        'name': '악성메일대응훈련',
        'list': [
            {
                'uri': 'base',
                'name': '기본설정',
                'list': [
                    {'uri': 'setting', 'name': '기본정보'},
                    {'uri': 'training', 'name': '훈련설정'},
                    {'uri': 'dblink', 'name': 'DB연동설정'},
                    {'uri': '/manual/files/base.md', 'name': '매뉴얼'},
                ]
            },
            {
                'uri':'rcpt',
                'name':'훈련대상자관리',
                'list': [
                    {'uri': 'list', 'name': '훈련대상그룹'},
                    {'uri': 'each', 'name': '훈련대상자'},
                    {'uri':'manual/files/rcpt.md','name':'대상자설정안내'},
                ]
            },
            {
                'uri':'mail',
                'name':'메일관리',
                'list': [
                    {'uri': 'list', 'name': '훈련메일관리'},
                    {'uri': 'manual/files/mail.md','name':'메일설정안내'},
                ]
            },
            {
                'uri':'training',
                'name':'훈련관리',
                'list': [
                    {'uri': 'list', 'name': '훈련목록'},
                    {'uri': 'manual/files/training.md','name':'훈련설정안내'},
                ]
            },
            {
                'uri':'report',
                'name':'훈련결과',
                'list': [
                    {'uri': 'summary', 'name': '훈련결과(요약)'},
                    {'uri': 'result', 'name': '세부결과'},
                    {'uri': 'stat', 'name': '훈련통계'},
                ]
            },
            {
                'uri':'manual',
                'name':'매뉴얼',
                'list': [
                    {'uri': 'README.md','name':'README'},
                ]
            },
            {
                'uri': 'log',
                'name': '로그',
            },
        ]
    },
    'setting_menu': None,
    'default_route': 'normal',
}


from plugin import *

P = create_plugin_instance(setting)

try:
    from .mod_base import ModuleBase
    from .mod_rcpt import ModuleRcpt
    from .mod_training import ModuleTraining
    from .mod_mail import ModuleMail
    from .mod_report import ModuleReport
    P.set_module_list([ModuleBase, ModuleRcpt, ModuleMail, ModuleTraining, ModuleReport])
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())

logger = P.logger
