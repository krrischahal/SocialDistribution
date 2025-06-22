import requests
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import *

GITHUB_API_URL = "https://api.github.com/users/{}/events/public"

def fetch_github_activity(github_url, event_type_filter=None):
    """
    Fetch and optionally filter recent public activity of a GitHub user.

    Args:
        github_url (str): The GitHub URL of the user.
        event_type_filter (list, optional): A list of event types to include. Default is None (no filtering).

    Returns:
        list: Filtered list of GitHub activities or all activities if no filter is provided.
    """
    # Extract the GitHub username from the GitHub URL
    username = github_url.strip('/').split('/')[-1]

    # Make a request to GitHub API to get user activity
    response = requests.get(GITHUB_API_URL.format(username))

    if response.status_code == 200:
        activities = response.json()
        if event_type_filter:
            # Filter activities based on the provided event types
            return [activity for activity in activities if activity['type'] in event_type_filter]
        return activities
    else:
        return None  # GitHub URL may be invalid or no activity found


def sync_github_activity(author):
    """
    Sync GitHub activity for a given author and create public posts for each new activity.
    """
    # Check if the author has a valid GitHub URL
    if not author.github:
        return {"error": "Author does not have a valid GitHub URL."}

    # Fetch the GitHub activity
    activities = fetch_github_activity(author.github, event_type_filter=['CreateEvent'])


    # If no activities are fetched, return an error
    if not activities:
        return {"error": "Unable to fetch GitHub activity or no recent activity found."}

    # Filter activities to include only user-generated actions
    relevant_events = []
    for activity in activities:
        if activity['type'] in ['PushEvent', 'CreateEvent', 'ForkEvent']:
            relevant_events.append(activity)

    # If no relevant events, return early
    if not relevant_events:
        return {"message": "No new relevant GitHub activities to sync."}

    # Iterate over each relevant GitHub activity and create a post
    for activity in relevant_events:
        post_id = f"github-{activity['id']}"  # Unique post ID based on GitHub activity

        # Check if the post for this GitHub activity already exists
        if Post.objects.filter(id=post_id).exists():
            continue  # Skip if the post already exists

        # Prepare the content for the post based on the event type
        if activity['type'] == 'PushEvent':
            commit_messages = "\n".join([commit['message'] for commit in activity['payload']['commits']])
            post_content = f"User pushed to {activity['repo']['name']}\nCommits:\n{commit_messages}"

        elif activity['type'] == 'CreateEvent':
            post_content = f"User created {activity['payload']['ref_type']} '{activity['payload']['ref']}' in {activity['repo']['name']}"

        elif activity['type'] == 'ForkEvent':
            post_content = f"User forked {activity['repo']['name']} to {activity['payload']['forkee']['full_name']}"

        # Create a new public post for the GitHub activity
        Post.objects.create(
            id=post_id,
            host=author.host,
            author=author,
            title=f"GitHub Activity: {activity['type']}",
            content_type="text/plain",
            content=post_content,
            visibility=Post.PUBLIC_VISIBILITY,
            published_at=timezone.now(),
        )
    
    return {"message": "GitHub activities synced and posts created."}

def are_friends(user1, user2):
    """
    Check if Two Users Are Friends

    **HTTP Method**: GET

    **When to use**:
    - To determine if two users have a mutual follow relationship, indicating they are friends.

    **Request Parameters**:
    - user1 (User): The first user object to check friendship for.
    - user2 (User): The second user object to check friendship for.

    **Returns**:
    - bool: True if the two users are friends (mutual follows), False otherwise.

    **Field Descriptions**:
    - user1_follows_user2: Boolean indicating if user1 follows user2 with an accepted friendship status.
    - user2_follows_user1: Boolean indicating if user2 follows user1 with an accepted friendship status.


    **Response Codes**:
    - 200: Successfully retrieved friendship status.
    """
    user1_follows_user2 = Follow.objects.filter(follower=user1, following=user2, status='accepted').exists()
    user2_follows_user1 = Follow.objects.filter(follower=user2, following=user1, status='accepted').exists()

    if user1_follows_user2 and user2_follows_user1:
        return True
    else:
        return False