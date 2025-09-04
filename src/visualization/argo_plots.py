"""
Visualization functions for ARGO data using Plotly and Folium.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ARGOVisualizer:
    """Creates visualizations for ARGO data."""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_float_map(self, float_data: pd.DataFrame, 
                        center_lat: float = 20.0, center_lon: float = 80.0,
                        zoom_start: int = 4) -> folium.Map:
        """
        Create an interactive map showing ARGO float locations.
        
        Args:
            float_data: DataFrame with float information
            center_lat: Center latitude for map
            center_lon: Center longitude for map
            zoom_start: Initial zoom level
            
        Returns:
            Folium map object
        """
        try:
            # Create base map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom_start,
                tiles='OpenStreetMap'
            )
            
            # Add float markers
            for idx, row in float_data.iterrows():
                # Create popup text
                popup_text = f"""
                <b>Float ID:</b> {row.get('float_id', 'N/A')}<br>
                <b>WMO ID:</b> {row.get('wmo_id', 'N/A')}<br>
                <b>Institution:</b> {row.get('institution', 'N/A')}<br>
                <b>Status:</b> {row.get('status', 'N/A')}<br>
                <b>Last Update:</b> {row.get('last_transmission', 'N/A')}
                """
                
                # Choose marker color based on status
                color = 'green' if row.get('status') == 'active' else 'red'
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"Float {row.get('float_id', 'N/A')}",
                    icon=folium.Icon(color=color, icon='ship', prefix='fa')
                ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creating float map: {e}")
            return folium.Map(location=[20, 80], zoom_start=4)
    
    def create_trajectory_map(self, trajectory_data: pd.DataFrame,
                             float_id: str = None) -> folium.Map:
        """
        Create a map showing ARGO float trajectory.
        
        Args:
            trajectory_data: DataFrame with trajectory points
            float_id: Specific float ID to highlight
            
        Returns:
            Folium map with trajectory
        """
        try:
            if trajectory_data.empty:
                return folium.Map(location=[20, 80], zoom_start=4)
            
            # Calculate map center
            center_lat = trajectory_data['latitude'].mean()
            center_lon = trajectory_data['longitude'].mean()
            
            # Create base map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=6,
                tiles='OpenStreetMap'
            )
            
            # Add trajectory line
            trajectory_points = [[row['latitude'], row['longitude']] 
                               for _, row in trajectory_data.iterrows()]
            
            folium.PolyLine(
                trajectory_points,
                color='blue',
                weight=3,
                opacity=0.8,
                popup=f"Trajectory for Float {float_id or 'Unknown'}"
            ).add_to(m)
            
            # Add start and end markers
            if len(trajectory_points) > 0:
                # Start marker
                folium.Marker(
                    trajectory_points[0],
                    popup="Start",
                    icon=folium.Icon(color='green', icon='play', prefix='fa')
                ).add_to(m)
                
                # End marker
                folium.Marker(
                    trajectory_points[-1],
                    popup="End",
                    icon=folium.Icon(color='red', icon='stop', prefix='fa')
                ).add_to(m)
            
            # Add trajectory points
            for idx, row in trajectory_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=3,
                    popup=f"Cycle {row.get('cycle_number', 'N/A')}<br>Date: {row.get('trajectory_time', 'N/A')}",
                    color='blue',
                    fill=True
                ).add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creating trajectory map: {e}")
            return folium.Map(location=[20, 80], zoom_start=4)
    
    def create_profile_plot(self, profile_data: pd.DataFrame, 
                           parameter: str = 'temperature',
                           float_id: str = None, cycle_number: int = None) -> go.Figure:
        """
        Create a depth profile plot for ARGO data.
        
        Args:
            profile_data: DataFrame with profile measurements
            parameter: Parameter to plot (temperature, salinity, etc.)
            float_id: Float ID for title
            cycle_number: Cycle number for title
            
        Returns:
            Plotly figure object
        """
        try:
            if profile_data.empty or parameter not in profile_data.columns:
                # Return empty plot
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for this parameter",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Remove NaN values
            clean_data = profile_data.dropna(subset=[parameter, 'pressure'])
            
            if clean_data.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="No valid data points for this parameter",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Create plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=clean_data[parameter],
                y=clean_data['pressure'],
                mode='lines+markers',
                name=parameter.title(),
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ))
            
            # Update layout
            title = f"{parameter.title()} Profile"
            if float_id:
                title += f" - Float {float_id}"
            if cycle_number:
                title += f" - Cycle {cycle_number}"
            
            fig.update_layout(
                title=title,
                xaxis_title=f"{parameter.title()}",
                yaxis_title="Pressure (dbar)",
                yaxis=dict(autorange='reversed'),  # Invert y-axis for depth
                template='plotly_white',
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating profile plot: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating plot: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_ts_diagram(self, profile_data: pd.DataFrame,
                         float_id: str = None) -> go.Figure:
        """
        Create a Temperature-Salinity diagram.
        
        Args:
            profile_data: DataFrame with temperature and salinity data
            float_id: Float ID for title
            
        Returns:
            Plotly figure object
        """
        try:
            if profile_data.empty or 'temperature' not in profile_data.columns or 'salinity' not in profile_data.columns:
                fig = go.Figure()
                fig.add_annotation(
                    text="Temperature and salinity data required for T-S diagram",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Remove NaN values
            clean_data = profile_data.dropna(subset=['temperature', 'salinity'])
            
            if clean_data.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="No valid temperature and salinity data",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Create T-S diagram
            fig = go.Figure()
            
            # Color by pressure if available
            if 'pressure' in clean_data.columns:
                fig.add_trace(go.Scatter(
                    x=clean_data['salinity'],
                    y=clean_data['temperature'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color=clean_data['pressure'],
                        colorscale='Viridis',
                        colorbar=dict(title="Pressure (dbar)"),
                        showscale=True
                    ),
                    name='Profile Points',
                    text=[f"P: {p:.1f} dbar" for p in clean_data['pressure']],
                    hovertemplate="<b>Salinity:</b> %{x:.3f}<br><b>Temperature:</b> %{y:.2f}°C<br>%{text}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=clean_data['salinity'],
                    y=clean_data['temperature'],
                    mode='markers',
                    marker=dict(size=6, color='blue'),
                    name='Profile Points'
                ))
            
            # Update layout
            title = "Temperature-Salinity Diagram"
            if float_id:
                title += f" - Float {float_id}"
            
            fig.update_layout(
                title=title,
                xaxis_title="Salinity (PSU)",
                yaxis_title="Temperature (°C)",
                template='plotly_white',
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating T-S diagram: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating T-S diagram: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_time_series_plot(self, time_series_data: pd.DataFrame,
                               parameter: str = 'temperature',
                               float_id: str = None) -> go.Figure:
        """
        Create a time series plot for ARGO data.
        
        Args:
            time_series_data: DataFrame with time series data
            parameter: Parameter to plot
            float_id: Float ID for title
            
        Returns:
            Plotly figure object
        """
        try:
            if time_series_data.empty or 'profile_time' not in time_series_data.columns:
                fig = go.Figure()
                fig.add_annotation(
                    text="No time series data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Group by time and calculate statistics
            if parameter in time_series_data.columns:
                time_stats = time_series_data.groupby('profile_time')[parameter].agg(['mean', 'std', 'min', 'max']).reset_index()
                
                fig = go.Figure()
                
                # Add mean line
                fig.add_trace(go.Scatter(
                    x=time_stats['profile_time'],
                    y=time_stats['mean'],
                    mode='lines+markers',
                    name=f'Mean {parameter.title()}',
                    line=dict(color='blue', width=2)
                ))
                
                # Add error bars
                fig.add_trace(go.Scatter(
                    x=time_stats['profile_time'],
                    y=time_stats['mean'] + time_stats['std'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=time_stats['profile_time'],
                    y=time_stats['mean'] - time_stats['std'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(0,100,80,0.2)',
                    name='±1 Std Dev',
                    hoverinfo='skip'
                ))
            
            else:
                # Just plot the number of profiles over time
                profile_counts = time_series_data.groupby('profile_time').size().reset_index(name='count')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=profile_counts['profile_time'],
                    y=profile_counts['count'],
                    mode='lines+markers',
                    name='Number of Profiles',
                    line=dict(color='green', width=2)
                ))
            
            # Update layout
            title = f"Time Series - {parameter.title()}" if parameter in time_series_data.columns else "Profile Count Over Time"
            if float_id:
                title += f" - Float {float_id}"
            
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title=f"{parameter.title()}" if parameter in time_series_data.columns else "Number of Profiles",
                template='plotly_white',
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series plot: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating time series plot: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_comparison_plot(self, profiles_data: List[pd.DataFrame],
                              parameter: str = 'temperature',
                              labels: List[str] = None) -> go.Figure:
        """
        Create a comparison plot for multiple profiles.
        
        Args:
            profiles_data: List of DataFrames with profile data
            parameter: Parameter to compare
            labels: Labels for each profile
            
        Returns:
            Plotly figure object
        """
        try:
            if not profiles_data:
                fig = go.Figure()
                fig.add_annotation(
                    text="No profiles to compare",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            fig = go.Figure()
            colors = px.colors.qualitative.Set1
            
            for i, profile_data in enumerate(profiles_data):
                if profile_data.empty or parameter not in profile_data.columns:
                    continue
                
                # Remove NaN values
                clean_data = profile_data.dropna(subset=[parameter, 'pressure'])
                
                if clean_data.empty:
                    continue
                
                label = labels[i] if labels and i < len(labels) else f"Profile {i+1}"
                color = colors[i % len(colors)]
                
                fig.add_trace(go.Scatter(
                    x=clean_data[parameter],
                    y=clean_data['pressure'],
                    mode='lines+markers',
                    name=label,
                    line=dict(color=color, width=2),
                    marker=dict(size=4)
                ))
            
            fig.update_layout(
                title=f"{parameter.title()} Profile Comparison",
                xaxis_title=f"{parameter.title()}",
                yaxis_title="Pressure (dbar)",
                yaxis=dict(autorange='reversed'),
                template='plotly_white',
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating comparison plot: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating comparison plot: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    def create_heatmap(self, data: pd.DataFrame, x_col: str, y_col: str, 
                      value_col: str, title: str = None) -> go.Figure:
        """
        Create a heatmap visualization.
        
        Args:
            data: DataFrame with data
            x_col: Column for x-axis
            y_col: Column for y-axis
            value_col: Column for values
            title: Plot title
            
        Returns:
            Plotly figure object
        """
        try:
            if data.empty or x_col not in data.columns or y_col not in data.columns or value_col not in data.columns:
                fig = go.Figure()
                fig.add_annotation(
                    text="Required columns not found in data",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
            
            # Create pivot table
            pivot_data = data.pivot_table(
                values=value_col,
                index=y_col,
                columns=x_col,
                aggfunc='mean'
            )
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale='Viridis',
                colorbar=dict(title=value_col.title())
            ))
            
            fig.update_layout(
                title=title or f"{value_col.title()} Heatmap",
                xaxis_title=x_col.title(),
                yaxis_title=y_col.title(),
                template='plotly_white',
                height=500
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating heatmap: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
