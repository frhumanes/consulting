!function($, wysi) {
    "use strict"

    var templates = {
        "font-styles":  "<li class='btn-group'>" +
                            "<a class='btn dropdown-toggle' data-toggle='dropdown' href='#'>" +
                                "<i class='icon-font'></i>&nbsp;<span class=''></span>&nbsp;<b class='caret'></b>" +
                            "</a>" +
                            "<ul class='dropdown-menu'>" +
                                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='div'>Normal</a></li>" +
                                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h2'>Título</a></li>" +
                                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h1'>Encabezado</a></li>" +
                            "</ul>" +
                        "</li>" +
                        "<li class='btn-group' data-wysihtml5-command-group='foreColor'>" +
                            "<a class='btn dropdown-toggle' data-toggle='dropdown' href='#'>" +
                                "<i class='icon-tint'></i>&nbsp;<span class='current-color'>&nbsp;</span>&nbsp;<b class='caret'></b>" +
                            "</a>" +
                            "<ul class='dropdown-menu'>" +
                                "<li><a data-wysihtml5-command='foreColor' data-wysihtml5-command-value='black' style='color: black'>Negro</a></li>" +
                                "<li><a data-wysihtml5-command='foreColor' data-wysihtml5-command-value='red' style='color: red'>Rojo</a></li>" +
                                "<li><a data-wysihtml5-command='foreColor' data-wysihtml5-command-value='green' style='color: green'>Verde</a></li>" +
                                "<li><a data-wysihtml5-command='foreColor' data-wysihtml5-command-value='blue' style='color: blue'>Azul</a></li>" +
                            "</ul>" +
                        "</li>",
        "emphasis":     "<li>" +
                            "<div class='btn-group'>"
                                + "<a class='btn' data-wysihtml5-command='bold' title='Negrita'>N</a>"
                                + "<a class='btn' data-wysihtml5-command='italic' title='Cursiva'>C</a>"
                                + "<a class='btn' data-wysihtml5-command='underline' title='Subrayado'>S</a>"
                            + "</div>"
                        + "</li>",
        "lists":    "<li>"
                        + "<div class='btn-group'>"
                            + "<a class='btn' data-wysihtml5-command='insertUnorderedList' title='Viñetas'><i class='icon-list'></i></a>"
                            + "<a class='btn' data-wysihtml5-command='insertOrderedList' title='Numeración'><i class='icon-th-list'></i></a>"
                            + "<a class='btn' data-wysihtml5-command='Outdent' title='Reducir sangría'><i class='icon-indent-right'></i></a>"
                            + "<a class='btn' data-wysihtml5-command='Indent' title='Aumentar sangría'><i class='icon-indent-left'></i></a>"
                        + "</div>"
                    + "</li>",

        "link":     "<li>"

                        + "<div class='bootstrap-wysihtml5-insert-link-modal modal hide fade'>"
                            + "<div class='modal-header'>"
                            + "<a class='close' data-dismiss='modal'>&times;</a>"
                              + "<h3>Insertar hiperenlace</h3>"
                            + "</div>"
                            + "<div class='modal-body'>"
                              + "<input value='http://' class='bootstrap-wysihtml5-insert-link-url input-xlarge'>"
                            + "</div>"
                            + "<div class='modal-footer'>"
                              + "<a href='#' class='btn' data-dismiss='modal'>Cancelar</a>"
                              + "<a href='#' class='btn btn-primary' data-dismiss='modal'>Insertar</a>"
                            + "</div>"
                        + "</div>"

                        + "<a class='btn' data-wysihtml5-command='createLink' title='Link'><i class='icon-share'></i></a>"

                    + "</li>",

            "image": "<li>"

                        + "<div class='bootstrap-wysihtml5-insert-image-modal modal hide fade'>"
                            + "<div class='modal-header'>"
                            + "<a class='close' data-dismiss='modal'>&times;</a>"
                              + "<h3>Insert Image</h3>"
                            + "</div>"
                            + "<div class='modal-body'>"
                              + "<input value='http://' class='bootstrap-wysihtml5-insert-image-url input-xlarge'>"
                            + "</div>"
                            + "<div class='modal-footer'>"
                              + "<a href='#' class='btn' data-dismiss='modal'>Cancel</a>"
                              + "<a href='#' class='btn btn-primary' data-dismiss='modal'>Insert image</a>"
                            + "</div>"
                        + "</div>"

                        + "<a class='btn' data-wysihtml5-command='insertImage' title='Insert image'><i class='icon-picture'></i></a>"

                    + "</li>",

        "html":
                        "<li>"
                            + "<div class='btn-group'>"
                                + "<a class='btn' data-wysihtml5-action='change_view' title='Edit HTML'><i class='icon-pencil'></i></a>"
                            + "</div>"
                        + "</li>"
    };

    var defaultOptions = {
        "font-styles": true,
        "emphasis": true,
        "lists": true,
        "html": false,
        "link": true,
        "image": true,
        events: {},
        parserRules: {
            classes: {
                "wysiwyg-color-black": 1,
                "wysiwyg-color-blue": 1,
                "wysiwyg-color-green": 1,
                "wysiwyg-color-red": 1
              },
            tags: {
                "b":  {},
                "i":  {},
                "br": {},
                "ol": {},
                "ul": {},
                "li": {},
                "h1": {},
                "h2": {},
                "u": 1,
                "font": {
                    "rename_tag": "span",
                    "add_class": {
                        "size": "size_font"
                    }
                },
                "img": {
                    "check_attributes": {
                        "width": "numbers",
                        "alt": "alt",
                        "src": "url",
                        "height": "numbers"
                    }
                },
                "a":  {
                    set_attributes: {
                        target: "_blank",
                        rel:    "nofollow"
                    },
                    check_attributes: {
                        href:   "url" // important to avoid XSS
                    }
                }
            }
        },
        stylesheets: []
    };

    var Wysihtml5 = function(el, options) {
        this.el = el;
        this.toolbar = this.createToolbar(el, options || defaultOptions);
        this.editor =  this.createEditor(options);

        window.editor = this.editor;

        $('iframe.wysihtml5-sandbox').each(function(i, el){
            $(el.contentWindow).off('focus.wysihtml5').on({
              'focus.wysihtml5' : function(){
                 $('li.dropdown').removeClass('open');
               }
            });
        });
    };

    Wysihtml5.prototype = {
        constructor: Wysihtml5,

    createEditor: function(options) {
      var parserRules = defaultOptions.parserRules;
      var stylesheets = defaultOptions.stylesheets;

      if(options && options.parserRules) {
        parserRules = options.parserRules;
      }

      if (options && options.stylesheets) {
        stylesheets = options.stylesheets;
      }

      var editor = new wysi.Editor(this.el.attr('id'), {
        toolbar: this.toolbar.attr('id'),
        parserRules: parserRules,
        stylesheets: stylesheets
      });

      if(options && options.events) {
        for(var eventName in options.events) {
          editor.on(eventName, options.events[eventName]);
        }
      }

      return editor;
    },

        createToolbar: function(el, options) {
            var self = this;
            var toolbar = $("<ul/>", {
                'id' : el.attr('id') + "-wysihtml5-toolbar",
                'class' : "wysihtml5-toolbar",
                'style': "display:none"
            });

            for(var key in defaultOptions) {
                var value = false;

                if(options[key] != undefined) {
                    if(options[key] == true) {
                        value = true;
                    }
                } else {
                    value = defaultOptions[key];
                }

                if(value == true) {
                    toolbar.append(templates[key]);

                    if(key == "html") {
                        this.initHtml(toolbar);
                    }

                    if(key == "link") {
                        this.initInsertLink(toolbar);
                    }

                    if(key == "image") {
                        this.initInsertImage(toolbar);
                    }
                }
            }

            var self = this;

            toolbar.find("a[data-wysihtml5-command='formatBlock']").click(function(e) {
                var el = $(e.srcElement);
                self.toolbar.find('.current-font').text($(this).html())
            });
            toolbar.find("a[data-wysihtml5-command='foreColor']").click(function(e) {
                var el = $(e.srcElement);
                self.toolbar.find('.current-color').css('color', $(this).css('color'))
            });

            this.el.before(toolbar);

            return toolbar;
        },

        initHtml: function(toolbar) {
            var changeViewSelector = "a[data-wysihtml5-action='change_view']";
            toolbar.find(changeViewSelector).click(function(e) {
                toolbar.find('a.btn').not(changeViewSelector).toggleClass('disabled');
            });
        },

        initInsertImage: function(toolbar) {
            var self = this;
            var insertImageModal = toolbar.find('.bootstrap-wysihtml5-insert-image-modal');
            var urlInput = insertImageModal.find('.bootstrap-wysihtml5-insert-image-url');
            var insertButton = insertImageModal.find('a.btn-primary');
            var initialValue = urlInput.val();

            var insertImage = function() {
                var url = urlInput.val();
                urlInput.val(initialValue);
                self.editor.composer.commands.exec("insertImage", url);
            };

            urlInput.keypress(function(e) {
                if(e.which == 13) {
                    insertImage();
                    insertImageModal.modal('hide');
                }
            });

            insertButton.click(insertImage);

            insertImageModal.on('shown', function() {
                urlInput.focus();
            });

            insertImageModal.on('hide', function() {
                self.editor.currentView.element.focus();
            });

            toolbar.find('a[data-wysihtml5-command=insertImage]').click(function() {
                insertImageModal.modal('show');
                return false;
            });
        },

        initInsertLink: function(toolbar) {
            var self = this;
            var insertLinkModal = toolbar.find('.bootstrap-wysihtml5-insert-link-modal');
            var urlInput = insertLinkModal.find('.bootstrap-wysihtml5-insert-link-url');
            var insertButton = insertLinkModal.find('a.btn-primary');
            var initialValue = urlInput.val();

            var insertLink = function() {
                var url = urlInput.val();
                urlInput.val(initialValue);
                self.editor.composer.commands.exec("createLink", {
                    href: url,
                    target: "_blank",
                    rel: "nofollow"
                });
            };
            var pressedEnter = false;

            urlInput.keypress(function(e) {
                if(e.which == 13) {
                    insertLink();
                    insertLinkModal.modal('hide');
                }
            });

            insertButton.click(insertLink);

            insertLinkModal.on('shown', function() {
                urlInput.focus();
            });

            insertLinkModal.on('hide', function() {
                self.editor.currentView.element.focus();
            });

            toolbar.find('a[data-wysihtml5-command=createLink]').click(function() {
                insertLinkModal.modal('show');
                return false;
            });
        }
    };

    $.fn.wysihtml5 = function (options) {
        return this.each(function () {
            var $this = $(this);
            $this.data('wysihtml5', new Wysihtml5($this, options));
        })
    };

    $.fn.wysihtml5.Constructor = Wysihtml5;

}(window.jQuery, window.wysihtml5);
