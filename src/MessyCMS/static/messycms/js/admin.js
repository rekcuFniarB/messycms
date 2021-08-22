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
    
    this.toggleFields = function(fieldsToggleMaps) {
        if (typeof fieldsToggleMaps === 'undefined') {
            // Get fields maps for curreyt type
            fetch(`${this.baseURL}fields-toggle-maps.json?field=${This.typeField.value}`).then((response) => {
                return response.json();
            }).then((data) => {
                This.toggleFields(data);
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
    }; // toggleFields()
    
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
    
    if (this.typeField) {
        this.typeField.addEventListener('change', (event) => {this.toggleFields();});
        
        //fetch(`${this.baseURL}fields-toggle-maps.json`).then((response) => {
        //    return response.json();
        //}).then((data) => {
        //    This.fieldsToggleMaps = data;
        //    This.toggleFields();
        //});
        this.toggleFields();
    }
    
    if (typeof window.tinymce === 'object') {
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
}

window.addEventListener('load', function() {
    MessyCMSAdmin.instance = new MessyCMSAdmin();
});
