import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

def load_and_process_data(file_path):
    """CSV 파일을 로드하고 처리하는 함수"""
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')
            
       # 진학과 외국인 제외
        df_filtered = df[~df['취업구분1'].isin(['진학', '외국인'])]
        
        # 취업자 필터링
        employed_df = df_filtered[df_filtered['취업구분1'] == '취업'].copy()
        
        total_stats = {
            'total': len(df_filtered),  # 전체 대상자 (진학, 외국인 제외)
            'employed': len(employed_df),
            'unemployed': len(df_filtered) - len(employed_df),
            'employment_rate': (len(employed_df) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        }
        
        return df_filtered, employed_df, total_stats
    
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {str(e)}")
        return None, None, None

def create_yearly_analysis(df):
    """연도별 취업현황 분석"""
    if '조사년도' not in df.columns or '취업구분1' not in df.columns:
        st.error("'조사년도' 또는 '취업구분1' 컬럼을 찾을 수 없습니다.")
        return pd.DataFrame()
    
    yearly_stats = df.groupby('조사년도').agg({
        '학번': 'count',
        '취업구분1': lambda x: (x == '취업').sum()
    }).reset_index()
    
    yearly_stats.columns = ['연도', '전체인원', '취업자수']
    yearly_stats['미취업자수'] = yearly_stats['전체인원'] - yearly_stats['취업자수']
    yearly_stats['취업률'] = (yearly_stats['취업자수'] / yearly_stats['전체인원'] * 100).round(1)
    
    return yearly_stats

def create_regional_analysis(employed_df):
    """지역별 분석"""
    if '기업지역' not in employed_df.columns:
        st.error("'기업지역' 컬럼을 찾을 수 없습니다.")
        return pd.DataFrame()
    
    regional_stats = employed_df['기업지역'].value_counts().reset_index()
    regional_stats.columns = ['지역', '취업자수']
    regional_stats['비율'] = (regional_stats['취업자수'] / regional_stats['취업자수'].sum() * 100).round(1)
    return regional_stats

def create_company_type_analysis(employed_df, company_column='기업구분'):
    """기업구분별 분석"""
    if company_column not in employed_df.columns:
        st.error(f"'{company_column}' 컬럼을 찾을 수 없습니다.")
        return pd.DataFrame()
    
    company_stats = employed_df[company_column].value_counts().reset_index()
    company_stats.columns = ['기업구분', '취업자수']
    company_stats['비율'] = (company_stats['취업자수'] / company_stats['취업자수'].sum() * 100).round(1)
    return company_stats

def create_company_size_analysis(employed_df, size_column='회사구분'):
    """회사구분별 분석"""
    if size_column not in employed_df.columns:
        st.error(f"'{size_column}' 컬럼을 찾을 수 없습니다.")
        return pd.DataFrame()
    
    size_stats = employed_df[size_column].value_counts().reset_index()
    size_stats.columns = ['회사구분', '취업자수']
    size_stats['비율'] = (size_stats['취업자수'] / size_stats['취업자수'].sum() * 100).round(1)
    return size_stats

def main():
    st.set_page_config(page_title="취업 현황(진학자/외국인제외)", layout="wide")
    st.title("20년도~23년도 취업 현황 대시보드")
    
    file_path = "졸업자취업현황_20_21_22_23_통합.csv"
    
    if not os.path.exists(file_path):
        st.error(f"'{file_path}' 파일을 찾을 수 없습니다.")
        return
        
    df, employed_df, total_stats = load_and_process_data(file_path)
    
    if df is None or employed_df is None:
        return
        
    # 전체 통계
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 졸업자", f"{total_stats['total']:,}명")
    with col2:
        st.metric("취업자", f"{total_stats['employed']:,}명")
    with col3:
        st.metric("미취업자", f"{total_stats['unemployed']:,}명")
    with col4:
        st.metric("취업률", f"{total_stats['employment_rate']:.1f}%")
    
    st.markdown("---")
    
    # 연도별 분석
    st.subheader("연도별 취업현황")
    yearly_stats = create_yearly_analysis(df)
    if not yearly_stats.empty:
        fig_yearly_rate = px.bar(yearly_stats, 
                                x='연도', 
                                y='취업률',
                                text='취업률',
                                labels={'취업률': '취업률 (%)'},
                                title='연도별 취업률 추이')
        fig_yearly_rate.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig_yearly_rate.update_xaxes(tickformat='d', dtick=1)
        fig_yearly_rate.update_traces(marker_color='royalblue')
        st.plotly_chart(fig_yearly_rate, use_container_width=True)
        
        fig_yearly_status = px.bar(yearly_stats, 
                                 x='연도',
                                 y=['취업자수', '미취업자수'],
                                 title='연도별 취업자/미취업자 현황',
                                 barmode='stack',
                                 labels={'value': '인원 수', 'variable': '구분'})
        fig_yearly_status.update_layout(
            xaxis_title="연도",
            yaxis_title="인원 수",
            legend_title="구분"
        )
        fig_yearly_status.update_xaxes(tickformat='d', dtick=1)
        st.plotly_chart(fig_yearly_status, use_container_width=True)
        
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
            with metrics_col1:
                max_rate_year = yearly_stats.loc[yearly_stats['취업률'].idxmax()]
                st.metric("최고 취업률", f"{max_rate_year['취업률']}%", f"{max_rate_year['연도']}년")
            with metrics_col2:
                min_rate_year = yearly_stats.loc[yearly_stats['취업률'].idxmin()]
                st.metric("최저 취업률", f"{min_rate_year['취업률']}%", f"{min_rate_year['연도']}년")
            with metrics_col3:
                avg_rate = yearly_stats['취업률'].mean()
                st.metric("평균 취업률", f"{avg_rate:.1f}%")
    
    st.markdown("---")
    
    # 지역별 분석
    regional_stats = create_regional_analysis(employed_df)
    if not regional_stats.empty:
        st.subheader("취업자 지역 분포")
        fig_region = px.bar(regional_stats, 
                          x='지역', 
                          y='취업자수',
                          text='비율',
                          labels={'취업자수': '취업자 수'},
                          title='지역별 취업자 분포')
        fig_region.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_region, use_container_width=True)
    
    # 기업 분석
    col1, col2 = st.columns(2)
    with col1:
        company_stats = create_company_type_analysis(employed_df)
        if not company_stats.empty:
            st.subheader("기업구분별 분포")
            fig_company = px.pie(company_stats, 
                               values='취업자수', 
                               names='기업구분',
                               title='기업구분별 취업자 분포')
            st.plotly_chart(fig_company, use_container_width=True)
            st.dataframe(company_stats, use_container_width=True)
    
    with col2:
        size_stats = create_company_size_analysis(employed_df)
        if not size_stats.empty:
            st.subheader("회사구분별 분포")
            fig_size = px.pie(size_stats, 
                            values='취업자수', 
                            names='회사구분',
                            title='회사구분별 취업자 분포')
            st.plotly_chart(fig_size, use_container_width=True)
            st.dataframe(size_stats, use_container_width=True)
    
    # 상세 데이터
    st.markdown("---")
    st.subheader("상세 데이터")
    
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        years = sorted(df['조사년도'].unique())
        selected_year = st.selectbox("연도 선택", ["전체"] + list(years))
    
    with filter_col2:
        search = st.text_input("데이터 검색", "")
    
    filtered_df = employed_df.copy()
    
    if selected_year != "전체":
        filtered_df = filtered_df[filtered_df['조사년도'] == selected_year]
    
    if search:
        filtered_df = filtered_df[
            filtered_df.astype(str).apply(
                lambda x: x.str.contains(search, case=False, na=False)
            ).any(axis=1)
        ]
    
    st.write(f"검색된 데이터: {len(filtered_df):,}건")
    st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
