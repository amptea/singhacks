"""
MAS Regulation Scraping Results Viewer
Streamlit-based interface for viewing regulatory compliance comparison results
"""

import streamlit as st
import json
import os
import pandas as pd
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
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Data", "📊 Transaction Viewer", "📋 Clause Comparison", "🔍 Raw Data"])
    
    with tab1:
        st.header("📁 Data Upload")
        st.markdown("""
        Upload your CSV file containing transaction data for validation against MAS Notice 626 requirements.
        The uploaded data will be cross-referenced with regulatory clauses for compliance analysis.
        """)
        
        # File uploader with drag & drop
        uploaded_file = st.file_uploader(
            "Drag and drop your CSV file here",
            type=['csv'],
            help="Upload a CSV file with transaction data for compliance validation"
        )
        
        if uploaded_file is not None:
            # File info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            
            st.json(file_details)
            
            # Preview upload
            st.success("✅ File uploaded successfully!")
            
            try:
                # Read CSV file
                df = pd.read_csv(uploaded_file)
                
                st.subheader("📊 Data Preview")
                st.markdown(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
                
                # Display first few rows
                st.dataframe(df.head(10), use_container_width=True)
                
                # Column info
                with st.expander("📋 Column Details"):
                    col_info = pd.DataFrame({
                        'Column': df.columns,
                        'Type': df.dtypes.astype(str),
                        'Non-Null Count': df.count(),
                        'Null Count': df.isnull().sum()
                    })
                    st.dataframe(col_info, use_container_width=True)
                
                st.markdown("---")
                
                # Risk Analysis Section
                st.subheader("🔍 Run Risk Analysis")
                st.markdown("""
                Analyze the uploaded transactions for money laundering risk using AI-powered analysis.
                Each transaction will be evaluated against MAS Notice 626 AML/CFT requirements.
                """)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Option to limit number of transactions
                    analyze_all = st.checkbox("Analyze all transactions", value=True)
                    if not analyze_all:
                        max_transactions = st.number_input(
                            "Number of transactions to analyze",
                            min_value=1,
                            max_value=len(df),
                            value=min(10, len(df)),
                            step=1
                        )
                    else:
                        max_transactions = len(df)
                
                with col2:
                    st.metric("Transactions to Analyze", max_transactions)
                
                # Save uploaded file temporarily for analysis
                temp_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "temp_uploaded_transactions.csv")
                
                if st.button("🚀 Start Risk Analysis", type="primary", use_container_width=True):
                    # Save the uploaded file
                    df.to_csv(temp_csv_path, index=False)
                    
                    # Import and run the analysis agent
                    try:
                        import sys
                        agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "agents", "part1")
                        if agent_path not in sys.path:
                            sys.path.insert(0, agent_path)
                        
                        from risk_analysis_agent import analyze_transactions
                        
                        with st.spinner(f"🔄 Analyzing {max_transactions} transaction(s)... This may take a few minutes."):
                            # Create a progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Set output path
                            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
                            output_csv = os.path.join(output_dir, "transactions_analysis_results.csv")
                            
                            status_text.text("Initializing analysis...")
                            progress_bar.progress(10)
                            
                            # Run the analysis
                            limit = None if analyze_all else max_transactions
                            analyze_transactions(
                                transactions_csv=temp_csv_path,
                                output_csv=output_csv,
                                limit=limit
                            )
                            
                            progress_bar.progress(100)
                            status_text.text("Analysis complete!")
                            
                        st.success(f"✅ Analysis completed! {max_transactions} transaction(s) analyzed.")
                        st.info("📊 View the results in the **Transaction Viewer** tab above.")
                        
                        # Add a button to switch to the viewer tab
                        st.markdown("---")
                        if st.button("📈 View Analysis Results", use_container_width=True):
                            st.session_state.switch_to_viewer = True
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                        st.info("Please ensure all dependencies are installed and the risk analysis agent is properly configured.")
                        with st.expander("Show Error Details"):
                            st.code(str(e))
                
                st.markdown("---")
                
                # Download processed data option
                st.download_button(
                    label="💾 Download Uploaded Data",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
                st.info("Please ensure the file is a valid CSV format (.csv)")
    
    with tab2:
        
        # Add refresh button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        # Path to the risk analysis output CSV
        output_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output", "transactions_analysis_results.csv")
        
        if os.path.exists(output_csv_path):
            try:
                # Load the analysis results
                results_df = pd.read_csv(output_csv_path)
                
                st.subheader(f"📈 Total Transactions Analyzed: {len(results_df)}")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Count risk levels
                risk_counts = results_df['risk_label'].value_counts()
                
                with col1:
                    high_risk = risk_counts.get('High', 0)
                    st.metric("🔴 High Risk", high_risk)
                
                with col2:
                    medium_risk = risk_counts.get('Medium', 0)
                    st.metric("🟡 Medium Risk", medium_risk)
                
                with col3:
                    low_risk = risk_counts.get('Low', 0)
                    st.metric("🟢 Low Risk", low_risk)
                
                with col4:
                    avg_score = results_df['score'].mean()
                    st.metric("📊 Avg Risk Score", f"{avg_score:.1f}/100")
                
                st.markdown("---")
                
                # Filter options
                st.subheader("🔍 Filter Transactions")
                
                # Simple dropdown filter
                risk_filter = st.selectbox(
                    "Filter by Risk Level",
                    options=['All', 'High', 'Medium', 'Low', 'Error'],
                    index=0
                )
                
                # Apply filter
                if risk_filter == 'All':
                    filtered_df = results_df.copy()
                else:
                    filtered_df = results_df[results_df['risk_label'] == risk_filter]
                
                st.markdown(f"**Showing {len(filtered_df)} of {len(results_df)} transactions**")
                
                # Display transactions table
                st.subheader("📋 Transaction Analysis Results")
                st.caption("💡 Click on any row to view detailed analysis below")
                
                # Format the dataframe for display
                display_df = filtered_df.copy()
                
                # Add color emoji to risk level
                def add_risk_emoji(risk_level):
                    if risk_level == 'High':
                        return '🔴 High'
                    elif risk_level == 'Medium':
                        return '🟡 Medium'
                    elif risk_level == 'Low':
                        return '🟢 Low'
                    else:
                        return '⚫ Error'
                
                display_df['risk_label'] = display_df['risk_label'].apply(add_risk_emoji)
                
                # Reorder columns for better display - put important columns first
                column_order = ['transaction_id', 'risk_label', 'score', 'matched_rules', 'explanation']
                display_columns = [col for col in column_order if col in display_df.columns]
                display_df = display_df[display_columns]
                
                # Rename columns for better readability
                display_df = display_df.rename(columns={
                    'transaction_id': 'Transaction ID',
                    'risk_label': 'Risk Level',
                    'score': 'Risk Score',
                    'matched_rules': 'Matched Rules',
                    'explanation': 'Explanation'
                })
                
                # Display interactive dataframe with selection
                event = st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    on_select="rerun",
                    selection_mode="single-row",
                    hide_index=True
                )
                
                # Detailed view based on selection
                st.markdown("---")
                st.subheader("🔎 Detailed Transaction View")
                
                if len(filtered_df) > 0:
                    # Check if a row is selected
                    if event.selection and len(event.selection.rows) > 0:
                        selected_idx = event.selection.rows[0]
                        tx_data = display_df.iloc[selected_idx]
                        
                        detail_col1, detail_col2 = st.columns([1, 2])
                        
                        with detail_col1:
                            st.markdown("**Transaction Details**")
                            st.write(f"**Transaction ID:** {tx_data['Transaction ID']}")
                            st.write(f"**Risk Level:** {tx_data['Risk Level']}")
                            st.write(f"**Risk Score:** {tx_data['Risk Score']}/100")
                            
                            # Display matched rules
                            if 'Matched Rules' in tx_data and pd.notna(tx_data['Matched Rules']):
                                try:
                                    matched_rules = eval(tx_data['Matched Rules']) if isinstance(tx_data['Matched Rules'], str) else tx_data['Matched Rules']
                                    st.write(f"**Matched Rules:** {len(matched_rules)}")
                                    for rule in matched_rules:
                                        st.write(f"- {rule}")
                                except:
                                    st.write(f"**Matched Rules:** {tx_data['Matched Rules']}")
                        
                        with detail_col2:
                            st.markdown("**Analysis Explanation**")
                            st.info(tx_data['Explanation'])
                    else:
                        st.info("👆 Click on a row in the table above to view detailed analysis")
                
                # Download filtered results
                st.markdown("---")
                csv_download = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download Filtered Results (CSV)",
                    data=csv_download,
                    file_name="filtered_transaction_analysis.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error loading transaction analysis results: {str(e)}")
                st.info("Please ensure the risk analysis agent has been run and the output file exists.")
        else:
            st.warning("⚠️ No transaction analysis results found")
            st.info(f"""
            **To view transaction analysis:**
            1. Run the risk analysis agent: `python agents/part1/risk_analysis_agent.py`
            2. The analysis results will be saved to: `{output_csv_path}`
            3. Refresh this page to view the results
            
            Alternatively, you can upload transaction data in the **Data** tab and run the analysis from there.
            """)
    
    with tab3:
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
