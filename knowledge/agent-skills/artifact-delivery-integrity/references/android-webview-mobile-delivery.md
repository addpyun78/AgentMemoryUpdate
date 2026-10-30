# Android WebView 모바일 전용 검증·전달

Android Kotlin WebView 앱을 모바일 단일 레이아웃으로 교정하고 APK/AAB/소스 ZIP을 전달할 때 사용하는 확장 체크리스트다.

## 모바일 계약부터 교정

CSS만 고치지 말고 페이지 핸드오프 계약부터 고친다.

- 제품 레이아웃: 320~430px 세로형 단일열
- 넓은 QA 캔버스: 430px 셸을 중앙 유지하되 태블릿/데스크톱 2열로 확장하지 않음
- 제품용 `@media (min-width: ...)`, 페이지 단위 2열, 데스크톱 전용 내비게이션 금지
- KPI처럼 카드 내부 소규모 grid의 허용 범위는 별도 명시
- 인증 화면은 사진/폼 좌우 분할 대신 세로 흐름
- fixed 하단바는 safe-area를 포함하고 앱 셸과 같은 최대 폭 사용

계약 변경 후 handoff validator를 실행하고 페이지 BUILD 프롬프트를 다시 컴파일한다. 이전 계약의 프롬프트는 재사용하지 않는다.

## 하단바 비가림 검증

큰 `padding-bottom`만 추가하지 않는다.

- 비인증 라우트를 하단바 상단까지의 독립 스크롤 영역으로 제한
- 끝까지 스크롤한 뒤 마지막 콘텐츠 하단과 하단바 상단 간격이 양수인지 DOM으로 측정
- 길이가 다른 대표 라우트와 추가 화면도 실제 버튼으로 이동해 확인

최소 영수증 필드:

```json
{
  "viewport": "390x844",
  "appShellWidth": 390,
  "contentColumns": 1,
  "bottomNavCount": 5,
  "bottomNavHeight": 76,
  "lastContentClearance": 33.5,
  "horizontalOverflow": false
}
```

## 정확 뷰포트 시각 증거

기본 QA 캔버스는 390×844, 768×1024, 1440×900이며 프로젝트 계약이 다른 값을 요구하면 그 값을 따른다.

- 실제 앱 자산을 안전한 HTTP/WebView 원점에서 실행
- 기존 브라우저의 DevTools Protocol 등으로 정확한 viewport 설정
- 불필요하게 프로젝트에 새 브라우저 의존성을 추가하지 않음
- 각 캡처에서 셸 폭, 열 수, 탭 수, 마지막 콘텐츠 여유, 가로 넘침을 기록
- PNG뿐 아니라 캡처 스크립트, DOM 측정값, 콘솔 오류, 소스 SHA-256, PNG SHA-256을 함께 저장
- CSP가 인라인 검증 스타일을 차단하면 CSP를 약화하지 말고 DevTools 제어를 사용

이전 화면에 하단바 가림이나 구형 CSS가 보이면 증거로 재사용하지 않는다.

## 원시 로그와 정확한 표현

다음을 원시 로그와 SHA-256으로 보존한다.

- 웹 계약 테스트
- 보안 경계 테스트
- Gradle build/lint/package
- 브라우저 콘솔·JavaScript 오류

`testDebugUnitTest`나 `testReleaseUnitTest`가 `NO-SOURCE`면 "단위 테스트 통과"라고 쓰지 않는다. "테스트 소스 없음; lint·빌드·패키징 성공"이라고 보고한다.

## APK/AAB 내장 자산·서명

1. APK/AAB를 ZIP으로 열어 CRC/구조 검사
2. APK 내부 `assets/www/index.html`, `styles.css`를 읽어 최신 캐시 버전·셸 폭·fixed safe-area 하단바·금지 미디어 쿼리 부재 확인
3. Debug/Release 파일의 크기와 SHA-256 계산
4. `apksigner verify --verbose --print-certs`로 APK 서명 확인
5. `jarsigner -verify` 등으로 AAB 서명 상태 확인
6. 배포 키가 없으면 이름과 보고서에 `unsigned`를 표시하고 출시를 `BLOCKED_EXTERNAL`로 유지

Debug 서명 성공은 Release 서명 성공이 아니다.

## 소스 ZIP denylist

표준 `zipfile`로도 충분하다. 다음은 제외한다.

- `.git`, `.gradle`, `.a2a`, `build`, `app/build`, `node_modules`, `__pycache__`
- `local.properties`, `google-services.json`, `.env*`
- `*.jks`, `*.keystore`, `*.p12`, `*.pfx`, `*.pem`, `*.key`
- 기존 `*.apk`, `*.aab`, `*.zip`
- 쿠키·브라우저 사용자 데이터·자격 증명 저장소

생성 후:

- `ZipFile.testzip()` CRC 검사
- 경로 탈출, 중복 엔트리, denylist 재검사
- 제한된 민감 패턴 검사(개인키 헤더, 잘 알려진 API 키/토큰 형식)
- 파일 수·크기·SHA-256 기록

활성 브라우저 프로필은 잠금 파일이 있을 수 있으므로 개별 파일을 임의 무시하지 말고 프로필 디렉터리 전체를 패키징 대상에서 제외한다.

## 해시 안정성을 위한 순서

1. 최종 소스·계약·테스트·시각 영수증 확정
2. 독립 검토 파일 저장
3. 프로젝트 계약 갱신
4. 실행 보고서 갱신
5. APK/AAB 복사
6. 보고서를 포함한 소스 ZIP 생성
7. ZIP CRC·금지 항목·민감 패턴 검사
8. 실제 파일을 다시 읽어 외부 전달 매니페스트 생성
9. 매니페스트의 모든 크기·SHA-256 재대조
10. APK 내부 최신 자산과 ZIP 내부 보고서가 live 파일과 일치하는지 최종 영수증 생성

매니페스트를 ZIP 안에 넣어 ZIP 해시와 매니페스트 해시의 순환을 만들지 않는다. 매니페스트는 archive 외부에 둔다.

## 독립 검토

독립 검토자는 다음을 직접 읽는다.

- 페이지 계약과 validator 상태
- 컴파일된 BUILD 프롬프트
- 실제 HTML/CSS와 금지 패턴
- 정확 viewport 영수증과 PNG 해시
- 원시 테스트 로그와 로그 해시
- 외부 차단을 기록한 미해결 실패 로그
- 전달 매니페스트와 최종 무결성 영수증

시각 결과가 PASS여도 감사 추적성이 부족하면 캡처 재현 스크립트, 소스↔PNG 해시, 원시 로그를 보완한 뒤 재검토한다.

## 종료 정리

- 검증용 HTTP 서버 종료
- 프로젝트 전용 headless Chrome/CDP 프로세스만 PID·프로필 경로로 한정해 종료
- 일반 사용자 브라우저는 종료하지 않음
- 포트와 프로젝트 전용 프로세스가 사라졌는지 재확인
- 임시 프로필이 소스 ZIP에 없는지 확인

## 로컬 전달 PASS 조건

- 계약·BUILD 프롬프트·소스가 모바일 전용 규칙으로 일치
- 웹·보안·Gradle 원시 로그 존재
- 실제 정확 viewport 화면과 DOM 측정 PASS
- 브라우저 오류 0 또는 명시적 처리
- APK 내부 최신 자산 확인
- ZIP CRC·denylist·민감 패턴 검사 PASS
- 매니페스트 해시가 실제 파일과 일치
- 독립 검토 PASS
- 외부 설정·서명 부족은 `BLOCKED_EXTERNAL`로 명시
