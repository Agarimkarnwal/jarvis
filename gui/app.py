"""
JARVIS GUI Application - Modern Holographic Interface
Built with Streamlit for optimal performance on i3 systems
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import threading
import asyncio
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.voice_engine import VoiceEngine, VoiceConfig
from core.ai_core import AICore, AIConfig
from core.system_controller import SystemController, SystemConfig

class JARVISInterface:
    """Main JARVIS GUI Application"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.voice_config = VoiceConfig()
        self.ai_config = AIConfig()
        self.system_config = SystemConfig()
        
        self.voice_engine = VoiceEngine(self.voice_config)
        self.ai_core = AICore(self.ai_config)
        self.system_controller = SystemController(self.system_config)
        
        # GUI State
        self.conversation_history = []
        self.system_metrics = {}
        self.voice_active = False
        self.ai_thinking = False
        
        # Configure callbacks
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """Setup voice engine callbacks"""
        self.voice_engine.set_callbacks(
            on_command=self._on_voice_command,
            on_wake_word=self._on_wake_word
        )
        
    def _on_voice_command(self, command: str):
        """Handle voice command"""
        # Add to conversation
        self.conversation_history.append({
            'role': 'user',
            'content': command,
            'timestamp': datetime.now(),
            'type': 'voice'
        })
        
        # Process command
        self._process_command(command)
        
    def _on_wake_word(self):
        """Handle wake word detection"""
        self.voice_active = True
        if hasattr(st, 'rerun'):
            st.rerun()
            
    def _process_command(self, command: str):
        """Process user command"""
        self.ai_thinking = True
        
        # Generate AI response
        response = asyncio.run(self.ai_core.generate_response(command))
        
        # Add response to conversation
        self.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now(),
            'type': 'text'
        })
        
        # Speak response
        self.voice_engine.speak(response)
        
        self.ai_thinking = False
        self.voice_active = False
        
    def render_header(self):
        """Render application header"""
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
        
        with col1:
            st.markdown("### 🤖 JARVIS")
            
        with col2:
            # Status indicator
            status = "🟢 Online" if self.voice_engine.listening_active else "🔴 Offline"
            st.markdown(f"**Status:** {status}")
            
        with col3:
            # CPU usage
            cpu_usage = self.system_metrics.get('cpu', {}).get('percent', 0)
            st.markdown(f"**CPU:** {cpu_usage:.1f}%")
            
        with col4:
            # Memory usage
            mem_usage = self.system_metrics.get('memory', {}).get('percent', 0)
            st.markdown(f"**RAM:** {mem_usage:.1f}%")
            
        with col5:
            # Voice status
            voice_status = "🎤 Active" if self.voice_active else "🔇 Idle"
            st.markdown(f"**Voice:** {voice_status}")
            
        st.markdown("---")
        
    def render_main_dashboard(self):
        """Render main dashboard with visualizations"""
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Dashboard", "💬 Conversation", "📊 System Monitor", "⚙️ Settings"])
        
        with tab1:
            self._render_dashboard_tab()
            
        with tab2:
            self._render_conversation_tab()
            
        with tab3:
            self._render_system_monitor_tab()
            
        with tab4:
            self._render_settings_tab()
            
    def _render_dashboard_tab(self):
        """Render main dashboard with holographic effects"""
        st.markdown("## 🌟 JARVIS Command Center")
        
        # Main visualization area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 3D-style system status visualization
            self._render_system_visualization()
            
        with col2:
            # Quick actions panel
            self._render_quick_actions()
            
        # Voice interaction area
        st.markdown("### 🎤 Voice Interaction")
        self._render_voice_interface()
        
    def _render_system_visualization(self):
        """Render animated system visualization"""
        # Get current metrics
        metrics = self.system_controller.monitor.get_current_metrics()
        
        if not metrics:
            st.warning("System metrics not available")
            return
            
        # Create subplots for multiple metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("CPU Usage", "Memory Usage", "Disk Usage", "Network Activity"),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "pie"}, {"type": "bar"}]]
        )
        
        # CPU Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics['cpu']['percent'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ),
            row=1, col=1
        )
        
        # Memory Gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics['memory']['percent'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Memory %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ),
            row=1, col=2
        )
        
        # Disk Usage Pie Chart
        disk_used = metrics['disk']['used']
        disk_free = metrics['disk']['free']
        fig.add_trace(
            go.Pie(
                labels=["Used", "Free"],
                values=[disk_used, disk_free],
                hole=0.3,
                marker_colors=["#ff6b35", "#00d4ff"]
            ),
            row=2, col=1
        )
        
        # Network Activity Bar Chart
        fig.add_trace(
            go.Bar(
                x=["Sent", "Received"],
                y=[metrics['network']['bytes_sent'], metrics['network']['bytes_recv']],
                marker_color=["#00d4ff", "#ff6b35"]
            ),
            row=2, col=2
        )
        
        # Update layout for holographic effect
        fig.update_layout(
            height=600,
            showlegend=False,
            paper_bgcolor='rgba(10, 14, 39, 0.8)',
            plot_bgcolor='rgba(26, 31, 58, 0.8)',
            font=dict(color='white'),
            title_font=dict(size=16, color='#00d4ff')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("#### ⚡ Quick Actions")
        
        # Action buttons with icons
        if st.button("🔊 Start Voice", key="start_voice"):
            self.voice_engine.start_listening()
            st.success("Voice listening started!")
            
        if st.button("🔇 Stop Voice", key="stop_voice"):
            self.voice_engine.stop_listening()
            st.success("Voice listening stopped!")
            
        if st.button("🧹 System Cleanup", key="cleanup"):
            results = self.system_controller.cleanup_system()
            st.success(f"Cleanup completed! Removed {results['temp_files_cleaned']} temp files.")
            
        if st.button("📊 System Info", key="sysinfo"):
            info = self.system_controller.get_system_info()
            st.json(info)
            
        st.markdown("---")
        st.markdown("#### 🚀 Application Launcher")
        
        # Application launcher
        apps = ["Chrome", "VS Code", "Spotify", "Discord", "Steam"]
        selected_app = st.selectbox("Select Application:", apps)
        
        if st.button(f"📱 Open {selected_app}"):
            result = asyncio.run(
                self.system_controller.execute_command(
                    'open_application', 
                    {'application': selected_app.lower()}
                )
            )
            if result['success']:
                st.success(f"Opened {selected_app}")
            else:
                st.error(f"Failed to open {selected_app}")
                
    def _render_voice_interface(self):
        """Render voice interaction interface"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Text input for commands
            user_input = st.text_input(
                "💬 Type your command or use voice:",
                placeholder="Ask JARVIS anything...",
                key="command_input"
            )
            
            if st.button("📤 Send Command", key="send_command"):
                if user_input:
                    self._process_command(user_input)
                    st.success("Command sent!")
                    
        with col2:
            # Voice controls
            if st.button("🎤 Talk to JARVIS", key="voice_button"):
                st.info("Listening... Say 'Hey JARVIS' to activate!")
                
        # Voice waveform visualization (placeholder)
        if self.voice_active:
            self._render_voice_waveform()
            
    def _render_voice_waveform(self):
        """Render animated voice waveform"""
        # Generate random waveform data for visualization
        x = np.linspace(0, 1, 100)
        y = np.sin(2 * np.pi * 5 * x) * np.random.random(100) * 0.3
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines',
            line=dict(color='#00d4ff', width=2),
            fill='tonexty',
            fillcolor='rgba(0, 212, 255, 0.3)'
        ))
        
        fig.update_layout(
            height=150,
            showlegend=False,
            paper_bgcolor='rgba(10, 14, 39, 0.8)',
            plot_bgcolor='rgba(26, 31, 58, 0.8)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_conversation_tab(self):
        """Render conversation history"""
        st.markdown("## 💬 Conversation History")
        
        if not self.conversation_history:
            st.info("No conversation history yet. Start talking to JARVIS!")
            return
            
        # Display conversation with styling
        for i, message in enumerate(reversed(self.conversation_history[-20:])):  # Last 20 messages
            if message['role'] == 'user':
                st.markdown(f"""
                <div style="background-color: rgba(0, 212, 255, 0.1); 
                           border-left: 4px solid #00d4ff; 
                           padding: 10px; 
                           margin: 5px 0; 
                           border-radius: 5px;">
                    <strong>👤 You ({message['timestamp'].strftime('%H:%M')}):</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: rgba(255, 107, 53, 0.1); 
                           border-left: 4px solid #ff6b35; 
                           padding: 10px; 
                           margin: 5px 0; 
                           border-radius: 5px;">
                    <strong>🤖 JARVIS ({message['timestamp'].strftime('%H:%M')}):</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", key="clear_conversation"):
            self.conversation_history.clear()
            st.rerun()
            
    def _render_system_monitor_tab(self):
        """Render detailed system monitoring"""
        st.markdown("## 📊 System Monitoring")
        
        # Get comprehensive system info
        system_info = self.system_controller.get_system_info()
        
        if not system_info:
            st.error("Unable to retrieve system information")
            return
            
        # System metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("CPU Usage", f"{system_info['current_metrics']['cpu']['percent']:.1f}%")
            
        with col2:
            st.metric("Memory Usage", f"{system_info['current_metrics']['memory']['percent']:.1f}%")
            
        with col3:
            st.metric("Disk Usage", f"{system_info['current_metrics']['disk']['percent']:.1f}%")
            
        with col4:
            uptime = datetime.now() - system_info['boot_time']
            st.metric("Uptime", str(uptime).split('.')[0])
            
        # Process list
        st.markdown("### 🔄 Running Processes")
        
        processes_df = pd.DataFrame(system_info['processes'])
        if not processes_df.empty:
            processes_df = processes_df.sort_values('cpu_percent', ascending=False).head(10)
            st.dataframe(processes_df, use_container_width=True)
        else:
            st.info("No process data available")
            
        # Performance graphs
        st.markdown("### 📈 Performance Trends")
        
        # Get historical data
        avg_metrics = self.system_controller.monitor.get_average_metrics(5)
        
        if avg_metrics:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_cpu = px.line(
                    title="CPU Usage (Last 5 minutes)",
                    x=[f"Sample {i}" for i in range(avg_metrics['sample_count'])],
                    y=[avg_metrics['avg_cpu_percent']] * avg_metrics['sample_count'],
                    labels={'x': 'Time', 'y': 'CPU %'}
                )
                fig_cpu.update_layout(
                    paper_bgcolor='rgba(10, 14, 39, 0.8)',
                    plot_bgcolor='rgba(26, 31, 58, 0.8)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig_cpu, use_container_width=True)
                
            with col2:
                fig_mem = px.line(
                    title="Memory Usage (Last 5 minutes)",
                    x=[f"Sample {i}" for i in range(avg_metrics['sample_count'])],
                    y=[avg_metrics['avg_memory_percent']] * avg_metrics['sample_count'],
                    labels={'x': 'Time', 'y': 'Memory %'}
                )
                fig_mem.update_layout(
                    paper_bgcolor='rgba(10, 14, 39, 0.8)',
                    plot_bgcolor='rgba(26, 31, 58, 0.8)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig_mem, use_container_width=True)
                
    def _render_settings_tab(self):
        """Render settings and configuration"""
        st.markdown("## ⚙️ Settings & Configuration")
        
        # Voice settings
        st.markdown("### 🎤 Voice Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            wake_word = st.text_input("Wake Word:", value=self.voice_config.wake_word)
            sensitivity = st.slider("Microphone Sensitivity:", 0.0, 1.0, self.voice_config.sensitivity)
            
        with col2:
            voice_speed = st.slider("Voice Speed:", 0.5, 2.0, self.voice_config.voice_speed)
            voice_volume = st.slider("Voice Volume:", 0.0, 1.0, self.voice_config.voice_volume)
            
        # AI settings
        st.markdown("### 🧠 AI Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider("AI Creativity:", 0.0, 1.0, self.ai_config.temperature)
            max_tokens = st.slider("Max Response Length:", 100, 1000, self.ai_config.max_tokens)
            
        with col2:
            model_info = self.ai_core.get_model_info()
            st.json(model_info)
            
        # System settings
        st.markdown("### 💻 System Settings")
        
        auto_cleanup = st.checkbox("Auto Cleanup", value=self.system_config.auto_cleanup)
        security_mode = st.selectbox("Security Mode:", ["standard", "high", "max"], 
                                    index=["standard", "high", "max"].index(self.system_config.security_mode))
        
        # Apply settings button
        if st.button("💾 Apply Settings", key="apply_settings"):
            # Update configurations
            self.voice_config.wake_word = wake_word
            self.voice_config.sensitivity = sensitivity
            self.voice_config.voice_speed = voice_speed
            self.voice_config.voice_volume = voice_volume
            
            self.ai_config.temperature = temperature
            self.ai_config.max_tokens = max_tokens
            
            self.system_config.auto_cleanup = auto_cleanup
            self.system_config.security_mode = security_mode
            
            st.success("Settings applied successfully!")
            
        # System actions
        st.markdown("### 🛠️ System Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Restart", key="restart_system"):
                result = asyncio.run(self.system_controller.execute_command('restart'))
                if result['success']:
                    st.success("Restart scheduled!")
                else:
                    st.error("Failed to schedule restart")
                    
        with col2:
            if st.button("😴 Sleep", key="sleep_system"):
                result = asyncio.run(self.system_controller.execute_command('sleep'))
                if result['success']:
                    st.success("System going to sleep!")
                else:
                    st.error("Failed to sleep system")
                    
        with col3:
            if st.button("🔒 Lock", key="lock_system"):
                result = asyncio.run(self.system_controller.execute_command('lock_screen'))
                if result['success']:
                    st.success("Screen locked!")
                else:
                    st.error("Failed to lock screen")
                    
        with col4:
            if st.button("🧹 Cleanup", key="cleanup_system"):
                results = self.system_controller.cleanup_system()
                st.success(f"Cleanup completed! Files removed: {results['temp_files_cleaned']}")
                
    def run(self):
        """Run the JARVIS GUI application"""
        # Configure Streamlit page
        st.set_page_config(
            page_title="JARVIS AI Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for holographic theme
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: white;
        }
        
        .stButton > button {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(45deg, #0099cc, #00d4ff);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3);
        }
        
        .stTextInput > div > div > input {
            background: rgba(26, 31, 58, 0.8);
            color: white;
            border: 1px solid #00d4ff;
            border-radius: 8px;
        }
        
        .stSelectbox > div > div > select {
            background: rgba(26, 31, 58, 0.8);
            color: white;
            border: 1px solid #00d4ff;
            border-radius: 8px;
        }
        
        .stMetric {
            background: rgba(26, 31, 58, 0.8);
            border: 1px solid #00d4ff;
            border-radius: 8px;
            padding: 10px;
        }
        
        .stDataFrame {
            background: rgba(26, 31, 58, 0.8);
            border: 1px solid #00d4ff;
            border-radius: 8px;
        }
        
        /* Holographic glow effect */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 50%, rgba(255, 107, 53, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Update system metrics periodically
        self.system_metrics = self.system_controller.monitor.get_current_metrics()
        
        # Render main interface
        self.render_header()
        self.render_main_dashboard()
        
        # Auto-refresh
        time.sleep(1)
        if hasattr(st, 'rerun'):
            st.rerun()

def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run JARVIS interface
    jarvis = JARVISInterface()
    jarvis.run()

if __name__ == "__main__":
    main()
