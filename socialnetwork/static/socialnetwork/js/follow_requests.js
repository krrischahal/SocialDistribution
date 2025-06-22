document.addEventListener('DOMContentLoaded', function() {
    // Handle Accept Buttons
    var acceptButtons = document.querySelectorAll('.accept-btn');
    acceptButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var followId = this.getAttribute('data-follow-id');
            respondToFollowRequest(followId, 'accept', this);
        });
    });

    // Handle Reject Buttons
    var rejectButtons = document.querySelectorAll('.reject-btn');
    rejectButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var followId = this.getAttribute('data-follow-id');
            respondToFollowRequest(followId, 'reject', this);
        });
    });

    // Handle Follow/Unfollow/Requested Buttons
    document.querySelectorAll('.follow-btn, .unfollow-btn, .requested-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const authorId = this.getAttribute('data-author-id');
            if (this.classList.contains('follow-btn')) {
                sendFollowRequest(authorId, this);
            } else if (this.classList.contains('unfollow-btn')) {
                unfollowAuthor(authorId, this);
            } else if (this.classList.contains('requested-btn')) {
                alert('Your follow request is pending approval.');
            }
        });
    });

    // Handle Remove Follower Buttons
    document.querySelectorAll('.remove-follower-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const authorId = this.getAttribute('data-author-id');
            removeFollower(authorId, this);
        });
    });

    function respondToFollowRequest(followId, action, button) {
        const csrfToken = getCookie('csrftoken');

        fetch(`/api/follow-requests/${followId}/${action}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                // Remove the request from the list
                const listItem = button.closest('li');
                listItem.parentNode.removeChild(listItem);
                console.log(`Follow request ${action}ed successfully.`);
            } else {
                response.json().then(data => {
                    console.error(`Failed to ${action} follow request:`, data.error || data);
                    alert(`Error: ${data.error || 'An error occurred.'}`);
                });
            }
        })
        .catch(error => {
            console.error(`Error ${action}ing follow request:`, error);
            alert(`Error: ${error.message || 'An error occurred.'}`);
        });
    }

    function sendFollowRequest(authorId, button) {
        const csrfToken = getCookie('csrftoken');

        const payload = {
            "author_id": authorId,
        };

        fetch('/api/follow/', {  // Send to your backend's follow endpoint
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })
        .then(response => {
            if (response.ok) {
                button.classList.remove('follow-btn');
                button.classList.add('requested-btn');
                button.textContent = 'Requested';
                console.log("Follow request sent.");
            } else {
                response.json().then(data => {
                    console.error("Failed to send follow request:", data.error || data);
                    alert(`Error: ${data.error || 'An error occurred.'}`);
                });
            }
        })
        .catch(error => {
            console.error("Error sending follow request:", error);
            alert(`Error: ${error.message || 'An error occurred.'}`);
        });
    }

    function unfollowAuthor(authorId, button) {
        const csrfToken = getCookie('csrftoken');

        fetch('/api/unfollow/', {  // Send to your backend's unfollow endpoint
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "author_id": authorId }),
        })
        .then(response => {
            if (response.ok) {
                button.classList.remove('unfollow-btn');
                button.classList.add('follow-btn');
                button.textContent = 'Follow';
                console.log("Unfollow request sent.");
            } else {
                response.json().then(data => {
                    console.error("Failed to send unfollow request:", data.error || data);
                    alert(`Error: ${data.error || 'An error occurred.'}`);
                });
            }
        })
        .catch(error => {
            console.error("Error sending unfollow request:", error);
            alert(`Error: ${error.message || 'An error occurred.'}`);
        });
    }

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
