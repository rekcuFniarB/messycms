/**
 * MessyCMS  https://github.com/rekcuFniarB/messycms#readme
 * License:  MIT
 */
function MessyCMSAdmin() {
    var This = this;
    this.typeField = document.getElementById('id_type');
    this.contentField = document.getElementById('id_content');
    this.form = document.getElementById('node_form');
    this.baseURL = (function(){
        var urlParts = document.location.pathname.split('/MessyCMS/node');
        var URL = '';
        if (urlParts.length > 1) {
            URL = [urlParts[0], '/MessyCMS/node/'].join('');
        }
        return URL;
    })();
    
    this.field = (function(field) {
        return document.getElementById(`id_${field}`);
    }).bind(this);
    
    this.show = function(element, show) {
        if (typeof show === 'undefined') show = true;
        
        var hideStyle = 'visibility: hidden; width: 0; height: 0; padding: 0; margin: 0;';
        var elementStyle = element.getAttribute('style');
        if (!elementStyle) elementStyle = '';
        elementStyle = elementStyle.replace(hideStyle, '');
        if (!show) {
            elementStyle = `${elementStyle} ${hideStyle}`;
        }
        element.setAttribute('style', elementStyle.trim());
    }
    
    this.setHelp = function(row, value) {
        let help = row.querySelector('.help');
        if (!help && !!value) {
            help = document.createElement('div');
            help.classList.add('help');
            row.children[0].append(help);
        }
        
        if (help) {
            if (help.getAttribute('data-origin-content') === null) {
                help.setAttribute('data-origin-content', help.textContent);
            }
            if (!!value) {
                help.textContent = value;
            } else {
                // Restore
                help.textContent = help.getAttribute('data-origin-content');
            }
        }
    };
    
    this.setLabel = function(row, value) {
        let label = row.querySelector('label');
        if (label.getAttribute('data-origin-content') === null) {
            label.setAttribute('data-origin-content', label.textContent);
        }
        if (!!value) {
            label.textContent = value;
        } else {
            // Restore
            label.textContent = label.getAttribute('data-origin-content');
        }
    };
    
    this.fieldsToggleMaps = undefined;
    
    this.toggleFields = function(event, fieldsToggleMaps) {
        if (typeof fieldsToggleMaps === 'undefined') {
            // Get fields maps for curreyt type
            fetch(`${this.baseURL}fields-toggle-maps.json?field=${This.typeField.value}`).then((response) => {
                return response.json();
            }).then((data) => {
                This.toggleFields(event, data);
            });
            // Run request and exit. This function will be called again when request is complete.
            return;
        }
        
        var fieldsRows = this.form.querySelectorAll('.form-row');
        
        if (typeof fieldsToggleMaps[this.typeField.value] === 'object' && fieldsToggleMaps[this.typeField.value].length) {
            for (let row of fieldsRows) {
                let filteredRows = fieldsToggleMaps[this.typeField.value].filter((item) => {
                    if (typeof item === 'object') {
                        return row.classList.contains(`field-${item.field}`);
                    } else {
                        return row.classList.contains(`field-${item}`);
                    }
                });
                
                if (filteredRows.length) {
                    var fieldConf = filteredRows[0];
                    // If field definition has special title.
                    if (typeof fieldConf === 'object') {
                        if (!!fieldConf.label) {
                            this.setLabel(row, `${fieldConf.label}:`);
                        }
                        if (!!fieldConf.help) {
                            this.setHelp(row, fieldConf.help);
                        }
                    } else {
                        this.setLabel(row, false);
                        this.setHelp(row, false);
                    }
                    this.show(row, true);
                }
                else {
                    // No definition for this field, hide it.
                    this.show(row, false);
                }
            }
        } else {
            // No definition for current type, reset all fields visibility.
            for (let row of fieldsRows) {
                this.setLabel(row, false);
                this.setHelp(row, false);
                this.show(row, true);
            }
        }
        
        var shortField = this.field('short');
        if (event.target.value == '.modelItem' && !shortField.clickEventAdded) {
            shortField.addEventListener('click', this.selectModel);
            shortField.clickEventAdded = true;
        }
    }; // toggleFields()
    
    this.selectModel = (function(event) {
        if (this.typeField.value == '.modelItem') {
            var parsedValue = event.target.value.split('=');
            var urlParams = parsedValue.join('/');
            if (!!urlParams) {
                urlParams += '/';
            }
            fetch(`${This.baseURL}select-model-modal/${urlParams}`).then((response) => {
                return response.text();
            }).then((response) => {
                // Open modal with response
                this.messy.modal.open(response).then(this.updateSelectModelField);
                var modelField = this.field('model_name');
                if (modelField && !modelField.eventAdded) {
                    modelField.addEventListener('change', this.onModelSelect);
                    modelField.eventAdded = true;
                }
            }).catch((error) => {
                console.error(error);
                this.messy.modal.open(error);
            });
        }
    }).bind(this);
    
    this.onModelSelect = (function(event) {
        var valueField = this.field('short');
        var oldValues = valueField.value.split('=');
        oldValues[0] = event.target.value;
        valueField.value = oldValues.join('=');
        
        if (!!event.target.value) {
            // Triggering click event to refresh popup content.
            valueField.click();
        }
    }).bind(this);
    
    this.updateSelectModelField = (function(target){
        var modelField = this.field('model_name');
        var modelItemIdField = this.field('model_item_id');
        var values = [];
        if (modelField && modelItemIdField) {
            values = [modelField.value, modelItemIdField.value];
        }
        var valueField = this.field('short');
        valueField.value = values.join('=');
        valueField.focus();
    }).bind(this);
    
    this.toggleWysiwyg = function(event) {
        if (event.target.checked) {
            if (typeof This.contentField.wysiwyg === 'undefined') {
                This.contentField.wysiwyg = null;
                tinyMCE.init({
                    //mode: "textareas",
                    theme: "silver",
                    selector: `#${This.contentField.id}`,
                    plugins: 'link,image',
                    menubar: 'file edit view format insert tools',
                    link_list: `${This.baseURL}nodes-links.json`,
                    convert_urls: false,
                    //toolbar: 'link',
                    //default_link_target: '_blank',
                    //plugins: "spellchecker,directionality,paste,searchreplace",
                    //language: "{{ language }}",
                    //directionality: "{{ directionality }}",
                    //spellchecker_languages : "{{ spellchecker_languages }}",
                    //spellchecker_rpc_url : "{{ spellchecker_rpc_url }}"
                }).then((data) => {
                    This.contentField.wysiwyg = data[0];
                    //document.querySelector('.tox-notification__dismiss').click();
                });
            } else {
                // Already initialized
                tinyMCE.execCommand('mceToggleEditor', true, This.contentField.id);
            }
        } else {
            // Uncheck event
            tinyMCE.execCommand('mceToggleEditor', false, This.contentField.id);
        }
    };
    
    this.toggleAvailable = function(event) {
        if (event.target.nodeName == 'IMG') {
            // Availability indicator icon was clicked
            var pk = null
            var tr = event.target.parentElement.parentElement;
            if (tr.nodeName == 'TR') {
                var node = tr.querySelector('[data-pk]');
                if (node) {
                    pk = node.dataset.pk
                }
            }
            if (pk) {
                var csrf = '';
                var csrfField = document.querySelector('[name="csrfmiddlewaretoken"]');
                if (csrfField) {
                    csrf = csrfField.value;
                }
                fetch(`${This.baseURL}toggle-available/${pk}/`, {
                    method: 'POST',
                    body: new URLSearchParams(`csrfmiddlewaretoken=${csrf}`)
                }).then((response) => {
                    try {
                        return response.json();
                    } catch (error) {
                        console.error('ERROR:', error);
                    }
                }).then((data) => {
                    fetch(This.baseURL).then((response) => { return response.text(); }).then((content) => {
                        var newContent = document.createElement('div');
                        newContent.innerHTML = content;
                        var newNode = newContent.querySelector(`[data-pk="${pk}"]`)
                        if (newNode) {
                            newTr = newNode.parentElement.parentElement;
                            if (newTr.nodeName == 'TR') {
                                // Updating old tr
                                tr.innerHTML = newTr.innerHTML;
                            }
                        }
                    });
                }).catch((error) => {
                    console.error(error);
                });
            }
        }
    }; // toggleAvailable()
    
    if (this.typeField) {
        this.typeField.addEventListener('change', (event) => {this.toggleFields(event);});
        
        //fetch(`${this.baseURL}fields-toggle-maps.json`).then((response) => {
        //    return response.json();
        //}).then((data) => {
        //    This.fieldsToggleMaps = data;
        //    This.toggleFields();
        //});
        this.toggleFields({target: this.typeField});
    }
    
    if (typeof window.tinymce === 'object' && this.contentField) {
        this.toggleWysiwygCheckbox = document.getElementById('id_toggle_wysiwyg');
        if (!this.toggleWysiwygCheckbox) {
            let toggleWysiwygCheckboxHtml = `<input type="checkbox" id="id_toggle_wysiwyg">
            <label class="vCheckboxLabel" for="id_toggle_wysiwyg">WYSIWYG</label>`;
            let checkboxWrap = document.createElement('div');
            checkboxWrap.classList.add('checkbox-row');
            checkboxWrap.innerHTML = toggleWysiwygCheckboxHtml;
            this.contentField.after(checkboxWrap);
            this.toggleWysiwygCheckbox = document.getElementById('id_toggle_wysiwyg');
            this.toggleWysiwygCheckbox.addEventListener('change', this.toggleWysiwyg);
        }
    }
    
    // Checking if we are at right pate
    var tAvailable = document.querySelector('#result_list .field-available img')
    if (tAvailable) {
        document.getElementById('result_list').addEventListener('click', this.toggleAvailable);
    }
    
    // Select parent node ID
    var curUrlParams = new URLSearchParams(document.location.search);
    var filterParams = curUrlParams.get('_changelist_filters');
    if  (!!filterParams) {
        filterParams = new URLSearchParams(filterParams);
        var filterQ = filterParams.get('q');
        if (!!filterQ) {
            var parentId = parseInt(filterQ.replace('parentId', '').replace('sections', ''));
            if (!!parentId) {
                var parentIdField = this.field('parent');
                if (!!parentIdField && parentIdField.nodeName == 'SELECT' && !parentIdField.value) {
                    parentIdField.value = parentId;
                }
            }
        }
    }
    
    // Add buttons FIXME consider doing it in templates rather than here.
    var curLink = document.querySelector('.app-MessyCMS.current-app a[aria-current]');
    if (!!curLink && document.location.href.indexOf('/change/')) {
        // If edit form
        var objectTools = document.querySelector('#content-main .object-tools');
        var curId = document.querySelector('.field-id .readonly');
        
        if (!!objectTools && curId && curId.innerText) {
            var newLi;
            newLi = document.createElement('li');
            newLi.childA = document.createElement('a');
            newLi.append(newLi.childA);
            newLi.childA.href = `${curLink.href}?q=sections${curId.innerText}`;
            newLi.childA.innerText = 'Properties';
            objectTools.prepend(newLi);
            newLi = document.createElement('li');
            newLi.childA = document.createElement('a');
            newLi.append(newLi.childA);
            newLi.childA.href = `${curLink.href}?q=parentId${curId.innerText}`;
            newLi.childA.innerText = 'Children';
            objectTools.prepend(newLi);
        }
    }
}

window.addEventListener('load', function() {
    if (typeof MessyCMSAdmin.instance === 'undefined') {
        MessyCMSAdmin.instance = new MessyCMSAdmin();
    }
    if (typeof MessyCMSAdmin.instance.messy === 'undefined') {
        MessyCMSAdmin.instance.messy = new MessyCMS();
    }
});
