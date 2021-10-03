/**
 * MessyCMS  https://github.com/rekcuFniarB/messycms#readme
 * License:  MIT
 */
MessyCMS = function() {
    var This = this;
    this.events = new function () {
        var parent = This;
        var This = this;
        this.add = (function(element, type, handler, name) {
            if (typeof element._event_handlers !== 'object') {
                element._event_handlers = [];
            }
            if (typeof element._event_handlers[type] === 'undefined') {
                element._event_handlers[type] = [];
                element.addEventListener(type, (function(event) {
                    if (typeof this._event_handlers[event.type] === 'object') {
                        for (var handler of this._event_handlers[event.type]) {
                            handler.bind(element);
                            handler(event);
                        }
                    }
                }).bind(element));
            }
            if (typeof handler === 'function') {
                handler._explicit_name = name;
                element._event_handlers[type].push(handler);
            }
        }).bind(this);
        // Remove event
        this.remove = (function(element, type, name) {
            element._event_handlers[type] = element._event_handlers[type].filter((item) => {
                return item._explicit_name != name;
            });
        }).bind(this);
    }; // events object
    
    this.initAjaxMode = function(container) {
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        if (typeof container === 'object') {
            container.metadata = (function(path) {
                var metadataContainer;
                if (path) {
                    metadataContainer = this.querySelector(`script.section-metadata[data-path="${path}"]`);
                } else {
                    metadataContainer = this.querySelector('script.section-metadata');
                }
                var metadata = {};
                if (!!metadataContainer) {
                    var div = document.createElement('div');
                    div.innerHTML = metadataContainer.innerText;
                    for (var element of div.children) {
                        metadata[element.dataset.field] = element.innerText;
                    }
                }
                return metadata;
            }).bind(container);
            
            container.loadContent = (function(url, pushState) {
                if (typeof pushState === 'undefined') pushState = true;
                //var requestURL = new URL(url);
                // URL class sucks, it doesn't accept relative paths
                var requestURL = document.createElement('a');
                requestURL.href = url;
                requestURL.params = new URLSearchParams(requestURL.search);
                requestURL.params.set('metadata', 'yes');
                requestURL.search = requestURL.params.toString();
                
                return fetch(requestURL.href, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then((response) => { return response.text(); })
                .then((response) => {
                this.innerHTML = response;
                    var metadata = this.metadata(requestURL.pathname);
                    if (!!metadata.title) {
                        document.title = metadata.title;
                    }
                    if (pushState) {
                        window.history.pushState({url: url, title: document.title}, document.title, url);
                    }
                })
                .then(() => {
                    window.dispatchEvent(new Event('load'));
                })
                .catch((error) => {
                    console.error('AJAX ERROR:', error);
                });
            }).bind(container);
            
            This.events.add(document.body, 'click', (event) => {
                if (event.target.nodeName == 'A') {
                    if (typeof event.target.dataset.noAjax !== 'undefined') return;
                    if (event.ctrlKey || event.altKey || event.shiftKey) return;
                    if (event.target.host != document.location.host) return;
                    if (event.target.protocol.indexOf('http') !== 0) return;
                    event.preventDefault();
                    container.loadContent(event.target.href);
                }
                // Add other handlers here
            }, 'AjaxMode');
            
            This.events.add(window, 'popstate', (event) => {
                if (!!event.state) {
                    if (!!event.state.url) {
                        container.loadContent(event.state.url, false);
                    }
                }
            }, 'AjaxMode');
        }
        return container;
    };
    
    this.modal = document.createElement('div');
    this.modal.open = (function(content) {
        if (!this.classList.contains('messy-modal')) {
            // Opening for first time, do init.
            this.classList.add('messy-modal');
            this.wrapper = document.createElement('div');
            this.wrapper.classList.add('messy-modal-wrapper', 'messy-d-none');
            document.body.append(this.wrapper);
            this.wrapper.append(this);
            
            // Close popup and resolve promise with value
            this.close = (function(value) {
                this.show(false);
                if (typeof this._resolve === 'function') {
                    this._resolve(value);
                }
            }).bind(this);
            
            // Close on clicks outside of modal window.
            this.wrapper.addEventListener('click', (event) => {
                if (event.target.classList.contains('messy-modal-wrapper')) {
                    this.close();
                }
            });
            
            // Close on Escape button press
            document.body.addEventListener('keyup', (event) => {
                if (event.key && event.key == 'Escape') {
                    this.close();
                }
            });
            
            this.show = (function(show) {
                if (show) {
                    this.wrapper.classList.replace('messy-d-none', 'messy-d-block');
                    this.wrapper.style.height = `${document.body.scrollHeight}px`;
                    // Calculate top
                    var modalTop = (window.innerHeight - This.modal.offsetHeight) / 2;
                    var modalLeft = (window.innerWidth - This.modal.offsetWidth) / 2;
                    this.style.top = `${modalTop}px`;
                    this.style.left = `${modalLeft}px`;
                } else {
                    this.wrapper.classList.replace('messy-d-block', 'messy-d-none');
                }
            }).bind(this);
        } // if was not "messy-modal" class (end of init on first time invokation)
        
        if (!!content) {
            this.innerHTML = '';
            if (typeof content == 'object') {
                this.append(object);
            }
            else if (typeof content == 'string') {
                this.innerHTML = content;
            }
        }
        
        // If was closed, create new promise
        if (this.wrapper.classList.contains('messy-d-none')) {
            this._promise = new Promise((resolve, reject) => {this._resolve = resolve;});
        }
        
        this.show(true);
        
        return this._promise;
    }).bind(this.modal);
    
    // Init
    // Extending Element class with our methods
    if (typeof Element.prototype.recalcHeight === 'undefined') {
        Element.prototype.recalcHeight = function(event) {
            if (document.body.scrollHeight < window.innerHeight) {
                // Fixing content container height
                this.style.minHeight = this.offsetHeight + (window.innerHeight - document.body.scrollHeight - 1) + 'px';
            } else {
                //this.style.minHeight = '';
            }
            
            if (typeof this.__recalcHeightEvent === 'undefined') {
                this.__recalcHeightEvent = true;
                This.events.add(window, 'resize', this.recalcHeight.bind(this), 'recalcHeight');
                This.events.add(window, 'load', this.recalcHeight.bind(this), 'recalcHeight');
            }
            
            return this;
        };
    }
    
    if (typeof Element.prototype.findParent === 'undefined') {
        Element.prototype.findParent = function(match) {
            var found = null;
            var current = this;
            while (!found && !!current && !!current.parentElement) {
                current = current.parentElement;
                if (match(current)) {
                    found = current;
                }
            }
            return found;
        };
    }
}
