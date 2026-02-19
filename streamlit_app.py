import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="LEGO Report 통합 관리",
    page_icon="📊",
    layout="wide"
)

st.title("📊 LEGO Report 통합 관리 시스템")
st.markdown("---")

# ==================== 함수 정의 ====================

def read_raw_sheet(file, file_name):
    """DAD, DMC, TA 파일의 raw 시트 읽기 (9번 행이 헤더)"""
    try:
        df = pd.read_excel(file, sheet_name='raw', skiprows=9)
        df = df.dropna(how='all')
        df.insert(0, 'Source_File', file_name)
        return df
    except Exception as e:
        st.error(f"{file_name} 파일 읽기 오류: {str(e)}")
        return None

def load_pca_template(file):
    """PCA 템플릿에서 맵핑 정보 추출"""
    try:
        df_full = pd.read_excel(file, sheet_name='Raw PCA Data', header=None)
        
        # 2번 행: 통합리포트 항목
        mapping_from = df_full.iloc[1].tolist()
        # 3번 행: PCA 항목
        mapping_to = df_full.iloc[2].tolist()
        
        # 맵핑 딕셔너리 생성
        mapping_dict = {}
        for from_col, to_col in zip(mapping_from, mapping_to):
            if pd.notna(from_col) and pd.notna(to_col):
                from_key = str(from_col).strip()
                to_key = str(to_col).strip()
                if from_key not in ['공란', '해당 항목 수기 선택', '통합리포트 항목', 'nan']:
                    mapping_dict[from_key] = to_key
        
        # PCA 헤더 순서
        pca_headers = [str(col).strip() for col in mapping_to if pd.notna(col) and str(col).strip() != '']
        
        return mapping_dict, pca_headers
    except Exception as e:
        st.error(f"PCA 템플릿 로드 오류: {str(e)}")
        return {}, []

def convert_to_pca_format(df, mapping_dict, pca_headers):
    """통합 리포트 데이터를 PCA 형식으로 변환"""
    try:
        pca_df = pd.DataFrame()
        
        for int_col, pca_col in mapping_dict.items():
            if int_col in df.columns:
                pca_df[pca_col] = df[int_col]
            else:
                pca_df[pca_col] = None
        
        # PCA 헤더 순서대로 재정렬
        existing_cols = [col for col in pca_headers if col in pca_df.columns]
        pca_df = pca_df[existing_cols]
        
        return pca_df
    except Exception as e:
        st.error(f"PCA 변환 오류: {str(e)}")
        return pd.DataFrame()

def format_dataframe(df):
    """데이터 포맷팅: 천단위 쉼표, % 표시"""
    formatted_df = df.copy()
    
    for col in formatted_df.columns:
        col_upper = str(col).upper()
        
        if 'YEAR' in col_upper:
            continue
            
        # CTR, VTR 등 비율은 % 표시
        if any(keyword in col_upper for keyword in ['CTR', 'VTR', 'RATE', 'RATIO', '%']):
            try:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x*100:.3f}%" if pd.notna(x) and isinstance(x, (int, float)) else x
                )
            except:
                pass
        # 숫자는 천단위 구분
        else:
            try:
                col_dtype = str(formatted_df[col].dtype)
                if col_dtype in ['int64', 'float64', 'int32', 'float32']:
                    formatted_df[col] = formatted_df[col].apply(
                        lambda x: f"{x:,.0f}" if pd.notna(x) else x
                    )
            except:
                pass
    
    return formatted_df

def save_to_excel(df):
    """데이터프레임을 엑셀로 저장"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='raw', index=False)
    output.seek(0)
    return output

def classify_files(uploaded_files):
    """파일 자동 분류"""
    dad_file = dmc_file = ta_file = None
    
    for file in uploaded_files:
        filename = file.name.upper()
        if 'DAD' in filename:
            dad_file = file
        elif 'DMC' in filename:
            dmc_file = file
        elif 'TA' in filename:
            ta_file = file
    
    return dad_file, dmc_file, ta_file

# ==================== 사이드바 ====================

st.sidebar.header("⚙️ 파일 업로드")

# 1. 데이터 파일 업로드
uploaded_files = st.sidebar.file_uploader(
    "📁 DAD, DMC, TA 파일 (3개)",
    type=['xlsx'],
    accept_multiple_files=True,
    key="data_files"
)

# 2. PCA 템플릿 업로드
pca_template = st.sidebar.file_uploader(
    "📋 PCA 템플릿 파일",
    type=['xlsx'],
    key="pca_template",
    help="PCA_import_final.xlsx"
)

# ==================== 메인 로직 ====================

if not uploaded_files:
    st.info("👆 왼쪽 사이드바에서 파일을 업로드해주세요")
    
    with st.expander("📖 사용 방법"):
        st.markdown("""
        ### 📂 필요한 파일
        1. **DAD, DMC, TA 파일** (3개) - 통합 리포트용
        2. **PCA 템플릿 파일** (1개) - PCA 형식 변환용
        
        ### 🔄 프로세스
        1. **1단계**: 통합 리포트 생성 (DAD+DMC+TA)
        2. **2단계**: 캠페인 선택 (PCA에 포함할 데이터)
        3. **3단계**: PCA 리포트 생성 (자동 형식 변환)
        
        ### ✨ 기능
        - 천단위 구분 쉼표 자동 적용
        - CTR, VTR 등 % 수치는 소수점 3자리
        - PCA 템플릿 기반 자동 컬럼 매핑
        """)

elif len(uploaded_files) != 3:
    st.warning(f"⚠️ {len(uploaded_files)}개 파일이 업로드됨. 정확히 3개 필요합니다.")
    for file in uploaded_files:
        st.write(f"- {file.name}")

else:
    # 파일 분류
    dad_file, dmc_file, ta_file = classify_files(uploaded_files)
    
    # 파일 확인
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"✅ DAD: {dad_file.name}" if dad_file else "❌ DAD 없음")
    with col2:
        st.success(f"✅ DMC: {dmc_file.name}" if dmc_file else "❌ DMC 없음")
    with col3:
        st.success(f"✅ TA: {ta_file.name}" if ta_file else "❌ TA 없음")
    
    if not (dad_file and dmc_file and ta_file):
        st.error("❌ 파일명에 'DAD', 'DMC', 'TA'가 포함되어야 합니다")
    
    elif not pca_template:
        st.warning("⚠️ PCA 템플릿을 업로드해주세요")
    
    else:
        # PCA 템플릿 로드
        mapping_dict, pca_headers = load_pca_template(pca_template)
        
        if not mapping_dict:
            st.error("❌ PCA 템플릿 로드 실패")
        else:
            st.success(f"✅ 모든 파일 준비 완료! (PCA 매핑: {len(mapping_dict)}개)")
            
            # 파일 읽기 시작
            if 'processed' not in st.session_state:
                st.session_state.processed = False
            
            if st.button("🚀 파일 통합 시작", type="primary") or st.session_state.processed:
                if not st.session_state.processed:
                    st.session_state.processed = True
                    st.rerun()
                
                with st.spinner("파일 처리 중..."):
                    # 파일 읽기 (session_state에 저장)
                    if 'integrated_df' not in st.session_state:
                        dad_df = read_raw_sheet(dad_file, "DAD")
                        dmc_df = read_raw_sheet(dmc_file, "DMC")
                        ta_df = read_raw_sheet(ta_file, "TA")
                        
                        if dad_df is None or dmc_df is None or ta_df is None:
                            st.error("❌ 파일 읽기 실패")
                            st.session_state.processed = False
                            st.stop()
                        
                        # 통합
                        integrated_df = pd.concat([dad_df, dmc_df, ta_df], ignore_index=True)
                        
                        # 날짜 정렬
                        if 'date' in integrated_df.columns:
                            try:
                                integrated_df['date'] = pd.to_datetime(integrated_df['date'], errors='coerce')
                                integrated_df = integrated_df.sort_values('date', ascending=False)
                            except:
                                pass
                        
                        st.session_state.integrated_df = integrated_df
                        st.session_state.mapping_dict = mapping_dict
                        st.session_state.pca_headers = pca_headers
                    
                    integrated_df = st.session_state.integrated_df
                    mapping_dict = st.session_state.mapping_dict
                    pca_headers = st.session_state.pca_headers
                    
                    # 1번, 2번 컬럼 제거 (있으면)
                    cols_to_drop = []
                    for col in integrated_df.columns:
                        if str(col) in ['1', '2', 'Unnamed: 0', 'Unnamed: 1']:
                            cols_to_drop.append(col)
                    if cols_to_drop:
                        integrated_df = integrated_df.drop(columns=cols_to_drop)
                
                # ========== 1단계: 통합 리포트 ==========
                st.header("1️⃣ 통합 리포트 (DAD + DMC + TA)")
                
                st.success(f"✅ 통합 완료: {len(integrated_df):,} 행")
                
                with st.expander("📊 통합 리포트 미리보기", expanded=True):
                    st.dataframe(format_dataframe(integrated_df.head(50)), use_container_width=True, height=300)
                
                # 다운로드
                today = datetime.now().strftime("%Y%m%d")
                integrated_excel = save_to_excel(integrated_df)
                
                st.download_button(
                    "📥 통합 리포트 다운로드",
                    data=integrated_excel,
                    file_name=f"LEGO_Report_통합_{today}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
                
                # ========== 2단계: 캠페인 선택 ==========
                st.markdown("---")
                st.header("2️⃣ PCA 리포트용 캠페인 선택")
                
                if 'Campaign' not in integrated_df.columns:
                    st.error("❌ 'Campaign' 컬럼이 없습니다")
                    selected_campaigns = []
                    show_pca = False
                else:
                    all_campaigns = integrated_df['Campaign'].dropna().unique().tolist()
                    
                    st.info(f"💡 총 {len(all_campaigns)}개 캠페인 중 PCA에 포함할 캠페인을 선택하세요")
                    
                    selected_campaigns = st.multiselect(
                        "캠페인 선택 (다중 선택 가능)",
                        options=all_campaigns,
                        default=[],
                        key="campaign_selector"
                    )
                    
                    # 캠페인 선택 여부에 따라 PCA 섹션 표시
                    if selected_campaigns:
                        st.success(f"✅ {len(selected_campaigns)}개 캠페인 선택됨")
                        show_pca = True
                    else:
                        st.warning("⚠️ 캠페인을 선택하지 않으면 빈 PCA 템플릿만 다운로드됩니다")
                        show_pca = st.checkbox("빈 PCA 템플릿 다운로드로 이동", value=False)
                
                # ========== PCA 리포트 (조건부 표시) ==========
                if show_pca:
                    st.markdown("---")
                    
                    if selected_campaigns:
                        filtered_df = integrated_df[integrated_df['Campaign'].isin(selected_campaigns)].copy()
                        pca_df = convert_to_pca_format(filtered_df, mapping_dict, pca_headers)
                        
                        st.success(f"✅ {len(selected_campaigns)}개 캠페인, {len(pca_df):,}행 → PCA 형식 변환 완료")
                        
                        with st.expander("📋 PCA 리포트 미리보기", expanded=True):
                            st.dataframe(format_dataframe(pca_df.head(50)), use_container_width=True, height=300)
                        
                        # 다운로드
                        pca_excel = save_to_excel(pca_df)
                        
                        st.download_button(
                            "📥 PCA 리포트 다운로드",
                            data=pca_excel,
                            file_name=f"LEGO_Report_PCA_{today}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            key="download_pca"
                        )
                    else:
                        # 빈 템플릿
                        empty_pca = pd.DataFrame(columns=pca_headers)
                        empty_excel = save_to_excel(empty_pca)
                        
                        st.info("ℹ️ 선택된 캠페인이 없어 빈 PCA 템플릿을 제공합니다")
                        
                        st.download_button(
                            "📥 빈 PCA 템플릿 다운로드",
                            data=empty_excel,
                            file_name=f"LEGO_Report_PCA_Empty_{today}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_empty_pca"
                        )
                    
                    # ========== 통계 ==========
                    st.markdown("---")
                    st.subheader("📊 처리 결과")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("통합 리포트", f"{len(integrated_df):,} 행")
                    with col2:
                        st.metric("선택 캠페인", f"{len(selected_campaigns)} 개")
                    with col3:
                        if selected_campaigns:
                            st.metric("PCA 리포트", f"{len(pca_df):,} 행")
                        else:
                            st.metric("PCA 리포트", "0 행")

# 푸터
st.markdown("---")
st.caption("LEGO Report 통합 관리 시스템 v2.0")