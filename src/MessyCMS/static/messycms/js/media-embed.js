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
                //frameSrc.hostname = 'www.youtube-nocookie.com';
                frameSrc.searchParams.set('autoplay', 1);
                frameSrc.searchParams.set('rel', 0);
                frameSrc.searchParams.set('enablejsapi', 1);
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
            this._resolveFrame(this.frame);
            this.link.append(this.frame);
        } else {
            let div = document.createElement('div');
            div.innerHTML = this.data.html;
            this.frame = div.querySelector('iframe');
            if (!!this.frame) {
                this._resolveFrame(this.frame);
            }
            this.link.parentElement.replaceChild(div, this.link);
        }
        return this;
    }.bind(this);
    
    this._resolveFrame = function(iFrame) {
        if (typeof iFrame.ready === 'undefined') {
            // We will resolve this promise when frame loaded
            var promiseActions = {};
            iFrame.ready = new Promise((resolve, reject) => {
                promiseActions.resolve = resolve.bind(iFrame);
                promiseActions.reject = reject.bind(iFrame);
            });
            Object.assign(iFrame.ready, promiseActions);
            iFrame.addEventListener('load', function(event) {
                event.target.ready.resolve(event);
            });
        }
        return iFrame;
    }.bind(this);
    
    this.getOEmbed();
}

class MessyPlaylist {
    current;
    pollTimer;
    
    constructor(config) {
        if (typeof config === 'object') {
            Object.assign(this, config);
        }
        this[Symbol.iterator] = function() { return this; };
        if (typeof this.container !== 'object') {
            console.error('WARNING: no container supplied to constructor');
        } else {
            this.container.embed = function(media) {
                if (!this.embedPlace) {
                    this.embedPlace = this.querySelector('.embed-place');
                    if (!this.embedPlace) {
                        this.embedPlace = this;
                    }
                }
                this.embedPlace.innerHTML = '';
                this.embedPlace.append(media);
                this.classList.add('active');
            }.bind(this.container);
            this.container.addEventListener('click', this.onClick.bind(this));
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
        clearInterval(this.pollTimer);
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow) {
            if (typeof event.data === 'string') {
                if (event.origin.indexOf('23video.com') > -1) {
                    if (event.data.indexOf('"context":"player.js"') > -1 && event.data.indexOf('"event":"ready"') > -1) {
                        // 23video ready, start playback
                        // Source: https://github.com/23/GlueFrame
                        //this.current.frame.ready.then(event => {
                            // Start playback
                            this.current.frame.contentWindow.postMessage(JSON.stringify({
                                f: 'set',
                                cbId: 'playing',
                                args: ['playing', true]
                            }), '*');
                        //});
                    }
                    else if (event.data.indexOf('"cbId":"playing"') > -1) {
                        // They have a bug, "ready" message sent before frame load complete
                        // and playback doesn't start in this case.
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'set',
                            cbId: 'retryplaying',
                            args: ['playing', true]
                        }), '*');
                        setTimeout(() => {
                            this.current.frame.contentWindow.postMessage(JSON.stringify({
                                f: 'set',
                                cbId: 'retryplaying',
                                args: ['playing', true]
                            }), '*');
                        }, 500);
                        // Subscribing to playback end event
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'bind',
                            cbId: 'ended',
                            args: ['player:video:ended']
                        }), '*');
                        // Subscribing to timeupdate events
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'bind',
                            cbId: 'timeupdate',
                            args: ['player:video:timeupdate']
                        }), '*');
                    }
                    else if (event.data.indexOf('"cbId":"timeupdate"') > -1) {
                        // timeupdate event from 23video
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'get',
                            cbId: 'getCurrentTime',
                            args: ['currentTime']
                        }), '*');
                        this.current.frame.contentWindow.postMessage(JSON.stringify({
                            f: 'get',
                            cbId: 'getDuration',
                            args: ['duration']
                        }), '*');
                    }
                    else if (event.data.indexOf('"cbId":"getCurrentTime"') > -1 || event.data.indexOf('"cbId":"getDuration"') > -1) {
                        this.onPlaybackProgress(JSON.parse(event.data));
                    }
                    else if (event.data.indexOf('player:video:ended') > -1) {
                        // 23video ended
                        this.play(this.next().value);
                    }
                }
                else if (event.data.indexOf('"method":"ready"') > -1) {
                    // Soundcloud ready
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        {method: 'addEventListener', value: 'finish'}
                    ), '*');
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        {method: 'addEventListener', value: 'playProgress'}
                    ), '*');
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        {method: 'play'}
                    ), '*');
                }
                else if (event.data.indexOf('"method":"finish"') > -1) {
                    // SC playback finished
                    this.play(this.next().value);
                }
                else if (event.data.indexOf('"playerState":0') > -1) {
                    // YT end
                    this.play(this.next().value);
                }
                else if (event.data == 'playerinited') {
                    // Bandcamp.com
                    this.current.frame.contentWindow.postMessage(['#big_play_button', 'click'], '*');
                }
                else if (event.data.indexOf('"relativePosition":') > -1) {
                    this.onPlaybackProgress(JSON.parse(event.data));
                }
                else if (event.data.indexOf('"currentTime":') > -1) {
                    this.onPlaybackProgress(JSON.parse(event.data));
                }
                else if (event.data === 'FRAMELOADED') {
                    // pdj
                    this.current.frame.contentWindow.postMessage(JSON.stringify(
                        ['.playerr_bigplaybutton', 'click']
                    ), '*');
                }
            }
            else if (typeof event.data === 'object') {
                if (['ended', 'error', '_stalled'].indexOf(event.data.type) > -1) {
                    if (event.data.type !== 'ended') {
                        console.error('PLAYLIST ITEM ERROR:', event.data);
                    }
                    this.play(this.next().value);
                }
                else if (event.data.type === 'timeupdate') {
                    this.onPlaybackProgress(event);
                }
            }
        }
    }
    
    onClick(event) {
        if (event.target.classList.contains('playlist-item')) {
            this.play(event.target, event);
        }
        else if (event.target.classList.contains('btn-playlist-prev')) {
            this.play(this.prev().value);
        }
        else if (event.target.classList.contains('btn-playlist-next')) {
            this.play(this.next().value);
        }
        else if (event.target.classList.contains('player-progressbar')) {
            this.setCurrentTime(event);
        }
    }
    
    onPlaybackProgress(event) {
        if (!!this.container && !!this.current && this.current.frame) {
            if (!this.current.frame.progressBarCurrent) {
                this.current.frame.progressBarCurrent = this.container.querySelector('.player-progressbar-current');
            }
            if (typeof event.data === 'undefined') {
                if (typeof event.info === 'object') {
                    // This came from Youtube
                    event.data = event.info;
                } else {
                    event.data = {};
                }
            }
            if (!!event.value && !!event.value.relativePosition) {
                // This came from SC
                event.data.currentTime = event.value.currentPosition / 1000; // was in ms
                // relativePosition is 0.x values
                event.data.duration = event.data.currentTime / event.value.relativePosition;
            }
            else if (!!event.cbId) {
                // 23video
                if (event.cbId == 'getDuration' && !this.current.frame.dataset.duration) {
                    this.current.frame.dataset.duration = event.a
                }
                else if (event.cbId == 'getCurrentTime') {
                    event.data.currentTime = event.a;
                    event.data.duration = this.current.frame.dataset.duration;
                }
            }
            
            if (typeof event.data.duration === 'undefined' && typeof this.current.frame.dataset.duration != 'undefined') {
                // Some services doesn't send duration every time update
                event.data.duration = this.current.frame.dataset.duration;
            }
            
            if (!!this.current.frame.progressBarCurrent) {
                if (event.data.duration && event.data.currentTime) {
                    var width = (event.data.currentTime * 100) / event.data.duration;
                    if (width > 100) {
                        width = 100;
                    } else {
                        var arWidth = width.toString().split('.');
                        if (!!arWidth[1]) {
                            arWidth[1] = arWidth[1].slice(0, 1);
                        }
                        // Values like 10.1234566 become 10.1
                        width = parseFloat(arWidth.join('.'));
                    }
                    // Don't call to often to reduce CPU usage
                    if (this.current.frame.progressBarCurrent.currentWidth != width) {
                        window.requestAnimationFrame(() => {
                            // It may be undefined due to delayed execution
                            // especially when switched to next track.
                            if (!!this.current && !!this.current.frame && !!this.current.frame.progressBarCurrent) {
                                this.current.frame.progressBarCurrent.style.width = `${width}%`;
                                this.current.frame.progressBarCurrent.currentWidth = width;
                            }
                            this.current.frame.dataset.duration = event.data.duration;
                            this.current.frame.dataset.currentTime = event.data.currentTime;
                        });
                    }
                }
            }
        }
    }
    
    setCurrentTime(event) {
        var eRectangle = event.target.getBoundingClientRect();
        var eWidth = event.clientX - eRectangle.left;
        // Calculating relative offset
        var ratio = eWidth / event.target.offsetWidth;
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow && !!this.current.frame.dataset.duration) {
            var gotoTime = this.current.frame.dataset.duration * ratio;
            this.current.frame.contentWindow.postMessage(JSON.stringify({currentTime: gotoTime}), '*');
            // SC (expects in ms)
            this.current.frame.contentWindow.postMessage(JSON.stringify(
                {method: 'seekTo', value: gotoTime * 1000}
            ), '*');
            // 23video
            this.current.frame.contentWindow.postMessage(JSON.stringify({
                f: 'set',
                cbId: 'setCurrentTime',
                args: ['currentTime', gotoTime]
            }), '*');
            // YT
            this.current.frame.contentWindow.postMessage(JSON.stringify({
                event: "command", func: "seekTo", args: [gotoTime]
            }), '*')
        }
    }
    
    play(item, event) {
        this.current = item;
        // Reset progressbar
        //this.onPlaybackProgress({data: {duration: 0, currentTime: 0}});
        
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
            this.container.embed(embedMedia);
            embedMedia.embed = new MediaEmbedded(embedMedia);
            embedMedia.embed.ready.then((embed) => {
                this.current.frame = embed.embedFrame().frame;
                this.onEmbedReady({frame: this.current.frame});
            });
        }
    }
    
    onEmbedReady(event) {
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow) {
            this.pollYoutube();
            this.pollTimer = setInterval(this.pollYoutube.bind(this), 100);
        }
    }
    
    pollYoutube() {
        // https://stackoverflow.com/questions/7443578/youtube-iframe-api-how-do-i-control-an-iframe-player-thats-already-in-the-html
        // https://developers.google.com/youtube/iframe_api_reference?hl=en
        this.current.frame.contentWindow.postMessage(JSON.stringify({"event":"listening","id":"youtube"}), '*');
        this.current.frame.contentWindow.postMessage(JSON.stringify({"event":"command","func":"playVideo","args":""}), '*');
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
    
    prev() {
        var items = [...this.list.querySelectorAll('.playlist-item')];
        var result = {done: true, value: this.current};
        if (items.length > 0) {
            if (!this.current) {
                // Beginning
                this.current = result.value = items[0];
                result.done = false;
            } else {
                var curIndex = items.indexOf(this.current) - 1;
                if (curIndex > -1) {
                    // Can get next next
                    this.current = result.value = items[curIndex];
                    result.done = false;
                } else {
                    // Reached beginning, go to last item
                    result.done = false;
                    this.current = result.value = items[items.length - 1];
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
