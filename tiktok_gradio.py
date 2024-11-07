import streamlit as st
import requests
import pandas as pd
from time import sleep

def search_users(platform, query, api_token, max_results=100):
    """
    Search for users across social media platforms using EnsembleData API
    """
    base_url = "https://ensembledata.com/apis"
    
    # Different endpoints and parameters for each platform
    platform_configs = {
        "tiktok": {
            "endpoint": "/tt/user/search",
            "params": {"keyword": query, "cursor": 0},
            "response_path": ["data", "users"],
            "next_cursor_path": ["data", "nextCursor"]
        },
        "instagram": {
            "endpoint": "/instagram/search",
            "params": {"text": query},
            "response_path": ["data", "users"],
            "next_cursor_path": None  # Instagram doesn't support pagination for search
        },
        "threads": {
            "endpoint": "/threads/user/search",
            "params": {"name": query},
            "response_path": ["data"],
            "next_cursor_path": None  # Threads doesn't support pagination for search
        }
    }
    
    if platform not in platform_configs:
        st.error(f"Platform {platform} is not supported")
        return None
    
    config = platform_configs[platform]
    results = []
    
    with st.spinner(f'Searching {platform} users...'):
        try:
            # Add token to params
            params = {**config["params"], "token": api_token}
            
            response = requests.get(
                f"{base_url}{config['endpoint']}", 
                params=params
            )
            
            if response.status_code != 200:
                st.error(f"Error: {response.status_code} - {response.text}")
                return None
                
            data = response.json()
            
            # Extract results based on platform
            if platform == "tiktok":
                for user_data in data.get("data", {}).get("users", []):
                    if "user_info" in user_data:
                        user = user_data["user_info"]
                        results.append({
                            "username": user.get("unique_id", ""),
                            "nickname": user.get("nickname", ""),
                            "followers": user.get("follower_count", 0),
                            "following": user.get("following_count", 0),
                            "likes": user.get("total_favorited", 0),
                            "verified": user.get("custom_verify", ""),
                            "bio": user.get("signature", "")
                        })
            
            elif platform == "instagram":
                for user_data in data.get("data", {}).get("users", []):
                    user = user_data.get("user", {})
                    results.append({
                        "username": user.get("username", ""),
                        "full_name": user.get("full_name", ""),
                        "verified": user.get("is_verified", False),
                        "profile_pic_url": user.get("profile_pic_url", "")
                    })
            
            elif platform == "threads":
                for user_data in data.get("data", []):
                    node = user_data.get("node", {})
                    results.append({
                        "username": node.get("username", ""),
                        "full_name": node.get("full_name", ""),
                        "followers": node.get("follower_count", 0),
                        "verified": node.get("is_verified", False),
                        "profile_pic_url": node.get("profile_pic_url", "")
                    })
                    
        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
            return None
    
    return results[:max_results]

def format_results(platform, results):
    """
    Format the results into a pandas DataFrame based on the platform
    """
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Format numbers to be more readable
    numeric_columns = ['followers', 'following', 'likes']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:,}")
    
    # Reorder columns based on platform
    if platform == "tiktok":
        column_order = ['username', 'nickname', 'followers', 'following', 'likes', 'verified', 'bio']
        df = df[list(col for col in column_order if col in df.columns)]
    elif platform in ["instagram", "threads"]:
        column_order = ['username', 'full_name', 'followers', 'verified']
        df = df[list(col for col in column_order if col in df.columns)]
    
    return df

def main():
    st.title("Social Media User Search")
    
    # Sidebar for API token
    with st.sidebar:
        api_token = st.text_input("Enter your EnsembleData API token", type="password")
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This app searches for users across different social media platforms using the EnsembleData API.
        
        API Units per request:
        - TikTok: 2 units
        - Instagram: 4 units
        - Threads: 4 units
        """)
    
    # Main content
    platform = st.selectbox(
        "Select Platform",
        ["tiktok", "instagram", "threads"]
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Search Query")
    
    with col2:
        max_results = st.number_input("Max Results", min_value=1, max_value=100, value=10, step=1)
    
    if st.button("Search"):
        if not api_token:
            st.error("Please enter your API token in the sidebar")
            return
            
        if not search_query:
            st.error("Please enter a search query")
            return
            
        results = search_users(platform, search_query, api_token, max_results)
        
        if results:
            df = format_results(platform, results)
            
            # Display results
            st.subheader(f"Found {len(results)} results")
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name=f"{platform}_search_results.csv",
                mime="text/csv"
            )
        else:
            st.info("No results found")

if __name__ == "__main__":
    main()