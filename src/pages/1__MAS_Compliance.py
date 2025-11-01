"""
MAS Regulation Scraping Results Viewer
Streamlit-based interface for viewing regulatory compliance comparison results
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="MAS Regulation Compliance Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling (matching pdf_ocr_ui style)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stTable {
        border: 1px solid #ddd;
        border-radius: 5px;
        overflow: hidden;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-consistent {
        color: #28a745;
        font-weight: bold;
    }
    .status-different {
        color: #dc3545;
        font-weight: bold;
    }
    .status-missing {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def load_scraping_results(file_path):
    """Load scraping results from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Error loading results: {e}")
        return None

def format_timestamp(timestamp_str):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return timestamp_str

def display_document_match_table(document_match):
    """Display document match comparison as table"""
    st.subheader("📄 Document Match Verification")
    
    match_data = []
    all_match = True
    
    for key, value in document_match.items():
        field_name = key.replace('_', ' ').title()
        status = "✅ Match" if value.startswith("Match") else "⚠️ Different"
        clean_value = value.replace("Match - ", "") if value.startswith("Match") else value
        
        if not value.startswith("Match"):
            all_match = False
        
        match_data.append({
            "Field": field_name,
            "Value": clean_value,
            "Status": status
        })
    
    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(match_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if all_match:
        st.markdown('<div class="success-box">✅ All document metadata matches perfectly!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">⚠️ Some document metadata differs. Please review above.</div>', unsafe_allow_html=True)

def display_clause_comparison_table(clause_comparison):
    """Display clause-by-clause comparison as table"""
    st.subheader("📋 Clause-by-Clause Comparison")
    
    clause_data = []
    status_counts = {"CONSISTENT": 0, "DIFFERENT": 0, "MISSING": 0}
    
    for clause in clause_comparison:
        status = clause.get('status', 'UNKNOWN')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Format status with color
        if status == "CONSISTENT":
            status_display = "✅ CONSISTENT"
        elif status == "DIFFERENT":
            status_display = "❌ DIFFERENT"
        elif status == "MISSING":
            status_display = "⚠️ MISSING"
        else:
            status_display = status
        
        sub_clauses = ", ".join(clause.get('sub_clauses_checked', []))
        
        clause_data.append({
            "Clause ID": clause.get('clause_id', 'N/A'),
            "Clause Title": clause.get('clause_title', 'N/A'),
            "Status": status_display,
            "Sub-clauses Checked": sub_clauses,
            "Details": clause.get('details', 'N/A')[:200] + "..." if len(clause.get('details', '')) > 200 else clause.get('details', 'N/A')
        })
    
    # Display as dataframe
    import pandas as pd
    df = pd.DataFrame(clause_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Status summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Consistent", status_counts.get("CONSISTENT", 0))
    with col2:
        st.metric("❌ Different", status_counts.get("DIFFERENT", 0))
    with col3:
        st.metric("⚠️ Missing", status_counts.get("MISSING", 0))
    
    # Full details expander
    with st.expander("📖 View Full Clause Details"):
        for clause in clause_comparison:
            st.markdown(f"**{clause.get('clause_id')}**: {clause.get('clause_title')}")
            st.markdown(f"**Status**: {clause.get('status')}")
            st.markdown(f"**Details**: {clause.get('details')}")
            st.markdown("---")

def display_overall_assessment(overall_assessment):
    """Display overall assessment with metrics"""
    st.subheader("📊 Overall Assessment")
    
    consistency_score = overall_assessment.get('consistency_score', 'N/A')
    critical_differences = overall_assessment.get('critical_differences', [])
    minor_differences = overall_assessment.get('minor_differences', [])
    conclusion = overall_assessment.get('conclusion', 'N/A')
    
    # Consistency score display
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Consistency Score", consistency_score)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Critical differences
        if critical_differences:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.markdown("**🚨 Critical Differences:**")
            for diff in critical_differences:
                st.markdown(f"- {diff}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ No critical differences found!</div>', unsafe_allow_html=True)
        
        # Minor differences
        if minor_differences:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**ℹ️ Minor Differences:**")
            for diff in minor_differences:
                st.markdown(f"- {diff}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Conclusion
    st.markdown("**Conclusion:**")
    st.info(conclusion)

def display_pdf_documents_table(documents):
    """Display scraped PDF documents as table"""
    st.subheader("📑 Scraped Documents")
    
    doc_data = []
    for doc in documents:
        doc_data.append({
            "Title": doc.get('title', 'N/A'),
            "URL": doc.get('url', 'N/A'),
            "PDF Links": len(doc.get('pdf_links', [])),
            "PDF Content Length": f"{doc.get('pdf_full_length', 0):,} characters"
        })
    
    import pandas as pd
    df = pd.DataFrame(doc_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show PDF links in expander
    for i, doc in enumerate(documents):
        with st.expander(f"📄 View PDF Links for: {doc.get('title', 'Document')}"):
            pdf_links = doc.get('pdf_links', [])
            if pdf_links:
                link_data = []
                for link in pdf_links:
                    link_data.append({
                        "Link Text": link.get('link_text', 'N/A'),
                        "PDF URL": link.get('pdf_url', 'N/A')
                    })
                pdf_df = pd.DataFrame(link_data)
                st.dataframe(pdf_df, use_container_width=True, hide_index=True)
            else:
                st.info("No PDF links found")

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">📊 MAS Regulation Compliance Viewer</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # File path input
        default_path = os.path.join(os.getcwd(), "data", "scraping_results.json")
        file_path = st.text_input(
            "Results File Path",
            value=default_path,
            help="Path to scraping_results.json"
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.session_state.data = load_scraping_results(file_path)
            st.rerun()
        
        # Auto-load on startup
        if 'data' not in st.session_state:
            st.session_state.data = load_scraping_results(file_path)
        
        st.markdown("---")
        
        # Info section
        st.info("""
        **About this tool:**
        - View MAS regulation scraping results
        - Compare regulatory documents
        - Monitor compliance status
        - Track clause-by-clause changes
        """)
        
        # Display execution info if data loaded
        if st.session_state.data:
            st.markdown("---")
            st.subheader("📅 Last Execution")
            exec_time = st.session_state.data.get('execution_time', 'N/A')
            st.text(format_timestamp(exec_time))
            
            # Quick stats
            scraped_data = st.session_state.data.get('scraped_data', {})
            st.metric("Documents Found", scraped_data.get('documents_found', 0))
    
    # Main content
    if st.session_state.data is None:
        st.error("❌ Failed to load data. Please check the file path.")
        return
    
    # Get data sections
    scraped_data = st.session_state.data.get('scraped_data', {})
    mas_json_info = st.session_state.data.get('mas_json_info', {})
    comparison = st.session_state.data.get('comparison', {})
    
    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Clause Comparison", "📑 Documents", "🔍 Raw Data"])
    
    with tab1:
        st.header("Overview & Summary")
        
        # MAS JSON Info
        st.subheader("📘 Reference Document (mas.json)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Notice Number", mas_json_info.get('notice_number', 'N/A'))
        with col2:
            st.metric("Effective Date", mas_json_info.get('effective_date', 'N/A'))
        with col3:
            st.metric("Last Revised", mas_json_info.get('last_revised', 'N/A'))
        
        st.text(mas_json_info.get('title', 'N/A'))
        
        st.markdown("---")
        
        # Comparison results
        if 'analysis' in comparison:
            # Try to parse JSON from analysis
            try:
                analysis_text = comparison['analysis']
                # Extract JSON from markdown code block if present
                if "```json" in analysis_text:
                    json_start = analysis_text.find("```json") + 7
                    json_end = analysis_text.find("```", json_start)
                    json_str = analysis_text[json_start:json_end].strip()
                    analysis_data = json.loads(json_str)
                else:
                    analysis_data = json.loads(analysis_text)
                
                # Display document match
                if 'document_match' in analysis_data:
                    display_document_match_table(analysis_data['document_match'])
                
                st.markdown("---")
                
                # Display overall assessment
                if 'overall_assessment' in analysis_data:
                    display_overall_assessment(analysis_data['overall_assessment'])
                    
            except Exception as e:
                st.warning(f"⚠️ Could not parse analysis JSON: {e}")
                st.text_area("Raw Analysis", comparison.get('analysis', 'N/A'), height=300)
    
    with tab2:
        st.header("Clause-by-Clause Comparison")
        
        # Try to extract clause comparison from analysis
        try:
            analysis_text = comparison.get('analysis', '')
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                json_str = analysis_text[json_start:json_end].strip()
                analysis_data = json.loads(json_str)
            else:
                analysis_data = json.loads(analysis_text)
            
            if 'clause_by_clause_comparison' in analysis_data:
                display_clause_comparison_table(analysis_data['clause_by_clause_comparison'])
            else:
                st.info("No clause-by-clause comparison data available")
                
        except Exception as e:
            st.warning(f"⚠️ Could not load clause comparison: {e}")
    
    with tab3:
        st.header("Scraped Documents")
        
        documents = scraped_data.get('documents', [])
        if documents:
            display_pdf_documents_table(documents)
            
            # Show PDF content preview
            with st.expander("📖 View PDF Content Preview"):
                for doc in documents:
                    st.markdown(f"**{doc.get('title', 'Document')}**")
                    pdf_content = doc.get('pdf_content', 'N/A')
                    preview_length = min(2000, len(pdf_content))
                    st.text_area(
                        "First 2000 characters",
                        pdf_content[:preview_length] + ("..." if len(pdf_content) > preview_length else ""),
                        height=300
                    )
        else:
            st.info("No documents found in scraping results")
    
    with tab4:
        st.header("Raw Data")
        
        # Display full JSON
        st.subheader("📄 Full JSON Data")
        st.json(st.session_state.data)
        
        # Download button
        json_str = json.dumps(st.session_state.data, indent=2)
        st.download_button(
            label="💾 Download Raw JSON",
            data=json_str,
            file_name="scraping_results.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**MAS Regulation Compliance Viewer** | "
        "Data source: MAS website regulatory scraping agent"
    )

if __name__ == "__main__":
    main()
