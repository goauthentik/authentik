(function () {
    var $$ = {
        on: function(root, eventName, selector, fn) {
            root.addEventListener(eventName, function(event) {
                var target = event.target.closest(selector);
                if (root.contains(target)) {
                    fn.call(target, event);
                }
            });
        },
        show: function(element) {
            element.style.display = 'block';
        },
        hide: function(element) {
            element.style.display = 'none';
        },
        toggle: function(element, value) {
            if (value) {
                $$.show(element);
            } else {
                $$.hide(element);
            }
        },
        visible: function(element) {
            style = getComputedStyle(element);
            return style.display !== 'none';
        },
        executeScripts: function(root) {
            root.querySelectorAll('script').forEach(function(e) {
                var clone = document.createElement('script');
                clone.src = e.src;
                root.appendChild(clone);
            });
        },
    };

    var onKeyDown = function(event) {
        if (event.keyCode == 27) {
            djdt.hide_one_level();
        }
    };

    var ajax = function(url, init) {
        init = Object.assign({credentials: 'same-origin'}, init);
        return fetch(url, init).then(function(response) {
            if (response.ok) {
                return response.text();
            } else {
                var win = document.querySelector('#djDebugWindow');
                win.innerHTML = '<div class="djDebugPanelTitle"><a class="djDebugClose djDebugBack" href=""></a><h3>'+response.status+': '+response.statusText+'</h3></div>';
                $$.show(win);
                return Promise.reject();
            }
        });
    };

    var djdt = {
        handleDragged: false,
        events: {
            ready: []
        },
        isReady: false,
        init: function() {
            var djDebug = document.querySelector('#djDebug');
            $$.show(djDebug);
            $$.on(djDebug.querySelector('#djDebugPanelList'), 'click', 'li a', function(event) {
                event.preventDefault();
                if (!this.className) {
                    return;
                }
                var current = djDebug.querySelector('#' + this.className);
                if ($$.visible(current)) {
                    djdt.hide_panels();
                } else {
                    djdt.hide_panels();

                    $$.show(current);
                    this.parentElement.classList.add('djdt-active');

                    var inner = current.querySelector('.djDebugPanelContent .djdt-scroll'),
                        store_id = djDebug.getAttribute('data-store-id');
                    if (store_id && inner.children.length === 0) {
                        var url = djDebug.getAttribute('data-render-panel-url');
                        var url_params = new URLSearchParams();
                        url_params.append('store_id', store_id);
                        url_params.append('panel_id', this.className);
                        url += '?' + url_params.toString();
                        ajax(url).then(function(body) {
                            inner.previousElementSibling.remove();  // Remove AJAX loader
                            inner.innerHTML = body;
                            $$.executeScripts(inner);
                        });
                    }
                }
            });
            $$.on(djDebug, 'click', 'a.djDebugClose', function(event) {
                event.preventDefault();
                djdt.hide_one_level();
            });
            $$.on(djDebug, 'click', '.djDebugPanelButton input[type=checkbox]', function() {
                djdt.cookie.set(this.getAttribute('data-cookie'), this.checked ? 'on' : 'off', {
                    path: '/',
                    expires: 10
                });
            });

            // Used by the SQL and template panels
            $$.on(djDebug, 'click', '.remoteCall', function(event) {
                event.preventDefault();

                var name = this.tagName.toLowerCase();
                var ajax_data = {};

                if (name == 'button') {
                    var form = this.closest('form');
                    ajax_data.url = this.getAttribute('formaction');

                    if (form) {
                        ajax_data.body = new FormData(form);
                        ajax_data.method = form.getAttribute('method') || 'POST';
                    }
                }

                if (name == 'a') {
                    ajax_data.url = this.getAttribute('href');
                }

                ajax(ajax_data.url, ajax_data).then(function(body) {
                    var win = djDebug.querySelector('#djDebugWindow');
                    win.innerHTML = body;
                    $$.executeScripts(win);
                    $$.show(win);
                });
            });

            // Used by the cache, profiling and SQL panels
            $$.on(djDebug, 'click', 'a.djToggleSwitch', function(event) {
                event.preventDefault();
                var self = this;
                var id = this.getAttribute('data-toggle-id');
                var open_me = this.textContent == this.getAttribute('data-toggle-open');
                if (id === '' || !id) {
                    return;
                }
                var name = this.getAttribute('data-toggle-name');
                var container = this.closest('.djDebugPanelContent').querySelector('#' + name + '_' + id);
                container.querySelectorAll('.djDebugCollapsed').forEach(function(e) {
                    $$.toggle(e, open_me);
                });
                container.querySelectorAll('.djDebugUncollapsed').forEach(function(e) {
                    $$.toggle(e, !open_me);
                });
                this.closest('.djDebugPanelContent').querySelectorAll('.djToggleDetails_' + id).forEach(function(e) {
                    if (open_me) {
                        e.classList.add('djSelected');
                        e.classList.remove('djUnselected');
                        self.textContent = self.getAttribute('data-toggle-close');
                    } else {
                        e.classList.remove('djSelected');
                        e.classList.add('djUnselected');
                        self.textContent = self.getAttribute('data-toggle-open');
                    }
                    var switch_ = e.querySelector('.djToggleSwitch')
                    if (switch_) switch_.textContent = self.textContent;
                });
            });

            djDebug.querySelector('#djHideToolBarButton').addEventListener('click', function(event) {
                event.preventDefault();
                djdt.hide_toolbar(true);
            });
            djDebug.querySelector('#djShowToolBarButton').addEventListener('click', function(event) {
                event.preventDefault();
                if (!djdt.handleDragged) {
                    djdt.show_toolbar();
                }
            });
            var startPageY, baseY;
            var handle = document.querySelector('#djDebugToolbarHandle');
            var onHandleMove = function(event) {
                // Chrome can send spurious mousemove events, so don't do anything unless the
                // cursor really moved.  Otherwise, it will be impossible to expand the toolbar
                // due to djdt.handleDragged being set to true.
                if (djdt.handleDragged || event.pageY != startPageY) {
                    var top = baseY + event.pageY;

                    if (top < 0) {
                        top = 0;
                    } else if (top + handle.offsetHeight > window.innerHeight) {
                        top = window.innerHeight - handle.offsetHeight;
                    }

                    handle.style.top = top + 'px';
                    djdt.handleDragged = true;
                }
            };
            djDebug.querySelector('#djShowToolBarButton').addEventListener('mousedown', function(event) {
                event.preventDefault();
                startPageY = event.pageY;
                baseY = handle.offsetTop - startPageY;
                document.addEventListener('mousemove', onHandleMove);
            });
            document.addEventListener('mouseup', function (event) {
                document.removeEventListener('mousemove', onHandleMove);
                if (djdt.handleDragged) {
                    event.preventDefault();
                    djdt.cookie.set('djdttop', handle.offsetTop, {
                        path: '/',
                        expires: 10
                    });
                    setTimeout(function () {
                        djdt.handleDragged = false;
                    }, 10);
                }
            });
            if (djdt.cookie.get('djdt') == 'hide') {
                djdt.hide_toolbar(false);
            } else {
                djdt.show_toolbar();
            }
            djdt.isReady = true;
            djdt.events.ready.forEach(function(callback) {
                callback(djdt);
            });
        },
        hide_panels: function() {
            $$.hide(djDebug.querySelector('#djDebugWindow'));
            djDebug.querySelectorAll('.djdt-panelContent').forEach(function(e) {
                $$.hide(e);
            });
            djDebug.querySelectorAll('#djDebugToolbar li').forEach(function(e) {
                e.classList.remove('djdt-active');
            });
        },
        hide_toolbar: function(setCookie) {
            djdt.hide_panels();
            $$.hide(djDebug.querySelector('#djDebugToolbar'));

            var handle = document.querySelector('#djDebugToolbarHandle');
            $$.show(handle);
            // set handle position
            var handleTop = djdt.cookie.get('djdttop');
            if (handleTop) {
                handleTop = Math.min(handleTop, window.innerHeight - handle.offsetHeight);
                handle.style.top = handleTop + 'px';
            }

            document.removeEventListener('keydown', onKeyDown);

            if (setCookie) {
                djdt.cookie.set('djdt', 'hide', {
                    path: '/',
                    expires: 10
                });
            }
        },
        hide_one_level: function(skipDebugWindow) {
            if ($$.visible(djDebug.querySelector('#djDebugWindow'))) {
                $$.hide(djDebug.querySelector('#djDebugWindow'));
            } else if (djDebug.querySelector('#djDebugToolbar li.djdt-active')) {
                djdt.hide_panels();
            } else {
                djdt.hide_toolbar(true);
            }
        },
        show_toolbar: function() {
            document.addEventListener('keydown', onKeyDown);
            $$.hide(djDebug.querySelector('#djDebugToolbarHandle'));
            $$.show(djDebug.querySelector('#djDebugToolbar'));
            djdt.cookie.set('djdt', 'show', {
                path: '/',
                expires: 10
            });
        },
        ready: function(callback){
            if (djdt.isReady) {
                callback(djdt);
            } else {
                djdt.events.ready.push(callback);
            }
        },
        cookie: {
            get: function(key){
                if (document.cookie.indexOf(key) === -1) return null;

                var cookieArray = document.cookie.split('; '),
                    cookies = {};

                cookieArray.forEach(function(e){
                    var parts = e.split('=');
                    cookies[ parts[0] ] = parts[1];
                });

                return cookies[ key ];
            },
            set: function(key, value, options){
                options = options || {};

                if (typeof options.expires === 'number') {
                    var days = options.expires, t = options.expires = new Date();
                    t.setDate(t.getDate() + days);
                }

                document.cookie = [
                    encodeURIComponent(key) + '=' + String(value),
                    options.expires ? '; expires=' + options.expires.toUTCString() : '',
                    options.path    ? '; path=' + options.path : '',
                    options.domain  ? '; domain=' + options.domain : '',
                    options.secure  ? '; secure' : ''
                ].join('');

                return value;
            }
        },
        applyStyle: function(name) {
            var selector = '#djDebug [data-' + name + ']';
            document.querySelectorAll(selector).forEach(function(element) {
                element.style[name] = element.getAttribute('data-' + name);
            });
        }
    };
    window.djdt = {
        show_toolbar: djdt.show_toolbar,
        hide_toolbar: djdt.hide_toolbar,
        close: djdt.hide_one_level,
        cookie: djdt.cookie,
        applyStyle: djdt.applyStyle
    };
    document.addEventListener('DOMContentLoaded', djdt.init);
})();
