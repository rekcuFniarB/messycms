/**
 * HTML Mess  https://github.com/rekcuFniarB/messycms/tree/master/src/MessyCMS/static/messycms/js/html-mess#readme
 * License:  MIT
 * 
 * Handlebars templates plugin for HtmlMess.
 */

class HtmlMessHandlebarsPlugin {
    name = 'handlebars';
    handlebarsSrc = '';
    
    constructor(conf, parent) {
        Object.assign(this, conf || {});
        this.parent = parent;
    }
    
    method(data, template) {
        if (typeof window.Handlebars?.compile === 'function') {
            if (!template._hb_tpl_render) {
                template._hb_tpl_render = Handlebars.compile(template.innerHTML);
            
                // Compiling all templates once if not compiled yet.
                for (let t in this.parent.templates) {
                    if (typeof this.parent.templates[t].dataset.handlebars !== 'undefined') {
                        if (!this.parent.templates[t]._hb_tpl_render) {
                            this.parent.templates[t]._hb_tpl_render =
                                Handlebars.compile(this.parent.templates[t].innerHTML);
                        }
                    }
                    else if (typeof this.parent.templates[t].dataset.handlebarsPartial !== 'undefined') {
                        if (!Handlebars.partials[template.id]) {
                            Handlebars.registerPartial(this.parent.templates[t].id, this.parent.templates[t].innerHTML);
                        }
                    }
                }
            }
            
            let promise = data;
            if (typeof promise.then !== 'function') {
                promise = new Promise((resolve, reject) => {
                    resolve(data);
                });
            }
            
            return promise.then(data => {
                let html = template._hb_tpl_render(data);
                let tpl = document.createElement('div');
                tpl.innerHTML = template.outerHTML;
                // Getting copy of template
                tpl = tpl.children[0];
                tpl.id = '';
                delete tpl.dataset.select;
                delete tpl.dataset.handlebars;
                tpl.innerHTML = html;
                
                let results = [];
                // Processing all other rules if defined
                for (let e of this.parent.constructor.getElementsToProcess(tpl)) {
                    let r = this.parent.processTemplate(e, tpl);
                    results.push(...r);
                }
                
                return Promise.all(results)
                    .then(results => {
                        if (results.some(x => x)) {
                            return tpl;
                        }
                        return false;
                    });
            });
        }
        else {
            console.error('ERROR: Handlebars init failed.');
        }
    }
}

if (typeof HtmlMess?.knownPlugins?.handlebars === 'undefined') {
    HtmlMess.knownPlugins.handlebars = HtmlMessHandlebarsPlugin;
}
