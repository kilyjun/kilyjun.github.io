window.addEventListener('DOMContentLoaded', (event) => {
    var videoContainers = Array.from(document.querySelectorAll('.video-container'));
    var scrollPerSecond = window.innerHeight / 100; // Adjust this to change scroll sensitivity
    var lastKnownScrollPosition = 0;
    var ticking = false;
    var videos = ['cocacola3.mp4', 'bird.mp4', 'nike2.mp4', 'musk.mp4']; // Add your videos here

    function setupVideo(container) {
        var video = container.querySelector('video');
        var spacer = container.querySelector('.spacer');

        video.addEventListener('loadedmetadata', function() {
            var spacerHeight = (video.duration * scrollPerSecond) - container.offsetHeight;
            spacer.style.height = spacerHeight + 'px';
        });
    }

    function checkVisibility(elem) {
        var rect = elem.getBoundingClientRect();
        return rect.top < window.innerHeight && rect.bottom >= 0;
    }

    videoContainers.forEach(setupVideo);

    window.addEventListener('scroll', function() {
        lastKnownScrollPosition = window.scrollY;
        if (!ticking) {
            window.requestAnimationFrame(function() {
                videoContainers.forEach((container, index) => {
                    var video = container.querySelector('video');

                    if (checkVisibility(video)) {
                        if (video.paused) {
                            video.play();
                        }
                    } else if (!video.paused) {
                        video.pause();
                    }
                });

                // If the user has scrolled within 1000px of the bottom, add more videos
                if (lastKnownScrollPosition > document.documentElement.scrollHeight - window.innerHeight - 1000) {
                    videos.forEach(src => {
                        var newContainer = document.createElement('div');
                        newContainer.classList.add('video-container');

                        var newVideo = document.createElement('video');
                        newVideo.src = src;
                        newVideo.preload = 'metadata';
                        newVideo.muted = true;
                        newContainer.appendChild(newVideo);

                        var newSpacer = document.createElement('div');
                        newSpacer.classList.add('spacer');
                        newContainer.appendChild(newSpacer);

                        document.body.appendChild(newContainer);
                        setupVideo(newContainer);
                        videoContainers.push(newContainer);
                    });
                }

                ticking = false;
            });

            ticking = true;
        }
    });
});
