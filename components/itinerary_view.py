import streamlit as st
import json
import base64
from typing import Optional, Dict, Any, List
import database as db
from auth import get_current_user

def render_itinerary_view(active_trip: Optional[Dict[str, Any]] = None, **kwargs):

    st.markdown("### 🗺️ Interactive Trip Itinerary & Cumulative Budget")

    user = get_current_user()
    if not user:
        st.warning("Please sign in or continue as Guest to access saved itineraries.")
        return

    if not active_trip:
        st.info("No active trip selected. Set up a trip in the 'Trip Setup' tab first.")
        return

    trip_id = active_trip["id"]
    curr = active_trip["currency"]
    scans = db.get_trip_scans(trip_id)

    # Calculate cumulative totals
    daily_budget = float(active_trip["daily_budget_limit"])
    duration_days = int(active_trip["duration_days"])
    total_budget = daily_budget * duration_days

    total_spent = sum(s["total_cost"] for s in scans)
    total_ticket = sum(s["ticket_cost"] for s in scans)
    total_transport = sum(s["transport_cost"] for s in scans)
    total_food = sum(s["food_cost"] for s in scans)
    remaining_budget = total_budget - total_spent

    # Cumulative Budget Summary Card
    st.markdown("#### 💳 Cumulative Spending Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trip Budget", f"{curr} {total_budget:,.2f}", f"{duration_days} Days")
    with col2:
        st.metric("Total Spent", f"{curr} {total_spent:,.2f}")
    with col3:
        delta_color = "normal" if remaining_budget >= 0 else "inverse"
        st.metric("Remaining Budget", f"{curr} {remaining_budget:,.2f}", delta=f"{curr} {remaining_budget:,.2f}", delta_color=delta_color)
    with col4:
        avg_per_day = total_spent / duration_days if duration_days > 0 else 0
        st.metric("Daily Avg Spent", f"{curr} {avg_per_day:,.2f}", f"Target: {curr} {daily_budget:,.2f}")

    # Progress bar and status banner
    progress_val = min(1.0, max(0.0, total_spent / total_budget if total_budget > 0 else 0))
    st.progress(progress_val)

    if remaining_budget < 0:
        st.error(f"⚠️ Budget Alert: You have exceeded your trip budget by {curr} {abs(remaining_budget):,.2f}! Consider low-cost/free recommendations.")
    elif progress_val > 0.8:
        st.warning(f"🔔 You have utilized {progress_val * 100:.1f}% of your total budget. {curr} {remaining_budget:,.2f} remaining.")
    else:
        st.success(f"✨ On Track: You have {curr} {remaining_budget:,.2f} ({100 - (progress_val * 100):.1f}%) remaining in your budget.")

    # Category Breakdown Cards
    st.markdown("##### 🏷️ Category Spending Breakdown")
    cat1, cat2, cat3 = st.columns(3)
    with cat1:
        st.markdown(f"""
        <div class="cost-box">
            <div class="cost-label">🎟️ Tickets & Entry</div>
            <div class="cost-val">{curr} {total_ticket:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with cat2:
        st.markdown(f"""
        <div class="cost-box">
            <div class="cost-label">🚕 Local Transit</div>
            <div class="cost-val">{curr} {total_transport:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with cat3:
        st.markdown(f"""
        <div class="cost-box">
            <div class="cost-label">🥪 Food & Dining</div>
            <div class="cost-val">{curr} {total_food:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # List of Saved Stops in this Trip
    st.markdown(f"#### 📍 Visited Landmarks & Stops ({len(scans)})")

    if not scans:
        st.info("No landmarks saved for this trip yet. Go to the **Snap & Identify** tab to snap photos and add your first stop!")
        return

    for idx, scan in enumerate(scans, 1):
        with st.container():
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #1E293B;">Stop #{idx}: {scan['landmark_name']}</h4>
                        <span style="font-weight: 700; color: #059669; font-size: 1.1rem;">{curr} {scan['total_cost']:,.2f}</span>
                    </div>
                    <div style="color: #64748B; font-size: 0.88rem; margin-top: 4px;">📍 {scan['location']} | Scanned: {scan['scanned_at']}</div>
                    <div style="display: flex; gap: 15px; margin-top: 10px; font-size: 0.85rem; color: #475569;">
                        <span>🎟️ Ticket: <b>{curr} {scan['ticket_cost']:,.2f}</b></span>
                        <span>🚕 Transit: <b>{curr} {scan['transport_cost']:,.2f}</b></span>
                        <span>🥪 Food: <b>{curr} {scan['food_cost']:,.2f}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"📜 View Details & Tips for {scan['landmark_name']}"):
                    if scan.get("history_points"):
                        st.markdown("**Historical Significance:**")
                        for hp in scan["history_points"]:
                            st.markdown(f"- {hp}")
                    if scan.get("local_tips"):
                        st.markdown("**Insider Tips:**")
                        for tip in scan["local_tips"]:
                            st.markdown(f"- {tip}")
                    if scan.get("nearby_attractions"):
                        st.markdown("**Recommended Next Spots:**")
                        for na in scan["nearby_attractions"]:
                            st.markdown(f"- **{na.get('name')}** ({na.get('distance', '')}): {na.get('highlights', '')} — *Est: {curr} {na.get('estimated_cost', 0)}*")

            with col_del:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete", key=f"del_scan_{scan['id']}", use_container_width=True):
                    db.delete_scan(scan["id"])
                    st.success("Deleted stop.")
                    st.rerun()

    # Export Itinerary Feature
    st.divider()
    st.markdown("#### 📤 Export Itinerary")
    exp_col1, exp_col2 = st.columns(2)

    # Generate Markdown Itinerary
    md_lines = [
        f"# Trip Itinerary: {active_trip['trip_name']}",
        f"- **Destination:** {active_trip['destination_city']}",
        f"- **Duration:** {duration_days} Days",
        f"- **Budget Tier:** {active_trip['budget_tier']}",
        f"- **Daily Budget Limit:** {curr} {daily_budget:,.2f}",
        f"- **Total Budget:** {curr} {total_budget:,.2f}",
        f"- **Total Spent:** {curr} {total_spent:,.2f}",
        f"- **Remaining Balance:** {curr} {remaining_budget:,.2f}\n",
        "## Visited Landmarks & Expenses\n"
    ]
    for idx, s in enumerate(scans, 1):
        md_lines.append(f"### Stop {idx}: {s['landmark_name']}")
        md_lines.append(f"- **Location:** {s['location']}")
        md_lines.append(f"- **Visit Cost:** {curr} {s['total_cost']:,.2f} (Ticket: {curr} {s['ticket_cost']:,.2f}, Transit: {curr} {s['transport_cost']:,.2f}, Food: {curr} {s['food_cost']:,.2f})")
        if s.get("history_points"):
            md_lines.append("- **Historical Highlights:**")
            for hp in s["history_points"]:
                md_lines.append(f"  * {hp}")
        md_lines.append("")

    markdown_export = "\n".join(md_lines)

    # Generate JSON Export
    json_export = json.dumps({
        "trip": active_trip,
        "summary": {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "remaining_budget": remaining_budget,
            "stops_count": len(scans)
        },
        "stops": scans
    }, indent=2)

    with exp_col1:
        st.download_button(
            label="📄 Download Itinerary (Markdown)",
            data=markdown_export,
            file_name=f"{active_trip['trip_name'].replace(' ', '_')}_itinerary.md",
            mime="text/markdown",
            use_container_width=True
        )

    with exp_col2:
        st.download_button(
            label="💾 Download Raw Data (JSON)",
            data=json_export,
            file_name=f"{active_trip['trip_name'].replace(' ', '_')}_data.json",
            mime="application/json",
            use_container_width=True
        )

