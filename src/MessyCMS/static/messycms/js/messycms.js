/**
 * MessyCMS  https://github.com/rekcuFniarB/messycms#readme
 * License:  MIT
 */

(function() {
    if (typeof Element.prototype.addToEventHandlers === 'undefined') {
        Element.prototype.addToEventHandlers = function(type, handler) {
            // Type may be in format of "click.namespace mouseover.namespace"
            
            if (typeof this._event_handlers !== 'object') {
                this._event_handlers = [];
            }
            
            for (var evName of type.split(' ')) {
                if (!!evName) {
                    var evNames = evName.split('.');
                    evName = evNames[0];
                    var evNamespace = evNames.join('.').replace(`${evName}.`, '');
                    if (typeof this._event_handlers[evName] === 'undefined') {
                        this._event_handlers[evName] = [];
                        this.addEventListener(evName, function(event) {
                            if (typeof this._event_handlers[event.type] === 'object') {
                                for (var handler of this._event_handlers[event.type]) {
                                    handler.bind(this);
                                    handler(event);
                                }
                            }
                        }.bind(this));
                    }
                    if (typeof handler === 'function') {
                        handler._event_namespace = evNamespace;
                        this._event_handlers[evName].push(handler);
                    }
                }
            }
        };
    }
    
    // Remove event
    if (typeof Element.prototype.removeFromEventHandlers === 'undefined') {
        Element.prototype.removeFromEventHandlers = function(what) {
            if (typeof this._event_handlers === 'undefined') return;
            
            if (typeof what === 'function') {
                // Remove requested function
                for (var evType in this._event_handlers) {
                    this._event_handlers[evType] = this._event_handlers[evType].filter((item) => {
                        return item != what;
                    });
                }
            } else {
                var evNames = what.split('.');
                what = evNames[0];
                var evNamespace = evNames.join('.').replace(`${what}.`, '');
                if (typeof this._event_handlers[what] === 'object') {
                    if (!!evNamespace && evNamespace != what) {
                        this._event_handlers[what] = this._event_handlers[what].filter((item) => {
                            return item._event_namespace != evNamespace;
                        });
                    } else {
                        // Remove all for this event type
                        this._event_handlers[what] = [];
                    }
                }
            }
        };
    }
    
    if (typeof Window.prototype.addToEventHandlers === 'undefined') {
        Window.prototype.addToEventHandlers = Element.prototype.addToEventHandlers;
    }
    if (typeof Document.prototype.addToEventHandlers === 'undefined') {
        Document.prototype.addToEventHandlers = Element.prototype.addToEventHandlers;
    }
    
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
                window.addToEventHandlers('load.recalc.height resize.recalc.height', this.recalcHeight.bind(this));
            }
            
            return this;
        };
    }
    
    if (typeof Element.prototype.stretchToParentHeight === 'undefined') {
        Element.prototype.stretchToParentHeight = function() {
            if (!!this.parentElement) {
                this.style.minHeight = `${this.parentElement.offsetHeight}px`;
                if (typeof this.__stretchToParentHeight === 'undefined') {
                    this.__stretchToParentHeight = true;
                    window.addToEventHandlers('resize.recalc.height load.recalc.height', this.stretchToParentHeight.bind(this));
                }
            }
            return this;
        }
    }
    
    if (typeof Element.prototype.findParent === 'undefined') {
        Element.prototype.findParent = function(match, found) {
            // match: callback, should return true or false.
            // found (optional): default value to return if not found.
            var parent = this;
            if (typeof found === 'undefined') found = null;
            while (parent = parent.parentElement) {
                if (match(parent)) {
                    found = parent;
                    parent = {};
                }
            }
            return found;
        };
    }
    
    if (typeof Element.prototype.getParents === 'undefined') {
        Element.prototype.getParents = function(match) {
            // match (optional): callback, should return true or false.
            var parent = this;
            var parents = [];
            while (parent = parent.parentElement) {
                if (typeof match === 'function') {
                    if (match(parent)) parents.push(parent);
                } else {
                    parents.push(parent);
                }
            }
            return parents;
        };
    }
    
    if (typeof Element.prototype.centerVertically === 'undefined') {
        Element.prototype.centerVertically = function(parent) {
            if (typeof parent === 'undefined') {
                parent = this.parentElement;
            }
            if (!!parent) {
                var parentHeight;
                if (typeof parent.innerHeight !== 'undefined') {
                    // It is window
                    parentHeight = parent.innerHeight;
                } else {
                    parentHeight = parent.offsetHeight;
                }
                var top = (parentHeight - this.offsetHeight) / 2;
                this.style.top = `${top}px`;
            }
            return this;
        };
    }
    
    if (typeof Element.prototype.centerHorizontally === 'undefined') {
        Element.prototype.centerHorizontally = function(parent) {
            if (typeof parent === 'undefined') {
                parent = this.parentElement;
            }
            if (!!parent) {
                var parentWidth;
                if (typeof parent.innerWidth !== 'undefined') {
                    // It is window
                    parentWidth = parent.innerWidth;
                } else {
                    parentWidth = parent.offsetWidth;
                }
                var left = (parentWidth - this.offsetWidth) / 2;
                this.style.left = `${left}px`;
            }
            return this;
        };
    }
})();

MessyCMS = function() {
    var This = this;
    
    this.initAjaxMode = function(container) {
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        if (typeof container === 'object') {
            container.metadata = function(path) {
                var metadataContainer;
                if (path) {
                    metadataContainer = this.querySelector(`script.section-metadata[data-path="${path}"]`);
                } else {
                    metadataContainer = this.querySelector('script.section-metadata');
                }
                var metadata = {};
                if (!!metadataContainer) {
                    if (metadataContainer.type.toLowerCase() == 'text/html') {
                        var div = document.createElement('div');
                        div.innerHTML = metadataContainer.innerText;
                        for (var element of div.children) {
                            metadata[element.dataset.field] = element.innerText;
                        }
                    }
                    else if (metadataContainer.type.toLowerCase() == 'application/json') {
                        try {
                            metadata = JSON.parse(metadataContainer.innerText);
                        }
                        catch(error) {
                            console.error('Metadata reading failed:', error);
                        }
                    }
                }
                return metadata;
            }.bind(container);
            
            container.loadContent = function(url, pushState, scrollOnFinish) {
                let eTarget = {dataset: {}};
                let target = this;
                
                if (typeof url === 'object') {
                    if (!url.href) {
                        return console.error('ERROR: loadContent(): object has no "href" param', url);
                    }
                    eTarget = url;
                    url = url.href;
                }
                
                if (typeof pushState === 'undefined') pushState = true;
                if (typeof scrollOnFinish === 'undefined') scrollOnFinish = true;
                
                if (eTarget.dataset.target) {
                    target = document.querySelector(eTarget.dataset.target);
                    if (!target) {
                        return console.error(`ERROR: AJAX target '${eTarget.dataset.target}' not found.`);
                    }
                    pushState = false;
                }
                
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
                    target.innerHTML = response;
                    var metadata = this.metadata(requestURL.pathname);
                    if (!!metadata.title) {
                        document.title = metadata.title;
                    }
                    for (let script of target.querySelectorAll('script')) {
                        // Executing new scripts
                        This.requireScript(script);
                    }
                    for (let template of target.querySelectorAll('template')) {
                        let targetAppend;
                        if (typeof template.dataset.moveToHead !== 'undefined') {
                            targetAppend = document.querySelector('head');
                        }
                        else if (typeof template.dataset.moveToBottom !== 'undefined') {
                            targetAppend = document.body;
                        }
                        if (!!targetAppend) {
                            for (let element of template.content.children) {
                                if (element.tagName == 'SCRIPT') {
                                    This.requireScript(script);
                                }
                                else {
                                    if (targetAppend.innerHTML.indexOf(element.outerHTML) == -1) {
                                        targetAppend.appendChild(element);
                                    }
                                }
                            }
                        }
                    }
                    if (pushState) {
                        window.history.pushState({url: url, title: document.title}, document.title, url);
                    }
                })
                .then(() => {
                    window.dispatchEvent(new Event('load'));
                    if (scrollOnFinish) {
                        var scrollToElement;
                        if (requestURL.hash.length > 1) {
                            scrollToElement = document.getElementById(requestURL.hash.substring(1));
                        }
                        if (!scrollToElement) {
                            scrollToElement = target;
                        }
                        if (typeof scrollToElement.scrollIntoView === 'function') {
                            scrollToElement.scrollIntoView({behavior: 'smooth'});
                        }
                    }
                })
                .catch((error) => {
                    console.error('AJAX ERROR:', error);
                    document.location = requestURL.href;
                });
            }.bind(container);
            
            document.body.addToEventHandlers('click.ajax.mode', (event) => {
                // Ensure target is a link.
                var eventTarget = event.target.closest('a');
                if (!!eventTarget) {
                    if (typeof eventTarget.dataset.noAjax !== 'undefined') return;
                    if (event.ctrlKey || event.altKey || event.shiftKey) return;
                    if (eventTarget.host != document.location.host) return;
                    if (!!eventTarget.href && eventTarget.getAttribute('href').indexOf('#') === 0) return;
                    if (eventTarget.protocol.indexOf('http') !== 0) return;
                    event.preventDefault();
                    container.loadContent(eventTarget);
                }
                // Add other handlers here);
            });
            
            window.addToEventHandlers('popstate.ajax.mode', (event) => {
                if (!!event.state) {
                    if (!!event.state.url) {
                        container.loadContent(event.state.url, false);
                    }
                }
            });
            
            window.history.replaceState({url: document.location.href, title: document.title}, document.title);
        }
        return container;
    };
    
    this.modal = document.createElement('div');
    this.modal.open = function(content) {
        if (!this.classList.contains('messy-modal')) {
            // Opening for first time, do init.
            this.classList.add('messy-modal');
            this.wrapper = document.createElement('div');
            this.wrapper.classList.add('messy-modal-wrapper', 'messy-d-none');
            document.body.append(this.wrapper);
            this.wrapper.append(this);
            
            // Close popup and resolve promise with value
            this.close = function(value) {
                this.show(false);
                if (typeof this._resolve === 'function') {
                    this._resolve(value);
                }
            }.bind(this);
            
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
            
            this.show = function(show) {
                if (show) {
                    this.wrapper.classList.replace('messy-d-none', 'messy-d-block');
                    this.wrapper.style.height = `${document.body.scrollHeight}px`;
                    // Center
                    this.centerVertically(window).centerHorizontally(window);
                } else {
                    this.wrapper.classList.replace('messy-d-block', 'messy-d-none');
                }
            }.bind(this);
        } // if was not "messy-modal" class (end of init on first time invokation)
        
        if (!!content) {
            this.innerHTML = '';
            if (typeof content == 'object') {
                this.append(content);
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
    }.bind(this.modal);
    
    this.waitForSuccess = function(callback, times, period) {
        if (!period) period = 100; // 100 ms
        if (!times) times = 10; // Try 10 times.
        var count = 0;
        
        return new Promise((resolve, reject) => {
            function retry() {
                if (count > times) {
                    reject(`Tried ${count} times with no success.`);
                } else {
                    var result = callback();
                    if (!!result) {
                        resolve(result);
                    } else {
                        setTimeout(retry, period);
                        count ++;
                    }
                }
            }
            retry();
        });
    }.bind(this);
    
    this.loadScript = function(src, type) {
        if (!type) type = 'text/javascript';
        var script = document.createElement('script');
        if (!script.promise) {
            script.promise = new Promise((resolve, reject) => {
                script.setAttribute('type', type);
                script.setAttribute('src', src);
                script.addEventListener('load', resolve.bind(script)); // binding doesn't work here :(
                document.body.append(script);
            });
        }
        return script.promise;
    }.bind(this);
    
    /**
     * Load and execute script only once.
     * @param scring|object src   Script URL or script object.
     * @param string type   script type
     * @return object       Promose object which is fulfilled when script is loaded.
     */
    this.requireScript = function(src, type) {
        var script;
        if (typeof src === 'string') {
            script = document.querySelector(`[src$="${src}"]`);
        }
        else if (typeof src === 'object' && src.tagName == 'SCRIPT') {
            script = src;
            src = script.src;
            
            if (!script.type || script.type.toLowerCase() == 'text/javascript') {
                if (!!script.src) {
                    return this.requireScript(script.src, script.type);
                } else {
                    eval.apply(window, [script.innerText]);
                }
            }
            
            return new Promise((resolve, reject) => {
                resolve({type: 'load', target: script});
            });
        }
        
        var promise;
        if (!script) {
            promise = this.loadScript(src, type);
        }
        else if (!!script.promise) {
            // Already loaded by this.loadScript
            promise = script.promise;
        }
        else {
            // Loaded not by this.loadScript
            promise = new Promise((resolve, reject) => {
                resolve({type: 'load', target: script});
            });
        }
        return promise;
    }.bind(this);
    
    this.storage = new function() {
        this.get = function(name, defaultVal) {
            var result;
            if (typeof defaultVal == 'undefined') {
                defaultVal = null;
            }
            try {
                result = window.localStorage.getItem(name);
            }
            catch (error) {
                console.error('Local Storage:', error);
            }
            if (!result) {
                result = defaultVal;
            }
            return result;
        }.bind(this.storage);
        this.set = function(name, value) {
            try {
                window.localStorage.setItem(name, value);
            }
            catch(error) {
                console.error('Local Storage:', error);
            }
        }.bind(this.storage);
        this.delete = function(name) {
            try {
                window.localStorage.removeItem(name);
            }
            catch (error) {
                console.error('Local Storage:', error);
            }
        }.bind(this.storage);
    };
};
