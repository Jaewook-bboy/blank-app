import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="LEGO Report 통합 관리",
    page_icon="📊",
    layout="wide"
)

st.title("📊 LEGO Report 통합 관리 시스템")
st.markdown("---")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")
st.sidebar.markdown("세 개의 엑셀 파일을 한꺼번에 드롭하세요!")

# 파일 업로드 (다중 파일)
st.sidebar.subheader("📁 파일 업로드")
uploaded_files = st.sidebar.file_uploader(
    "DAD, DMC, TA 파일을 모두 선택하거나 드래그 앤 드롭",
    type=['xlsx'],
    accept_multiple_files=True,
    help="세 개의 파일을 한번에 업로드할 수 있습니다."
)

def read_raw_sheet(file, file_name):
    """
    raw 시트를 읽어서 데이터프레임으로 반환
    9번 행이 헤더, 10번 행부터 데이터
    """
    try:
        # 9번 행을 헤더로 읽기 (skiprows=9, 그러면 9번 행이 헤더가 됨)
        df = pd.read_excel(file, sheet_name='raw', skiprows=9)
        
        # 완전히 빈 행 제거
        df = df.dropna(how='all')
        
        # 파일 출처 컬럼 추가
        df.insert(0, 'Source_File', file_name)
        
        return df
    except Exception as e:
        st.error(f"{file_name} 파일 읽기 오류: {str(e)}")
        return None

def merge_files(dad_df, dmc_df, ta_df):
    """
    세 개의 데이터프레임을 하나로 병합
    """
    try:
        # 세 파일을 세로로 연결
        merged_df = pd.concat([dad_df, dmc_df, ta_df], ignore_index=True)
        
        # 날짜 컬럼 정렬 (date 컬럼이 있다면)
        if 'date' in merged_df.columns:
            # datetime 타입으로 변환 시도 (에러 무시)
            try:
                merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')
                merged_df = merged_df.sort_values('date', ascending=False)
            except:
                # 변환 실패 시 정렬하지 않음
                pass
        
        return merged_df
    except Exception as e:
        st.error(f"파일 병합 오류: {str(e)}")
        return None

def save_to_excel(df):
    """
    데이터프레임을 엑셀 파일로 변환하여 BytesIO 객체로 반환
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='raw', index=False)
    
    output.seek(0)
    return output

def classify_files(uploaded_files):
    """
    업로드된 파일들을 DAD, DMC, TA로 자동 분류
    """
    dad_file = None
    dmc_file = None
    ta_file = None
    
    for file in uploaded_files:
        filename = file.name.upper()
        if 'DAD' in filename:
            dad_file = file
        elif 'DMC' in filename:
            dmc_file = file
        elif 'TA' in filename:
            ta_file = file
    
    return dad_file, dmc_file, ta_file

# 메인 로직
if uploaded_files:
    # 업로드된 파일 개수 확인
    if len(uploaded_files) != 3:
        st.warning(f"⚠️ {len(uploaded_files)}개의 파일이 업로드되었습니다. 정확히 3개의 파일(DAD, DMC, TA)을 업로드해주세요.")
        
        # 현재 업로드된 파일 목록 표시
        st.info("📄 업로드된 파일:")
        for file in uploaded_files:
            st.write(f"- {file.name}")
    else:
        # 파일 분류
        dad_file, dmc_file, ta_file = classify_files(uploaded_files)
        
        # 파일 분류 결과 표시
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if dad_file:
                st.success(f"✅ DAD: {dad_file.name}")
            else:
                st.error("❌ DAD 파일 없음")
        
        with col2:
            if dmc_file:
                st.success(f"✅ DMC: {dmc_file.name}")
            else:
                st.error("❌ DMC 파일 없음")
        
        with col3:
            if ta_file:
                st.success(f"✅ TA: {ta_file.name}")
            else:
                st.error("❌ TA 파일 없음")
        
        # 세 파일이 모두 있는지 확인
        if dad_file and dmc_file and ta_file:
            st.success("✅ 세 개의 파일이 모두 올바르게 업로드되었습니다!")
            
            # 파일 읽기 버튼
            if st.button("🔄 파일 통합 시작", type="primary"):
                with st.spinner("파일을 읽고 통합하는 중..."):
                    # 각 파일 읽기
                    dad_df = read_raw_sheet(dad_file, "DAD")
                    dmc_df = read_raw_sheet(dmc_file, "DMC")
                    ta_df = read_raw_sheet(ta_file, "TA")
                    
                    if dad_df is not None and dmc_df is not None and ta_df is not None:
                        # 파일 미리보기
                        st.subheader("📄 개별 파일 미리보기")
                        
                        tab1, tab2, tab3 = st.tabs(["DAD 파일", "DMC 파일", "TA 파일"])
                        
                        with tab1:
                            st.write(f"**총 {len(dad_df):,} 행 × {len(dad_df.columns)} 컬럼**")
                            st.dataframe(dad_df.head(20), use_container_width=True, height=300)
                            st.caption("처음 20행만 표시됩니다.")
                        
                        with tab2:
                            st.write(f"**총 {len(dmc_df):,} 행 × {len(dmc_df.columns)} 컬럼**")
                            st.dataframe(dmc_df.head(20), use_container_width=True, height=300)
                            st.caption("처음 20행만 표시됩니다.")
                        
                        with tab3:
                            st.write(f"**총 {len(ta_df):,} 행 × {len(ta_df.columns)} 컬럼**")
                            st.dataframe(ta_df.head(20), use_container_width=True, height=300)
                            st.caption("처음 20행만 표시됩니다.")
                        
                        st.markdown("---")
                        
                        # 파일 병합
                        merged_df = merge_files(dad_df, dmc_df, ta_df)
                        
                        if merged_df is not None:
                            st.success(f"✅ 통합 완료! 총 {len(merged_df):,} 행의 데이터")
                            
                            # 통합된 데이터 미리보기
                            st.subheader("📋 통합 데이터 미리보기")
                            
                            # 필터 옵션
                            col1, col2 = st.columns(2)
                            with col1:
                                source_filter = st.multiselect(
                                    "출처 필터",
                                    options=merged_df['Source_File'].unique(),
                                    default=merged_df['Source_File'].unique()
                                )
                            
                            with col2:
                                if 'Campaign' in merged_df.columns:
                                    campaigns = merged_df['Campaign'].dropna().unique()
                                    campaign_filter = st.multiselect(
                                        "캠페인 필터",
                                        options=campaigns,
                                        default=[]
                                    )
                            
                            # 필터 적용
                            filtered_df = merged_df[merged_df['Source_File'].isin(source_filter)]
                            if 'Campaign' in merged_df.columns and campaign_filter:
                                filtered_df = filtered_df[filtered_df['Campaign'].isin(campaign_filter)]
                            
                            # 데이터 표시
                            st.dataframe(
                                filtered_df.head(100),
                                use_container_width=True,
                                height=400
                            )
                            
                            st.info(f"ℹ️ 필터링된 데이터: {len(filtered_df):,} 행 (최대 100행까지 표시)")
                            
                            # 다운로드 섹션
                            st.markdown("---")
                            st.subheader("💾 통합 파일 다운로드")
                            
                            # 파일명 생성
                            today = datetime.now().strftime("%Y%m%d")
                            filename = f"LEGO_Report_통합관리_ALL_{today}.xlsx"
                            
                            # 엑셀 파일 생성
                            excel_file = save_to_excel(merged_df)
                            
                            # 다운로드 버튼
                            st.download_button(
                                label="📥 통합 엑셀 파일 다운로드",
                                data=excel_file,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                            
                            # 통계 정보
                            st.markdown("---")
                            st.subheader("📊 통계 정보")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("전체 행 수", f"{len(merged_df):,}")
                            
                            with col2:
                                st.metric("전체 컬럼 수", len(merged_df.columns))
                            
                            with col3:
                                if 'Campaign' in merged_df.columns:
                                    unique_campaigns = merged_df['Campaign'].nunique()
                                    st.metric("캠페인 수", f"{unique_campaigns:,}")
                            
                            with col4:
                                if 'date' in merged_df.columns:
                                    try:
                                        # datetime 타입인지 확인
                                        if pd.api.types.is_datetime64_any_dtype(merged_df['date']):
                                            min_date = merged_df['date'].min()
                                            max_date = merged_df['date'].max()
                                            if pd.notna(min_date) and pd.notna(max_date):
                                                date_range = f"{min_date.date()} ~ {max_date.date()}"
                                                st.metric("기간", date_range)
                                        else:
                                            # datetime이 아닌 경우 변환 시도
                                            temp_date = pd.to_datetime(merged_df['date'], errors='coerce')
                                            min_date = temp_date.min()
                                            max_date = temp_date.max()
                                            if pd.notna(min_date) and pd.notna(max_date):
                                                date_range = f"{min_date.date()} ~ {max_date.date()}"
                                                st.metric("기간", date_range)
                                    except:
                                        # 날짜 형식이 이상한 경우 표시하지 않음
                                        pass
        else:
            st.error("❌ DAD, DMC, TA 파일을 모두 업로드해주세요. 파일명에 'DAD', 'DMC', 'TA'가 포함되어야 합니다.")
                            
else:
    st.info("👆 왼쪽 사이드바에서 세 개의 엑셀 파일(DAD, DMC, TA)을 한꺼번에 드래그 앤 드롭하거나 선택해주세요.")
    
    # 사용 방법 안내
    with st.expander("📖 사용 방법"):
        st.markdown("""
        ### 사용 방법
        
        1. **파일 업로드**: 왼쪽 사이드바에서 세 개의 파일을 **한꺼번에** 드래그 앤 드롭하거나 선택합니다.
           - DAD 파일 (lego_report_통합관리_DAD_*.xlsx)
           - DMC 파일 (lego_report_통합관리_DMC_*.xlsx)
           - TA 파일 (lego_report_통합관리_TA_*.xlsx)
           
           💡 **팁**: 파일명에 'DAD', 'DMC', 'TA'가 포함되어 있으면 자동으로 분류됩니다!
        
        2. **파일 확인**: 업로드된 파일이 올바르게 분류되었는지 확인합니다.
        
        3. **통합 시작**: "파일 통합 시작" 버튼을 클릭합니다.
        
        4. **데이터 확인**: 통합된 데이터를 미리보기로 확인합니다.
        
        5. **다운로드**: "통합 엑셀 파일 다운로드" 버튼을 클릭하여 파일을 저장합니다.
        
        ### 기능
        
        - ✅ 세 파일 **한번에 드래그 앤 드롭** 가능
        - ✅ 파일명 기반 자동 분류 (DAD, DMC, TA)
        - ✅ 세 파일의 `raw` 시트 자동 병합
        - ✅ 출처 파일 구분 (Source_File 컬럼 추가)
        - ✅ 날짜 기준 정렬
        - ✅ 필터링 기능 (출처, 캠페인)
        - ✅ 통계 정보 표시
        - ✅ 엑셀 파일 다운로드
        
        ### 주의사항
        
        - **정확히 3개의 파일**을 업로드해야 합니다.
        - 파일명에 'DAD', 'DMC', 'TA'가 반드시 포함되어야 합니다.
        - 모든 파일에 `raw` 시트가 있어야 합니다.
        - 파일 형식은 `.xlsx` 만 지원됩니다.
        """)

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>LEGO Report 통합 관리 시스템 v1.0</div>",
    unsafe_allow_html=True
)