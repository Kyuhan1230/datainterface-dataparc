# DataInterface - DataParc

이 프로젝트는 DataParc시스템과 상호작용하는 Python 클래스를 제공하여, 태그 데이터를 쉽게 조회하고 관리할 수 있도록 도와줍니다.

## 설치 방법

1. 프로젝트를 클론합니다.
   ```bash
   git clone https://github.com/kyuhan1230/datainterface-dataparc.git
   ```
   
2. 필요한 패키지를 설치합니다.
   ```bash
   cd my_dataparc_project
   ```

3. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

4. .env 파일을 설정합니다.
   ```bash
   DATAPARC_SERVER=your_server_address
   DATAPARC_USERNAME=your_username
   DATAPARC_PASSWORD=your_password
   DATAPARC_SITE_ABBREVIATION=your_site_abbreviation
   DATAPARC_TIMEZONE=your_timezone
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

## 주요 기능
- check_connection(): DataParc 시스템과의 연결 상태를 확인합니다.
- fetch_latest_values(tag_list): 여러 태그의 최신 값을 조회합니다.
- fetch_raw_data(tag_list, start_time, end_time): 특정 시간 범위 내의 원시 데이터를 조회합니다.
- fetch_interpolated_data(tag_list, start_time, end_time, step_size, aggregate): 보간된 데이터를 조회합니다.
- fetch_data_at_times(tag_list, timestamps): 특정 시점의 데이터를 조회합니다.

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