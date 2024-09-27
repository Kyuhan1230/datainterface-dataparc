# DataInterface - DataParc

이 프로젝트는 DataParc시스템과 상호작용하는 Python 클래스를 제공하여, 태그 데이터를 쉽게 조회하고 관리할 수 있도록 도와줍니다.

## 설치 방법

1. 프로젝트를 클론합니다.
   ```bash
   git clone https://github.com/kyuhan1230/datainterface-dataparc.git
   ```
   
2. 프로젝트의 루트/설치 경로로 이동합니다.
   ```bash
   cd my_dataparc_project
   ```

3. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

4. .env 파일을 설정합니다.
   ```bash
   DATAPARC_SERVER=your_server_address       # 데이터베이스 서버 주소
   DATAPARC_USERNAME=your_username           # 데이터베이스 사용자 이름
   DATAPARC_PASSWORD=your_password           # 데이터베이스 비밀번호
   DATAPARC_SITE_ABBREVIATION=your_site_abbreviation  # 사이트 약어 (예: 'CTC')
   DATAPARC_TIMEZONE=your_timezone           # 시간대 (예: 'UTC', 'Asia/Seoul')
   ```

## 사용 방법
```python
from dataparc.data_parc_connector import DataParcConnector
from datetime import datetime

# DataParcConnector 인스턴스 생성
connector = DataParcConnector()

# 최신 값 조회
current_values = connector.fetch_latest_values(["Tag1", "Tag2"])
print(current_values)

# 특정 시간 범위의 원시 데이터 조회
start_time = datetime(2024, 8, 1, 0, 0, 0)
end_time = datetime(2024, 8, 2, 0, 0, 0)
raw_data = connector.fetch_raw_data(["Tag1"], start_time, end_time)
print(raw_data)

# 보간된 데이터 조회
interpolated_data = connector.fetch_interpolated_data(["Tag1"], start_time, end_time, 3600, "AVERAGE")
print(interpolated_data)

# 특정 시점의 데이터 조회
timestamps = [datetime(2024, 8, 1, 12, 0, 0), datetime(2024, 8, 1, 18, 0, 0)]
data_at_times = connector.fetch_data_at_times(["Tag1", "Tag2"], timestamps)
print(data_at_times)
```
### 데이터 반환 구조와 활용
- 모듈에서 제공하는 함수들은 Dict[str, TagMeasurement] 형식의 데이터를 반환합니다. 
- 즉, 각 태그명을 키로 하고, 해당 태그의 측정값, 타임스탬프, 품질 정보를 담고 있는 TagMeasurement 객체를 값으로 갖는 딕셔너리를 반환합니다.

- TagMeasurement 클래스의 주요 속성:
   - value: 태그의 측정값을 나타내는 float 값입니다.
   - timestamp: 태그 값이 측정된 시간을 나타내는 datetime 객체입니다.
   - quality: 해당 태그 데이터의 품질 상태를 나타내는 int 값입니다. (예: 192 = Good, 0 = Bad)
   - quality_str(): 품질 상태를 쉽게 확인할 수 있도록 문자열로 반환하는 메서드입니다.
- 반환예시
   ```python
   {
      "Tag1": TagMeasurement(value=24.5, timestamp=datetime(2024, 8, 1, 12, 0, 0), quality=192),
      "Tag2": TagMeasurement(value=15.3, timestamp=datetime(2024, 8, 1, 12, 5, 0), quality=0)
   }
   ```
- 데이터 활용 방법
  -  받은 데이터를 처리하려면 반환된 딕셔너리에서 태그 이름으로 해당 TagMeasurement 객체에 접근한 후, 필요한 속성 값(value, timestamp, quality)을 사용하면 됩니다.

   ```python
   # 예시: 최신 태그 값 가져오기
   current_values = connector.fetch_latest_values(["Tag1", "Tag2"])

   # "Tag1"의 측정값, 타임스탬프, 품질 상태를 가져오기
   tag1_measurement = current_values["Tag1"]

   # 값 출력
   print(f"Tag1 측정값: {tag1_measurement.value}")
   print(f"Tag1 시간: {tag1_measurement.timestamp}")
   print(f"Tag1 품질 상태: {tag1_measurement.quality_str()}")

   # "Tag2"의 값을 비슷한 방식으로 사용할 수 있습니다.
   ```

## 주요 기능
- `check_connection()`: DataParc 시스템과의 연결 상태 확인
- `fetch_latest_values(tag_list)`: 여러 태그의 최신 값을 조회
- `fetch_raw_data(tag_list, start_time, end_time)`: 특정 시간 범위 내의 원시 데이터를 조회
- `fetch_interpolated_data(tag_list, start_time, end_time, step_size, aggregate)`: 보간된 데이터를 조회
- `fetch_data_at_times(tag_list, timestamps)`: 특정 시점의 데이터를 조회


### 예외 처리

이 라이브러리는 두 가지 주요 예외를 사용합니다:

DatabaseError: 데이터베이스 관련 오류 발생 시 발생합니다.
UnexpectedError: 예상치 못한 오류 발생 시 발생합니다.

## 테스트 실행

테스트를 실행하려면 다음 명령을 사용하세요.
   ```bash
   python -m unittest discover tests
   ```

테스트는 다음과 같은 사항을 확인합니다:
  - 연결 상태 확인
  - 최신 값 조회
  - 원시 데이터 조회
  - 보간된 데이터 조회
  - 특정 시점의 데이터 조회
  - 예외 상황 처리 (빈 태그 리스트, 잘못된 시간 범위 등)

## 라이선스
이 프로젝트는 MIT 라이선스하에 배포됩니다.