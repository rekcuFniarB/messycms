/**
 * HTML Mess  https://github.com/rekcuFniarB/messycms/tree/master/src/MessyCMS/static/messycms/js/html-mess#readme
 * License:  MIT
 * 
 * Plugin for HtmlMess
 * Takes all elements <noscript data-sanitize-element></noscript>,
 * applies DOMPurify.sanitize and inserts sanitized html into page.
 */

class HtmlMessSanitizeElementPlugin {
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
                    html = DOMPurify.sanitize(html.trim());
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
