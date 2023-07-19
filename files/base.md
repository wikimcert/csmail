#### 1. 기본정보
- 데이터 저장경로: 등록한 메일, 보고서용 파일들이 생성될 경로
    - 기본 값 `/data/csmail` 위치에 'files', 'mail', 'report' 등 폴더를 자동으로 생성하고 하위에 파일을 생성함
    - ※ 일반적인경우 변경할 필요 없음
- 호스트IP: 메일서버에서 인식하는 훈련시스템의 IP주소
    - 메일DB 조회시 발신자IP주소 값으로 활용됨
- SMTP 메일서버 주소: IP:PORT 형태로 입력(별도로 메일서버 설정에 relay 허용필요)
    - port정보를 입력하지 않은 경우 기본포트(25)로 동작
- 훈련메일전송 발송간격: 메일 전송 간격(msec)
- 페이지당 목록 수: 각종 목록화면에서 한 페이지에 보여줄 목록의 수

#### 2.훈련설정
- 훈련 기본설정과 훈련화명 설정을 다룸
##### 2.1 훈련기본설정
- 회사/기관명: 훈련화면에 표시할 기관명으로 활용
- 기본설정-XX: 메일미리보기, 훈련전 테스트메일 발송시 기본수신자 정보로 활용됨
##### 2.2 훈련화면설정
- 감염화면설정: 감염(훈련대상자가 훈련메일상 링크를 클릭한경우)시 이동할 화면 설정
    - 화면내용과 디자인은 편집가능 상/하단의 스크립트 수정시 오동작 할수 있으니 주의 필요
- 신고화면설정: 감염화면에서 신고하기 버튼 클릭시 신고처리 후 이동할 안내 화면 설정

```html
<button id="report_btn" name="report_btn" class="btn btn-outline-primary btn-lg"><strong>악성메일신고하기</strong></button>
```

```javascript
$("body").on('click', '#report_btn', function(e){
  e.preventDefault();
  var url = report_url + '&user_id='+emp_code+'&training_id='+training_id;
  window.location.href = url;
});

```
- 신고화면설정: 감염화면에서 신고보튼 클릭시 이동할 화면 설정
- 감염/신고화면에서 사용할 수 있는 예약어 목록
    - 기관명: {{arg['org_name']}}
    - 훈련명: {{arg['title']}}
    - 대상자 성명: {{arg['name']}}
    - 대상자 사번: {{arg['emp_code']}}
    - 대상자 메일: {{arg['email']}}

