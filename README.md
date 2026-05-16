# Naver Weather for Home Assistant

Home Assistant에서 네이버 날씨 검색 결과를 기반으로 현재 날씨, 주간 예보, 미세먼지와 대기질 정보를 제공하는 커스텀 통합입니다.

![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/badge/version-v2.5.5-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5.svg)

## 원작자 표기

이 저장소는 [miumida/naver_weather](https://github.com/miumida/naver_weather)를 기반으로 수정한 버전입니다.

원작자인 [@miumida](https://github.com/miumida)님과 기존 프로젝트에 기여해 주신 분들께 감사드립니다.  
현재 포크는 네이버 페이지 구조 변경 대응, 동 단위 지역 사용, 센서 정리, 주간 예보 및 대기질 센서 개선을 목적으로 유지보수하고 있습니다.

## 주요 기능

- Home Assistant `weather` 엔티티 생성
- 현재 날씨 센서 생성
- 주간 예보 센서 생성
- 미세먼지/초미세먼지 수치 및 등급 센서 생성
- 오존, 일산화탄소, 아황산가스, 이산화질소, 통합대기 등급 센서 생성
- 일출/일몰 센서 생성
  - 상태는 현재 시간 기준 다음 이벤트로 표시됩니다. 예: `일몰 19:34`, `일출 05:26`
  - 속성에는 `sunrise`, `sunset`, `next_event_datetime` 등이 포함됩니다.
- Config Flow와 Options Flow 지원
- 구 + 동 형식의 지역 입력 지원

## 설치

### HACS 사용자 저장소

1. Home Assistant에서 HACS를 엽니다.
2. `통합구성요소` 메뉴로 이동합니다.
3. 오른쪽 위 메뉴에서 `사용자 정의 저장소`를 선택합니다.
4. 저장소 주소를 입력합니다.

```text
https://github.com/af950833/naver_weather
```

5. 카테고리는 `Integration`을 선택합니다.
6. `Naver Weather`를 설치합니다.
7. Home Assistant를 재시작합니다.

### 수동 설치

1. 이 저장소의 `custom_components/naver_weather` 폴더를 Home Assistant 설정 경로에 복사합니다.

```text
<config>/custom_components/naver_weather
```

2. Home Assistant를 재시작합니다.
3. `설정 > 기기 및 서비스 > 통합 구성요소 추가`에서 `Naver Weather`를 추가합니다.

## 설정

통합 추가 화면에서 지역명을 입력합니다.

지역명은 `구 동` 형식으로 입력합니다.

```text
계양구 계양1동
계양구 장기동
```

허용되지 않는 예:

```text
장기동
인천 계양구 장기동
계양구
장기동 일기예보
```

네이버 검색에는 입력한 지역명 전체가 사용됩니다.

- 날씨 검색: `계양구 계양1동 일기예보`
- 미세먼지 검색: `계양구 계양1동 미세먼지`

## 옵션

통합의 옵션 화면에서 다음 값을 수정할 수 있습니다.

| 옵션 | 설명 |
| --- | --- |
| 지역 | `구 동` 형식의 조회 지역 |
| 주간예보에 오늘날씨 포함 | 주간 예보 센서에 오늘 예보를 포함할지 여부 |

## 생성되는 엔티티

지역이 `계양구 계양1동`인 경우 엔티티 ID는 대체로 다음과 같은 형식으로 생성됩니다.

```text
weather.naver_weather_gyeyang1
sensor.naver_weather_gyeyang1_temperature
sensor.naver_weather_gyeyang1_rain_probability
sensor.naver_weather_gyeyang1_fine_dust
sensor.naver_weather_gyeyang1_sun_times
```

Home Assistant의 엔티티 레지스트리 상태나 기존 동일 이름 엔티티 여부에 따라 `_2` 같은 suffix가 붙을 수 있습니다.

### 날씨/현재 상태

- 현재 온도
- 체감 온도
- 오늘 최고 온도
- 오늘 최저 온도
- 현재 습도
- 풍속
- 풍향
- 강수량
- 강수 확률
- 자외선 등급
- 현재 날씨
- 현재 날씨 요약
- 마지막 업데이트 성공 시간
- 마지막 업데이트 오류

### 예보

- 내일 오전 날씨
- 내일 오후 날씨
- 내일 최고 온도
- 내일 최저 온도
- 주간 예보 1-7

주간 예보 센서는 날짜, 오전/오후 상태, 최고/최저 온도, 오전/오후 강수 확률을 속성으로 제공합니다.

### 비 예보

- 오늘 비 시작 예상 시간
- 내일 비 시작 예상 시간
- 오늘 비 예보
- 내일 비 예보

비 예보 센서의 상태는 보기 좋게 `있음` 또는 `없음`으로 표시되며, 자동화용 boolean 값은 관련 속성에 유지됩니다.

### 대기질

- 미세먼지
- 미세먼지 등급
- 초미세먼지
- 초미세먼지 등급
- 오존
- 일산화탄소
- 아황산가스
- 이산화질소
- 통합대기
- 대기질 측정소
- 대기질 제공처
- 대기질 업데이트 시간

미세먼지와 초미세먼지 수치 센서는 등급에 따라 동적 아이콘을 사용합니다. 가스 및 통합대기 등급 센서도 등급에 따라 숫자 아이콘을 사용합니다.

### 일출/일몰

하나의 센서로 일출과 일몰 정보를 제공합니다.

```text
sensor.naver_weather_gyeyang1_sun_times
```

상태 예:

```text
일몰 19:34
```

주요 속성:

| 속성 | 설명 |
| --- | --- |
| `sunrise` | 오늘 일출 시간 |
| `sunset` | 오늘 일몰 시간 |
| `next_event` | 다음 이벤트. `sunrise` 또는 `sunset` |
| `next_event_label` | 다음 이벤트 표시명 |
| `next_event_time` | 다음 이벤트 시간 |
| `next_event_datetime` | 다음 이벤트 날짜/시간 |

## 참고 사항

- 이 통합은 네이버 공식 API가 아니라 네이버 검색 및 날씨 페이지의 공개 화면 데이터를 파싱합니다.
- 네이버 페이지 구조가 변경되면 일부 센서가 일시적으로 동작하지 않을 수 있습니다.
- 너무 짧은 주기의 업데이트는 권장하지 않습니다.
- 동일한 Home Assistant 인스턴스에 서로 다른 구의 같은 동 이름을 동시에 등록하면 Home Assistant가 엔티티 ID에 `_2` suffix를 붙일 수 있습니다.

## 문제 해결

### 센서가 생성되지 않음

- Home Assistant를 재시작했는지 확인합니다.
- 지역 입력이 `구 동` 형식인지 확인합니다.
- 네이버에서 같은 검색어로 날씨 결과가 정상 표시되는지 확인합니다.

### 기존 엔티티 ID가 예전 형식으로 남아 있음

Home Assistant는 엔티티 레지스트리를 보존합니다. 통합을 삭제해도 엔티티 ID가 즉시 원하는 형식으로 바뀌지 않을 수 있습니다.

필요하면 `설정 > 기기 및 서비스 > 엔티티`에서 기존 엔티티를 정리한 뒤 다시 추가하세요.

## 버전 정보

- 2026/05/16 V1.0.0.0 Initial Release


