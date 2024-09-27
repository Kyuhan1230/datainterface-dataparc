# Copyright (c) 2024 KyuHan Seok
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# dataparc/connect_dataparc.py

import os
import pymssql
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo


def create_response(status_code: int, result: Any, message: str) -> Dict[str, Any]:
    """표준화된 API 응답 형식을 생성하는 함수

    Args:
        status_code (int): 상태 코드
        result (Any): 결과 데이터
        message (str): 응답 메시지

    Returns:
        Dict[str, Any]: 응답 딕셔너리
    """
    return {
        "status_code": status_code,
        "result": result,
        "message": message
    }

@dataclass
class DataTag:
    """데이터 태그 정보를 나타내는 데이터 클래스"""
    id: str
    description: str
    units: str

@dataclass
class TagMeasurement:
    """태그의 측정값과 관련 정보를 저장하는 데이터 클래스"""
    value: float
    timestamp: datetime
    quality: int

    def quality_str(self) -> str:
        """품질 값을 문자열로 반환

        Returns:
            str: 품질 상태 문자열
        """
        if self.quality == 192:
            return 'Good'
        elif self.quality == 0:
            return 'Bad'
        else:
            return 'Unknown'

    def __str__(self):
        """측정값의 문자열 표현

        Returns:
            str: 측정값의 문자열 표현
        """
        return f"{self.value:.2f} at {self.timestamp:%m/%d/%y %H:%M:%S %z} (S:{self.quality_str()})"

    def __repr__(self):
        """객체의 표현을 반환

        Returns:
            str: 객체의 문자열 표현
        """
        return self.__str__()

class DatabaseError(Exception):
    """데이터베이스 관련 오류를 위한 사용자 정의 예외"""
    pass

class UnexpectedError(Exception):
    """예상치 못한 오류를 위한 사용자 정의 예외"""
    pass


class DataParcConnector:
    """DataParc 시스템과 상호작용하기 위한 커넥터 클래스"""

    def __init__(
        self,
        site_abbreviation: Optional[str] = None,
        server: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timezone: Optional[str] = None,
        database: str = 'ctc_config'
    ):
        """DataParcConnector 초기화

        Args:
            site_abbreviation (Optional[str], optional): 사이트 약어. Defaults to None.
            server (Optional[str], optional): 데이터베이스 서버 주소. Defaults to None.
            user (Optional[str], optional): 데이터베이스 사용자 이름. Defaults to None.
            password (Optional[str], optional): 데이터베이스 비밀번호. Defaults to None.
            timezone (Optional[str], optional): 시간대 정보. Defaults to None.
            database (str, optional): 데이터베이스 이름. Defaults to 'ctc_config'.
        """
        self.server = server or os.environ.get('DATAPARC_SERVER')
        self.user = user or os.environ.get('DATAPARC_USERNAME')
        self.password = password or os.environ.get('DATAPARC_PASSWORD')
        self.database = database
        self.abbreviation = site_abbreviation or os.environ.get('DATAPARC_SITE_ABBREVIATION')
        self.timezone = ZoneInfo(timezone or os.environ.get('DATAPARC_TIMEZONE', "UTC"))

        if not self.server or not self.user or not self.password:
            raise ValueError("Database connection information is incomplete. Please check the environment variables.")

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """안전하게 쿼리를 실행하고 결과를 반환하는 내부 메서드

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, optional): 쿼리에 사용될 파라미터 튜플. Defaults to ().

        Returns:
            List[Dict[str, Any]]: 쿼리 결과의 리스트

        Raises:
            DatabaseError: 데이터베이스 관련 오류 발생 시
            UnexpectedError: 예기치 못한 오류 발생 시
        """
        try:
            with pymssql.connect(self.server, self.user, self.password, self.database) as conn:
                with conn.cursor(as_dict=True) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except pymssql.Error as e:
            error_message = f"Database error occurred: {str(e)}"
            raise DatabaseError(error_message) from e
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            raise UnexpectedError(error_message) from e

    def check_connection(self) -> Dict[str, Any]:
        """DataParc 시스템의 연결 상태를 확인하는 함수

        Returns:
            Dict[str, Any]: 연결 상태에 대한 응답 딕셔너리
        """
        try:
            self._execute_query("SELECT 1")
            return create_response(200, None, "Connection successful")
        except DatabaseError as e:
            return create_response(500, None, f"Database connection failed: {str(e)}")
        except UnexpectedError as e:
            return create_response(500, None, f"Unexpected error during connection check: {str(e)}")

    def fetch_latest_values(self, tag_list: Iterable[str]) -> Dict[str, Any]:
        """여러 태그에 대한 최신값을 가져오는 함수

        Args:
            tag_list (Iterable[str]): 조회할 태그의 리스트

        Returns:
            Dict[str, Any]: 태그별 최신값을 담은 딕셔너리
        """
        if not tag_list:
            return create_response(400, None, "Tag list cannot be empty")

        tag_string = ",".join(tag_list)
        query = "SELECT tagName, timestamp, value, quality FROM ctc_fn_PARCdata_ReadLastTags (%s, ',')"

        try:
            results = self._execute_query(query, (tag_string,))
            result_data = {
                r['tagName']: TagMeasurement(
                    r['value'],
                    r['timestamp'].replace(tzinfo=self.timezone),
                    r['quality']
                )
                for r in results
            }
            return create_response(200, result_data, "Successfully fetched latest values")
        except DatabaseError as e:
            return create_response(500, None, f"Database error while fetching latest values: {str(e)}")
        except UnexpectedError as e:
            return create_response(500, None, f"Unexpected error while fetching latest values: {str(e)}")

    def fetch_raw_data(
        self,
        tag_list: Iterable[str],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """여러 태그에 대한 특정 시간 범위 내의 원시 데이터를 가져오는 함수

        Args:
            tag_list (Iterable[str]): 조회할 태그의 리스트
            start_time (datetime): 시작 시간
            end_time (datetime): 종료 시간

        Returns:
            Dict[str, Any]: 태그별 원시 데이터를 담은 딕셔너리
        """
        if not tag_list:
            return create_response(400, None, "Tag list cannot be empty")
        if start_time >= end_time:
            return create_response(400, None, "Start time must be before end time")

        tag_string = ",".join(tag_list)
        query = "SELECT tagName, timestamp, value, quality FROM ctc_fn_PARCdata_ReadRawTags (%s, %s, %s, 1, ',')"

        try:
            results = self._execute_query(query, (tag_string, start_time, end_time))
            data = {}
            for r in results:
                if r['tagName'] not in data:
                    data[r['tagName']] = []
                data[r['tagName']].append(
                    TagMeasurement(
                        r['value'],
                        r['timestamp'].replace(tzinfo=self.timezone),
                        r['quality']
                    )
                )
            return create_response(200, data, "Successfully fetched raw data")
        except DatabaseError as e:
            return create_response(500, None, f"Database error while fetching raw data: {str(e)}")
        except UnexpectedError as e:
            return create_response(500, None, f"Unexpected error while fetching raw data: {str(e)}")

    def fetch_interpolated_data(
        self,
        tag_list: Iterable[str],
        start_time: datetime,
        end_time: datetime,
        step_size: int,
        aggregate: str
    ) -> Dict[str, Any]:
        """여러 태그에 대한 특정 시간 범위 내의 보간된 데이터를 가져오는 함수

        Args:
            tag_list (Iterable[str]): 조회할 태그의 리스트
            start_time (datetime): 시작 시간
            end_time (datetime): 종료 시간
            step_size (int): 스텝 크기(초 단위)
            aggregate (str): 집계 방법 (예: 'AVERAGE', 'MIN', 'MAX')

        Returns:
            Dict[str, Any]: 태그별 보간된 데이터를 담은 딕셔너리
        """
        if not tag_list:
            return create_response(400, None, "Tag list cannot be empty")

        if start_time >= end_time:
            return create_response(400, None, "Start time must be before end time")

        if step_size <= 0:
            return create_response(400, None, "Step size must be greater than zero")

        tag_string = ",".join(tag_list)
        query = ("SELECT tagName, timestamp, value, quality "
                 "FROM ctc_fn_PARCdata_ReadInterpolatedTags (%s, %s, %s, %s, %s, ',')")

        try:
            results = self._execute_query(
                query,
                (tag_string, start_time, end_time, aggregate, step_size)
            )
            data = {}
            for r in results:
                if r['tagName'] not in data:
                    data[r['tagName']] = []
                data[r['tagName']].append(
                    TagMeasurement(
                        r['value'],
                        r['timestamp'].replace(tzinfo=self.timezone),
                        r['quality']
                    )
                )
            return create_response(200, data, "Successfully fetched interpolated data")
        except DatabaseError as e:
            return create_response(500, None, f"Database error while fetching interpolated data: {str(e)}")
        except UnexpectedError as e:
            return create_response(500, None, f"Unexpected error while fetching interpolated data: {str(e)}")

    def fetch_data_at_times(
        self,
        tag_list: Iterable[str],
        timestamps: Iterable[datetime]
    ) -> Dict[str, Any]:
        """여러 태그에 대한 특정 시점의 데이터를 가져오는 함수

        Args:
            tag_list (Iterable[str]): 조회할 태그의 리스트
            timestamps (Iterable[datetime]): 조회할 타임스탬프 리스트

        Returns:
            Dict[str, Any]: 태그별 특정 시점의 데이터를 담은 딕셔너리
        """
        if not tag_list:
            return create_response(400, None, "Tag list cannot be empty")

        if not timestamps:
            return create_response(400, None, "Timestamps list cannot be empty")

        tag_string = ",".join(tag_list)
        timestamp_string = ",".join([ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps])
        query = "SELECT tagName, timestamp, value, quality FROM ctc_fn_PARCdata_ReadAtTimeTags (%s, %s, ',')"

        try:
            results = self._execute_query(query, (tag_string, timestamp_string))
            data = {}
            for r in results:
                if r['tagName'] not in data:
                    data[r['tagName']] = []
                data[r['tagName']].append(
                    TagMeasurement(
                        r['value'],
                        r['timestamp'].replace(tzinfo=self.timezone),
                        r['quality']
                    )
                )
            return create_response(200, data, "Successfully fetched data at specified times")
        except DatabaseError as e:
            return create_response(500, None, f"Database error while fetching data at specified times: {str(e)}")
        except UnexpectedError as e:
            return create_response(500, None, f"Unexpected error while fetching data at specified times: {str(e)}")
