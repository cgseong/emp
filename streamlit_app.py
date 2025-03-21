import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from typing import Tuple, Dict, List, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class EmploymentStats:
    """취업 통계 정보를 저장하는 데이터 클래스"""
    total: int = 0
    employed: int = 0
    unemployed: int = 0
    employment_rate: float = 0.0


class EmploymentDashboard:
    """취업 현황 대시보드의 핵심 클래스"""
    
    def __init__(self, file_path: str):
        """
        초기화 메서드
        
        Args:
            file_path: 취업 현황 데이터 파일 경로
        """
        self.file_path = file_path
        self.df = None
        self.employed_df = None
        self.total_stats = None
    
    def load_data(self) -> bool:
        """
        취업 현황 데이터를 로드하고 초기 처리를 수행합니다.
        
        Returns:
            bool: 로드 성공 여부
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(self.file_path):
                st.error(f"'{self.file_path}' 파일을 찾을 수 없습니다.")
                return False
            
            # 다양한 인코딩 시도
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(self.file_path, encoding='cp949')
            
            # 진학과 외국인 제외
            df_filtered = df[~df['취업구분1'].isin(['진학', '외국인'])]
            
            # 취업자 필터링
            employed_df = df_filtered[df_filtered['취업구분1'] == '취업'].copy()
            
            # 전체 통계 계산
            self.df = df_filtered
            self.employed_df = employed_df
            self.total_stats = self._calculate_total_stats()
            
            return True
            
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {str(e)}")
            return False
    
    def _calculate_total_stats(self) -> EmploymentStats:
        """
        전체 취업 통계를 계산합니다.
        
        Returns:
            EmploymentStats: 취업 통계 정보
        """
        if self.df is None or self.employed_df is None:
            return EmploymentStats()
        
        total = len(self.df)
        employed = len(self.employed_df)
        unemployed = total - employed
        employment_rate = (employed / total * 100) if total > 0 else 0
        
        return EmploymentStats(
            total=total,
            employed=employed,
            unemployed=unemployed,
            employment_rate=employment_rate
        )
    
    def display_total_stats(self) -> None:
        """전체 취업 통계를 화면에 표시합니다."""
        if self.total_stats is None:
            st.error("통계 데이터가 없습니다.")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 졸업자", f"{self.total_stats.total:,}명")
        with col2:
            st.metric("취업자", f"{self.total_stats.employed:,}명")
        with col3:
            st.metric("미취업자", f"{self.total_stats.unemployed:,}명")
        with col4:
            st.metric("취업률", f"{self.total_stats.employment_rate:.1f}%")
    
    def create_yearly_analysis(self) -> pd.DataFrame:
        """
        연도별 취업 현황을 분석합니다.
        
        Returns:
            pd.DataFrame: 연도별 취업 통계
        """
        if self.df is None:
            st.error("데이터가 로드되지 않았습니다.")
            return pd.DataFrame()
        
        if '조사년도' not in self.df.columns or '취업구분1' not in self.df.columns:
            st.error("'조사년도' 또는 '취업구분1' 컬럼을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        yearly_stats = self.df.groupby('조사년도').agg({
            '학번': 'count',
            '취업구분1': lambda x: (x == '취업').sum()
        }).reset_index()
        
        yearly_stats.columns = ['연도', '전체인원', '취업자수']
        yearly_stats['미취업자수'] = yearly_stats['전체인원'] - yearly_stats['취업자수']
        yearly_stats['취업률'] = (yearly_stats['취업자수'] / yearly_stats['전체인원'] * 100).round(1)
        
        return yearly_stats
    
    def display_yearly_analysis(self, yearly_stats: pd.DataFrame) -> None:
        """
        연도별 취업 현황 분석 결과를 화면에 표시합니다.
        
        Args:
            yearly_stats: 연도별 취업 통계
        """
        if yearly_stats.empty:
            st.warning("연도별 분석 데이터가 없습니다.")
            return
        
        # 연도별 취업률 추이 그래프
        fig_yearly_rate = px.bar(
            yearly_stats, 
            x='연도', 
            y='취업률',
            text='취업률',
            labels={'취업률': '취업률 (%)'},
            title='연도별 취업률 추이'
        )
        fig_yearly_rate.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig_yearly_rate.update_xaxes(tickformat='d', dtick=1)
        fig_yearly_rate.update_traces(marker_color='royalblue')
        st.plotly_chart(fig_yearly_rate, use_container_width=True)
        
        # 연도별 취업자/미취업자 현황 그래프
        fig_yearly_status = px.bar(
            yearly_stats, 
            x='연도',
            y=['취업자수', '미취업자수'],
            title='연도별 취업자/미취업자 현황',
            barmode='stack',
            labels={'value': '인원 수', 'variable': '구분'}
        )
        fig_yearly_status.update_layout(
            xaxis_title="연도",
            yaxis_title="인원 수",
            legend_title="구분"
        )
        fig_yearly_status.update_xaxes(tickformat='d', dtick=1)
        st.plotly_chart(fig_yearly_status, use_container_width=True)
        
        # 연도별 통계 및 주요 지표 표시
        self._display_yearly_stats_tables(yearly_stats)
    
    def _display_yearly_stats_tables(self, yearly_stats: pd.DataFrame) -> None:
        """
        연도별 통계 테이블과 주요 지표를 표시합니다.
        
        Args:
            yearly_stats: 연도별 취업 통계
        """
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("연도별 통계")
            st.dataframe(yearly_stats.style.format({
                '전체인원': '{:,}명',
                '취업자수': '{:,}명',
                '미취업자수': '{:,}명',
                '취업률': '{:.1f}%'
            }), use_container_width=True)
        
        with col2:
            st.subheader("주요 통계")
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            # 최고 취업률
            with metrics_col1:
                max_rate_year = yearly_stats.loc[yearly_stats['취업률'].idxmax()]
                st.metric("최고 취업률", f"{max_rate_year['취업률']}%", f"{max_rate_year['연도']}년")
            
            # 최저 취업률
            with metrics_col2:
                min_rate_year = yearly_stats.loc[yearly_stats['취업률'].idxmin()]
                st.metric("최저 취업률", f"{min_rate_year['취업률']}%", f"{min_rate_year['연도']}년")
            
            # 평균 취업률
            with metrics_col3:
                avg_rate = yearly_stats['취업률'].mean()
                st.metric("평균 취업률", f"{avg_rate:.1f}%")
    
    def create_regional_analysis(self) -> pd.DataFrame:
        """
        지역별 취업자 분포를 분석합니다.
        
        Returns:
            pd.DataFrame: 지역별 취업자 통계
        """
        if self.employed_df is None:
            st.error("취업자 데이터가 로드되지 않았습니다.")
            return pd.DataFrame()
        
        if '기업지역' not in self.employed_df.columns:
            st.error("'기업지역' 컬럼을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        regional_stats = self.employed_df['기업지역'].value_counts().reset_index()
        regional_stats.columns = ['지역', '취업자수']
        
        total_employed = regional_stats['취업자수'].sum()
        regional_stats['비율'] = (regional_stats['취업자수'] / total_employed * 100).round(1)
        
        return regional_stats
    
    def display_regional_analysis(self, regional_stats: pd.DataFrame) -> None:
        """
        지역별 취업자 분포 분석 결과를 화면에 표시합니다.
        
        Args:
            regional_stats: 지역별 취업자 통계
        """
        if regional_stats.empty:
            st.warning("지역별 분석 데이터가 없습니다.")
            return
        
        st.subheader("취업자 지역 분포")
        
        # 지역별 취업자 분포 그래프
        fig_region = px.bar(
            regional_stats, 
            x='지역', 
            y='취업자수',
            text='비율',
            labels={'취업자수': '취업자 수'},
            title='지역별 취업자 분포'
        )
        fig_region.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_region, use_container_width=True)
        
        # 지역별 취업자 통계 테이블
        st.dataframe(regional_stats.style.format({
            '취업자수': '{:,}명',
            '비율': '{:.1f}%'
        }), use_container_width=True)
    
    def create_company_analysis(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        기업 유형별, 회사 규모별 취업자 분포를 분석합니다.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (기업 유형별 통계, 회사 규모별 통계)
        """
        if self.employed_df is None:
            st.error("취업자 데이터가 로드되지 않았습니다.")
            return pd.DataFrame(), pd.DataFrame()
        
        # 기업 유형별 분석
        company_stats = pd.DataFrame()
        if '기업구분' in self.employed_df.columns:
            company_stats = self.employed_df['기업구분'].value_counts().reset_index()
            company_stats.columns = ['기업구분', '취업자수']
            company_stats['비율'] = (company_stats['취업자수'] / company_stats['취업자수'].sum() * 100).round(1)
        
        # 회사 규모별 분석
        size_stats = pd.DataFrame()
        if '회사구분' in self.employed_df.columns:
            size_stats = self.employed_df['회사구분'].value_counts().reset_index()
            size_stats.columns = ['회사구분', '취업자수']
            size_stats['비율'] = (size_stats['취업자수'] / size_stats['취업자수'].sum() * 100).round(1)
        
        return company_stats, size_stats
    
    def display_company_analysis(self, company_stats: pd.DataFrame, size_stats: pd.DataFrame) -> None:
        """
        기업 유형별, 회사 규모별 취업자 분포 분석 결과를 화면에 표시합니다.
        
        Args:
            company_stats: 기업 유형별 통계
            size_stats: 회사 규모별 통계
        """
        col1, col2 = st.columns(2)
        
        # 기업 유형별 분석 표시
        with col1:
            if not company_stats.empty:
                st.subheader("기업구분별 분포")
                
                # 기업 유형별 취업자 분포 원형 차트
                fig_company = px.pie(
                    company_stats, 
                    values='취업자수', 
                    names='기업구분',
                    title='기업구분별 취업자 분포'
                )
                st.plotly_chart(fig_company, use_container_width=True)
                
                # 기업 유형별 취업자 통계 테이블
                st.dataframe(company_stats.style.format({
                    '취업자수': '{:,}명',
                    '비율': '{:.1f}%'
                }), use_container_width=True)
            else:
                st.warning("기업 유형별 분석 데이터가 없습니다.")
        
        # 회사 규모별 분석 표시
        with col2:
            if not size_stats.empty:
                st.subheader("회사구분별 분포")
                
                # 회사 규모별 취업자 분포 원형 차트
                fig_size = px.pie(
                    size_stats, 
                    values='취업자수', 
                    names='회사구분',
                    title='회사구분별 취업자 분포'
                )
                st.plotly_chart(fig_size, use_container_width=True)
                
                # 회사 규모별 취업자 통계 테이블
                st.dataframe(size_stats.style.format({
                    '취업자수': '{:,}명',
                    '비율': '{:.1f}%'
                }), use_container_width=True)
            else:
                st.warning("회사 규모별 분석 데이터가 없습니다.")
    
    def display_detailed_data(self) -> None:
        """상세 취업자 데이터를 필터링하고 표시합니다."""
        if self.employed_df is None or self.df is None:
            st.error("데이터가 로드되지 않았습니다.")
            return
        
        st.subheader("상세 데이터")
        
        # 필터링 컨트롤
        filter_col1, filter_col2 = st.columns([1, 3])
        
        with filter_col1:
            # 연도 선택 필터
            years = sorted(self.df['조사년도'].unique())
            selected_year = st.selectbox("연도 선택", ["전체"] + list(years))
        
        with filter_col2:
            # 텍스트 검색 필터
            search = st.text_input("데이터 검색", "")
        
        # 필터 적용
        filtered_df = self._filter_detailed_data(selected_year, search)
        
        # 필터링된 데이터 표시
        st.write(f"검색된 데이터: {len(filtered_df):,}건")
        st.dataframe(filtered_df, use_container_width=True)
    
    def _filter_detailed_data(self, selected_year: str, search: str) -> pd.DataFrame:
        """
        상세 데이터를 필터링합니다.
        
        Args:
            selected_year: 선택된 연도 (또는 '전체')
            search: 검색어
            
        Returns:
            pd.DataFrame: 필터링된 데이터
        """
        filtered_df = self.employed_df.copy()
        
        # 연도 필터 적용
        if selected_year != "전체":
            filtered_df = filtered_df[filtered_df['조사년도'] == selected_year]
        
        # 검색어 필터 적용
        if search:
            filtered_df = filtered_df[
                filtered_df.astype(str).apply(
                    lambda x: x.str.contains(search, case=False, na=False)
                ).any(axis=1)
            ]
        
        return filtered_df


def main():
    st.set_page_config(page_title="취업 현황(진학자/외국인제외)", layout="wide")
    st.title("20 ~ 23년도 취업 현황")
    
    # 대시보드 객체 생성 및 데이터 로드
    file_path = "졸업자취업현황_20_21_22_23_통합.csv"
    dashboard = EmploymentDashboard(file_path)
    
    if not dashboard.load_data():
        return
    
    # 전체 통계 표시
    dashboard.display_total_stats()
    st.markdown("---")
    
    # 연도별 분석
    st.subheader("연도별 취업현황")
    yearly_stats = dashboard.create_yearly_analysis()
    dashboard.display_yearly_analysis(yearly_stats)
    st.markdown("---")
    
    # 지역별 분석
    regional_stats = dashboard.create_regional_analysis()
    dashboard.display_regional_analysis(regional_stats)
    st.markdown("---")
    
    # 기업 유형 및 규모별 분석
    company_stats, size_stats = dashboard.create_company_analysis()
    dashboard.display_company_analysis(company_stats, size_stats)
    st.markdown("---")
    
    # 상세 데이터 표시
    dashboard.display_detailed_data()


if __name__ == "__main__":
    main()
