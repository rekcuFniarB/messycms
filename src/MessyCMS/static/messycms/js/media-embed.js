/**
 * MessyCMS  https://github.com/rekcuFniarB/messycms#readme
 * License:  MIT
 */
class MessyMediaEmbed {
    _promise;
    
    constructor(link) {
        this.link = link;
        this.oEmbedApis = {
            'vimeo.com': 'https://vimeo.com/api/oembed.json?autoplay=true&format=json',
            'player.vimeo.com': 'https://vimeo.com/api/oembed.json?autoplay=true&api=true&format=json'
        };
        this.then();
    }
    
    catch(...args) {
        return this._promise.catch(...args);
    }
    
    finally(...args) {
        return this._promise.finally(...args);
    }
    
    then(resolve) {
        if (!this._promise) {
            this._promise = new Promise((embedResolve, embedReject) => {
                if (!this.data) {
                    var oEmbedUrl = document.createElement('a');
                    if (typeof this.oEmbedApis[this.link.hostname] !== 'undefined') {
                        oEmbedUrl.href = this.oEmbedApis[this.link.hostname];
                        oEmbedUrl._search = new URLSearchParams(oEmbedUrl.search);
                        oEmbedUrl._search.set('url', this.link.href);
                        oEmbedUrl.search = oEmbedUrl._search.toString();
                    }
                    else if (!!this.link.dataset.oembedUrl) {
                        oEmbedUrl.href = this.link.dataset.oembedUrl;
                        oEmbedUrl.search = new URLSearchParams({
                            url: this.link.href,
                            format: 'json',
                        }).toString();
                    }
                    else {
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
                            this.link.addEventListener('click', (event) => {
                                this.embedFrame(event).tryToPlay(null, 'click');
                            }, {once: true});
                        }
                        
                        data.thumbnail_url = this.link.dataset.embedThumbnail || this.link.dataset.thumbnailUrl || data.thumbnail_url || null;
                        
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
                        embedResolve();
                    }
                    
                    if (!!this.link.dataset.embedFrameSrc) {
                        // If predefined frame url
                        this.data.html = `<iframe src="${this.link.dataset.embedFrameSrc}" allow="autoplay; fullscreen"></iframe>`;
                        embedDataReady.bind(this)(this.data);
                    }
                    else if (!!this.link.dataset.embedTemplate) {
                        let embedTemplate = document.getElementById(this.link.dataset.embedTemplate);
                        if (!!embedTemplate) {
                            this.data.html = embedTemplate.innerHTML;
                            this.data.embedTemplate = embedTemplate;
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
                                embedReject(error);
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
                } else {
                    // Normally we shouldn't get here
                    embedResolve();
                }
            });
        }
        return this._promise.then(result => {
            if (typeof resolve === 'function') {
                return resolve(this);
            } else {
                return result;
            }
        });
    }
    
    embedFrame(event) {
        if (!!event) {
            event.preventDefault();
            if (typeof this.frame === 'object') {
                // Already embedded.
                return this;
            }
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
                // Youtube doesn't play some videos if we don't send full referrer.
                this.frame.referrerPolicy = 'no-referrer-when-downgrade';
            }
            else if (frameSrc.hostname == 'w.soundcloud.com') {
                frameSrc.searchParams.set('auto_play', 'true');
                frameSrc.searchParams.set('show_teaser', 'false');
                frameSrc.searchParams.set('hide_related', 'true');
                frameSrc.searchParams.set('show_comments', 'false');
                frameSrc.searchParams.set('show_reposts', 'false');
            }
            frameSrc.search = frameSrc.searchParams.toString();
            this.frame.src = this.link.dataset.embedFrameSrc = frameSrc.href;
            var frameHost = frameSrc.hostname.split('.').reverse();
            var documentHost = document.location.hostname.split('.').reverse();
            if (documentHost[0] === frameHost[0] && documentHost[1] === frameHost[1]) {
                this.frame.referrerPolicy = 'origin';
            }
            //this.frame.width = '';
            //this.frame.height = '';
            //this.frame.style.width = '100%';
            //this.frame.style.height = '100%';
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
            //if (!!this.link.playIcon && sizeUpd) {
            //    this.link.playIcon.centerHorizontally().centerVertically();
            //}
            if (!!this.link.playIcon) {
                this.link.playIcon.style.display = 'none';
            }
            this.link.style.position = 'relative';
            this.frame.style.position = 'absolute';
            this.frame.style.left = 0;
            this.frame.style.top = 0;
            this.frame.style.border = 0;
            this.frame.setAttribute('loading', 'lazy');
            this.frame.setAttribute('allowfullscreen', true);
            this.frame.setAttribute('allow', 'fullscreen; autoplay');
            this._makeOnLoadPromise(this.frame);
            this.link.append(this.frame);
            // Don't use it, oterwise frame will be unclickable
            //this.link.style.pointerEvents = 'none';
            if (!this.link.dataset.href) {
                this.link.dataset.href = this.link.href;
            }
            this.link.removeAttribute('href');
        } else {
            let div = document.createElement('div');
            div.innerHTML = this.data.html;
            this.frame = div.querySelector('iframe');
            if (!!this.frame) {
                this._makeOnLoadPromise(this.frame);
            }
            this.link.parentElement.replaceChild(div, this.link);
        }
        return this;
    } // embedFrame()
    
    tryToPlay(times, source) {
        if (typeof times === 'undefined') {
            times = -1
        }
        times ++;
        if (times > 70) {
            return;
        }
        
        if (!!this.frame && !!this.frame.contentWindow) {
            // 23
            this.frame.contentWindow.postMessage(JSON.stringify({
                f: 'set',
                cbId: 'playing',
                args: ['playing', true]
            }), '*');
            // SC
            this.frame.contentWindow.postMessage(JSON.stringify(
                {method: 'play'}
            ), '*');
            // YT
            this.frame.contentWindow.postMessage(JSON.stringify(
                {event: 'command', func: 'playVideo', args: ''}
            ), '*');
            setTimeout(() => { this.tryToPlay(times, 'setTimeout'); }, 100);
        }
    } // tryToPlay()
    
    /**
     * Making promise interface
     */
    _makeOnLoadPromise(element) {
        if (typeof element.then === 'undefined') {
            // We will resolve this promise when content of element is loaded
            var promise = new Promise((resolve, reject) => {
                element.resolve = resolve.bind(element);
                element.reject = reject.bind(element);
            });
            for (let fn of ['then', 'catch', 'finally']) {
                element[fn] = (...args) => { return promise[fn](...args); };
            }
            element.addEventListener('load', function(event) {
                event.target.resolve(event);
            });
        }
        return element;
    } // _makeOnLoadPromise()
}

class MessyPlaylist {
    current;
    pollTimer;
    soundTested;
    
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
                if (!!media) {
                    this.embedPlace.append(media);
                    this.classList.add('active');
                } else {
                    this.classList.remove('active');
                }
            }.bind(this.container);
            this.container.addEventListener('click', this.onClick.bind(this));
        }
        if (typeof this.list !== 'object') {
            console.error('ERROR: no playlist element supplied to constructor');
        } else {
            this.list.addEventListener('click', this.onClick.bind(this));
        }
        //this.testSound();
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
        context._osc = context.createOscillator(); // instantiate an oscillator
        context._osc.type = 'sine'; // this is the default - also square, sawtooth, triangle
        context._osc.frequency.value = 20000; // Hz
        context._osc.connect(context.destination); // connect it to the destination
        context._osc.start(); // start the oscillator
        context._osc.stop(context.currentTime + 0.1); // stop 0.1 seconds after the current time
        return context;
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
                        //this.current.frame.then(event => {
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
                else if (event.origin.indexOf('vimeo.com') > -1) {
                    // https://github.com/vimeo/player-api/blob/archived/javascript/froogaloop.js
                    if (event.data.indexOf('"event":"ready"') > -1) {
                        this.current.frame.contentWindow.postMessage(JSON.stringify(
                            {method: 'play'}
                        ), '*');
                        this.current.frame.contentWindow.postMessage(JSON.stringify(
                            {method: 'addEventListener', value: 'timeupdate'}
                        ), '*');
                        this.current.frame.contentWindow.postMessage(JSON.stringify(
                            {method: 'addEventListener', value: 'ended'}
                        ), '*');
                    }
                    else if (event.data.indexOf('"event":"playProgress"') > -1) {
                        this.onPlaybackProgress(JSON.parse(event.data));
                    }
                    else if (event.data.indexOf('"event":"finish"') > -1) {
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
        if (!this.soundTested) {
            this.soundTested = this.testSound();
        }
        
        if (!!event.target.closest('.btn-playlist-prev')) {
            this.play(this.prev().value);
        }
        else if (!!event.target.closest('.btn-playlist-next')) {
            this.play(this.next().value);
        }
        else if (!!event.target.closest('.btn-playlist-close')) {
            // Close popup.
            this.play(null);
        }
        else if (!!event.target.closest('.player-progressbar')) {
            this.setCurrentTime(event);
        }
        else if (event.target.closest('.playlist-item') || event.target.closest('li')) {
            let playlistItem = event.target.closest('.playlist-item');
            if (!playlistItem) {
                let li = event.target.closest('li');
                if (!!li) {
                    let items = li.querySelectorAll('.playlist-item');
                    if (items.length === 1) {
                        playlistItem = items[0];
                    }
                }
            }
            
            if (!!this.container && !!this.container.currentPlaylist) {
                // If there was other playlist playing.
                this.container.currentPlaylist.play(null);
            }
            this.play(playlistItem, event);
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
            else if (!!event.data && !!event.data.seconds && !event.data.currentTime) {
                // Vimeo
                event.data.currentTime = event.data.seconds;
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
                                this.current.frame.dataset.duration = event.data.duration;
                                this.current.frame.dataset.currentTime = event.data.currentTime;
                            }
                        });
                    }
                }
            }
        }
    }
    
    setCurrentTime(event) {
        var gotoTime;
        
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow && !!this.current.frame.dataset.duration) {
            if (!!event && !!event.target) {
                var eRectangle = event.target.getBoundingClientRect();
                var eWidth = event.clientX - eRectangle.left;
                // Calculating relative offset
                var ratio = eWidth / event.target.offsetWidth;
                gotoTime = this.current.frame.dataset.duration * ratio;
            }
            else if (!!event && !!event.seekTo) {
                gotoTime = event.seekTo;
            }
            else {
                return false;
            }
            
            if (this.current.frame.src.indexOf('soundcloud') > -1) {
                // SC (expects in ms)
                this.current.frame.contentWindow.postMessage(JSON.stringify({
                    method: 'seekTo', value: gotoTime * 1000
                }), '*');
            }
            else if (this.current.frame.src.indexOf('vimeo') > -1) {
                this.current.frame.contentWindow.postMessage(JSON.stringify({
                    method: 'seekTo', value: gotoTime
                }), '*');
            }
            else if (this.current.frame.src.indexOf('youtube') > -1) {
                this.current.frame.contentWindow.postMessage(JSON.stringify({
                    event: "command", func: "seekTo", args: [gotoTime]
                }), '*');
            }
            else if (this.current.frame.src.indexOf('23video') > -1 || this.current.frame.src.indexOf('twentythree') > -1) {
                this.current.frame.contentWindow.postMessage(JSON.stringify({
                    f: 'set',
                    cbId: 'setCurrentTime',
                    args: ['currentTime', gotoTime]
                }), '*');
            }
            else {
                this.current.frame.contentWindow.postMessage(JSON.stringify({
                    currentTime: gotoTime
                }), '*');
            }
        }
    }
    
    play(item, event) {
        this.current = item;
        // Reset progressbar
        //this.onPlaybackProgress({data: {duration: 0, currentTime: 0}});
        
        if (!!this.container && !!this.container.currentPlaylist && this.container.currentPlaylist != this) {
            // Some other playlist is already playing.
            return false;
        }
        
        if (!!this.list) {
            for (let listItem of this.list.querySelectorAll('li')) {
                if (listItem.contains(item)) {
                    listItem.classList.add('active');
                } else {
                    listItem.classList.remove('active');
                }
            }
        }
        
        if (!item) {
            // End of playlist?
            if (!!this.container) {
                this.container.embed(false);
                this.container.currentPlaylist = null;
                return false;
            }
        }
        
        this.container.currentPlaylist = this;
        
        var embedMedia = document.createElement('a');
        embedMedia.classList.add('media-embed');
        embedMedia.href = item.href;
        Object.assign(embedMedia.dataset, item.dataset);
        if (!!this.container) {
            if (!!event) {
                event.preventDefault();
            }
            this.container.embed(embedMedia);
            embedMedia.embed = new MessyMediaEmbed(embedMedia);
            embedMedia.embed.then(embed => {
                this.current.frame = embed.embedFrame().frame;
                this.onEmbedReady({frame: this.current.frame});
            })
            .catch(error => {
                console.error('Failed to play playlist item:', item, error);
                // Skip current
                this.play(this.next().value);
            });
        }
    }
    
    onEmbedReady(event) {
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow) {
            if (this.current.frame.src.indexOf('youtube') > -1) {
                this.pollYoutube();
                this.pollTimer = setInterval(this.pollYoutube.bind(this), 100);
            }
        }
    }
    
    pollYoutube() {
        if (!!this.current && !!this.current.frame && !!this.current.frame.contentWindow && this.current.frame.src.indexOf('youtube') > -1) {
            // https://stackoverflow.com/questions/7443578/youtube-iframe-api-how-do-i-control-an-iframe-player-thats-already-in-the-html
            // https://developers.google.com/youtube/iframe_api_reference?hl=en
            this.current.frame.contentWindow.postMessage(JSON.stringify({event: 'listening', id: 'youtube'}), '*');
            this.current.frame.contentWindow.postMessage(JSON.stringify({event: 'command', func: 'playVideo', args: ''}), '*');
        } else {
            clearInterval(this.pollTimer);
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
