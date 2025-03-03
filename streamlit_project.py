"""
Make sure you have the following installed:
- streamlit
- mplsoccer
- pandas
"""
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

# Set page config
st.set_page_config(page_title="Euros 2024 Shot Map", layout="wide")

# Add a title
st.title("Euros 2024 Shot Map")
st.subheader("Filter to any team/player to see all their shots taken!")

try:
    # Read and process the data with the correct encoding
    df = pd.read_csv('euros_2024_shot_map.csv', encoding='utf-8')
    
    # Clean column names (remove any whitespace)
    df.columns = df.columns.str.strip()
    
    # Filter only shots and reset index
    df = df[df['type'] == 'Shot'].copy()
    df = df.reset_index(drop=True)
    
    # Convert location string to list
    def parse_location(loc_str):
        try:
            if pd.isna(loc_str):
                return [0, 0]
            # Clean the string and convert to JSON
            clean_str = str(loc_str).strip().replace("'", '"')
            return json.loads(clean_str)
        except:
            return [0, 0]  # Default location if parsing fails
            
    df['location'] = df['location'].apply(parse_location)
    
    def filter_data(df: pd.DataFrame, team: str, player: str):
        filtered = df.copy()
        if team and team != 'All Teams':
            filtered = filtered[filtered['team'] == team]
        if player and player != 'All Players':
            filtered = filtered[filtered['player'] == player]
        return filtered

    def plot_shots(df, ax, pitch):
        scatter_points = []
        annotations = []
        
        for _, row in df.iterrows():
            try:
                x, y = row['location'][0], row['location'][1]
                shot_xg = float(row.get('shot_statsbomb_xg', 0.05))
                is_goal = str(row.get('shot_outcome')).strip() == 'Goal'
                
                # Create scatter point
                point = pitch.scatter(
                    x=float(x),
                    y=float(y),
                    ax=ax,
                    s=1000 * shot_xg,  # Size based on xG
                    color='green' if is_goal else 'red',
                    edgecolors='black',
                    alpha=0.7 if is_goal else 0.3,
                    zorder=2 if is_goal else 1
                )
                
                # Add annotation with shot details
                shot_info = [
                    f"Player: {row.get('player', 'Unknown')}",
                    f"Team: {row.get('team', 'Unknown')}",
                    f"Outcome: {row.get('shot_outcome', 'Unknown')}",
                    f"xG: {shot_xg:.3f}",
                    f"Type: {row.get('shot_type', 'Unknown')}"
                ]
                
                # Add optional shot details if available
                if 'shot_technique' in row and pd.notna(row['shot_technique']):
                    shot_info.append(f"Technique: {row['shot_technique']}")
                if 'shot_body_part' in row and pd.notna(row['shot_body_part']):
                    shot_info.append(f"Body Part: {row['shot_body_part']}")
                if 'minute' in row and pd.notna(row['minute']):
                    shot_info.append(f"Minute: {row['minute']}")
                
                annotation = ax.annotate(
                    '\n'.join(shot_info),
                    xy=(x, y),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8),
                    visible=False
                )
                
                scatter_points.append(point)
                annotations.append(annotation)
                
            except Exception as e:
                st.warning(f"Error plotting shot: {e}")
                continue
        
        return scatter_points, annotations

    # Create filters
    col1, col2 = st.columns(2)
    with col1:
        team_options = ['All Teams'] + sorted(df['team'].unique().tolist())
        team = st.selectbox("Select a team", options=team_options)
    
    with col2:
        if team and team != 'All Teams':
            player_options = ['All Players'] + sorted(df[df['team'] == team]['player'].unique().tolist())
        else:
            player_options = ['All Players'] + sorted(df['player'].unique().tolist())
        player = st.selectbox("Select a player", options=player_options)

    # Filter the data
    filtered_df = filter_data(df, team, player)

    # Create and display the pitch
    pitch = VerticalPitch(
        pitch_type='statsbomb',
        line_zorder=2,
        pitch_color='#22312b',
        line_color='white',
        half=True
    )

    # Create the figure and plot
    fig, ax = pitch.draw(figsize=(10, 10))
    scatter_points, annotations = plot_shots(filtered_df, ax, pitch)
    
    # Add a title to the plot
    title = f"Shot Map - {team}"
    if player and player != 'All Players':
        title += f" - {player}"
    ax.set_title(title, color='white', pad=20)

    # Display the plot
    st.pyplot(fig)

    # Display detailed statistics
    st.subheader("Shot Statistics")
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Shots", len(filtered_df))
        goals = len(filtered_df[filtered_df['shot_outcome'].str.strip() == 'Goal'])
        st.metric("Goals", goals)
    
    with col2:
        avg_xg = filtered_df['shot_statsbomb_xg'].mean()
        total_xg = filtered_df['shot_statsbomb_xg'].sum()
        st.metric("Average xG", f"{avg_xg:.3f}")
        st.metric("Total xG", f"{total_xg:.3f}")
    
    with col3:
        conversion_rate = (goals / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")

    # Team and Player Rankings
    st.subheader("Team and Player Rankings")
    
    # Calculate team statistics
    team_stats = df.groupby('team').agg({
        'shot_statsbomb_xg': ['sum', 'mean'],
        'shot_outcome': lambda x: (x.str.strip() == 'Goal').sum(),
        'type': 'count'
    }).round(3)
    
    team_stats.columns = ['Total xG', 'Avg xG', 'Goals', 'Shots']
    team_stats['Conversion Rate'] = (team_stats['Goals'] / team_stats['Shots'] * 100).round(1)
    
    # Calculate player statistics
    player_stats = df.groupby(['player', 'team']).agg({
        'shot_statsbomb_xg': ['sum', 'mean'],
        'shot_outcome': lambda x: (x.str.strip() == 'Goal').sum(),
        'type': 'count'
    }).round(3)
    
    player_stats.columns = ['Total xG', 'Avg xG', 'Goals', 'Shots']
    player_stats['Conversion Rate'] = (player_stats['Goals'] / player_stats['Shots'] * 100).round(1)
    
    # Display Team Rankings
    st.write("Team Rankings")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Top 5 Teams by Total xG")
        st.dataframe(
            team_stats.sort_values('Total xG', ascending=False).head(),
            hide_index=False
        )
        
        st.write("Top 5 Teams by Conversion Rate")
        st.dataframe(
            team_stats.sort_values('Conversion Rate', ascending=False).head(),
            hide_index=False
        )
    
    with col2:
        st.write("Top 5 Teams by Goals")
        st.dataframe(
            team_stats.sort_values('Goals', ascending=False).head(),
            hide_index=False
        )
        
        st.write("Top 5 Teams by Average xG")
        st.dataframe(
            team_stats.sort_values('Avg xG', ascending=False).head(),
            hide_index=False
        )
    
    # Display Player Rankings
    st.write("Player Rankings")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Top 5 Players by Total xG")
        st.dataframe(
            player_stats.sort_values('Total xG', ascending=False).head(),
            hide_index=False
        )
        
        st.write("Top 5 Players by Conversion Rate (min. 3 shots)")
        min_shots_players = player_stats[player_stats['Shots'] >= 3]
        st.dataframe(
            min_shots_players.sort_values('Conversion Rate', ascending=False).head(),
            hide_index=False
        )
    
    with col2:
        st.write("Top 5 Players by Goals")
        st.dataframe(
            player_stats.sort_values('Goals', ascending=False).head(),
            hide_index=False
        )
        
        st.write("Top 5 Players by Average xG (min. 3 shots)")
        st.dataframe(
            min_shots_players.sort_values('Avg xG', ascending=False).head(),
            hide_index=False
        )

    # Shot breakdown
    st.subheader("Shot Breakdown")
    
    # Shot outcomes
    st.write("Shot Outcomes")
    outcome_counts = filtered_df['shot_outcome'].value_counts()
    st.bar_chart(outcome_counts)
    
    # Show detailed shot data
    st.subheader("Shot Details")
    
    # Get available columns for shot details
    available_columns = ['player', 'team', 'minute', 'shot_outcome', 'shot_statsbomb_xg', 'shot_type']
    optional_columns = ['shot_technique', 'shot_body_part']
    
    for col in optional_columns:
        if col in df.columns:
            available_columns.append(col)
    
    shot_details = filtered_df[available_columns].copy()
    
    # Clean up the data for display
    for col in shot_details.columns:
        if shot_details[col].dtype == 'object':
            shot_details[col] = shot_details[col].str.strip()
    
    shot_details = shot_details.sort_values('minute')
    
    st.dataframe(
        shot_details,
        column_config={
            'shot_statsbomb_xg': st.column_config.NumberColumn(
                'xG',
                format="%.3f"
            ),
            'minute': st.column_config.NumberColumn(
                'Minute',
                format="%d"
            )
        },
        hide_index=True
    )

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please check your data file and try again.")
    # Print more detailed error information
    import traceback
    st.write("Detailed error:")
    st.code(traceback.format_exc())
