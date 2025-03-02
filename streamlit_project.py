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
    # Read and process the data
    df = pd.read_csv('euros_2024_shot_map.csv')
    
    # Filter only shots
    df = df[df['type'] == 'Shot'].reset_index(drop=True)
    
    # Convert location string to list
    def parse_location(loc_str):
        try:
            return json.loads(loc_str.replace("'", '"') if isinstance(loc_str, str) else loc_str)
        except:
            return [0, 0]  # Default location if parsing fails
            
    df['location'] = df['location'].apply(parse_location)
    
    def filter_data(df: pd.DataFrame, team: str, player: str):
        filtered = df.copy()
        if team:
            filtered = filtered[filtered['team'] == team]
        if player:
            filtered = filtered[filtered['player'] == player]
        return filtered

    def plot_shots(df, ax, pitch):
        for _, row in df.iterrows():
            try:
                x, y = row['location'][0], row['location'][1]
                shot_xg = float(row.get('shot_statsbomb_xg', 0.05))  # Default xg if missing
                is_goal = row.get('shot_outcome') == 'Goal'
                
                pitch.scatter(
                    x=float(x),
                    y=float(y),
                    ax=ax,
                    s=1000 * shot_xg,  # Size based on xG
                    color='green' if is_goal else 'red',
                    edgecolors='black',
                    alpha=0.7 if is_goal else 0.3,
                    zorder=2 if is_goal else 1
                )
            except Exception as e:
                st.warning(f"Error plotting shot: {e}")
                continue

    # Create filters
    col1, col2 = st.columns(2)
    with col1:
        team = st.selectbox("Select a team", options=[''] + sorted(df['team'].unique().tolist()))
    
    with col2:
        player_options = [''] + sorted(df[df['team'] == team]['player'].unique().tolist()) if team else ['']
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
    fig, ax = pitch.draw(figsize=(8, 8))
    plot_shots(filtered_df, ax, pitch)
    
    # Add a title to the plot
    title = f"Shot Map - {team if team else 'All Teams'}"
    if player:
        title += f" - {player}"
    ax.set_title(title, color='white', pad=20)

    # Display the plot
    st.pyplot(fig)

    # Display statistics
    st.subheader("Shot Statistics")
    total_shots = len(filtered_df)
    goals = len(filtered_df[filtered_df['shot_outcome'] == 'Goal'])
    avg_xg = filtered_df['shot_statsbomb_xg'].mean()

    stats_col1, stats_col2, stats_col3 = st.columns(3)
    stats_col1.metric("Total Shots", total_shots)
    stats_col2.metric("Goals", goals)
    stats_col3.metric("Average xG", f"{avg_xg:.3f}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Please check your data file and try again.")
