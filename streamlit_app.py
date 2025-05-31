"""
취업 현황 분석 시스템 (Employment Status Analysis System)
PRD 요구사항에 따른 Streamlit 기반 대시보드 구현
버전: 2.0 (리팩토링된 버전)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import warnings
import time
from datetime import datetime
warnings.filterwarnings('ignore')

# =====================
# 상수 정의 및 설정
# =====================

# 앱 설정
CONFIG = {
    'page_title': "취업 현황 분석 대시보드",
    'page_icon': "📊",
    'layout': "wide",
    'initial_sidebar_state': "expanded"
}

# 데이터 설정
DATA_CONFIG = {
    'file_path': "졸업자취업현황_20_21_22_23.csv",
    'cache_ttl': 3600,  # 1시간
    'exclude_categories': ['진학', '외국인'],
    'min_year': 2000,
    'encoding_options': ['utf-8', 'cp949']
}

# 앱 메타데이터
APP_META = {
    'title': "📊 취업 현황 분석 대시보드",
    'subtitle': "Employment Status Analysis Dashboard",
    'version': "v2.0",
    'period': "2020년 ~ 2023년",
    'target': "학부 졸업자 (진학자/외국인 제외)"
}

# 색상 팔레트
COLORS = {
    'primary': '#007bff',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# =====================
# 유틸리티 함수
# =====================

def init_app():
    """앱 초기 설정"""
    st.set_page_config(**CONFIG)

def load_css():
    """CSS 스타일 로드"""
    css = f"""
    <style>
        .main-header {{
            text-align: center;
            padding: 1rem 0;
            background: linear-gradient(90deg, {COLORS['primary']} 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, {COLORS['light']} 0%, #e9ecef 100%);
            padding: 1.2rem;
            border-radius: 12px;
            border-left: 4px solid {COLORS['primary']};
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .insight-box {{
            background: linear-gradient(135deg, #e8f4f8 0%, #d1ecf1 100%);
            padding: 1.2rem;
            border-radius: 12px;
            border-left: 4px solid {COLORS['info']};
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .status-box {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid;
        }}
        
        .success-box {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left-color: {COLORS['success']};
        }}
        
        .warning-box {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border-left-color: {COLORS['warning']};
        }}
        
        .error-box {{
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-left-color: {COLORS['danger']};
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            background-color: {COLORS['light']};
            padding: 8px;
            border-radius: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: #f1f3f4;
            border-color: {COLORS['primary']};
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, #0056b3 100%);
            color: white;
            border-color: {COLORS['primary']};
            box-shadow: 0 2px 4px rgba(0,123,255,0.3);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def show_progress(text: str, progress: int):
    """진행률 표시 헬퍼"""
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = st.progress(0)
        st.session_state.status_text = st.empty()
    
    st.session_state.status_text.text(text)
    st.session_state.progress_bar.progress(progress)

def cleanup_progress():
    """진행률 표시 정리"""
    if 'progress_bar' in st.session_state:
        st.session_state.progress_bar.progress(100)
        time.sleep(0.5)
        st.session_state.progress_bar.empty()
        st.session_state.status_text.empty()
        del st.session_state.progress_bar
        del st.session_state.status_text

def format_number(num: int) -> str:
    """숫자 포맷팅"""
    return f"{num:,}"

def calculate_rate(numerator: int, denominator: int) -> float:
    """비율 계산"""
    return round((numerator / denominator * 100), 1) if denominator > 0 else 0.0

# =====================
# 메시지 및 UI 헬퍼
# =====================

def show_message(message: str, msg_type: str = "info"):
    """스타일된 메시지 표시"""
    icon_map = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️'
    }
    
    icon = icon_map.get(msg_type, 'ℹ️')
    class_name = f"{msg_type}-box"
    
    st.markdown(f'''
    <div class="status-box {class_name}">
        {icon} {message}
    </div>
    ''', unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: Optional[str] = None):
    """메트릭 카드 생성"""
    delta_html = f"<small style='color: #6c757d;'>{delta}</small>" if delta else ""
    
    st.markdown(f'''
    <div class="metric-card">
        <h4 style="margin: 0; color: {COLORS['dark']};">{title}</h4>
        <h2 style="margin: 0.5rem 0; color: {COLORS['primary']};">{value}</h2>
        {delta_html}
    </div>
    ''', unsafe_allow_html=True)

def safe_divide(numerator, denominator, default=0):
    """안전한 나눗셈"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

# =====================
# 데이터 클래스
# =====================
@dataclass
class EmploymentStats:
    """취업 통계 정보를 저장하는 데이터 클래스"""
    total: int = 0
    employed: int = 0
    unemployed: int = 0
    employment_rate: float = 0.0
    year: Optional[str] = None
    
    @property
    def employment_rate_str(self) -> str:
        return f"{self.employment_rate:.1f}%"

@dataclass
class TrendAnalysis:
    """트렌드 분석 결과를 저장하는 데이터 클래스"""
    best_year: str = ""
    worst_year: str = ""
    best_rate: float = 0.0
    worst_rate: float = 0.0
    average_rate: float = 0.0
    trend_direction: str = ""
    
    @property
    def trend_emoji(self) -> str:
        if self.trend_direction == "상승":
            return "📈"
        elif self.trend_direction == "하락":
            return "📉"
        else:
            return "📊"

# =====================
# 데이터 처리 클래스 (리팩토링된 버전)
# =====================
class EmploymentDataProcessor:
    """취업 현황 데이터 로더 및 전처리 (리팩토링된 버전)"""
    
    def __init__(self, file_path: str = DATA_CONFIG['file_path']):
        self.file_path = file_path
        self.raw_df: Optional[pd.DataFrame] = None
        self.df: Optional[pd.DataFrame] = None
        self.employed_df: Optional[pd.DataFrame] = None
        self.data_quality_report: Dict = {}
        
    def load_data(self) -> bool:
        """CSV 파일을 읽고 기본 전처리 수행"""
        try:
            # 캐시된 데이터 로드 시도
            cached_data = self._load_cached_data(self.file_path)
            if cached_data is not None:
                self.df, self.employed_df, self.raw_df, self.data_quality_report = cached_data
                show_message(f"✅ 캐시된 데이터 로드 완료: 총 {len(self.df):,}건", "success")
                return True
            
            show_progress("📂 파일 읽는 중...", 10)
            
            # 파일 존재 확인
            if not self._check_file_exists():
                return False
            
            # 데이터 읽기
            df = self._read_csv_with_encoding()
            if df is None:
                return False
                
            show_progress("🔍 데이터 검증 중...", 30)
            
            # 데이터 검증 및 품질 리포트 생성
            self.raw_df = df.copy()
            self.data_quality_report = self._generate_quality_report(df)
            
            if not self._validate_data(df):
                return False
            
            show_progress("🧹 데이터 정제 중...", 50)
            
            # 데이터 필터링 및 정제
            df_filtered = self._filter_data(df)
            df_cleaned = self._clean_data(df_filtered)
            
            show_progress("📊 최종 처리 중...", 80)
            
            # 최종 데이터 저장
            self.df = df_cleaned
            self.employed_df = df_cleaned[df_cleaned['취업구분1'] == '취업'].copy()
            
            # 데이터 캐시 저장
            self._save_cached_data(self.df, self.employed_df, self.raw_df, self.data_quality_report)
            
            cleanup_progress()
            show_message(f"✅ 데이터 로드 완료: 총 {len(df_cleaned):,}건", "success")
            
            return True
            
        except Exception as e:
            cleanup_progress()
            show_message(f"❌ 데이터 로드 실패: {str(e)}", "error")
            st.error(f"상세 오류: {str(e)}")
            return False
    
    def _load_cached_data(self, file_path: str) -> Optional[Tuple]:
        """세션 상태에서 캐시된 데이터 로드"""
        try:
            # 세션 상태에서 캐시 확인
            if 'cached_data' not in st.session_state:
                return None
            
            cached = st.session_state['cached_data']
            
            # 캐시 유효성 검사
            if not os.path.exists(file_path):
                return None
            
            # 파일 수정 시간과 캐시 시간 비교
            file_mtime = os.path.getmtime(file_path)
            cache_time = cached.get('timestamp', 0)
            
            # 파일이 캐시보다 최신이면 캐시 무효화
            if file_mtime > cache_time:
                return None
            
            # 캐시 TTL 확인 (1시간)
            current_time = time.time()
            if current_time - cache_time > DATA_CONFIG['cache_ttl']:
                return None
            
            # 캐시된 데이터 반환
            return (
                cached['df'],
                cached['employed_df'], 
                cached['raw_df'],
                cached['quality_report']
            )
            
        except Exception as e:
            st.warning(f"캐시 로드 중 오류: {str(e)}")
            return None
    
    def _save_cached_data(self, df: pd.DataFrame, employed_df: pd.DataFrame, 
                         raw_df: pd.DataFrame, quality_report: Dict):
        """처리된 데이터를 세션 상태에 캐시"""
        st.session_state['cached_data'] = {
            'df': df,
            'employed_df': employed_df,
            'raw_df': raw_df,
            'quality_report': quality_report,
            'timestamp': time.time()
        }
    
    def _check_file_exists(self) -> bool:
        """파일 존재 확인 및 경로 처리"""
        # 현재 작업 디렉토리 확인
        current_dir = os.getcwd()
        
        # 절대 경로로 변환
        if not os.path.isabs(self.file_path):
            abs_path = os.path.join(current_dir, self.file_path)
        else:
            abs_path = self.file_path
        
        if not os.path.exists(abs_path):
            # 대안 경로들 시도
            alternative_paths = [
                self.file_path,
                os.path.join(current_dir, self.file_path),
                os.path.join(current_dir, 'data', self.file_path),
                os.path.join(os.path.dirname(__file__), self.file_path),
                os.path.join(os.path.dirname(__file__), 'data', self.file_path)
            ]
            
            for path in alternative_paths:
                if os.path.exists(path):
                    self.file_path = path               
                    return True
            
            # 파일을 찾지 못한 경우
            show_message(f"📁 '{self.file_path}' 파일을 찾을 수 없습니다.", "error")
            st.error(f"""
            **파일을 찾을 수 없습니다.**
            
            시도한 경로들:
            {chr(10).join(f"- {path}" for path in alternative_paths)}
            
            **해결 방법:**
            1. 파일이 올바른 위치에 있는지 확인하세요
            2. 파일명이 정확한지 확인하세요 ('{os.path.basename(self.file_path)}')
            3. 현재 작업 디렉토리: {current_dir}
            """)
            return False
        
        self.file_path = abs_path        
        return True
    
    def _read_csv_with_encoding(self) -> Optional[pd.DataFrame]:
        """인코딩을 시도하며 CSV 파일 읽기 (개선된 버전)"""
        last_error = None
        
        for encoding in DATA_CONFIG['encoding_options']:
            try:
                # 파일 크기 확인
                file_size = os.path.getsize(self.file_path)
                if file_size == 0:
                    show_message("❌ 파일이 비어있습니다.", "error")
                    return None              
                
                
                # CSV 파일 읽기 (추가 옵션 포함)
                df = pd.read_csv(
                    self.file_path, 
                    encoding=encoding,
                    low_memory=False,  # 데이터 타입 추론 개선
                    na_values=['', 'NA', 'N/A', 'null', 'NULL', 'nan', 'NaN'],  # 결측값 처리
                    keep_default_na=True
                )
                
                if df.empty:
                    show_message("⚠️ 파일에서 데이터를 읽을 수 없습니다.", "warning")
                    return None                
                
                return df
                
            except UnicodeDecodeError as e:
                last_error = f"인코딩 오류 ({encoding}): {str(e)}"
                continue
            except pd.errors.EmptyDataError:
                show_message("❌ 파일에 데이터가 없습니다.", "error")
                return None
            except pd.errors.ParserError as e:
                last_error = f"파싱 오류 ({encoding}): {str(e)}"
                continue
            except Exception as e:
                last_error = f"예상치 못한 오류 ({encoding}): {str(e)}"
                continue
        
        show_message(f"❌ 지원되는 인코딩으로 파일을 읽을 수 없습니다.", "error")
        if last_error:
            st.error(f"마지막 오류: {last_error}")
        
        return None
    
    def _filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """진학자, 외국인 등 제외 대상 필터링"""
        original_count = len(df)
        
        # 제외 대상 필터링
        excluded_mask = df['취업구분1'].isin(DATA_CONFIG['exclude_categories'])
        excluded_count = excluded_mask.sum()
        
        df_filtered = df[~excluded_mask].copy()
        
        if excluded_count > 0:
            show_message(f"🔄 제외 대상 {excluded_count:,}건 필터링 완료 "
                        f"(진학자: {(df['취업구분1'] == '진학').sum():,}명, "
                        f"외국인: {(df['취업구분1'] == '외국인').sum():,}명)", "info")
        
        return df_filtered
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        """상세한 데이터 유효성 검증"""
        # 필수 컬럼 확인
        required_columns = ['조사년도', '취업구분', '취업구분1']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ 필수 컬럼이 누락되었습니다: {missing_columns}")
            return False
        
        # 데이터 타입 검증
        if not pd.api.types.is_numeric_dtype(df['조사년도']):
            try:
                df['조사년도'] = pd.to_numeric(df['조사년도'], errors='coerce')
                if df['조사년도'].isnull().any():
                    st.warning("⚠️ 일부 조사년도 데이터가 올바르지 않습니다.")
            except:
                st.error("❌ 조사년도 컬럼의 데이터 타입이 올바르지 않습니다.")
                return False
        
        # 년도 범위 검증
        current_year = datetime.now().year
        if df['조사년도'].min() < DATA_CONFIG['min_year'] or df['조사년도'].max() > current_year:
            st.warning(f"⚠️ 조사년도 범위가 예상과 다릅니다: {df['조사년도'].min()}-{df['조사년도'].max()}")
        
        # 빈 데이터 확인
        if len(df) == 0:
            st.error("❌ 데이터가 비어있습니다.")
            return False
        
        return True
    
    def _generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """데이터 품질 보고서 생성 (개선된 버전)"""
        try:
            # 결측값 계산
            missing_values = df.isnull().sum()
            total_cells = len(df) * len(df.columns)
            missing_cells = missing_values.sum()
            completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
            
            # 데이터 품질 지표 계산
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            
            report = {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'completeness': round(completeness, 2),
                'missing_data': missing_values.to_dict(),
                'missing_values': missing_values[missing_values > 0].to_dict(),  # 결측값이 있는 컬럼만
                'duplicate_records': df.duplicated().sum(),
                'data_types': df.dtypes.astype(str).to_dict(),
                'unique_values': {col: df[col].nunique() for col in df.columns},
                'numeric_columns': numeric_columns,
                'categorical_columns': categorical_columns,
                'year_range': (int(df['조사년도'].min()), int(df['조사년도'].max())) if '조사년도' in df.columns else None,
                'memory_usage': df.memory_usage(deep=True).sum(),
                'file_size': os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0,
                'processing_time': time.time()
            }
            
            # 데이터 품질 점수 계산 (0-100)
            quality_score = self._calculate_quality_score(df, report)
            report['quality_score'] = quality_score
            
            return report
        except Exception as e:
            st.warning(f"품질 보고서 생성 중 오류: {str(e)}")
            return {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'error': str(e)
            }
    
    def _calculate_quality_score(self, df: pd.DataFrame, report: Dict) -> int:
        """데이터 품질 점수 계산 (0-100)"""
        try:
            score = 100
            
            # 완성도 점수 (40점 만점)
            completeness_score = min(40, report['completeness'] * 0.4)
            
            # 중복 데이터 점수 (20점 만점)
            duplicate_ratio = report['duplicate_records'] / report['total_records']
            duplicate_score = max(0, 20 - (duplicate_ratio * 100))
            
            # 데이터 일관성 점수 (20점 만점)
            consistency_score = 20
            if '조사년도' in df.columns:
                year_consistency = df['조사년도'].notna().sum() / len(df)
                consistency_score = min(20, year_consistency * 20)
            
            # 데이터 다양성 점수 (20점 만점)
            if '취업구분1' in df.columns:
                diversity_ratio = df['취업구분1'].nunique() / len(df) if len(df) > 0 else 0
                diversity_score = min(20, diversity_ratio * 100 * 20)
            else:
                diversity_score = 10
            
            total_score = completeness_score + duplicate_score + consistency_score + diversity_score
            return int(min(100, max(0, total_score)))
            
        except Exception:
            return 50  # 기본 점수
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정제 및 표준화 (개선된 버전)"""
        df = df.copy()
        
        # 조사년도 정제 - .5년도 제거
        if '조사년도' in df.columns:
            # 숫자로 변환하고 정수부분만 사용 (예: 2020.5 -> 2020)
            df['조사년도'] = pd.to_numeric(df['조사년도'], errors='coerce')
            df['조사년도'] = df['조사년도'].apply(lambda x: int(x) if pd.notna(x) and x == int(x) else int(x) if pd.notna(x) else x)
            # .5년도 데이터 제거 (정수가 아닌 연도)
            df = df[df['조사년도'].apply(lambda x: pd.notna(x) and float(x).is_integer())].copy()
            df['조사년도'] = df['조사년도'].astype(int)
        
        # 기업지역 정제 및 표준화
        if '기업지역' in df.columns:
            df['기업지역'] = df['기업지역'].fillna('미상')
            df['기업지역'] = df['기업지역'].astype(str).str.strip()
            
            # 지역명 표준화 (더 포괄적)
            region_mapping = {
                '서울특별시': '서울', '서울시': '서울',
                '부산광역시': '부산', '부산시': '부산',
                '대구광역시': '대구', '대구시': '대구',
                '인천광역시': '인천', '인천시': '인천',
                '광주광역시': '광주', '광주시': '광주',
                '대전광역시': '대전', '대전시': '대전',
                '울산광역시': '울산', '울산시': '울산',
                '경기도': '경기', '강원도': '강원', '강원특별자치도': '강원',
                '충청북도': '충북', '충북': '충북',
                '충청남도': '충남', '충남': '충남',
                '전라북도': '전북', '전북': '전북',
                '전라남도': '전남', '전남': '전남',
                '경상북도': '경북', '경북': '경북',
                '경상남도': '경남', '경남': '경남',
                '제주특별자치도': '제주', '제주도': '제주', '제주': '제주'
            }
            df['기업지역'] = df['기업지역'].replace(region_mapping)
        
        # 기업구분 정제 및 표준화
        if '기업구분' in df.columns:
            df['기업구분'] = df['기업구분'].fillna('미분류')
            df['기업구분'] = df['기업구분'].astype(str).str.strip()
            
            # 기업구분 표준화 (더 포괄적)
            company_mapping = {
                '대기업': '대기업', '대': '대기업',
                '중견기업': '중견기업', '중견': '중견기업',
                '중소기업': '중소기업', '중소': '중소기업',
                '공공기관': '공공기관', '공기업': '공공기관', '공공': '공공기관',
                '외국계기업': '외국계기업', '외국계': '외국계기업',
                '비영리단체': '비영리기관', '비영리법인': '비영리기관', 
                '비영리': '비영리기관', '학교': '교육기관', '대학교': '교육기관'
            }
            df['기업구분'] = df['기업구분'].replace(company_mapping)
        
        # 회사명 정제
        if '국내진학학교명/국내기업명' in df.columns:
            df['회사명_정제'] = df['국내진학학교명/국내기업명'].fillna('미상')
            df['회사명_정제'] = df['회사명_정제'].astype(str).str.strip()
            
            # 회사명에서 그룹사 정보 추출 (예: 삼성전자 -> 삼성그룹)
            major_groups = {
                '삼성': '삼성그룹', 'LG': 'LG그룹', '현대': '현대그룹', 
                'SK': 'SK그룹', '롯데': '롯데그룹', '한화': '한화그룹',
                'CJ': 'CJ그룹', '네이버': '네이버', '카카오': '카카오',
                'KT': 'KT그룹', '포스코': '포스코그룹'
            }
            
            df['기업그룹'] = '기타'
            for keyword, group_name in major_groups.items():
                mask = df['회사명_정제'].str.contains(keyword, case=False, na=False)
                df.loc[mask, '기업그룹'] = group_name
        
        # 전공일치여부 정제
        if '전공일치여부' in df.columns:
            df['전공일치여부'] = df['전공일치여부'].fillna('미상')
            # Y/N을 한글로 변환
            match_mapping = {'Y': '일치', 'N': '불일치', 'y': '일치', 'n': '불일치'}
            df['전공일치여부'] = df['전공일치여부'].replace(match_mapping)
        
        return df
    
    def get_overall_stats(self) -> EmploymentStats:
        """전체 취업 통계 계산"""
        if self.df is None:
            return EmploymentStats()
            
        total = len(self.df)
        employed = len(self.employed_df) if self.employed_df is not None else 0
        unemployed = total - employed
        employment_rate = (employed / total * 100) if total > 0 else 0
        
        return EmploymentStats(total, employed, unemployed, employment_rate)
    
    def get_yearly_stats(self) -> pd.DataFrame:
        """연도별 취업 통계 계산"""
        if self.df is None:
            return pd.DataFrame()
            
        yearly_stats = self.df.groupby('조사년도').agg({
            '학번': 'count',
            '취업구분1': lambda x: (x == '취업').sum()
        }).reset_index()
        
        yearly_stats.columns = ['연도', '전체인원', '취업자수']
        yearly_stats['미취업자수'] = yearly_stats['전체인원'] - yearly_stats['취업자수']
        yearly_stats['취업률'] = (yearly_stats['취업자수'] / yearly_stats['전체인원'] * 100).round(1)
        
        return yearly_stats
    
    def get_regional_stats(self) -> pd.DataFrame:
        """지역별 취업 통계 계산"""
        if self.employed_df is None or '기업지역' not in self.employed_df.columns:
            return pd.DataFrame()
            
        regional_stats = self.employed_df['기업지역'].value_counts().reset_index()
        regional_stats.columns = ['지역', '취업자수']
        
        total = regional_stats['취업자수'].sum()
        regional_stats['비율'] = (regional_stats['취업자수'] / total * 100).round(1)
        
        return regional_stats
    
    def get_company_stats(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """기업 유형별 및 규모별 취업 통계 계산"""
        company_type_stats = pd.DataFrame()
        company_size_stats = pd.DataFrame()
        
        if self.employed_df is not None:
            # 기업 유형별 통계
            if '기업구분' in self.employed_df.columns:
                company_type_stats = self.employed_df['기업구분'].value_counts().reset_index()
                company_type_stats.columns = ['기업구분', '취업자수']
                total = company_type_stats['취업자수'].sum()
                company_type_stats['비율'] = (company_type_stats['취업자수'] / total * 100).round(1)
            
            # 회사 규모별 통계
            if '회사구분' in self.employed_df.columns:
                company_size_stats = self.employed_df['회사구분'].value_counts().reset_index()
                company_size_stats.columns = ['회사규모', '취업자수']
                total = company_size_stats['취업자수'].sum()
                company_size_stats['비율'] = (company_size_stats['취업자수'] / total * 100).round(1)
        
        return company_type_stats, company_size_stats
    
    def get_trend_analysis(self) -> TrendAnalysis:
        """트렌드 분석 수행"""
        yearly_stats = self.get_yearly_stats()
        
        if yearly_stats.empty:
            return TrendAnalysis()
        
        best_idx = yearly_stats['취업률'].idxmax()
        worst_idx = yearly_stats['취업률'].idxmin()
        
        best_year = str(yearly_stats.loc[best_idx, '연도'])
        worst_year = str(yearly_stats.loc[worst_idx, '연도'])
        best_rate = yearly_stats.loc[best_idx, '취업률']
        worst_rate = yearly_stats.loc[worst_idx, '취업률']
        average_rate = yearly_stats['취업률'].mean()
        
        # 트렌드 방향 계산 (최근 2년 비교)
        if len(yearly_stats) >= 2:
            recent_change = yearly_stats.iloc[-1]['취업률'] - yearly_stats.iloc[-2]['취업률']
            if recent_change > 1:
                trend_direction = "상승"
            elif recent_change < -1:
                trend_direction = "하락"
            else:
                trend_direction = "보합"
        else:
            trend_direction = "데이터 부족"
        
        return TrendAnalysis(best_year, worst_year, best_rate, worst_rate, average_rate, trend_direction)

# =====================
# 시각화 함수
# =====================
class VisualizationModule:
    """시각화 관련 함수들을 관리하는 클래스"""
    
    @staticmethod
    def create_kpi_metrics(stats: EmploymentStats):
        """KPI 메트릭 카드 생성"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="🎓 전체 졸업자",
                value=f"{stats.total:,}명",
                help="진학자 및 외국인 제외"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="✅ 취업자",
                value=f"{stats.employed:,}명",
                delta=f"{stats.employment_rate:.1f}% 취업률"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="❌ 미취업자",
                value=f"{stats.unemployed:,}명",
                delta=f"{100-stats.employment_rate:.1f}% 미취업률"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            # 취업률에 따른 색상 결정
            rate_color = "🟢" if stats.employment_rate >= 80 else "🟡" if stats.employment_rate >= 60 else "🔴"
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label=f"{rate_color} 취업률",
                value=f"{stats.employment_rate:.1f}%"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def create_yearly_trend_chart(yearly_stats: pd.DataFrame) -> go.Figure:
        """연도별 취업률 트렌드 차트 생성"""
        # 연도를 정수로 변환
        yearly_stats_copy = yearly_stats.copy()
        yearly_stats_copy['연도'] = yearly_stats_copy['연도'].astype(int)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('연도별 취업률 추이', '연도별 취업자/미취업자 현황'),
            vertical_spacing=0.15,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # 취업률 라인 차트
        fig.add_trace(
            go.Scatter(
                x=yearly_stats_copy['연도'],
                y=yearly_stats_copy['취업률'],
                mode='lines+markers+text',
                name='취업률',
                text=[f"{rate}%" for rate in yearly_stats_copy['취업률']],
                textposition="top center",
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(size=10, color=COLORS['primary'])
            ),
            row=1, col=1
        )
        
        # 취업자/미취업자 스택 바 차트
        fig.add_trace(
            go.Bar(
                x=yearly_stats_copy['연도'],
                y=yearly_stats_copy['취업자수'],
                name='취업자',
                marker_color=COLORS['success'],
                text=yearly_stats_copy['취업자수'],
                textposition='inside'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=yearly_stats_copy['연도'],
                y=yearly_stats_copy['미취업자수'],
                name='미취업자',
                marker_color=COLORS['danger'],
                text=yearly_stats_copy['미취업자수'],
                textposition='inside'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            title_text="📈 연도별 취업 현황 분석",
            barmode='stack'
        )
        
        # X축을 정수로 표시하도록 설정
        fig.update_xaxes(
            title_text="연도", 
            tickformat='d',  # 정수 포맷
            dtick=1,  # 1년 간격
            tickmode='linear',
            row=1, col=1
        )
        fig.update_xaxes(
            title_text="연도", 
            tickformat='d',  # 정수 포맷
            dtick=1,  # 1년 간격
            tickmode='linear',
            row=2, col=1
        )
        fig.update_yaxes(title_text="취업률 (%)", row=1, col=1)
        fig.update_yaxes(title_text="인원 수", row=2, col=1)
        
        return fig
    
    @staticmethod
    def create_regional_chart(regional_stats: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
        """지역별 분석 차트 생성"""
        # 막대 차트
        bar_fig = px.bar(
            regional_stats.head(10),  # 상위 10개 지역만 표시
            x='지역',
            y='취업자수',
            text='비율',
            title='🗺️ 상위 10개 지역별 취업자 분포',
            labels={'취업자수': '취업자 수 (명)', '지역': '지역'},
            color='취업자수',
            color_continuous_scale='viridis'
        )
        bar_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        bar_fig.update_layout(height=400, showlegend=False)
        
        # 파이 차트 (상위 8개 지역 + 기타)
        top_regions = regional_stats.head(8)
        other_count = regional_stats.iloc[8:]['취업자수'].sum() if len(regional_stats) > 8 else 0
        
        if other_count > 0:
            other_row = pd.DataFrame({'지역': ['기타'], '취업자수': [other_count], '비율': [other_count/regional_stats['취업자수'].sum()*100]})
            pie_data = pd.concat([top_regions, other_row], ignore_index=True)
        else:
            pie_data = top_regions
        
        pie_fig = px.pie(
            pie_data,
            values='취업자수',
            names='지역',
            title='지역별 취업자 비율',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(height=400)
        
        return bar_fig, pie_fig
    
    @staticmethod
    def create_company_charts(company_type_stats: pd.DataFrame, company_size_stats: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
        """기업 분석 차트 생성"""
        type_fig = go.Figure()
        size_fig = go.Figure()
        
        if not company_type_stats.empty:
            type_fig = px.pie(
                company_type_stats,
                values='취업자수',
                names='기업구분',
                title='🏢 기업 유형별 취업자 분포',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            type_fig.update_traces(textposition='inside', textinfo='percent+label')
        
        if not company_size_stats.empty:
            size_fig = px.pie(
                company_size_stats,
                values='취업자수',
                names='회사규모',
                title='🏭 회사 규모별 취업자 분포',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            size_fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return type_fig, size_fig

# =====================
# UI 구성 함수
# =====================
def show_header():
    """헤더 섹션 표시"""
    st.markdown(f'''
    <div class="main-header">
        <h1>{APP_META['title']}</h1>
        <p>{APP_META['subtitle']}</p>
        <p>📅 분석 기간: {APP_META['period']} | 🎯 대상: {APP_META['target']}</p>
    </div>
    ''', unsafe_allow_html=True)

def show_insights(trend: TrendAnalysis, stats: EmploymentStats):
    """주요 인사이트 표시"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="insight-box">
            <h4>📊 주요 통계 인사이트</h4>
            <ul>
                <li><strong>최고 취업률:</strong> {trend.best_year}년 {trend.best_rate:.1f}%</li>
                <li><strong>최저 취업률:</strong> {trend.worst_year}년 {trend.worst_rate:.1f}%</li>
                <li><strong>평균 취업률:</strong> {trend.average_rate:.1f}%</li>
                <li><strong>최근 트렌드:</strong> {trend.trend_emoji} {trend.trend_direction}</li>
            </ul>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        # 취업률 평가
        if stats.employment_rate >= 80:
            status = "우수"
            color = COLORS['success']
            recommendation = "현재 수준을 유지하고 질적 향상에 집중하세요."
        elif stats.employment_rate >= 60:
            status = "양호"
            color = COLORS['warning']
            recommendation = "취업률 향상을 위한 추가 프로그램 검토가 필요합니다."
        else:
            status = "개선 필요"
            color = COLORS['danger']
            recommendation = "취업 지원 프로그램의 전면적인 검토와 개선이 시급합니다."
        
        st.markdown(f'''
        <div class="insight-box">
            <h4>💡 개선 방향 제안</h4>
            <p><strong>현재 상태:</strong> <span style="color: {color};">{status}</span></p>
            <p><strong>권장사항:</strong> {recommendation}</p>
        </div>
        ''', unsafe_allow_html=True)

def show_advanced_filters(processor: EmploymentDataProcessor):
    """고급 필터링 및 검색 인터페이스"""
    st.subheader("🔍 상세 데이터 탐색")
    
    if processor.employed_df is None:
        st.warning("취업자 데이터가 없습니다.")
        return
    
    # 필터 컨트롤
    col1, col2, col3 = st.columns(3)
    
    with col1:
        years = ['전체'] + sorted(processor.df['조사년도'].unique().tolist())
        selected_year = st.selectbox("📅 연도 선택", years)
    
    with col2:
        regions = ['전체'] + sorted(processor.employed_df['기업지역'].dropna().unique().tolist())
        selected_region = st.selectbox("🗺️ 지역 선택", regions)
    
    with col3:
        if '기업구분' in processor.employed_df.columns:
            company_types = ['전체'] + sorted(processor.employed_df['기업구분'].dropna().unique().tolist())
            selected_company_type = st.selectbox("🏢 기업유형 선택", company_types)
        else:
            selected_company_type = '전체'
    
    # 검색어 입력
    search_term = st.text_input("🔍 통합 검색 (회사명, 지역, 기업구분 등)", placeholder="검색어를 입력하세요...")
    
    # 데이터 필터링
    filtered_df = processor.employed_df.copy()
    
    if selected_year != '전체':
        filtered_df = filtered_df[filtered_df['조사년도'] == selected_year]
    
    if selected_region != '전체':
        filtered_df = filtered_df[filtered_df['기업지역'] == selected_region]
    
    if selected_company_type != '전체' and '기업구분' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['기업구분'] == selected_company_type]
    
    if search_term:
        mask = filtered_df.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # 결과 표시
    st.write(f"📋 검색 결과: **{len(filtered_df):,}건** (전체 {len(processor.employed_df):,}건 중)")
    
    if not filtered_df.empty:
        # 표시할 컬럼 선택
        display_columns = ['조사년도', '취업구분1']
        if '국내진학학교명/국내기업명' in filtered_df.columns:
            display_columns.append('국내진학학교명/국내기업명')
        if '기업지역' in filtered_df.columns:
            display_columns.append('기업지역')
        if '기업구분' in filtered_df.columns:
            display_columns.append('기업구분')
        if '회사구분' in filtered_df.columns:
            display_columns.append('회사구분')
        if '전공일치여부' in filtered_df.columns:
            display_columns.append('전공일치여부')
        
        # 데이터테이블 표시
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            height=400
        )
        
        # 다운로드 버튼
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 필터된 데이터 다운로드 (CSV)",
            data=csv,
            file_name=f"취업현황_필터결과_{selected_year}_{selected_region}_{selected_company_type}.csv",
            mime="text/csv"
        )

def setup_sidebar():
    """사이드바 설정"""
    with st.sidebar:
        st.markdown(f"""
        ### {APP_META['title']} {APP_META['version']}
        
        **📊 주요 기능**
        - 연도별 취업률 분석
        - 지역별 취업 현황
        - 기업 유형별 분석
        - 전공일치도 분석
        - 데이터 품질 리포트
        
        **📅 분석 기간**
        {APP_META['period']}
        
        **🎯 분석 대상**
        {APP_META['target']}
        """)

def render_dashboard(processor: EmploymentDataProcessor, stats: EmploymentStats, trend: TrendAnalysis):
    """메인 대시보드 구성"""
    # KPI 메트릭 표시
    VisualizationModule.create_kpi_metrics(stats)
    
    # 인사이트 표시
    show_insights(trend, stats)
    
    # 탭 기반 대시보드 구성 (품질보고서 탭 제거)
    tabs = st.tabs(["📈 연도별 분석", "🗺️ 지역별 분석", "🏢 기업별 분석", "🔍 상세 데이터"])
    
    with tabs[0]:
        render_yearly_analysis(processor)
    
    with tabs[1]:
        render_regional_analysis(processor)
    
    with tabs[2]:
        render_company_analysis(processor)
    
    with tabs[3]:
        show_advanced_filters(processor)
    
    # 푸터
    render_footer()

def render_yearly_analysis(processor: EmploymentDataProcessor):
    """연도별 분석 탭 렌더링"""
    st.subheader("📈 연도별 취업 현황 분석")
    
    yearly_stats = processor.get_yearly_stats()
    if yearly_stats.empty:
        show_message("연도별 데이터가 없습니다.", "warning")
        return
    
    # 차트 생성 및 표시
    yearly_chart = VisualizationModule.create_yearly_trend_chart(yearly_stats)
    st.plotly_chart(yearly_chart, use_container_width=True)
    
    # 상세 테이블
    st.subheader("📋 연도별 상세 통계")
    styled_df = yearly_stats.style.background_gradient(
        subset=['취업률'], cmap='RdYlGn'
    ).format({
        '취업률': '{:.2f}%',  # 소수점 2자리까지 표시
        '전체인원': '{:,}명',
        '취업자수': '{:,}명',
        '미취업자수': '{:,}명'
    })
    st.dataframe(styled_df, use_container_width=True)
    
    # 인사이트 생성
    generate_yearly_insights(yearly_stats)

def render_regional_analysis(processor: EmploymentDataProcessor):
    """지역별 분석 탭 렌더링"""
    st.subheader("🗺️ 지역별 취업 현황 분석")
    
    regional_stats = processor.get_regional_stats()
    if regional_stats.empty:
        show_message("지역별 데이터가 없습니다.", "warning")
        return
    
    # 차트 생성
    bar_chart, pie_chart = VisualizationModule.create_regional_chart(regional_stats)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart, use_container_width=True)
    with col2:
        st.plotly_chart(pie_chart, use_container_width=True)
    
    # 지역별 인사이트
    generate_regional_insights(regional_stats)

def render_company_analysis(processor: EmploymentDataProcessor):
    """기업 분석 탭 렌더링"""
    st.subheader("🏢 기업 유형별 취업 현황 분석")
    
    company_type_stats, company_group_stats = processor.get_company_stats()
    
    if not company_type_stats.empty:
        type_chart, size_chart = VisualizationModule.create_company_charts(company_type_stats, company_group_stats)
        
        # 차트 표시
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(type_chart, use_container_width=True)
        with col2:
            if not company_group_stats.empty:
                st.plotly_chart(size_chart, use_container_width=True)
        
        # 데이터 표 표시
        st.subheader("📊 상세 데이터")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**🏢 기업 유형별 취업자 분포**")
            # 기업 유형별 데이터 표 스타일링
            styled_company_type = company_type_stats.style.background_gradient(
                subset=['취업자수'], cmap='Blues'
            ).format({
                '취업자수': '{:,}명',
                '비율': '{:.1f}%'
            })
            st.dataframe(styled_company_type, use_container_width=True)
        
        with col2:
            if not company_group_stats.empty:
                st.write("**🏭 회사 규모별 취업자 분포**")
                # 회사 규모별 데이터 표 스타일링
                styled_company_size = company_group_stats.style.background_gradient(
                    subset=['취업자수'], cmap='Greens'
                ).format({
                    '취업자수': '{:,}명',
                    '비율': '{:.1f}%'
                })
                st.dataframe(styled_company_size, use_container_width=True)
            else:
                st.info("회사 규모별 데이터가 없습니다.")
        
        # 요약 통계
        st.subheader("📋 요약 통계")
        total_employed = company_type_stats['취업자수'].sum()
        top_company_type = company_type_stats.iloc[0] if not company_type_stats.empty else None
        
        col1, col2, col3 = st.columns(3)
        with col1:
            create_metric_card("총 취업자 수", f"{total_employed:,}명")
        with col2:
            if top_company_type is not None:
                create_metric_card("최다 기업유형", f"{top_company_type['기업구분']} ({top_company_type['비율']:.1f}%)")
        with col3:
            company_diversity = len(company_type_stats)
            create_metric_card("기업유형 다양성", f"{company_diversity}개 유형")
    else:
        show_message("기업 분석 데이터가 없습니다.", "warning")

def render_footer():
    """푸터 렌더링"""
    st.markdown(f'''
    <div class="footer">
        <p>📊 {APP_META['title']} {APP_META['version']} | 
        ⚡ Powered by Streamlit & Plotly | 
        📅 {APP_META['period']}</p>
    </div>
    ''', unsafe_allow_html=True)

# =====================
# 인사이트 생성 함수들
# =====================

def generate_yearly_insights(yearly_stats: pd.DataFrame):
    """연도별 인사이트 생성"""
    if len(yearly_stats) < 2:
        return
    
    # CAGR 계산
    years = yearly_stats['연도'].max() - yearly_stats['연도'].min()
    if years > 0:
        start_rate = yearly_stats.iloc[0]['취업률']
        end_rate = yearly_stats.iloc[-1]['취업률']
        cagr = ((end_rate / start_rate) ** (1/years) - 1) * 100
        
        st.markdown(f'''
        <div class="insight-box">
            <h4>📊 연도별 인사이트</h4>
            <ul>
                <li><strong>연평균 증가율(CAGR):</strong> {cagr:+.1f}%</li>
                <li><strong>취업률 변동폭:</strong> {yearly_stats['취업률'].max() - yearly_stats['취업률'].min():.1f}%p</li>
                <li><strong>최대 증감:</strong> {yearly_stats['취업률'].diff().abs().max():.1f}%p</li>
            </ul>
        </div>
        ''', unsafe_allow_html=True)

def generate_regional_insights(regional_stats: pd.DataFrame):
    """지역별 인사이트 생성"""
    if regional_stats.empty:
        return
    
    total_employed = regional_stats['취업자수'].sum()
    top_region = regional_stats.iloc[0]
    seoul_busan_rate = regional_stats[regional_stats['지역'].isin(['서울', '부산'])]['비율'].sum()
    
    # Shannon Entropy로 지역 다양성 계산
    probabilities = regional_stats['비율'] / 100
    diversity_index = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    max_diversity = np.log2(len(regional_stats))
    diversity_score = (diversity_index / max_diversity) * 100
    
    st.markdown(f'''
    <div class="insight-box">
        <h4>🌍 지역별 인사이트</h4>
        <ul>
            <li><strong>최다 취업 지역:</strong> {top_region['지역']} ({top_region['비율']:.1f}%)</li>
            <li><strong>수도권 집중도:</strong> {seoul_busan_rate:.1f}%</li>
            <li><strong>지역 다양성 지수:</strong> {diversity_score:.1f}/100</li>
        </ul>
    </div>
    ''', unsafe_allow_html=True)

def main():
    """메인 애플리케이션 함수 (리팩토링된 버전)"""
    # 앱 초기화
    init_app()
    load_css()
    
    # 헤더 표시
    show_header()
    
    # 사이드바 설정
    setup_sidebar()
    
    # 데이터 로드 및 처리
    processor = EmploymentDataProcessor()
    if not processor.load_data():
        st.stop()
    
    # 기본 통계 계산
    stats = processor.get_overall_stats()
    trend = processor.get_trend_analysis()
    
    # 메인 대시보드 구성
    render_dashboard(processor, stats, trend)

if __name__ == "__main__":
    main()
