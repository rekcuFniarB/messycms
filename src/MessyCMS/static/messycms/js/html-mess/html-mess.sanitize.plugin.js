/**
 * HTML Mess  https://github.com/rekcuFniarB/messycms/tree/master/src/MessyCMS/static/messycms/js/html-mess#readme
 * License:  MIT
 * 
 * Plugin for HtmlMess
 * Takes all elements <noscript data-sanitize-element></noscript>,
 * applies DOMPurify.sanitize and inserts sanitized html into page.
 */

class HtmlMessSanitizePlugin {
    name = 'sanitizeElement';
    domPurifySrc = '';
    
    constructor(conf, parent) {
        Object.assign(this, conf || {});
        this.parent = parent;
    }
    
    method(element, template) {
        return this.parent.requireScript(this.domPurifySrc)
            .then(() => {
                if (typeof DOMPurify?.sanitize === 'function') {
                    let html = '';
                    if (['TEMPLATE', 'SCRIPT', 'NOSCRIPT'].indexOf(element.tagName) > -1) {
                        html = element.innerHTML;
                    }
                    else {
                        html = element.outerHTML;
                    }
                    
                    const config = {
                        ALLOW_DATA_ATTR: false,
                        ALLOW_ARIA_ATTR: false,
                        FORBID_TAGS: ['style', 'svg', 'mathml', 'object']
                    };
                    
                    if (template.dataset.forbidAttr) {
                        config.FORBID_ATTR = template.dataset.forbidAttr
                            .split(',')
                            .map(x => x.trim())
                            .filter(x => x);
                    }
                    
                    if (template.dataset.forbidTags) {
                        config.FORBID_TAGS = template.dataset.forbidTags
                            .split(',')
                            .map(x => x.trim())
                            .filter(x => x);
                    }
                    
                    html = DOMPurify.sanitize(html.trim(), config);
                    
                    let sanitizedNodes =
                        [...this.parent.constructor.getHtmlFromTemplate(html).childNodes];
                    for (let node of sanitizedNodes) {
                        element.parentElement.insertBefore(node, element);
                    }
                    // Removing source element
                    element.remove();
                    element = null;
                    return true;
                }
                else {
                    console.error('ERROR: no html sanitize method defined.');
                }
            });
    }
}
