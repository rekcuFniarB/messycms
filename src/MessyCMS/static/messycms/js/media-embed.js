/**
 * MessyCMS  https://github.com/rekcuFniarB/messycms#readme
 * License:  MIT
 */
function MediaEmbedded(link) {
    var This = this;
    this.link = link;
    this.oEmbedApis = {
        'vimeo.com': 'https://vimeo.com/api/oembed.json?autoplay=true&format=json',
        'player.vimeo.com': 'https://vimeo.com/api/oembed.json?autoplay=true&format=json'
    };
    this.getOEmbed = function() {
        if (!this.data) {
            var oEmbedUrl = document.createElement('a');
            if (typeof this.oEmbedApis[this.link.hostname] !== 'undefined') {
                oEmbedUrl.href = this.oEmbedApis[this.link.hostname];
                oEmbedUrl._search = new URLSearchParams(oEmbedUrl.search);
                oEmbedUrl._search.set('url', this.link.href);
                oEmbedUrl.search = oEmbedUrl._search.toString();
            } else {
                // Fallback to link url
                oEmbedUrl.href = this.link.href;
                oEmbedUrl.pathname = '/oembed';
                oEmbedUrl.search = new URLSearchParams({
                    url: this.link.href,
                    format: 'json',
                }).toString();
            }
            if (oEmbedUrl.hostname == 'youtu.be') oEmbedUrl.hostname = 'www.youtube.com';
            
            fetch(oEmbedUrl.href)
                .then((response) => {return response.json()})
                .then((data) => {
                    this.data = data;
                    if (!!data.html) {
                        this.link.addEventListener('click', this.embedFrame, {once: true});
                    }
                    if (!!data.thumbnail_url) {
                        this.link.style.backgroundImage = `url(${data.thumbnail_url})`;
                        this.link.style.backgroundRepeat = 'no-repeat';
                        this.link.style.backgroundSize = '100%';
                        this.link.style.backgroundPosition = 'center';
                        this.link.style.backgroundSize = 'cover';
                    }
                    if (!!data.title) {
                        this.link.setAttribute('title', data.title);
                    }
                    this.link.dispatchEvent(new Event('load'));
                })
                .catch((error) => {
                    console.error('Request error:', error);
                });
            
            var playIcon = document.createElement('div');
            playIcon.classList.add('embed-play-icon');
            this.link.append(playIcon);
            this.link.style.position = 'relative';
            playIcon.style.position = 'absolute';
            playIcon.centerVertically().centerHorizontally();
        }
        return this;
    }.bind(this);
    
    this.embedFrame = function(event) {
        if (!!event) {
            event.preventDefault();
        }
        var div = document.createElement('div');
        div.innerHTML = this.data.html;
        this.frame = div.querySelector('iframe');
        if (!!this.frame) {
            var frameSrc = document.createElement('a');
            frameSrc.href= this.frame.src;
            frameSrc.searchParams = new URLSearchParams(frameSrc.search);
            if (frameSrc.hostname == 'www.youtube.com') {
                frameSrc.hostname = 'www.youtube-nocookie.com';
                frameSrc.searchParams.set('autoplay', 1);
                frameSrc.searchParams.set('rel', 0);
            }
            else if (frameSrc.hostname == 'w.soundcloud.com') {
                frameSrc.searchParams.set('auto_play', 'true');
            }
            frameSrc.search = frameSrc.searchParams.toString();
            this.frame.src = frameSrc.href;
            this.frame.width = '';
            this.frame.height = '';
            this.frame.style.width = '100%';
            this.frame.style.height = '100%';
            this.link.style.position = 'relative';
            this.frame.style.position = 'absolute';
            this.frame.style.left = 0;
            this.frame.style.top = 0;
            this.frame.setAttribute('loading', 'lazy');
            this.frame.setAttribute('allowfullscreen', true);
            this.frame.setAttribute('allow', 'fullscreen; autoplay');
            this.link.append(this.frame);
        } else {
            this.link.innerHTML = this.data.html;
        }
        
        return this;
    }.bind(this);
    
    this.getOEmbed();
}
