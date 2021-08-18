function MessyCMSAdmin() {
    var This = this;
    this.typeField = document.getElementById('id_type');
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
    
    this.toggleFields = function() {
        if (!this.fieldsToggleMaps) return;
        
        var fieldsRows = this.form.querySelectorAll('.form-row');
        
        if (typeof this.fieldsToggleMaps[this.typeField.value] !== 'undefined') {
            for (let row of fieldsRows) {
                let filteredRows = this.fieldsToggleMaps[this.typeField.value].filter((item) => {
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
    
    if (this.typeField) {
        this.typeField.addEventListener('change', (event) => {this.toggleFields();});
        
        fetch(`${this.baseURL}fields-toggle-maps.json`).then((response) => {
            return response.json();
        }).then((data) => {
            This.fieldsToggleMaps = data;
            This.toggleFields();
        });
    }
}

window.addEventListener('load', function() {
    MessyCMSAdmin.instance = new MessyCMSAdmin();
});
