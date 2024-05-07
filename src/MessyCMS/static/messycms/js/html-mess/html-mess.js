/**
 * HTML Mess  https://github.com/rekcuFniarB/messycms/tree/master/src/MessyCMS/static/messycms/js/html-mess#readme
 * License:  MIT
 */

class HtmlMess {
    // Postprocess cycle imit
    // for preventing infinite loop
    postprocessCycleLimit = 15;
    ajaxModeSelect = '';
    ajaxModeTarget = '';
    // Event name which will trigger postprocessing
    postprocessEvent = 'load';
    templates = {};
    methods = [
        'includeUrl',
        'applyFunction',
        'removeElement',
        'insertAfter',
        'insertBefore',
        'appendChild',
        'wrapElement',
        'removeClasses',
        'addClasses',
    ];
    plugins = {};
    
    constructor(conf) {
        const This = this;
        
        if (typeof conf === 'object') {
            Object.assign(this, conf)
        }
        
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
        
        if (this.ajaxModeTarget) {
            let target;
            if (typeof this.ajaxModeTarget === 'string') {
                target = document.querySelector(this.ajaxModeTarget);
            }
            else {
                target = this.ajaxModeTarget;
            }
            
            if (target?.tagName && target.isConnected && !target.dataset.ajaxMode) {
                target.dataset.ajaxMode = 'true';
                
                document.addToEventHandlers('click.ajax.mode', (event) => {
                    // Ensure target is a link.
                    var eventTarget = event.target.closest('a');
                    if (eventTarget) {
                        if (typeof eventTarget.dataset.noAjax !== 'undefined') return;
                        if (event.ctrlKey || event.altKey || event.shiftKey) return;
                        if (eventTarget.host != document.location.host) return;
                        if (!!eventTarget.href && eventTarget.getAttribute('href').indexOf('#') === 0) return;
                        if (eventTarget.protocol.indexOf('http') !== 0) return;
                        if (eventTarget.target && eventTarget.target != '_self') return;
                        event.preventDefault();
                        This.loadContent(eventTarget);
                    }
                });
                
                document.addToEventHandlers('submit.ajax.mode', (event) => {
                    // Ensure target is a form.
                    var eventTarget = event.target.closest('form');
                    if (eventTarget) {
                        if (typeof eventTarget.dataset.noAjax !== 'undefined') return;
                        if (event.ctrlKey || event.altKey || event.shiftKey) return;
                        let actionUrl = new URL(eventTarget.action);
                        if (actionUrl.host != document.location.host) return;
                        if (actionUrl.protocol.indexOf('http') !== 0) return;
                        event.preventDefault();
                        This.loadContent(event);
                    }
                    // Add other handlers here);
                });
                
                window.addToEventHandlers('popstate.ajax.mode', (event) => {
                    if (!!event.state) {
                        if (!!event.state.url) {
                            let loadReady = This.loadContent(event.state.url, false, !event.state.scrollState);
                            // Restoring scroll state
                            loadReady.then(() => {
                                if (event.state.scrollState) {
                                    document.scrollingElement.scrollTop = event.state.scrollState;
                                }
                                if (event.state.title) {
                                    document.title = event.state.title;
                                }
                            });
                        }
                    }
                });
                
                // Current state on init
                window.history.replaceState({
                    url: document.location.href,
                    title: document.title,
                    scrollState: document.scrollingElement.scrollTop
                }, document.title);
            }
        }
        
        if (this.postprocessEvent) {
            window.addEventListener(this.postprocessEvent, event => this.postprocessAll(event));
        }
        
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
    } // constructor()
    
    /**
     * Load content via ajax
     * @param url <a> element or event or similar object
     * @param bool pushState enable push states (default true)
     * @param bool scrollOnFinish scroll to loaded content (default true)
     * @return Promise
     */
    loadContent(url, pushState, scrollOnFinish) {
        let eTarget = {dataset: {}};
        let target = null;
        let form = null;
        let event = null;
        const This = this;
        
        if (typeof url === 'object') {
            if (!url.href && url.target && url.type && url.currentTarget) {
                // Is event
                event = url;
                url = event.target;
            }
            
            if (url.tagName == 'FORM') {
                form = url;
                eTarget = form;
                url = url.action;
            }
            else {
                if (!url.href) {
                    return console.error('ERROR: loadContent(): object has no "href" param', url);
                }
                eTarget = url;
                url = url.href;
            }
        }
        
        if (typeof pushState === 'undefined') pushState = true;
        if (typeof scrollOnFinish === 'undefined') scrollOnFinish = true;
        
        // If we want to load result into some other container
        if (eTarget.dataset?.target) {
            if (eTarget.dataset.target.tagName) {
                // We can fake <a> element for some purposes
                target = eTarget.dataset.target;
            }
            else {
                target = document.querySelector(eTarget.dataset.target);
            }
            if (!target) {
                return console.error(`ERROR: AJAX target '${eTarget.dataset.target}' not found.`);
            }
            pushState = false;
        }
        
        if (!target) {
            if (typeof this.ajaxModeTarget == 'string') {
                target = document.querySelector(this.ajaxModeTarget);
            }
            else {
                target = this.ajaxModeTarget;
            }
        }
        
        if (!target) {
            target = document.querySelector('main') || document.body;
            console.error('WARNING: ajax mode target was not found and set to ', target);
        }
        
        let requestURL = new URL(url, document.location.href);
        let requestConf = {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            method: 'GET',
        };
        
        if (form) {
            requestURL.href = event?.submitter?.formaction || form.action;
            requestConf.method = (event?.submitter?.formmethod || form.method || 'get').toUpperCase();
        }
        if (requestConf.method == 'GET') {
            // requestURL.searchParams.set('metadata', 'yes');
            if (form) {
                for (let [k, v] of (new FormData(form)).entries()) {
                    requestURL.searchParams.append(k, v);
                }
                if (event?.submitter?.value && event?.submitter?.name) {
                    requestURL.searchParams.set(event?.submitter?.name, event?.submitter?.value);
                }
            }
        }
        else {
            requestConf.body = new FormData(form);
            if (event?.submitter?.value && event?.submitter?.name) {
                requestConf.body.set(event?.submitter?.name, event?.submitter?.value);
            }
            pushState = false;
            scrollOnFinish = false;
        }
        
        if (pushState) {
            // Refreshing current state
            window.history.replaceState({
                url: document.location.href,
                title: document.title,
                scrollState: document.scrollingElement.scrollTop
            }, document.title);
        }
        
        if (eTarget.dataset.modifyRequest) {
            const modifyRequest =
                this.constructor.getValueByName(eTarget.dataset.modifyRequest);
            if (typeof modifyRequest === 'function') {
                const modified = modifyRequest(requestURL, requestConf, eTarget);
                requestURL = modified.requestURL || requestURL;
                requestConf = modified.requestConf || requestConf;
                eTarget = modified.eTarget || eTarget;
            }
        }
        
        document.body.classList.add('loading');
        return fetch(requestURL.href, requestConf)
        .then(response => {
            let contentType = response.headers.get('content-type');
            if (
                // If no custom handler
                // and response is not text
                !eTarget.dataset.handler
                && contentType.indexOf('text') === -1
            ) {
                throw new Error(`ERROR: bad content type for ajax response from ${requestURL.href}: ${contentType}`);
            }
            
            if (contentType.indexOf('json') > -1) {
                return response.json();
            }
            else {
                return response.text();
            }
        })
        .then(response => {
            if (eTarget.dataset.handler) {
                // Continue with custom handler if defined.
                let handler = this.constructor.getValueByName(eTarget.dataset.handler);
                if (typeof handler === 'function') {
                    return handler({url: requestURL, response: response, event: event || {target: eTarget}});
                }
            }
            
            let responseHtml;
            let responseChildrenSelector = eTarget.dataset.selectChildren || This.ajaxModeSelect;
            if (responseChildrenSelector) {
                // Instead inserting whole response,
                // we should select particular elements
                // from the response.
                responseHtml =
                    This.constructor.getHtmlFromTemplate(response);
                
                let foundById = false;
                // If there is selector '[id]', updating only
                // elements with matching id's
                if (responseChildrenSelector.indexOf('[id]') !== -1) {
                    for (let el of responseHtml.querySelectorAll('[id]')) {
                        let old = target.querySelector(`#${el.id}`);
                        if (!old && target.id == el.id) {
                            old = target;
                        }
                        if (old) {
                            foundById = true;
                            old.parentElement.insertBefore(el, old);
                            old.remove();
                        }
                    }
                }
                
                if (!foundById) {
                    target.innerHTML = '';
                    for (let el of responseHtml.querySelectorAll(responseChildrenSelector)) {
                        target.appendChild(el);
                    }
                }
            }
            else {
                target.innerHTML = response;
            }
            
            let metadata = this.constructor.getMetadata(requestURL.pathname, target);
            if (!!metadata.title) {
                document.title = metadata.title;
            }
            else {
                // Workaround if we accidentally got full html
                responseHtml = responseHtml
                    || This.constructor.getHtmlFromTemplate(response);
                let title = responseHtml.querySelector('title');
                if (title) {
                    document.title = title.textContent;
                }
            }
            
            for (let script of target.querySelectorAll('script')) {
                // Executing new scripts
                if (script.closest('noscript')) {
                    continue;
                }
                This.loadScript(script);
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
                            if (!element.closest('noscript')) {
                                This.requireScript(script);
                            }
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
                window.history.pushState({
                    url: url,
                    title: document.title
                }, document.title, url);
            }
            
            return response;
        })
        .then(response => {
            let loadEvent = new Event('load', {bubbles: true, cancelable: true});
            document.dispatchEvent(loadEvent);
            window.dispatchEvent(loadEvent);
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
            
            const result = {url: requestURL, response: response, event: event || {target: eTarget}};
            if (eTarget.dataset.onSuccess) {
                let callback = This.constructor.getValueByName(eTarget.dataset.onSuccess);
                if (typeof callback === 'function') {
                    callback(result);
                }
            }
            return result;
        })
        .catch((error) => {
            console.error('AJAX ERROR:', error);
            if (!eTarget?.dataset?.target) {
                document.location = requestURL.href;
            }
        }).finally(() => {
            document.body.classList.remove('loading');
        });
    }
    
    /**
     * This updates page title and other things
     * for ajax mode. Needs support from backend.
     */
    static getMetadata(path, target) {
        if (!target) {
            target = document;
        }
        
        if (!target.querySelector || !target.isConnected) {
            return {};
        }
        
        let metadataContainer;
        if (path) {
            metadataContainer = target.querySelector(`script.section-metadata[data-path="${path}"]`);
        } else {
            metadataContainer = target.querySelector('script.section-metadata');
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
    }
    
    static waitForSuccess(callback, times, period) {
        const This = this;
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
    } // waitForSuccess()
    
    loadScript(src, type) {
        const This = this;
        if (typeof document.alreadyLoadedScripts !== 'object') {
            document.alreadyLoadedScripts = [];
        }
        
        if (!type) type = 'text/javascript';
        var script = document.createElement('script');
        if (!script.promise) {
            script.promise = new Promise((resolve, reject) => {
                const inject = function(script, srcScript) {
                    if (srcScript && srcScript.parentElement) {
                        srcScript.parentElement.insertBefore(script, srcScript);
                    } else {
                        document.body.appendChild(script);
                    }
                };
                
                if (typeof src === 'object' && src.tagName == 'SCRIPT') {
                    // For scripts injected by AJAX response
                    for (let attr of src.attributes) {
                        script.setAttribute(attr.name, attr.value);
                    }
                    script.innerHTML = src.innerHTML;
                    script.originScript = src;
                } else {
                    script.setAttribute('type', type);
                    script.setAttribute('src', src);
                }
                
                if (script.src) {
                    if (document.alreadyLoadedScripts.indexOf(script.src) > -1) {
                        return resolve({target: script.originScript || script, type: 'load'});
                    }
                    document.alreadyLoadedScripts.push(script.src);
                }
                
                script.addEventListener('load', resolve.bind(script)); // binding doesn't work here :(
                inject(script, src);
            });
        }
        return script.promise;
    } // loadScript()
    
    /**
     * Load and execute script only once.
     * @param scring|object src   Script URL or script object.
     * @param string type   script type
     * @return object       Promose object which is fulfilled when script is loaded.
     */
    requireScript(src, type) {
        const This = this;
        var script;
        if (typeof src === 'string') {
            script = document.querySelector(`[src$="${src}"]`);
        }
        else if (typeof src === 'object' && src.tagName == 'SCRIPT') {
            script = src;
            src = script.src;
            
            if (!script.type || ['text/javascript', 'module'].indexOf(script.type.toLowerCase()) > -1) {
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
    } // requireScript()
    
    /**
     * const SomeObject = {subObject: {value: 'my value'}}
     * getValueByName('SomeObject.subObject.value')
     *   will return 'my value'
     * @param name Can by path like SomeObject.subObject.value
     * @return mixed
     */
    static getValueByName(name) {
        if (!name || typeof name !== 'string') {
            return name;
        }
        return name.split('.').reduce((obj, key) => obj?.[key], window);
    }
    
    // Special variant of querySelectorAll
    static qsAll(selector, start) {
        // Special selector 'foo < bar'
        // it selects 'foo' only if contains 'bar'
        let parts = selector.split('<');
        parts = parts.map(x => x.trim());
        
        start = start || document;
        let elements = start.querySelectorAll(parts.pop());
        let closestSelector;
        while (closestSelector = parts.pop()) {
            let closestElements = [];
            for (let e of elements) {
                e = e?.closest(closestSelector);
                if (e) {
                    closestElements.push(e);
                }
            }
            elements = closestElements;
        }
        
        return new Set(elements);
    }
    
    async loadTemplates(path) {
        const templates = this.constructor.getHtmlFromTemplate(
            await fetch(path)
                .then(response => response.text())
        );
        
        const templatesList = {};
        for (let template of templates.querySelectorAll('template,script[type="text/html"]')) {
            if (!template.id) continue;
            this.templates[template.id] = template;
            templatesList[template.id] = template;
        }
        
        window.dispatchEvent(new Event(this.postprocessEvent, {bubbles: true, cancelable: true}));
        return templatesList;
    }
    
    postprocessAll(event) {
        const results = [];
        if (document.body.classList.contains('htmlmess-processing')) {
            results.push(true);
            return false;
        }
        document.body.classList.add('htmlmess-processing');
        document.body.classList.remove('htmlmess-processing-done');
        if (!this._htmlPostprocessCount) {
            this._htmlPostprocessCount = 0;
        }
        this._htmlPostprocessCount ++;
        
        // Converting all methods to kebab-case names
        // for [data-method-name]
        let dataSelectors = [];
        for (let x of this.methods) {
            if (typeof this[x] === 'function') {
                x = x.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
                x = `[data-${x}]`;
                dataSelectors.push(x);
            }
        }
        
        for (let template of document.querySelectorAll(
            dataSelectors.join(',')
        )) {
            for (let e of this.constructor.getElementsToProcess(template)) {
                // Processing elements on page first
                // e.g. usually non <template> elements
                // if they have rules too
                // like <div data-include-url="...">
                let r = this.processTemplate(e, e);
                if (window.DEBUG || this.DEBUG) {
                    console.log('DEBUG: processing', e, r);
                }
                results.push(...r);
            }
        }
        
        for (let template of Object.values(this.templates)) {
            for (let e of this.constructor.getElementsToProcess(template)) {
                let r = this.processTemplate(e, template);
                if (window.DEBUG || this.DEBUG) {
                    console.log('DEBUG: processing', e, template, r);
                }
                results.push(...r);
            }
        }
        
        // Methods can be async by returning promise
        return Promise.all(results)
            .then(results => {
                if (window.DEBUG || this.DEBUG) {
                    console.log('DEBUG: proc results', results);
                }
                document.body.classList.remove('htmlmess-processing');
                document.body.classList.add('htmlmess-processing-done');
                
                // If any of results have non empty value
                if (results.some(x => x)) {
                    if (this._htmlPostprocessCount > this.postprocessCycleLimit) {
                        this._htmlPostprocessCount = 0;
                        console.error(`ERROR: postprocess limit ${this.postprocessCycleLimit} reached, you need to find what causes infinite loop.`, results);
                    }
                    else {
                        // Second pass untill nothing found to process
                        window.dispatchEvent(
                            new Event(this.postprocessEvent),
                            {cancelable: true, bubbles: true}
                        );
                    }
                }
                else {
                    this._htmlPostprocessCount = 0;
                }
                return results;
            })
            .finally(() => {
                // document.body.classList.remove('htmlmess-processing');
                // document.body.classList.add('htmlmess-processing-done');
            });
    }
    
    processTemplate(element, template) {
        const results = [];
        
        if (
            template.dataset.ifSelector
            && !this.constructor.qsAll(template.dataset.ifSelector).size
        ) {
            // data-if-selector defined and no result
            // for that selector
            return results;
        }
        
        if (
            template.dataset.notIfSelector
            && this.constructor.qsAll(template.dataset.notIfSelector).size
        ) {
            // data-not-if-selector defined
            // and  there is result for that selector
            return results;
        }
        
        for (let f in template.dataset) {
            if (
                typeof this[f] === 'function'
                && this.methods.indexOf(f) > -1
            ) {
                let result = this[f](element, template);
                if (
                    result && (this.DEBUG || window.DEBUG)
                    && typeof result.then === 'undefined'
                ) {
                    let r = {};
                    r[`#${template.id} ${f}()`] = result;
                    result = r;
                }
                results.push(result);
            }
        }
        
        return results;
    }
    
    static getElementsToProcess(template) {
        let elements = [];
        
        if (template.dataset.select) {
            let dataGet = this.getValueByName(template.dataset.select);
            if (typeof dataGet === 'function') {
                elements = dataGet(template);
                if (
                    typeof elements.length === 'undefined'
                    && typeof elements.size === 'undefined'
                ) {
                    elements = [elements];
                }
                if (typeof elements[0].querySelector === 'undefined') {
                    // Not html element
                    return elements;
                }
            }
            else {
                elements = [...this.qsAll(template.dataset.select)];
            }
        }
        else {
            // Use self
            if (['TEMPLATE', 'SCRIPT'].indexOf(template.tagName) > -1) {
                elements = [...this.getHtmlFromTemplate(template).children];
            }
            else {
                elements = [template];
            }
        }
        
        if (template.dataset.closest) {
            // Moving upper to this selector
            elements = elements.map(x =>
                x.closest(template.dataset.closest))
                .filter(x => x);
            elements = [...new Set(elements)];
        }
        
        if (template.dataset.hasParent) {
            // Removing element from the set
            // if it hasn't parent with selector
            // data-has-parent
            elements = elements.filter(x =>
                x.closest(template.dataset.hasParent));
        }
        
        if (template.dataset.hasNotParent) {
            // Removing element from the set
            // if it has parent with selector 'data-has-not-parent'
            elements = elements.filter(x =>
                !x.closest(template.dataset.hasNotParent));
        }
        
        if (template.dataset.hasChildren) {
            // Keeping only elements which have children
            // with selector data-has-children
            elements = elements.filter(x =>
                x.querySelector(template.dataset.hasChildren));
        }
        
        if (template.dataset.hasNotChildren) {
            // Keeping only elements which haven't
            // children with selector data-has-not-children
            elements = elements.filter(x =>
                !x.querySelector(template.dataset.hasNotChildren));
        }
        
        return elements;
    }
    
    includeUrl(element, template) {
        if (!template.dataset.includeUrl) {
            return false;
        }
        
        return this.loadContent(
            {
                // Faking <a> element
                href: template.dataset.includeUrl,
                dataset: Object.assign({
                    target: template
                }, template.dataset)
            },
            // no pushState, no scroll into element
            false, false
        ).then(response => {
            // Not to process next time.
            template.dataset.includedUrl = template.dataset.includeUrl;
            template.dataset.includeUrl = '';
            return response;
        });
    }
    
    addClasses(element, template) {
        if (!element.tagName) return false;
        
        let changed = false;
        let length = element.classList.length;
        let classes = template.dataset.addClasses.split(' ');
        classes = classes.filter(c => c);
        if (!classes.length) {
            return false;
        }
        element.classList.add(...classes);
        return length < element.classList.length;
    }
    
    removeClasses(element, template) {
        if (!element.tagName) return false;
        
        let changed = false;
        let length = element.classList.length;
        let classes = template.dataset.removeClasses.split(' ');
        classes = classes.filter(c => c);
        if (!classes.length) {
            return false;
        }
        element.classList.remove(...classes);
        return length > element.classList.length;
    }
    
    wrapElement(element, template) {
        if (!element.tagName) return false;
        
        const wrapper = this.constructor.getHtmlFromTemplate(template);
        let target = wrapper.querySelector('[data-insert]');
        if (!target) return false;
        
        // Inserting wrapper before element
        for (let c of wrapper.children) {
            element.parentElement.insertBefore(c, element);
        }
        
        // If should use content only
        if (typeof template.dataset.stripHtml !== 'undefined') {
            target.textContent = element.textContent;
            element.remove();
        }
        // Or insert as is
        else {
            target.appendChild(element);
        }
        
        return target;
    }
    
    appendChild(element, template) {
        if (!element.tagName) return false;
        
        let target = this.constructor.qsAll(
            template.dataset.appendChild
            || template.dataset.insertBefore
            || template.dataset.insertAfter
        ).values().next().value;
        if (!target) return false;
        
        if (template.dataset.replace) {
            let existing = this.constructor.qsAll(template.dataset.replace, target)
                .values().next().value;
            if (existing) {
                existing.remove();
            }
        }
        
        // Should clone
        if (typeof template.dataset.clone !== 'undefined') {
            element = this.constructor.getHtmlFromTemplate(element).children[0];
        }
        
        if (template.dataset.insertBefore) {
            target.parentElement.insertBefore(element, target);
        }
        else if (template.dataset.insertAfter) {
            if (target.nextSibling) {
                target.parentElement.insertBefore(element, target.nextSibling);
            }
            else {
                target.parentElement.appendChild(element);
            }
        }
        else {
            target.appendChild(element);
        }
        return element;
    }
    
    insertBefore(element, template) {
        return this.appendChild(element, template);
    }
    
    insertAfter(element, template) {
        return this.appendChild(element, template);
    }
    
    removeElement(element, template) {
        if (typeof element.remove !== 'function') return false;
        
        return element.remove();
    }
    
    applyFunction(element, template) {
        let method = this.constructor.getValueByName(template.dataset.applyFunction);
        if (typeof method === 'function') {
            return method(element, template);
        }
    }
    
    /**
     * Makes HTML elements from template.
     * @param template can be string of html
     *   or <template> element.
     * @return HTMLElement with content from template.
     */
    static getHtmlFromTemplate(template) {
        if (template?.tagName) {
            template = template.innerHTML;
        }
        return Object.assign(document.createElement('div'), {
            innerHTML: template || ''
        });
    }
    
    /**
     * Get elemet selector.
     * @param element HTMLElement
     * @param string selector if need seletor relative to parents.
     * @return string
     */
    static getElementSelector(element, parents) {
        if (element.id) {
            return `#${element.id}`;
        }
        
        let selectors = [element.tagName.toLowerCase()];
        selectors.push(...element.classList);
        
        if (
            parents && element.parentElement
        ) {
            if (element.parentElement.closest(parents) == element.parentElement) {
                parents = null;
            }
            
            return [
                this.getElementSelector(element.parentElement, parents),
                selectors.join('.')
            ].join(' > ');
        }
        else {
            return selectors.join('.');
        }
    }
    
    registerPlugin(plugin, conf) {
        const plug = new plugin(conf, this);
        this.plugins[plug.name] = plug;
        
        this[plug.name] = (element, template) => {
            return plug.method(element, template);
        };
        
        this.methods.push(plug.name);
    }
} // class HtmlMess
