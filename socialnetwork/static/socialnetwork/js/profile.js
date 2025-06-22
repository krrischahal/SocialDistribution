document.addEventListener('DOMContentLoaded', function() {
    const followBtn = document.getElementById('follow-btn');
    if (followBtn) {
      followBtn.addEventListener('click', function() {
        const authorId = this.getAttribute('data-author-id');
        if (this.classList.contains('follow-btn')) {
          sendFollowRequest(authorId, this);
        } else if (this.classList.contains('unfollow-btn')) {
          unfollowAuthor(authorId, this);
        } else if (this.classList.contains('requested-btn')) {
          alert('Your follow request is pending approval.');
        }
      });
    }
  });
  
  function sendFollowRequest(authorId, button) {
    fetch(`${window.location.origin}/api/authors/${authorId}/inbox/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        "type": "follow",
        "summary": `${userDisplayName} wants to follow you.`,
        "actor": {
          "type": "author",
          "id": userId,
          "host": userHost,
          "displayName": userDisplayName,
          "url": userUrl,
          "github": userGithub,
          "profileImage": userProfileImage,
        },
        "object": {
          "type": "author",
          "id": `${window.location.origin}/api/authors/${authorId}/`,
          "host": `${window.location.origin}/`,
          "displayName": button.dataset.authorDisplayName,
          "url": `${window.location.origin}/authors/${authorId}/`,
          "github": button.dataset.authorGithub,
          "profileImage": button.dataset.authorProfileImage,
        }
      }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.message) {
        button.classList.remove('follow-btn');
        button.classList.add('requested-btn');
        button.textContent = 'Requested';
        button.disabled = true;
      } else if (data.error) {
        alert(data.error);
      }
    })
    .catch(error => console.error('Error:', error));
  }
  
  
  
  function unfollowAuthor(authorId, button) {
    const userIdEncoded = encodeURIComponent(userId);

    //alert(`${window.location.origin}/api/authors/${authorId}/followers/${userIdEncoded}/`)
    fetch(`${window.location.origin}/api/authors/${authorId}/followers/${userIdEncoded}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
    })
    .then(response => {
      if (response.status === 204 || response.status === 200) {
        button.classList.remove('unfollow-btn');
        button.classList.add('follow-btn');
        button.textContent = 'Follow';
      } else {
        return response.json().then(data => {
          alert(data.error);
        });
      }
    })
    .catch(error => console.error('Error:', error));
  }
  
  
  

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }