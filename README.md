## 악성메일 대응훈련 Plugin for FlaskFarm
- - - 
#### 1. FlaskFarm
- FlaskFarm(FF)는 Flask 기반의 Python 패키지로 모듈형태의 플러그인을 자유롭게 붙일 수 있는 개발프레임워크입니다.
- FF에 관한 보다 상세한 정보는 아래 링크를 참고하세요. 
- github: <https://github.com/flaskfarm/flaskfarm>
- githubio: <https://flaskfarm.github.io/>
- PyPi: <https://pypi.org/project/FlaskFarm/>
- docker: <https://hub.docker.com/repository/docker/flaskfarm/flaskfarm>

#### 2. csmail 플러그인
- FF 기반의 플러그인 모듈로 악성메일 대응훈련을 Web UI를 통해 편하게 관리할 목적으로 개발되었습니다.
- Concept
    - 훈련대상자에게 메일을 발송시 메일읽음확인 및 메일의 링크를 클릭을 감지할 수 있어야함
    - 메일의 링크를 클릭(감염)한 경우 훈련안내 페이지로 이동하여 신고할 수 있고, 신고정보를 저장/관리 가능해야함
    - 메일의 발송/읽음/링크클릭(감염)/신고의 기록을 남기고 자료화 할 수 잇어야함
    - 훈련대상자의 목록을 등록하고 관리할 수 있어야함
    - 훈련메일을 등록하고 관리할 수 있어야함

#### 3. 기본 기능 및 순서 설명
- 훈련을 위해서 먼저 기본설정 > 훈려대상자설정 > 메일설정 > 훈련 설정이 필요합니다.
    - 세부적인 사항은 각 설정페이지의 안내서를 참고.
- 기본설정: 훈련과 관련된 기본적인 설정을 관리함
    - 기본정보: 메일서버IP, 메일전송 간격 등 기본사항
    - 훈련설정: 기본적으로 사용될 훈련 관련 정보, 감염/신고화면 등 설정
    - DB연동설정: 사용자정보DB와 메일시스템의 DB 연동정보 설정(옵션)
- 훈련대상자관리: 훈련대상자 그룹, 대상자를 등록/관리 함
    - 그룹을 먼저 등록후 그룹에 대상자를 등록하는 형태가능(빈그룹 등록 후 대상자 등록)
    - 훈련대상그룹: 여러대상자를 하나의 그룹으로 관리(훈련별로 구분적용 가능)
    - 훈련대상자: 훈련대상자를 개별로 등록/관리 할 수 있는 기능
- 메일관리: 훈련메일을 등록/관리
    - html 형태의 훈련 메일을 등록/관리, 메일편집 및 미리보기 가능
    - 예약어는 실제훈련시에는 변환되어 처리됨
- 훈련관리: 등록한 훈련대상그룹-훈련메일을 매핑하여 훈련 등록
    - 훈련등록/관리/테스트/실행 등 기능 지원(충분히 테스트 후 실행권장)
- 훈련결과: 훈련결과를 요약정보/세부(개인별)결과/통계 및 보고서 제공
    - 메일DB 연동시 메일시스템의 신고기능을 통해 신고된 메일 정보 반영 기능 지원

#### 4. 설치 및 초기 설정 안내
- 1. FlaskFarm(FF) 설치(Docker 설치 추천)
    - 기본포트는 9999 설정을 통해 변경 가능
    - network 는 브릿지로 사용 가능
    - OS별 설치 방법 안내(<https://flaskfarm.github.io/posts/%EC%8B%A4%ED%96%89-Docker/>)
    - 도커 실행 샘플 스크립트
```bash
docker run -d \                                                                                                                                                                                                                     
--name cert \
--network=host \
--log-opt max-file=5 \
--log-opt max-size=10m \
-v /opt/flaskfarm:/data \
-v /:/host \
--privileged \
flaskfarm/flaskfarm:4.0

```
- 2. FF접속 및 기본 설정
    - 실행후 FF 접속(http://ip:9999), 시스템 - 설정 - 인증에서 인증설정(ID/PW) 및 APIKEY설정(사용: On)
    - 시스템 - 설정 - 기본에서 DDNS 설정
- 3. 필수 플러그인 설치
    - 시스템 - 플러그인관리 - 플러그인 설치 주소에 아래 주소 입력하여 설치
    - 편집기(flaskcode): `https://github.com/flaskfarm/flaskcode`
    - 악성메일대응훈련(csmail): `https://github.com/wikimcert/csmail`
- 4. 시스템 재시작
    - 시스템 - 재시작을 통해 재시작 및 플러그인 로드
