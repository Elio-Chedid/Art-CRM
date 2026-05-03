// Notification count updater
function updateNotificationCount() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationCount');
            if (badge && data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

// Update notification count on page load and every 30 seconds
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationCount();
    setInterval(updateNotificationCount, 30000);
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirm before form submission for destructive actions
    const destructiveForms = document.querySelectorAll('form[data-confirm]');
    destructiveForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});

// Format dates nicely
function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(date).toLocaleDateString('en-US', options);
}

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add to top button
window.addEventListener('scroll', function() {
    const scrollBtn = document.getElementById('scrollToTop');
    if (scrollBtn) {
        if (window.pageYOffset > 300) {
            scrollBtn.style.display = 'block';
        } else {
            scrollBtn.style.display = 'none';
        }
    }
});

// Notification management
function updateNotificationCount() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationCount');
            if (badge && data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(notifications => {
            const notifList = document.getElementById('notificationList');
            if (!notifList) return;
            
            if (notifications.length === 0) {
                notifList.innerHTML = `
                    <li class="text-center py-3 text-muted">
                        <i class="fas fa-inbox"></i><br>
                        No new notifications
                    </li>
                `;
                return;
            }
            
            let html = '';
            notifications.forEach(notif => {
                const iconMap = {
                    'new_reservation': 'fa-calendar-plus',
                    'cancellation': 'fa-times-circle',
                    'update': 'fa-edit'
                };
                const icon = iconMap[notif.type] || 'fa-bell';
                
                html += `
                    <li class="notification-item unread" data-id="${notif.id}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="notification-title">
                                    <i class="fas ${icon}"></i> ${notif.title}
                                </div>
                                <div class="notification-message">${notif.message}</div>
                                <div class="notification-time">${notif.created_at}</div>
                            </div>
                            <button class="btn btn-sm btn-link text-success p-0 ms-2 mark-read-btn" 
                                    onclick="markAsRead(${notif.id}, event)">
                                <i class="fas fa-check"></i>
                            </button>
                        </div>
                    </li>
                `;
            });
            
            notifList.innerHTML = html;
        })
        .catch(error => console.error('Error loading notifications:', error));
}

function markAsRead(notificationId, event) {
    event.stopPropagation();
    
    fetch(`/api/notifications/mark-read/${notificationId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = document.querySelector(`[data-id="${notificationId}"]`);
            if (item) {
                item.style.opacity = '0.5';
                item.classList.remove('unread');
                setTimeout(() => {
                    loadNotifications();
                    updateNotificationCount();
                }, 300);
            }
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

// Mark all as read
document.addEventListener('DOMContentLoaded', function() {
    const markAllBtn = document.getElementById('markAllRead');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fetch('/api/notifications/mark-all-read', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadNotifications();
                    updateNotificationCount();
                }
            });
        });
    }
    
    // Load notifications when dropdown is opened
    const notifBell = document.getElementById('notificationBell');
    if (notifBell) {
        notifBell.addEventListener('shown.bs.dropdown', function() {
            loadNotifications();
        });
    }
    
    // Update count on page load and every 30 seconds
    updateNotificationCount();
    loadNotifications();
    setInterval(() => {
        updateNotificationCount();
    }, 30000);
    
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});