import streamlit as st
import requests
from datetime import datetime, timedelta
import isodate  # To parse video duration

# ==============================
# CONFIG
# ==============================
API_KEY = "AIzaSyDsbHeo-ELkhih7CqA8f1TByD26tVCaFjA"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

ALLOWED_LANGUAGES = ["en", "pt", "es", "de"]  # English, Portuguese, Spanish, German only

# ==============================
# APP
# ==============================
st.title("🔎 YouTube Viral Topics Tool (No Shorts + Pro Filters)")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# Keywords
keywords = [
    "mysterious missing person case unsolved", "unsolved disappearance cold case 1950s",
    "girl vanished mysteriously story", "dark family secret revealed true story",
    "family hidden crimes documentary", "shocking family history mystery",
    "true dark family secrets uncovered", "orphanage horror real events",
    "religious school disappearance case", "claustrophobic convent secret exposed",
    "serial killer family history true", "family of killers real story",
    "multiple murder family case", "serial killer siblings uncovered",
    "reddit crime", "reddit horror story"
]

# ==============================
# FETCH DATA
# ==============================
if st.button("🚀 Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Loop through keywords
        for keyword in keywords:
            st.write(f"Searching for keyword: **{keyword}**")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
            channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v]

            if not video_ids or not channel_ids:
                continue

            # Fetch video statistics + duration + language
            stats_params = {"part": "statistics,snippet,contentDetails", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            if "items" not in stats_data:
                continue

            # Fetch channel statistics
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in channel_data:
                continue

            stats = stats_data["items"]
            channels = channel_data["items"]

            # Collect results
            for video, stat, channel in zip(videos, stats, channels):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                # Duration filter → skip if <=60 sec (shorts)
                duration_iso = stat["contentDetails"].get("duration", "PT0S")
                duration_sec = int(isodate.parse_duration(duration_iso).total_seconds())
                if duration_sec <= 60:
                    continue

                # Language filter
                lang = stat["snippet"].get("defaultAudioLanguage") or stat["snippet"].get("defaultLanguage") or "unknown"
                lang = lang.split("-")[0]

                if subs >= 3000 and lang in ALLOWED_LANGUAGES:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "Language": lang,
                        "Duration (sec)": duration_sec
                    })

        # ==============================
        # DISPLAY RESULTS
        # ==============================
        if all_results:
            all_results = sorted(all_results, key=lambda x: x["Views"], reverse=True)
            st.success(f"✅ Found {len(all_results)} valid videos!")
            for result in all_results:
                st.markdown(
                    f"**🎬 Title:** {result['Title']}  \n"
                    f"**📝 Description:** {result['Description']}  \n"
                    f"**🌍 Language:** {result['Language']}  \n"
                    f"**⏱ Duration:** {result['Duration (sec)']//60} min {result['Duration (sec)']%60} sec  \n"
                    f"**🔗 URL:** [Watch Video]({result['URL']})  \n"
                    f"**👀 Views:** {result['Views']:,}  \n"
                    f"**👤 Subscribers:** {result['Subscribers']:,}"
                )
                st.write("---")
        else:
            st.warning("⚠️ No results found matching your filters.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
