import streamlit as st

def apply_custom_styles():
    """Injects modern, responsive CSS styles into Streamlit."""
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* App Header / Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        border-radius: 20px;
        padding: 30px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #FFE66D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #E2E8F0;
        margin-top: 8px;
        font-weight: 400;
    }

    /* Feature Badge */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .badge-budget {
        background: rgba(78, 205, 196, 0.15);
        color: #0d9488;
        border: 1px solid rgba(78, 205, 196, 0.4);
    }
    .badge-moderate {
        background: rgba(59, 130, 246, 0.15);
        color: #2563eb;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    .badge-luxury {
        background: rgba(245, 158, 11, 0.15);
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    /* Modern Card Container */
    .trip-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .trip-card:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    }

    /* Landmark Detail Header */
    .landmark-header-card {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin-bottom: 18px;
        border-left: 6px solid #4ECDC4;
    }
    .landmark-name {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    .landmark-loc {
        font-size: 0.95rem;
        color: #94A3B8;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Budget Breakdown Grid */
    .cost-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .cost-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 12px;
        text-align: center;
    }
    .cost-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .cost-val {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .cost-total-box {
        background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
        border: 1px solid #A7F3D0;
    }
    .cost-total-box .cost-val {
        color: #065F46;
    }

    /* Recommendation Spot Cards */
    .spot-card {
        background: #F8FAFC;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        margin-bottom: 12px;
    }
    .spot-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .spot-dist {
        font-size: 0.8rem;
        font-weight: 600;
        color: #4ECDC4;
        background: #E6FFFA;
        padding: 2px 8px;
        border-radius: 12px;
    }
    .spot-desc {
        font-size: 0.88rem;
        color: #475569;
        margin-top: 6px;
    }
    .spot-cost {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0284C7;
        margin-top: 4px;
    }

    /* Cumulative Budget Progress */
    .budget-status-box {
        background: #F1F5F9;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 20px;
        border: 1px solid #CBD5E1;
    }

    /* Streamlit Button Tweaks */
    div.stButton > button:first-child {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Responsive Mobile Adjustments */
    @media (max-width: 768px) {
        .hero-banner {
            padding: 20px;
        }
        .hero-title {
            font-size: 1.6rem;
        }
        .cost-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    /* Transit Card Styles */
    .transit-container {
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        margin-top: 25px;
        margin-bottom: 25px;
    }
    .transit-hero {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
        color: white;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .transit-route {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.3px;
    }
    .transit-dist-pill {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .transit-mode-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
        transition: transform 0.15s ease;
    }
    .transit-mode-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    .fare-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 8px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .fare-pill {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 8px 10px;
        text-align: center;
    }
    .fare-class {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
    }
    .fare-price {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 2px;
    }
    .water-callout {
        background: #EFF6FF;
        border-left: 5px solid #3B82F6;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 10px;
        font-size: 0.9rem;
        color: #1E3A8A;
    }
    </style>
    """, unsafe_allow_html=True)


