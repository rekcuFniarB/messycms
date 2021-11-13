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
    var readyPromise = {};
    this.ready = new Promise((resolve, reject) => {
        readyPromise.resolve = resolve;
        readyPromise.reject = reject;
    });
    
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
            
            this.data = {html: ''};
            Object.assign(this.data, this.link.dataset);
            
            function embedDataReady(data) {
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
                readyPromise.resolve(this);
            }
            
            if (!!this.link.dataset.embedFrameSrc) {
                // If predefined frame url
                this.data.html = `<iframe src="${this.link.dataset.embedFrameSrc}" allow="autoplay; fullscreen"></iframe>`;
                
                if (!!this.link.dataset.embedThumbnail) {
                    this.data.thumbnail_url = this.link.dataset.embedThumbnail;
                }
                embedDataReady.bind(this)(this.data);
            }
            else if (!!this.link.dataset.embedTemplate) {
                let embedTemplate = document.getElementById(this.link.dataset.embedTemplate);
                if (!!embedTemplate) {
                    this.data.html = embedTemplate.innerHTML;
                    this.data.embedTemplate = embedTemplate;
                }
                if (!!this.link.dataset.embedThumbnail) {
                    this.data.thumbnail_url = this.link.dataset.embedThumbnail;
                }
                embedDataReady.bind(this)(this.data);
            }
            else {
                fetch(oEmbedUrl.href)
                    .then((response) => {return response.json()})
                    .then((data) => {
                        this.data = data;
                        embedDataReady.bind(this)(this.data);
                    })
                    .catch((error) => {
                        console.error(`Request error for oEmbed URL ${oEmbedUrl.href}:`, error);
                        readyPromise.reject(error);
                    });
            }
            
            if (!this.link.dataset.embedNoPlayIcon) {
                this.link.playIcon = document.createElement('div');
                this.link.playIcon.classList.add('embed-play-icon');
                this.link.append(this.link.playIcon);
                this.link.style.position = 'relative';
                this.link.playIcon.style.position = 'absolute';
                this.link.playIcon.centerVertically().centerHorizontally();
            }
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
        if (!!this.frame && !this.data.embedTemplate) {
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
                frameSrc.searchParams.set('show_teaser', 'false');
                frameSrc.searchParams.set('hide_related', 'true');
                frameSrc.searchParams.set('show_comments', 'false');
                frameSrc.searchParams.set('show_reposts', 'false');
            }
            frameSrc.search = frameSrc.searchParams.toString();
            this.frame.src = frameSrc.href;
            this.frame.width = '';
            this.frame.height = '';
            this.frame.style.width = '100%';
            this.frame.style.height = '100%';
            var sizeUpd = false;
            if (!!this.data.embedWidth) {
                this.link.style.width = this.data.embedWidth;
                sizeUpd = true;
            }
            if (!!this.data.embedHeight) {
                this.link.style.height = this.data.embedHeight;
                this.link.style.paddingBottom = 0;
                sizeUpd = true;
            }
            if (!!this.link.playIcon && sizeUpd) {
                this.link.playIcon.centerHorizontally().centerVertically();
            }
            this.link.style.position = 'relative';
            this.frame.style.position = 'absolute';
            this.frame.style.left = 0;
            this.frame.style.top = 0;
            this.frame.style.border = 0;
            this.frame.setAttribute('loading', 'lazy');
            this.frame.setAttribute('allowfullscreen', true);
            this.frame.setAttribute('allow', 'fullscreen; autoplay');
            // We will resolve this promise when frame loaded
            var promiseActions = {};
            this.frame.ready = new Promise((resolve, reject) => {
                promiseActions.resolve = resolve.bind(this.frame);
                promiseActions.reject = reject.bind(this.frame);
            });
            Object.assign(this.frame.ready, promiseActions);
            this.frame.addEventListener('load', function(event) {
                event.target.ready.resolve(event);
            });
            this.link.append(this.frame);
        } else {
            let div = document.createElement('div');
            div.innerHTML = this.data.html;
            this.link.parentElement.replaceChild(div, this.link);
        }
        
        return this;
    }.bind(this);
    
    this.getOEmbed();
}

class MessyPlaylist {
    current;
    constructor(config) {
        if (typeof config === 'object') {
            Object.assign(this, config);
        }
        this[Symbol.iterator] = function() { return this; };
        if (typeof this.container !== 'object') {
            console.error('WARNING: no container supplied to constructor');
        }
        if (typeof this.list !== 'object') {
            console.error('ERROR: no playlist element supplied to constructor');
        } else {
            this.list.addEventListener('click', this.onClick.bind(this));
        }
        this.testSound();
        window.addEventListener('message', this.postMessagesResponse.bind(this));
    }
    
    log(...args) {
        if (!!this.debug) {
            if (typeof console[args[0]] === 'function') {
                return console[args[0]](...args.slice(1));
            } else {
                return console.info(...args);
            }
        }
    }
    
    testSound() { // https://stackoverflow.com/a/16573282
        // one context per document
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator(); // instantiate an oscillator
        osc.type = 'sine'; // this is the default - also square, sawtooth, triangle
        osc.frequency.value = 20000; // Hz
        osc.connect(context.destination); // connect it to the destination
        osc.start(); // start the oscillator
        osc.stop(context.currentTime + 0.1); // stop 0.1 seconds after the current time
    }
    
    postMessagesResponse(event) {
        this.log('MESSAGE', event.data, event.origin);
        if (!!this.current.frame && !!this.current.frame.contentWindow) {
            if (typeof event.data === 'string') {
                if (event.data.indexOf('"method":"ready"') > -1) {
                    // Soundcloud ready
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        {method: 'addEventListener', value: 'finish'}
                    ), '*');
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        {method: 'play'}
                    ), '*');
                }
                else if (event.data.indexOf('"method":"finish"') > -1) {
                    // SC playback finished
                    this.play(this.next().value);
                }
                else if (event.data.indexOf('player:video:ended') > -1) {
                    // 23video ended
                    this.play(this.next().value);
                }
                else if (event.data == 'playerinited') {
                    // Bandcamp.com
                    this.current.frame.contentWindow.postMessage(['#big_play_button', 'click'], '*');
                }
            }
            else if (typeof event.data === 'object') {
                if (['ended', 'error'].indexOf(event.data.type) > -1) {
                    if (event.data.type === 'error') {
                        console.error('PLAYLIST ITEM ERROR:', event.data);
                    }
                    this.play(this.next().value);
                }
            }
        }
    }
    
    onClick(event) {
        if (event.target.classList.contains('playlist-item')) {
            this.play(event.target, event);
        }
    }
    
    play(item, event) {
        this.current = item;
        if (!item) {
            // End of playlist?
            if (!!this.container) {
                this.container.classList.remove('active');
                return false;
            }
        }
        var embedMedia = document.createElement('a');
        embedMedia.classList.add('media-embed');
        embedMedia.href = item.href;
        Object.assign(embedMedia.dataset, item.dataset);
        if (!!this.container) {
            if (!!event) {
                event.preventDefault();
            }
            this.container.innerHTML = '';
            this.container.append(embedMedia);
            this.container.classList.add('active');
            embedMedia.embed = new MediaEmbedded(embedMedia);
            embedMedia.embed.ready.then((embed) => {
                this.current.frame = embed.embedFrame().frame;
                var frameSrc = document.createElement('a');
                frameSrc.href = this.current.frame.src;
                if (frameSrc.hostname.indexOf('23video.com') > -1) {
                    // Source: https://github.com/23/GlueFrame
                    this.current.frame.ready.then(event => {
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'set',
                            cbId: 'playing',
                            args: ['playing', true]
                        }), '*');
                        // Subscribing to playback end event
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'bind',
                            cbId: 'ended',
                            args: ['player:video:ended']
                        }), '*');
                    });
                }
            });
        }
    }
    
    next() {
        var items = [...this.list.querySelectorAll('.playlist-item')];
        var result = {done: true, value: this.current};
        if (items.length > 0) {
            if (!this.current) {
                // Beginning
                this.current = result.value = items[0];
                result.done = false;
            } else {
                var curIndex = items.indexOf(this.current) + 1;
                if (curIndex < items.length) {
                    // Can get next next
                    this.current = result.value = items[curIndex];
                    result.done = false;
                } else {
                    // Reached the end
                    result.done = true;
                    this.current = result.value = null;
                }
                result.curIndex = curIndex;
            }
        } else {
            result.done = true;
            this.current = result.value = null;
        }
        return result;
    }
}
