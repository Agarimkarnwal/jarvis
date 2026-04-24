"""
JARVIS Web Dashboard - Holographic UI with Streamlit
Real-time monitoring, voice control, and interactive chat
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import psutil
import time
import threading
import queue
import random
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from voice_engine_v2 import VoiceEngineV2, PYAUDIO_AVAILABLE
from command_processor import CommandProcessor, CommandType

# Page config - MUST be first st call
st.set_page_config(
    page_title="JARVIS AI Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for EPIC holographic JARVIS theme
st.markdown("""
<style>
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #0a0a0a, #1a1a2e, #16213e, #0f3460, #1a1a2e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* JARVIS title - Iron Man style */
    .jarvis-title {
        font-size: 72px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #00d4ff 0%, #00ff88 25%, #00d4ff 50%, #0099cc 75%, #00d4ff 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        text-shadow: 0 0 60px rgba(0, 212, 255, 0.8), 0 0 120px rgba(0, 212, 255, 0.4);
        margin-bottom: 5px;
        letter-spacing: 8px;
        font-family: 'Orbitron', sans-serif;
    }
    
    @keyframes shine {
        to { background-position: 200% center; }
    }
    
    /* Holographic ring animation */
    .holo-ring {
        width: 200px;
        height: 200px;
        border: 3px solid transparent;
        border-top: 3px solid #00d4ff;
        border-radius: 50%;
        animation: spin 2s linear infinite;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Advanced glassmorphism cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 
            0 8px 32px 0 rgba(0, 212, 255, 0.1),
            inset 0 0 20px rgba(0, 212, 255, 0.05);
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        box-shadow: 
            0 12px 40px 0 rgba(0, 212, 255, 0.2),
            inset 0 0 30px rgba(0, 212, 255, 0.1);
        transform: translateY(-3px);
    }
    
    /* Glowing text effects */
    .glow-text {
        color: #00d4ff;
        text-shadow: 
            0 0 5px #00d4ff,
            0 0 10px #00d4ff,
            0 0 20px #00d4ff,
            0 0 40px #00d4ff;
        animation: flicker 3s infinite;
    }
    
    @keyframes flicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
        52% { opacity: 0.3; }
        54% { opacity: 1; }
    }
    
    /* Status indicators with pulse */
    .status-online {
        color: #00ff88;
        text-shadow: 0 0 10px #00ff88, 0 0 20px #00ff88;
        animation: pulse-green 2s infinite;
    }
    .status-offline {
        color: #ff4444;
        text-shadow: 0 0 10px #ff4444, 0 0 20px #ff4444;
        animation: pulse-red 2s infinite;
    }
    
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 5px #00ff88; }
        50% { box-shadow: 0 0 20px #00ff88, 0 0 40px #00ff88; }
    }
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 5px #ff4444; }
        50% { box-shadow: 0 0 20px #ff4444, 0 0 40px #ff4444; }
    }
    
    /* Enhanced chat messages with holographic borders */
    .user-message {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-left: 4px solid #00d4ff;
        padding: 12px 18px;
        margin: 8px 0;
        border-radius: 0 15px 15px 0;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.1);
    }
    .jarvis-message {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 255, 136, 0.05) 100%);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-left: 4px solid #00ff88;
        padding: 12px 18px;
        margin: 8px 0;
        border-radius: 0 15px 15px 0;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.1);
    }
    
    /* Futuristic buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 50%, #00d4ff 100%);
        background-size: 200% auto;
        color: white;
        border: 2px solid rgba(0, 212, 255, 0.5);
        border-radius: 30px;
        padding: 12px 25px;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 
            0 0 10px rgba(0, 212, 255, 0.3),
            0 4px 15px rgba(0, 212, 255, 0.2);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-position: right center;
        box-shadow: 
            0 0 20px rgba(0, 212, 255, 0.6),
            0 0 40px rgba(0, 212, 255, 0.3),
            0 6px 20px rgba(0, 212, 255, 0.4);
        transform: translateY(-3px) scale(1.02);
        border-color: #00d4ff;
    }
    
    /* Metric cards with neon glow */
    .metric-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 0, 0, 0.2) 100%);
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 
            0 4px 15px rgba(0, 212, 255, 0.1),
            inset 0 0 20px rgba(0, 212, 255, 0.05);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        box-shadow: 
            0 8px 25px rgba(0, 212, 255, 0.2),
            inset 0 0 30px rgba(0, 212, 255, 0.1);
        border-color: rgba(0, 212, 255, 0.6);
    }
    
    /* Section headers with underline glow */
    .section-header {
        color: #00d4ff;
        font-size: 24px;
        font-weight: bold;
        border-bottom: 2px solid rgba(0, 212, 255, 0.5);
        padding-bottom: 10px;
        margin-bottom: 20px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        background: rgba(0, 212, 255, 0.05);
        border: 2px solid rgba(0, 212, 255, 0.3);
        border-radius: 25px;
        color: #00d4ff;
        padding: 12px 20px;
        font-size: 16px;
        box-shadow: inset 0 0 10px rgba(0, 212, 255, 0.1);
    }
    .stTextInput>div>div>input:focus {
        border-color: #00d4ff;
        box-shadow: 
            inset 0 0 10px rgba(0, 212, 255, 0.2),
            0 0 20px rgba(0, 212, 255, 0.3);
    }
    
    /* Toggle styling */
    .stCheckbox {
        color: #00d4ff;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0, 212, 255, 0.05);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00d4ff, #0099cc);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00ff88, #00d4ff);
    }
    
    /* Animated orb */
    .jarvis-orb {
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(0,212,255,0.8) 0%, rgba(0,212,255,0.4) 40%, transparent 70%);
        border-radius: 50%;
        animation: orb-pulse 2s ease-in-out infinite;
        box-shadow: 0 0 60px rgba(0, 212, 255, 0.6);
    }
    
    @keyframes orb-pulse {
        0%, 100% { 
            transform: scale(1);
            opacity: 0.8;
        }
        50% { 
            transform: scale(1.1);
            opacity: 1;
        }
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        animation: typing 1.4s infinite;
        margin: 0 2px;
    }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'system_metrics' not in st.session_state:
    st.session_state.system_metrics = {
        'cpu_history': [],
        'memory_history': [],
        'timestamps': []
    }
if 'voice_active' not in st.session_state:
    st.session_state.voice_active = False
if 'command_processor' not in st.session_state:
    st.session_state.command_processor = CommandProcessor()
if 'voice_engine' not in st.session_state:
    st.session_state.voice_engine = VoiceEngineV2()

# Header with animated orb
header_col1, header_col2, header_col3 = st.columns([1, 2, 1])

with header_col1:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
        <div class="holo-ring" style="width: 80px; height: 80px;"></div>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown('<h1 class="jarvis-title">JARVIS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #00d4ff; font-size: 20px; letter-spacing: 4px; text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);">JUST A RATHER VERY INTELLIGENT SYSTEM</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-top: 10px;">
        <span class="status-online" style="font-size: 14px;">● ONLINE</span>
        <span style="color: #666; margin: 0 10px;">|</span>
        <span style="color: #00d4ff; font-size: 14px;">v2.0</span>
    </div>
    """, unsafe_allow_html=True)

with header_col3:
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
        <div class="jarvis-orb" style="width: 60px; height: 60px;"></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar - Status & Settings
with st.sidebar:
    st.markdown('<h3 class="section-header">📊 System Status</h3>', unsafe_allow_html=True)
    
    # Status indicators
    voice_status = "✅ Online" if PYAUDIO_AVAILABLE else "❌ Offline"
    tts_status = "✅ Online" if st.session_state.voice_engine.tts_engine else "❌ Offline"
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Voice Recognition</h4>
        <span class="{'status-online' if PYAUDIO_AVAILABLE else 'status-offline'}">{voice_status}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Text-to-Speech</h4>
        <span class="{'status-online' if st.session_state.voice_engine.tts_engine else 'status-offline'}">{tts_status}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown('<h3 class="section-header">⚡ Quick Actions</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 Chrome", use_container_width=True):
            st.session_state.command_processor.process_command("open chrome")
            st.success("Chrome opened!")
    with col2:
        if st.button("📝 Notepad", use_container_width=True):
            st.session_state.command_processor.process_command("open notepad")
            st.success("Notepad opened!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧮 Calc", use_container_width=True):
            st.session_state.command_processor.process_command("open calculator")
            st.success("Calculator opened!")
    with col2:
        if st.button("📁 Explorer", use_container_width=True):
            st.session_state.command_processor.process_command("open file explorer")
            st.success("Explorer opened!")
    
    st.markdown("---")
    
    # Settings
    st.markdown('<h3 class="section-header">⚙️ Settings</h3>', unsafe_allow_html=True)
    
    st.session_state.voice_active = st.toggle("🎤 Voice Control", value=st.session_state.voice_active)
    
    if st.session_state.voice_active and PYAUDIO_AVAILABLE:
        st.success("Voice control active! Say 'Hey JARVIS'")
    elif st.session_state.voice_active:
        st.error("PyAudio not installed. Voice control unavailable.")
    
    st.markdown("---")
    
    # Command Stats
    st.markdown('<h3 class="section-header">📈 Command Stats</h3>', unsafe_allow_html=True)
    stats = st.session_state.command_processor.get_command_stats()
    st.metric("Total Commands", stats.get('total', 0))
    
    # Popular commands
    if stats.get('by_type'):
        st.markdown("**Most Used:**")
        for cmd_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True)[:3]:
            st.markdown(f"- {cmd_type}: {count}")

# Main content area
col_left, col_right = st.columns([2, 1])

with col_left:
    # System Monitoring
    st.markdown('<h3 class="section-header">📊 Real-Time System Monitoring</h3>', unsafe_allow_html=True)
    
    # Get current metrics
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Update history (keep last 60 points)
    current_time = datetime.now().strftime('%H:%M:%S')
    st.session_state.system_metrics['cpu_history'].append(cpu_percent)
    st.session_state.system_metrics['memory_history'].append(memory.percent)
    st.session_state.system_metrics['timestamps'].append(current_time)
    
    if len(st.session_state.system_metrics['cpu_history']) > 60:
        st.session_state.system_metrics['cpu_history'].pop(0)
        st.session_state.system_metrics['memory_history'].pop(0)
        st.session_state.system_metrics['timestamps'].pop(0)
    
    # Gauges row
    gauge_col1, gauge_col2, gauge_col3, gauge_col4 = st.columns(4)
    
    with gauge_col1:
        fig_cpu = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_percent,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU", 'font': {'color': '#00d4ff', 'size': 24}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#00d4ff'},
                'bar': {'color': '#00d4ff'},
                'bgcolor': 'rgba(0,0,0,0)',
                'borderwidth': 2,
                'bordercolor': '#00d4ff',
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0, 212, 255, 0.1)'},
                    {'range': [50, 80], 'color': 'rgba(255, 193, 7, 0.2)'},
                    {'range': [80, 100], 'color': 'rgba(244, 67, 54, 0.3)'}
                ]
            }
        ))
        fig_cpu.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cpu, use_container_width=True, key="cpu_gauge")
    
    with gauge_col2:
        fig_mem = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory.percent,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "RAM", 'font': {'color': '#00ff88', 'size': 24}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#00ff88'},
                'bar': {'color': '#00ff88'},
                'bgcolor': 'rgba(0,0,0,0)',
                'borderwidth': 2,
                'bordercolor': '#00ff88',
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(0, 255, 136, 0.1)'},
                    {'range': [50, 80], 'color': 'rgba(255, 193, 7, 0.2)'},
                    {'range': [80, 100], 'color': 'rgba(244, 67, 54, 0.3)'}
                ]
            }
        ))
        fig_mem.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_mem, use_container_width=True, key="mem_gauge")
    
    with gauge_col3:
        disk_percent = (disk.used / disk.total) * 100
        fig_disk = go.Figure(go.Indicator(
            mode="gauge+number",
            value=disk_percent,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Disk", 'font': {'color': '#ff6b6b', 'size': 24}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#ff6b6b'},
                'bar': {'color': '#ff6b6b'},
                'bgcolor': 'rgba(0,0,0,0)',
                'borderwidth': 2,
                'bordercolor': '#ff6b6b',
                'steps': [
                    {'range': [0, 70], 'color': 'rgba(255, 107, 107, 0.1)'},
                    {'range': [70, 90], 'color': 'rgba(255, 193, 7, 0.2)'},
                    {'range': [90, 100], 'color': 'rgba(244, 67, 54, 0.3)'}
                ]
            }
        ))
        fig_disk.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_disk, use_container_width=True, key="disk_gauge")
    
    with gauge_col4:
        # Network indicator
        net_io = psutil.net_io_counters()
        net_speed = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
        fig_net = go.Figure(go.Indicator(
            mode="number",
            value=net_speed,
            number={'suffix': ' MB', 'font': {'color': '#ff00ff', 'size': 30}},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Network", 'font': {'color': '#ff00ff', 'size': 24}}
        ))
        fig_net.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_net, use_container_width=True, key="net_indicator")
    
    # CPU & Memory History Graph
    st.markdown('<h3 class="section-header">📈 Performance History</h3>', unsafe_allow_html=True)
    
    fig_history = go.Figure()
    fig_history.add_trace(go.Scatter(
        x=st.session_state.system_metrics['timestamps'],
        y=st.session_state.system_metrics['cpu_history'],
        mode='lines',
        name='CPU %',
        line=dict(color='#00d4ff', width=2)
    ))
    fig_history.add_trace(go.Scatter(
        x=st.session_state.system_metrics['timestamps'],
        y=st.session_state.system_metrics['memory_history'],
        mode='lines',
        name='RAM %',
        line=dict(color='#00ff88', width=2)
    ))
    fig_history.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.2)',
        font=dict(color='#ffffff'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Time'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Usage %', range=[0, 100]),
        legend=dict(font=dict(color='#ffffff')),
        height=300
    )
    st.plotly_chart(fig_history, use_container_width=True, key="history_chart")

with col_right:
    # Chat Interface
    st.markdown('<h3 class="section-header">💬 Chat with JARVIS</h3>', unsafe_allow_html=True)
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history[-20:]:  # Show last 20 messages
            if msg['type'] == 'user':
                st.markdown(f'<div class="user-message"><b>👤 You:</b> {msg["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="jarvis-message"><b>🤖 JARVIS:</b> {msg["text"]}</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    col_input, col_button = st.columns([4, 1])
    
    with col_input:
        user_input = st.text_input("", placeholder="Type a command...", key="chat_input", label_visibility="collapsed")
    
    with col_button:
        send_button = st.button("➤", use_container_width=True)
    
    # Voice button
    if PYAUDIO_AVAILABLE:
        voice_button = st.button("🎤 Speak Command", use_container_width=True)
        if voice_button:
            st.info("🎤 Voice input activated - speak your command!")
    
    # Process input
    if (send_button or user_input) and user_input:
        # Add user message
        st.session_state.chat_history.append({'type': 'user', 'text': user_input, 'time': datetime.now()})
        
        # Process command
        result = st.session_state.command_processor.process_command(user_input)
        
        # Add JARVIS response
        st.session_state.chat_history.append({'type': 'jarvis', 'text': result.message, 'time': datetime.now()})
        
        # Speak if TTS available
        if st.session_state.voice_engine.tts_engine:
            st.session_state.voice_engine.speak(result.message)
        
        # Clear input
        st.rerun()
    
    # Quick commands
    st.markdown('<h3 class="section-header">⚡ Quick Commands</h3>', unsafe_allow_html=True)
    
    quick_cmds = [
        ("⏰ Time", "time"),
        ("📅 Date", "date"),
        ("📊 Status", "status"),
        ("❓ Help", "help")
    ]
    
    for label, cmd in quick_cmds:
        if st.button(label, use_container_width=True, key=f"quick_{cmd}"):
            # Process command
            result = st.session_state.command_processor.process_command(cmd)
            
            # Add to chat
            st.session_state.chat_history.append({'type': 'user', 'text': cmd, 'time': datetime.now()})
            st.session_state.chat_history.append({'type': 'jarvis', 'text': result.message, 'time': datetime.now()})
            
            # Speak
            if st.session_state.voice_engine.tts_engine:
                st.session_state.voice_engine.speak(result.message)
            
            st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>JARVIS AI Assistant v2.0 | Built with Streamlit</p>", unsafe_allow_html=True)

# Auto-refresh for real-time monitoring
time.sleep(1)
st.rerun()
